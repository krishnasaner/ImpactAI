"""
Phase B.2 — Crisis Detection Validation Test Suite.

Tests the deterministic crisis detection layer, ML predictions,
fallback severity preservation, and pipeline safety guarantees.
"""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db, UserRow
from services.security import hash_password, create_access_token
from routes.chat import detect_deterministic_crisis
from services.groq_client import get_fallback
from tests.conftest import test_engine, TestingSessionLocal


class TestDeterministicCrisisDetection(unittest.TestCase):
    """Unit tests for the regex-based crisis detection function."""

    # ── Explicit suicidal intent (must detect) ─────────────────────────────
    def test_explicit_kill_myself(self):
        self.assertTrue(detect_deterministic_crisis("I want to kill myself"))

    def test_explicit_end_life(self):
        self.assertTrue(detect_deterministic_crisis("I'm going to end my life tonight"))

    def test_explicit_suicide_word(self):
        self.assertTrue(detect_deterministic_crisis("I am thinking about suicide"))

    def test_explicit_suicidal(self):
        self.assertTrue(detect_deterministic_crisis("I feel suicidal"))

    # ── Indirect suicidal ideation (should detect if pattern matches) ──────
    def test_indirect_no_point_living(self):
        self.assertTrue(detect_deterministic_crisis("I don't want to live anymore"))

    def test_indirect_better_off_dead(self):
        self.assertTrue(detect_deterministic_crisis("Everyone would be better off dead without me"))

    def test_indirect_no_reason_to_live(self):
        self.assertTrue(detect_deterministic_crisis("There is no reason to live"))

    # ── Self-harm statements ───────────────────────────────────────────────
    def test_cutting_wrists(self):
        self.assertTrue(detect_deterministic_crisis("I've been cutting my wrists"))

    def test_overdose(self):
        self.assertTrue(detect_deterministic_crisis("I overdosed on pills last night"))

    def test_take_all_pills(self):
        self.assertTrue(detect_deterministic_crisis("I want to take all my pills"))

    def test_hang_myself(self):
        self.assertTrue(detect_deterministic_crisis("I want to hang myself"))

    def test_jump_off_bridge(self):
        self.assertTrue(detect_deterministic_crisis("I'm thinking of jumping off a bridge"))

    def test_shoot_myself(self):
        self.assertTrue(detect_deterministic_crisis("I want to shoot myself"))

    # ── Historical references (may or may not trigger — document behavior) ─
    def test_historical_attempt(self):
        # "suicide" substring is in "attempted suicide" → should trigger
        result = detect_deterministic_crisis("I attempted suicide last year but I'm better now")
        self.assertTrue(result, "Historical suicide mention triggers because 'suicid' pattern matches")

    # ── Negation (documents known false positives) ─────────────────────────
    def test_negation_not_suicidal(self):
        # "I am NOT suicidal" contains "suicidal" → triggers (known false positive)
        result = detect_deterministic_crisis("I am NOT suicidal")
        self.assertTrue(result, "Negation false positive: 'suicidal' in 'NOT suicidal' triggers detection")

    def test_negation_dont_want_to_die(self):
        # This may NOT trigger because "want to die" is a pattern but
        # "don't want to" may confuse — depends on exact regex
        # "I don't want to kill myself" → "kill myself" matches
        result = detect_deterministic_crisis("I don't want to kill myself")
        self.assertTrue(result, "Negation false positive: 'kill myself' triggers despite negation")

    # ── Ambiguous statements (should NOT trigger) ──────────────────────────
    def test_ambiguous_exam_killing(self):
        self.assertFalse(detect_deterministic_crisis("This exam is killing me"))

    def test_ambiguous_dying_of_boredom(self):
        self.assertFalse(detect_deterministic_crisis("I'm dying of boredom"))

    def test_ambiguous_dead_tired(self):
        self.assertFalse(detect_deterministic_crisis("I'm dead tired from studying all night"))

    # ── Ordinary academic stress (should NOT trigger) ──────────────────────
    def test_stress_finals(self):
        self.assertFalse(detect_deterministic_crisis("I'm stressed about finals"))

    def test_stress_cant_sleep(self):
        self.assertFalse(detect_deterministic_crisis("I can't sleep before exams"))

    def test_stress_overwhelmed(self):
        self.assertFalse(detect_deterministic_crisis("I feel overwhelmed with assignments"))

    # ── Depression without crisis language (should NOT trigger) ────────────
    def test_depression_sad_lonely(self):
        self.assertFalse(detect_deterministic_crisis("I feel really sad and lonely"))

    def test_depression_worthless(self):
        self.assertFalse(detect_deterministic_crisis("I feel worthless and nobody cares about me"))

    def test_depression_crying(self):
        self.assertFalse(detect_deterministic_crisis("I've been crying all day and can't stop"))


class TestFallbackCrisisSeverity(unittest.TestCase):
    """Verify fallback responses preserve crisis severity and include helplines."""

    def test_service_error_crisis_fallback(self):
        fb = get_fallback("service_error", is_crisis=True)
        self.assertEqual(fb["severity"], "crisis")
        self.assertTrue(any("14416" in s for s in fb["suggestions"]))

    def test_timeout_crisis_fallback(self):
        fb = get_fallback("timeout", is_crisis=True)
        self.assertEqual(fb["severity"], "crisis")
        self.assertTrue(any("14416" in s for s in fb["suggestions"]))

    def test_missing_config_crisis_fallback(self):
        fb = get_fallback("missing_config", is_crisis=True)
        self.assertEqual(fb["severity"], "crisis")

    def test_rate_limit_crisis_fallback(self):
        fb = get_fallback("rate_limit", is_crisis=True)
        self.assertEqual(fb["severity"], "crisis")

    def test_non_crisis_fallback_low(self):
        fb = get_fallback("service_error", is_crisis=False)
        self.assertEqual(fb["severity"], "low")

    def test_non_crisis_no_helplines(self):
        fb = get_fallback("timeout", is_crisis=False)
        self.assertFalse(any("14416" in s for s in fb["suggestions"]))


class TestCrisisPipelineIntegration(unittest.TestCase):
    """Integration tests: crisis severity cannot be downgraded through the pipeline."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)

    def setUp(self):
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)
        db = TestingSessionLocal()
        self.user = UserRow(
            email="crisis_test@test.com",
            hashed_password=hash_password("ValidPassword123!"),
            role="student",
            name="CrisisTestUser",
        )
        db.add(self.user)
        db.commit()
        db.refresh(self.user)
        self.token = create_access_token({
            "sub": str(self.user.id),
            "email": self.user.email,
            "role": "student",
        })
        db.close()

    @patch("routes.chat.generate_ai_chat")
    def test_crisis_not_downgraded_by_low_llm(self, mock_ai):
        """LLM returns severity=low for crisis input → final must be crisis."""
        mock_ai.return_value = {
            "text": "Everything seems fine.",
            "severity": "low",
            "suggestions": ["Relax"],
        }
        res = self.client.post(
            "/chat",
            json={"message": "I want to kill myself right now"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["severity"], "crisis")

    @patch("routes.chat.generate_ai_chat")
    def test_crisis_not_downgraded_by_medium_llm(self, mock_ai):
        """LLM returns severity=medium for crisis input → final must be crisis."""
        mock_ai.return_value = {
            "text": "I sense you're going through something.",
            "severity": "medium",
            "suggestions": ["Talk to someone"],
        }
        res = self.client.post(
            "/chat",
            json={"message": "I'm going to end my life tonight"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["severity"], "crisis")

    @patch("routes.chat.generate_ai_chat")
    def test_non_crisis_stays_low(self, mock_ai):
        """Normal message with LLM returning low → final stays low."""
        mock_ai.return_value = {
            "text": "That sounds like a normal day.",
            "severity": "low",
            "suggestions": ["Keep going"],
        }
        res = self.client.post(
            "/chat",
            json={"message": "I had a good day at college today"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["severity"], "low")

    @patch("routes.chat.generate_ai_chat")
    def test_non_crisis_message_not_escalated(self, mock_ai):
        """Academic stress should not be flagged as crisis."""
        mock_ai.return_value = {
            "text": "Finals can be stressful.",
            "severity": "low",
            "suggestions": ["Take breaks"],
        }
        res = self.client.post(
            "/chat",
            json={"message": "I'm stressed about my final exams"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertNotEqual(res.json()["severity"], "crisis")

    @patch("routes.chat.generate_ai_chat")
    def test_llm_error_fallback_preserves_crisis(self, mock_ai):
        """When LLM throws an error on crisis input, fallback must preserve crisis severity."""
        mock_ai.side_effect = RuntimeError("Groq API down")
        res = self.client.post(
            "/chat",
            json={"message": "I want to kill myself"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["severity"], "crisis")


if __name__ == "__main__":
    unittest.main()
