"""
Comprehensive automated tests for ImpactAI expanded backend modules:
- User profile & preferences
- Data export (GDPR compliance) & account deletion cascade
- Private journaling system (CRUD + search)
- Personal wellness plans & goal progress tracking
- Curated resource library & bookmarking
- Counsellor appointments workflow
- In-app notification center
- Chat session renaming, message feedback & pagination
- Admin governance & system health
"""

import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from database import Base, UserRow
from main import app
from services.security import create_access_token, hash_password
from tests.conftest import TestingSessionLocal, test_engine


class BackendExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)

    def setUp(self):
        Base.metadata.create_all(bind=test_engine)
        self.db = TestingSessionLocal()

        # Seed student user
        self.student = UserRow(
            email=f"student_{uuid4().hex[:6]}@test.com",
            hashed_password=hash_password("StudentPass123!@"),
            role="student",
            name="Alice Student",
            created_at=datetime.now(timezone.utc),
            is_verified=1,
        )
        # Seed counsellor user
        self.counsellor = UserRow(
            email=f"counselor_{uuid4().hex[:6]}@campus.edu",
            hashed_password=hash_password("CounselorPass123!@"),
            role="counselor",
            name="Dr. Taylor",
            created_at=datetime.now(timezone.utc),
            is_verified=1,
        )
        self.db.add_all([self.student, self.counsellor])
        self.db.commit()
        self.db.refresh(self.student)
        self.db.refresh(self.counsellor)

        self.student_token = create_access_token({
            "sub": str(self.student.id),
            "email": self.student.email,
            "role": "student",
        })
        self.counsellor_token = create_access_token({
            "sub": str(self.counsellor.id),
            "email": self.counsellor.email,
            "role": "counselor",
        })

    def tearDown(self):
        self.db.close()

    # ── 1. User Profile & Preferences ─────────────────────────────────────────

    def test_user_profile_get_and_update(self):
        headers = {"Authorization": f"Bearer {self.student_token}"}
        # Get profile
        res = self.client.get("/users/profile", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], self.student.email)

        # Update profile
        update_res = self.client.put(
            "/users/profile",
            json={
                "display_name": "Ali S.",
                "university": "State University",
                "major": "Computer Science",
                "student_id": "ST-98765",
                "bio": "Sophomore balancing classes and wellness.",
            },
            headers=headers,
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["display_name"], "Ali S.")
        self.assertEqual(update_res.json()["university"], "State University")

    def test_user_preferences_get_and_update(self):
        headers = {"Authorization": f"Bearer {self.student_token}"}
        # Get default preferences
        res = self.client.get("/users/preferences", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["preferred_language"], "en")

        # Update preferences
        update_res = self.client.put(
            "/users/preferences",
            json={
                "preferred_language": "hi",
                "theme": "dark",
                "mood_reminders": False,
                "anonymous_mode": True,
            },
            headers=headers,
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["preferred_language"], "hi")
        self.assertEqual(update_res.json()["theme"], "dark")
        self.assertFalse(update_res.json()["mood_reminders"])
        self.assertTrue(update_res.json()["anonymous_mode"])

    def test_data_export_privacy(self):
        headers = {"Authorization": f"Bearer {self.student_token}"}
        res = self.client.get("/users/export", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("export_metadata", data)
        self.assertIn("profile", data)
        self.assertIn("mood_history", data)
        self.assertIn("journal_entries", data)
        self.assertIn("wellness_plans", data)

    # ── 2. Private Journaling System ──────────────────────────────────────────

    def test_journal_crud_and_search(self):
        headers = {"Authorization": f"Bearer {self.student_token}"}
        # 1. Create journal
        create_res = self.client.post(
            "/journal",
            json={
                "title": "Reflections after Midterms",
                "content": "Today felt lighter after taking a long walk through the campus gardens.",
                "mood_score": 4,
                "tags": ["reflection", "campus", "walking"],
                "is_pinned": True,
            },
            headers=headers,
        )
        self.assertEqual(create_res.status_code, 201)
        entry_id = create_res.json()["id"]

        # 2. List journals
        list_res = self.client.get("/journal", headers=headers)
        self.assertEqual(list_res.status_code, 200)
        self.assertGreaterEqual(len(list_res.json()), 1)

        # 3. Search journals
        search_res = self.client.get("/journal/search?q=gardens", headers=headers)
        self.assertEqual(search_res.status_code, 200)
        self.assertGreaterEqual(len(search_res.json()), 1)

        # 4. Update journal
        put_res = self.client.put(
            f"/journal/{entry_id}",
            json={"title": "Reflections after Midterms (Updated)"},
            headers=headers,
        )
        self.assertEqual(put_res.status_code, 200)
        self.assertEqual(put_res.json()["title"], "Reflections after Midterms (Updated)")

        # 5. Delete journal
        del_res = self.client.delete(f"/journal/{entry_id}", headers=headers)
        self.assertEqual(del_res.status_code, 200)

        # Verify not found
        get_res = self.client.get(f"/journal/{entry_id}", headers=headers)
        self.assertEqual(get_res.status_code, 404)

    # ── 3. Wellness Plans & Goals ─────────────────────────────────────────────

    def test_wellness_plan_and_activities(self):
        headers = {"Authorization": f"Bearer {self.student_token}"}
        # 1. Generate suggested plan
        gen_res = self.client.post(
            "/wellness/generate-plan",
            json={"category": "academic"},
            headers=headers,
        )
        self.assertEqual(gen_res.status_code, 200)
        plan_proposal = gen_res.json()
        self.assertIn("activities", plan_proposal)
        self.assertGreater(len(plan_proposal["activities"]), 0)

        # 2. Create personal plan
        create_res = self.client.post(
            "/wellness/plans",
            json={
                "title": plan_proposal["title"],
                "description": plan_proposal["description"],
                "category": plan_proposal["category"],
                "activities": [
                    {"title": "Pomodoro study sprint", "frequency": "daily"},
                    {"title": "Evening 15-minute walk", "frequency": "daily"},
                ],
            },
            headers=headers,
        )
        self.assertEqual(create_res.status_code, 201)
        plan_id = create_res.json()["id"]
        activities = create_res.json()["activities"]
        self.assertEqual(len(activities), 2)
        activity_id = activities[0]["id"]

        # 3. Update activity progress
        prog_res = self.client.patch(
            f"/wellness/activities/{activity_id}/progress",
            json={"progress": 100, "completed": True},
            headers=headers,
        )
        self.assertEqual(prog_res.status_code, 200)
        self.assertTrue(prog_res.json()["completed"])
        self.assertEqual(prog_res.json()["progress"], 100)

        # 4. Delete plan
        del_res = self.client.delete(f"/wellness/plans/{plan_id}", headers=headers)
        self.assertEqual(del_res.status_code, 200)

    # ── 4. Resource Library & Bookmarking ─────────────────────────────────────

    def test_resource_library_and_bookmarks(self):
        headers = {"Authorization": f"Bearer {self.student_token}"}
        # 1. List resources
        list_res = self.client.get("/resources")
        self.assertEqual(list_res.status_code, 200)
        resources = list_res.json()
        self.assertGreater(len(resources), 0)
        target_resource = resources[0]["id"]

        # 2. Get categories
        cat_res = self.client.get("/resources/categories")
        self.assertEqual(cat_res.status_code, 200)
        self.assertIn("categories", cat_res.json())

        # 3. Bookmark resource
        bm_res = self.client.post(f"/resources/{target_resource}/bookmark", headers=headers)
        self.assertEqual(bm_res.status_code, 200)
        self.assertTrue(bm_res.json()["bookmarked"])

        # 4. List bookmarks
        my_bms = self.client.get("/resources/bookmarks", headers=headers)
        self.assertEqual(my_bms.status_code, 200)
        self.assertTrue(any(r["id"] == target_resource for r in my_bms.json()))

        # 5. Toggle off bookmark
        un_bm_res = self.client.post(f"/resources/{target_resource}/bookmark", headers=headers)
        self.assertEqual(un_bm_res.status_code, 200)
        self.assertFalse(un_bm_res.json()["bookmarked"])

    # ── 5. Counsellor Appointments Workflow ───────────────────────────────────

    def test_counsellor_booking_workflow(self):
        student_headers = {"Authorization": f"Bearer {self.student_token}"}
        counsellor_headers = {"Authorization": f"Bearer {self.counsellor_token}"}

        # 1. List counsellors
        c_res = self.client.get("/counsellors")
        self.assertEqual(c_res.status_code, 200)

        # 2. Book appointment
        booking_date = datetime.now(timezone.utc) + timedelta(days=2)
        book_res = self.client.post(
            "/appointments",
            json={
                "counsellor_id": self.counsellor.id,
                "appointment_date": booking_date.isoformat(),
                "duration_minutes": 45,
                "meeting_type": "video",
                "notes": "Discussing exam stress and time prioritization.",
            },
            headers=student_headers,
        )
        self.assertEqual(book_res.status_code, 201)
        appointment_id = book_res.json()["id"]

        # 3. Student views appointments
        s_apps = self.client.get("/appointments", headers=student_headers)
        self.assertEqual(s_apps.status_code, 200)
        self.assertTrue(any(a["id"] == appointment_id for a in s_apps.json()))

        # 4. Counsellor views appointments
        c_apps = self.client.get("/appointments", headers=counsellor_headers)
        self.assertEqual(c_apps.status_code, 200)
        self.assertTrue(any(a["id"] == appointment_id for a in c_apps.json()))

        # 5. Counsellor completes appointment with notes
        update_res = self.client.patch(
            f"/appointments/{appointment_id}",
            json={
                "status": "completed",
                "counsellor_notes": "Student showed excellent insight; recommended sleep hygiene routine.",
            },
            headers=counsellor_headers,
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["status"], "completed")

    # ── 6. In-App Notification Center ─────────────────────────────────────────

    def test_notification_flow(self):
        headers = {"Authorization": f"Bearer {self.student_token}"}
        # In earlier booking test, a notification was dispatched
        res = self.client.get("/notifications", headers=headers)
        self.assertEqual(res.status_code, 200)

        # Mark all as read
        mark_res = self.client.post("/notifications/mark-all-read", headers=headers)
        self.assertEqual(mark_res.status_code, 200)
        self.assertTrue(mark_res.json()["success"])

    # ── 7. Chat Enhancements (Sessions, Feedback, Rename) ─────────────────────

    @patch("routes.chat.generate_ai_chat")
    def test_chat_session_rename_and_feedback(self, mock_ai):
        mock_ai.return_value = {
            "text": "Nervousness before a presentation is very natural.",
            "severity": "low",
            "suggestions": ["Practice once in the room", "Focus on your opening slide"],
        }
        headers = {"Authorization": f"Bearer {self.student_token}"}
        # Send chat message to create session
        chat_res = self.client.post(
            "/chat",
            json={"message": "Can we talk about feeling nervous before presentations?"},
            headers=headers,
        )
        self.assertEqual(chat_res.status_code, 200)
        session_id = chat_res.json()["session_id"]
        message_id = int(chat_res.json()["id"])

        # Rename session
        rename_res = self.client.patch(
            f"/chat/sessions/{session_id}",
            json={"title": "Presentation Nerves Discussion"},
            headers=headers,
        )
        self.assertEqual(rename_res.status_code, 200)
        self.assertEqual(rename_res.json()["title"], "Presentation Nerves Discussion")

        # Submit feedback (+1 helpful)
        feedback_res = self.client.post(
            f"/chat/messages/{message_id}/feedback",
            json={"rating": 1, "comment": "Grounded advice on stage fright."},
            headers=headers,
        )
        self.assertEqual(feedback_res.status_code, 200)
        self.assertTrue(feedback_res.json()["success"])

        # Paginated message retrieval
        msg_res = self.client.get(f"/chat/sessions/{session_id}/messages?limit=10", headers=headers)
        self.assertEqual(msg_res.status_code, 200)
        self.assertGreater(msg_res.json()["total"], 0)

    # ── 8. Admin & Governance Governance ─────────────────────────────────────

    def test_admin_dashboard_role_authorization(self):
        student_headers = {"Authorization": f"Bearer {self.student_token}"}
        counsellor_headers = {"Authorization": f"Bearer {self.counsellor_token}"}

        # Student forbidden (403)
        res_student = self.client.get("/admin/dashboard", headers=student_headers)
        self.assertEqual(res_student.status_code, 403)

        # Counsellor authorized (200)
        res_counsellor = self.client.get("/admin/dashboard", headers=counsellor_headers)
        self.assertEqual(res_counsellor.status_code, 200)
        data = res_counsellor.json()
        self.assertIn("user_metrics", data)
        self.assertIn("engagement_metrics", data)
        self.assertIn("safety_metrics", data)

    def test_admin_system_health(self):
        counsellor_headers = {"Authorization": f"Bearer {self.counsellor_token}"}
        res = self.client.get("/admin/system-health", headers=counsellor_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["database"]["status"], "reachable")
        self.assertEqual(data["ml_pipeline"]["status"], "loaded")


if __name__ == "__main__":
    unittest.main()
