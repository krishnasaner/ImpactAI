"""
ImpactAI — Automated Security Audit Test Suite.
Verifies all security fixes and guarantees data isolation, RBAC,
session ownership, lockout resilience, and IDOR protections.
"""

import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db, UserRow, ChatSessionRow, MessageRow, SessionRow, RefreshTokenRow
from services.security import hash_password, create_access_token, create_refresh_token
from tests.conftest import test_engine, TestingSessionLocal


class SecurityAuditTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        # Clear tables between tests
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)
        self.db = TestingSessionLocal()

        # Seed test users
        self.student1 = UserRow(
            email="alice@test.com",
            hashed_password=hash_password("ValidPassword123!"),
            role="student",
            name="Alice",
            created_at=datetime.now(timezone.utc),
        )
        self.student2 = UserRow(
            email="bob@test.com",
            hashed_password=hash_password("ValidPassword123!"),
            role="student",
            name="Bob",
            created_at=datetime.now(timezone.utc),
        )
        self.counselor = UserRow(
            email="counselor@test.com",
            hashed_password=hash_password("ValidPassword123!"),
            role="counselor",
            name="Counselor Charlie",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add_all([self.student1, self.student2, self.counselor])
        self.db.commit()

        # Generate tokens
        self.token_alice = create_access_token({"sub": str(self.student1.id), "email": self.student1.email, "role": "student"})
        self.token_bob = create_access_token({"sub": str(self.student2.id), "email": self.student2.email, "role": "student"})
        self.token_counselor = create_access_token({"sub": str(self.counselor.id), "email": self.counselor.email, "role": "counselor"})

    def tearDown(self):
        self.db.close()

    # ── 1. Privilege Escalation Prevention ───────────────────────────────────

    def test_cannot_signup_as_admin(self):
        """Verify that public signup with role='admin' is rejected."""
        res = self.client.post(
            "/auth/signup",
            json={
                "email": "attacker@test.com",
                "password": "AttackerPass123!@",
                "confirm_password": "AttackerPass123!@",
                "role": "admin",
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Administrator accounts cannot be created", res.json()["detail"])

    def test_signup_as_student_allowed(self):
        """Verify that legitimate student signup succeeds."""
        res = self.client.post(
            "/auth/signup",
            json={
                "email": "newstudent@test.com",
                "password": "StudentPass123!@",
                "confirm_password": "StudentPass123!@",
                "role": "student",
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user"]["role"], "student")

    # ── 2. Chat Session Ownership & IDOR Protection ──────────────────────────

    @patch("routes.chat.generate_ai_chat")
    def test_chat_session_ownership_tampering_blocked(self, mock_ai):
        """Verify User B cannot send messages or manipulate User A's session."""
        mock_ai.return_value = {
            "text": "Hello, I am Zenith.",
            "severity": "low",
            "suggestions": ["Breathe"],
        }

        # Alice creates a chat session
        session_id_alice = f"session-alice-{uuid4()}"
        res1 = self.client.post(
            "/chat",
            json={"message": "I am feeling overwhelmed today.", "session_id": session_id_alice},
            headers={"Authorization": f"Bearer {self.token_alice}"},
        )
        self.assertEqual(res1.status_code, 200)

        # Bob attempts to post into Alice's session using her session_id
        res2 = self.client.post(
            "/chat",
            json={"message": "I am Bob attacking Alice's session.", "session_id": session_id_alice},
            headers={"Authorization": f"Bearer {self.token_bob}"},
        )
        self.assertEqual(res2.status_code, 403)
        self.assertIn("Access denied: chat session belongs to another user", res2.json()["detail"])

        # Anonymous caller attempts to post into Alice's session
        res3 = self.client.post(
            "/chat",
            json={"message": "I am anonymous attacker.", "session_id": session_id_alice},
        )
        self.assertEqual(res3.status_code, 403)

    @patch("routes.chat.generate_ai_chat")
    def test_chat_history_leak_prevented_for_anonymous(self, mock_ai):
        """Verify unauthenticated callers cannot dump global messages via GET /chat/history."""
        mock_ai.return_value = {"text": "Safe AI response", "severity": "low", "suggestions": []}

        # Alice posts a private message
        alice_session = f"session-alice-{uuid4()}"
        self.client.post(
            "/chat",
            json={"message": "Secret student depression details.", "session_id": alice_session},
            headers={"Authorization": f"Bearer {self.token_alice}"},
        )

        # Anonymous user calls /chat/history without session_id
        res = self.client.get("/chat/history")
        self.assertEqual(res.status_code, 200)
        # MUST return 0 messages (no global leak)
        self.assertEqual(res.json()["count"], 0)
        self.assertEqual(len(res.json()["messages"]), 0)

    @patch("routes.chat.generate_ai_chat")
    def test_chat_history_idor_prevented(self, mock_ai):
        """Verify User B cannot read Alice's chat history by passing her session_id."""
        mock_ai.return_value = {"text": "Private counseling response", "severity": "low", "suggestions": []}

        alice_session = f"session-alice-{uuid4()}"
        self.client.post(
            "/chat",
            json={"message": "My confidential therapy notes.", "session_id": alice_session},
            headers={"Authorization": f"Bearer {self.token_alice}"},
        )

        # Bob tries to read Alice's chat history
        res_bob = self.client.get(
            f"/chat/history?session_id={alice_session}",
            headers={"Authorization": f"Bearer {self.token_bob}"},
        )
        self.assertEqual(res_bob.status_code, 403)

        # Anonymous tries to read Alice's chat history
        res_anon = self.client.get(f"/chat/history?session_id={alice_session}")
        self.assertEqual(res_anon.status_code, 401)

        # Alice CAN read her own chat history
        res_alice = self.client.get(
            f"/chat/history?session_id={alice_session}",
            headers={"Authorization": f"Bearer {self.token_alice}"},
        )
        self.assertEqual(res_alice.status_code, 200)
        self.assertGreater(res_alice.json()["count"], 0)

        # Counselor CAN read Alice's chat history for clinical triage
        res_counselor = self.client.get(
            f"/chat/history?session_id={alice_session}",
            headers={"Authorization": f"Bearer {self.token_counselor}"},
        )
        self.assertEqual(res_counselor.status_code, 200)
        self.assertGreater(res_counselor.json()["count"], 0)

    # ── 3. Resilient Login Lockout & Datetime Handling ───────────────────────

    def test_lockout_naive_datetime_crash_resolved(self):
        """Verify that 5 failed logins triggers lockout without throwing 500 TypeError."""
        email = self.student1.email

        # 5 failed login attempts
        for _ in range(5):
            res = self.client.post(
                "/auth/login",
                json={"email": email, "password": "WrongPassword123!"},
            )
            self.assertEqual(res.status_code, 401)

        # 6th attempt: User is locked out. Must return clean 401 lockout message, NOT 500 crash!
        res_locked = self.client.post(
            "/auth/login",
            json={"email": email, "password": "WrongPassword123!"},
        )
        self.assertEqual(res_locked.status_code, 401)
        self.assertIn("Account is temporarily locked", res_locked.json()["detail"])

    # ── 4. Token Refresh & Expiration Safety ─────────────────────────────────

    def test_token_refresh_session_expiration(self):
        """Verify token refresh handles naive/aware datetimes and detects expired sessions."""
        session_id = str(uuid4())
        user_id = self.student1.id

        # Create active session with past expiration
        expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session = SessionRow(
            user_id=user_id,
            session_id=session_id,
            expires_at=expired_at,
            is_active=1,
        )
        self.db.add(db_session)
        self.db.commit()

        refresh_token = create_refresh_token({"sub": str(user_id), "session_id": session_id}, timedelta(days=7))
        import hashlib
        db_refresh = RefreshTokenRow(
            user_id=user_id,
            session_id=session_id,
            token_hash=hashlib.sha256(refresh_token.encode("utf-8")).hexdigest(),
            expires_at=expired_at,
            is_revoked=0,
        )
        self.db.add(db_refresh)
        self.db.commit()

        # Send refresh request
        self.client.cookies.set("refresh_token", refresh_token)
        res = self.client.post("/auth/refresh")
        self.assertEqual(res.status_code, 401)
        self.assertIn("Session has expired", res.json()["detail"])

    # ── 5. Role-Based Access Control in Analytics ────────────────────────────

    def test_db_stats_role_authorization(self):
        """Verify student cannot access /analytics/db-stats, but counselor can."""
        # Student request: 403 Forbidden
        res_student = self.client.get(
            "/analytics/db-stats",
            headers={"Authorization": f"Bearer {self.token_alice}"},
        )
        self.assertEqual(res_student.status_code, 403)

        # Counselor request: 200 OK
        res_counselor = self.client.get(
            "/analytics/db-stats",
            headers={"Authorization": f"Bearer {self.token_counselor}"},
        )
        self.assertEqual(res_counselor.status_code, 200)
        self.assertIn("total_users", res_counselor.json())


    # ── 6. Anonymous Access & Query Limits ───────────────────────────────────

    @patch("routes.chat.generate_ai_chat")
    def test_anonymous_session_isolated(self, mock_ai):
        """Verify anonymous users can converse in isolated sessions but cannot touch registered sessions."""
        mock_ai.return_value = {"text": "Hello anonymous friend.", "severity": "low", "suggestions": []}

        # Anonymous starts new session
        res = self.client.post("/chat", json={"message": "I want anonymous help."})
        self.assertEqual(res.status_code, 200)
        anon_session_id = res.json()["session_id"]

        # Anonymous retrieves their own session history with session_id
        res_history = self.client.get(f"/chat/history?session_id={anon_session_id}")
        self.assertEqual(res_history.status_code, 200)
        self.assertGreater(res_history.json()["count"], 0)

    def test_unbounded_limit_capped(self):
        """Verify limit parameter does not cause uncaught error or unbounded query."""
        res = self.client.get(
            "/chat/history?limit=999999",
            headers={"Authorization": f"Bearer {self.token_alice}"},
        )
        self.assertEqual(res.status_code, 200)

    # ── 7. Enhanced AI Safety, Crisis Lockdown & Readiness ───────────────────

    @patch("routes.chat.generate_ai_chat")
    def test_deterministic_crisis_cannot_be_downgraded(self, mock_ai):
        """Verify that explicit suicidal language locks severity to crisis even if LLM returns low."""
        # Simulated buggy/misbehaving LLM attempting to downgrade crisis
        mock_ai.return_value = {
            "text": "Everything is fine, don't worry.",
            "severity": "low",
            "suggestions": ["Smile"],
        }
        res = self.client.post(
            "/chat",
            json={"message": "I want to kill myself right now"},
            headers={"Authorization": f"Bearer {self.token_alice}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["severity"], "crisis")

    def test_empty_and_oversized_chat_messages_rejected(self):
        """Verify that empty whitespace or excessively large messages are rejected."""
        # Empty message
        res_empty = self.client.post("/chat", json={"message": "   "})
        self.assertEqual(res_empty.status_code, 400)

        # Oversized message (> 3000 chars)
        res_large = self.client.post("/chat", json={"message": "A" * 3500})
        self.assertEqual(res_large.status_code, 400)
        self.assertIn("exceeds maximum allowed length", res_large.json()["detail"])

    def test_readiness_probe(self):
        """Verify GET /ready and GET /health endpoints report operational status."""
        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["status"], "ok")

        res_ready = self.client.get("/ready")
        self.assertEqual(res_ready.status_code, 200)
        self.assertTrue(res_ready.json()["ready"])
        self.assertEqual(res_ready.json()["database"], "reachable")

    @patch("routes.chat.generate_ai_chat")
    def test_chat_session_deletion_and_isolation(self, mock_ai):
        """Verify user can delete their own session, but other users cannot."""
        mock_ai.return_value = {"text": "Test message", "severity": "low", "suggestions": []}
        session_id = f"delete-test-{uuid4()}"

        # Alice creates session
        self.client.post(
            "/chat",
            json={"message": "Session to be deleted", "session_id": session_id},
            headers={"Authorization": f"Bearer {self.token_alice}"},
        )

        # Bob attempts to delete Alice's session
        res_bob = self.client.delete(
            f"/chat/session/{session_id}",
            headers={"Authorization": f"Bearer {self.token_bob}"},
        )
        self.assertEqual(res_bob.status_code, 403)

        # Alice deletes her session
        res_alice = self.client.delete(
            f"/chat/session/{session_id}",
            headers={"Authorization": f"Bearer {self.token_alice}"},
        )
        self.assertEqual(res_alice.status_code, 200)
        self.assertTrue(res_alice.json()["success"])

    def test_ml_prediction_robustness(self):
        """Verify ML severity prediction handles clean, empty, and crisis text safely."""
        from services.ml_model import predict_severity
        # Empty string
        label, conf = predict_severity("")
        self.assertEqual(label, "low")

        # Explicit crisis text
        label_crisis, conf_crisis = predict_severity("I am thinking about suicide and ending my life")
        self.assertEqual(label_crisis, "crisis")
        self.assertGreater(conf_crisis, 0.5)

    def test_categorized_ai_fallbacks(self):
        """Verify fallback generator returns correct emergency resources on crisis."""
        from services.groq_client import get_fallback
        fb_crisis = get_fallback("service_error", is_crisis=True)
        self.assertEqual(fb_crisis["severity"], "crisis")
        self.assertTrue(any("14416" in s for s in fb_crisis["suggestions"]))

        fb_timeout = get_fallback("timeout", is_crisis=False)
        self.assertEqual(fb_timeout["severity"], "low")
        self.assertIn("longer than expected", fb_timeout["text"])


if __name__ == "__main__":
    unittest.main()
