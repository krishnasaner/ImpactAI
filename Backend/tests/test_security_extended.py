"""
Phase B.5 — Extended Security Tests.

CSRF enforcement, expired tokens, refresh replay detection,
cross-user access prevention, rate limiting, and security headers.
"""

import hashlib
import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db, UserRow, SessionRow, RefreshTokenRow, MoodEntryRow
from services.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
    issue_csrf_token,
)
from tests.conftest import test_engine, TestingSessionLocal


class ExtendedSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)

    def setUp(self):
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)
        self.db = TestingSessionLocal()

        self.user_a = UserRow(
            email="usera@test.com",
            hashed_password=hash_password("ValidPassword123!"),
            role="student",
            name="User A",
            created_at=datetime.now(timezone.utc),
        )
        self.user_b = UserRow(
            email="userb@test.com",
            hashed_password=hash_password("ValidPassword123!"),
            role="student",
            name="User B",
            created_at=datetime.now(timezone.utc),
        )
        self.counselor = UserRow(
            email="counselor2@test.com",
            hashed_password=hash_password("ValidPassword123!"),
            role="counselor",
            name="Counselor",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add_all([self.user_a, self.user_b, self.counselor])
        self.db.commit()

        self.token_a = create_access_token({
            "sub": str(self.user_a.id),
            "email": self.user_a.email,
            "role": "student",
        })
        self.token_b = create_access_token({
            "sub": str(self.user_b.id),
            "email": self.user_b.email,
            "role": "student",
        })
        self.token_counselor = create_access_token({
            "sub": str(self.counselor.id),
            "email": self.counselor.email,
            "role": "counselor",
        })

    def tearDown(self):
        self.db.close()

    # ── CSRF Tests ─────────────────────────────────────────────────────────

    def test_csrf_missing_on_authenticated_post(self):
        """POST with auth cookie but no CSRF token → 403."""
        # Set access_token cookie but no CSRF cookie/header
        self.client.cookies.set("access_token", self.token_a)
        # Clear CSRF cookie
        self.client.cookies.delete("csrf_token")
        res = self.client.post("/mood", json={"mood": "happy"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("CSRF", res.json().get("message", ""))
        self.client.cookies.clear()

    def test_csrf_invalid_on_authenticated_post(self):
        """POST with auth cookie and garbage CSRF → 403."""
        csrf = issue_csrf_token()
        self.client.cookies.set("access_token", self.token_a)
        self.client.cookies.set("csrf_token", csrf)
        # Send a DIFFERENT value in the header
        res = self.client.post(
            "/mood",
            json={"mood": "happy"},
            headers={"X-CSRF-Token": "garbage_invalid_token"},
        )
        self.assertEqual(res.status_code, 403)
        self.client.cookies.clear()

    def test_csrf_valid_on_authenticated_post(self):
        """POST with correct CSRF cookie + header → passes CSRF check."""
        csrf = issue_csrf_token()
        self.client.cookies.set("access_token", self.token_a)
        self.client.cookies.set("csrf_token", csrf)
        res = self.client.post(
            "/mood",
            json={"mood": "happy"},
            headers={"X-CSRF-Token": csrf},
        )
        # Should pass CSRF and proceed (200 since Bearer token also works)
        # But since we set the cookie not Bearer, the route may need Bearer
        # Let's use Authorization header instead
        self.client.cookies.clear()

        # Proper test: Bearer auth + CSRF cookie + header match
        self.client.cookies.set("access_token", self.token_a)
        self.client.cookies.set("csrf_token", csrf)
        res = self.client.post(
            "/mood",
            json={"mood": "happy"},
            headers={
                "Authorization": f"Bearer {self.token_a}",
                "X-CSRF-Token": csrf,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.client.cookies.clear()

    # ── Expired Token Tests ────────────────────────────────────────────────

    def test_expired_access_token_rejected(self):
        """Request with expired access token → 401."""
        expired_token = create_access_token(
            {"sub": str(self.user_a.id), "email": self.user_a.email, "role": "student"},
            expires_minutes=-5,  # Expired 5 minutes ago
        )
        res = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        self.assertEqual(res.status_code, 401)

    # ── Refresh Token Replay Detection ─────────────────────────────────────

    def test_revoked_refresh_token_triggers_replay_detection(self):
        """Using an already-revoked refresh token → all sessions revoked."""
        session_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        db_session = SessionRow(
            user_id=self.user_a.id,
            session_id=session_id,
            expires_at=expires_at,
            is_active=1,
            remember_me=1,
        )
        self.db.add(db_session)
        self.db.commit()

        refresh_tok = create_refresh_token(
            {"sub": str(self.user_a.id), "session_id": session_id},
            timedelta(days=7),
        )
        token_hash = hashlib.sha256(refresh_tok.encode("utf-8")).hexdigest()
        self.db.add(RefreshTokenRow(
            user_id=self.user_a.id,
            session_id=session_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=1,  # Already revoked
        ))
        self.db.commit()

        self.client.cookies.set("refresh_token", refresh_tok)
        res = self.client.post("/auth/refresh")
        self.assertEqual(res.status_code, 401)
        self.assertIn("revoked", res.json()["detail"].lower())
        self.client.cookies.clear()

    # ── Cross-User Access Prevention ───────────────────────────────────────

    def test_user_b_cannot_access_user_a_moods(self):
        """User B requesting mood history → sees only their own (empty)."""
        # Create mood for User A
        mood_entry = MoodEntryRow(
            user_id=self.user_a.id,
            mood="sad",
            note="Private mood",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(mood_entry)
        self.db.commit()

        # User B requests mood history
        res = self.client.get(
            "/mood/history",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(res.status_code, 200)
        # User B should see 0 moods (only their own, which is empty)
        self.assertEqual(res.json()["count"], 0)

    def test_student_cannot_access_db_stats(self):
        """Student role → 403 on /analytics/db-stats."""
        res = self.client.get(
            "/analytics/db-stats",
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        self.assertEqual(res.status_code, 403)

    def test_counselor_can_access_db_stats(self):
        """Counselor role → 200 on /analytics/db-stats."""
        res = self.client.get(
            "/analytics/db-stats",
            headers={"Authorization": f"Bearer {self.token_counselor}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("total_users", res.json())

    # ── Security Headers ───────────────────────────────────────────────────

    def test_security_headers_present(self):
        """Verify all security headers are set on responses."""
        res = self.client.get("/health")
        headers = res.headers

        self.assertIn("content-security-policy", headers)
        self.assertIn("x-content-type-options", headers)
        self.assertEqual(headers["x-content-type-options"], "nosniff")
        self.assertIn("x-frame-options", headers)
        self.assertEqual(headers["x-frame-options"], "DENY")
        self.assertIn("strict-transport-security", headers)
        self.assertIn("referrer-policy", headers)
        self.assertIn("permissions-policy", headers)

    # ── Rate Limiting Test ─────────────────────────────────────────────────

    def test_login_rate_limiting(self):
        """Exceeding login rate limit → 429 with Retry-After."""
        # Send many rapid login attempts (rate limit: 10 per IP per 60s for login_email)
        got_429 = False
        for i in range(15):
            res = self.client.post("/auth/login", json={
                "email": "ratelimit@test.com",
                "password": "WrongPass123!",
            })
            if res.status_code == 429:
                got_429 = True
                self.assertIn("Retry-After", res.headers)
                break

        self.assertTrue(got_429, "Expected 429 rate limit to trigger within 15 login attempts")


if __name__ == "__main__":
    unittest.main()
