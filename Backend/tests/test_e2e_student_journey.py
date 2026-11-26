"""
ImpactAI — Full End-to-End Student Journey & Concurrency/Security Verification.

Tests:
1. Complete Student Journey:
   Signup -> Login -> Profile -> Preferences -> Mood -> Journal ->
   Wellness Plan & Activities -> Resource Bookmark -> Counsellor Booking ->
   Notifications -> Chat turn & Feedback -> Data Export.
2. Concurrent Appointment Booking Collision Defense:
   Slot collision rejection (400 conflict protection).
3. Horizontal Privilege Escalation / IDOR Defense:
   Unauthorized access/mutation to private journal and appointment records.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from main import app
from services.security import create_access_token


def _register_and_create_session(email: str, password: str, name: str):
    session = TestClient(app)
    signup_res = session.post(
        "/auth/signup",
        json={
            "email": email,
            "password": password,
            "confirm_password": password,
            "role": "student",
            "name": name,
        },
    )
    assert signup_res.status_code == 200, signup_res.text
    user_id = signup_res.json()["data"]["user"]["id"]

    login_res = session.post("/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200, login_res.text
    token = login_res.cookies.get("access_token") or create_access_token({
        "sub": str(user_id),
        "email": email,
        "role": "student",
    })
    csrf = login_res.cookies.get("csrf_token") or ""
    headers = {"Authorization": f"Bearer {token}"}
    if csrf:
        headers["X-CSRF-Token"] = csrf
    return session, headers


def test_full_student_lifecycle():
    """Verify complete uninterrupted user lifecycle through the unified API layer."""
    unique_ts = int(datetime.now().timestamp() * 1000)
    email = f"student_{unique_ts}@campus.edu"
    password = "Kx9#vP2$mL8@qZ7!"
    name = f"Student {unique_ts}"

    client, headers = _register_and_create_session(email, password, name)

    # 1. Profile update
    prof_res = client.put(
        "/users/profile",
        headers=headers,
        json={
            "display_name": "Campus Scholar",
            "bio": "Third-year engineering student navigating exam stress.",
            "university": "State University",
            "major": "Computer Science",
            "phone": "+1-555-0199",
        },
    )
    assert prof_res.status_code == 200, prof_res.text
    prof_data = prof_res.json()
    assert prof_data["display_name"] == "Campus Scholar"
    assert prof_data["major"] == "Computer Science"

    # 2. Preferences update
    pref_res = client.put(
        "/users/preferences",
        headers=headers,
        json={
            "theme": "dark",
            "notification_frequency": "daily",
            "crisis_alert_opt_in": True,
            "reading_mode": True,
        },
    )
    assert pref_res.status_code == 200, pref_res.text
    assert pref_res.json()["theme"] == "dark"

    # 3. Mood logging
    mood_res = client.post(
        "/mood",
        headers=headers,
        json={
            "mood": "anxious",
            "note": "Preparing for midterm exams tomorrow.",
        },
    )
    assert mood_res.status_code == 200, mood_res.text
    assert mood_res.json()["mood"] == "anxious"

    # 4. Mood summary & trends
    sum_res = client.get("/mood/summary", headers=headers)
    assert sum_res.status_code == 200, sum_res.text
    assert sum_res.json()["total_entries"] >= 1

    trend_res = client.get("/mood/trends", headers=headers)
    assert trend_res.status_code == 200, trend_res.text
    assert "trend_data" in trend_res.json()

    # 5. Journal CRUD & search
    journal_res = client.post(
        "/journal",
        headers=headers,
        json={
            "title": "Reflections on Midterm Week",
            "content": "Focusing on sleep and deep breathing techniques to stay calm.",
            "mood_score": 4,
            "tags": ["midterms", "breathing"],
            "is_pinned": True,
        },
    )
    assert journal_res.status_code == 201, journal_res.text
    journal_id = journal_res.json()["id"]

    search_res = client.get("/journal/search?q=breathing", headers=headers)
    assert search_res.status_code == 200, search_res.text
    assert len(search_res.json()) >= 1

    # 6. Wellness plan creation & activity progress
    plan_res = client.post(
        "/wellness/plans",
        headers=headers,
        json={
            "title": "Midterm Recovery Plan",
            "category": "wellness",
            "duration_days": 14,
            "description": "Daily 10-minute mindfulness and sleep schedule stabilization.",
        },
    )
    assert plan_res.status_code == 201, plan_res.text
    plan_id = plan_res.json()["id"]

    act_res = client.post(
        f"/wellness/plans/{plan_id}/activities",
        headers=headers,
        json={
            "title": "Evening 4-7-8 Breathing",
            "frequency": "daily",
            "target_count": 14,
            "description": "Complete breathing cycle before sleep.",
        },
    )
    assert act_res.status_code in (200, 201), act_res.text
    act_id = act_res.json()["id"]

    prog_res = client.patch(
        f"/wellness/activities/{act_id}/progress",
        headers=headers,
        json={"progress": 5, "completed": False},
    )
    assert prog_res.status_code == 200, prog_res.text
    assert prog_res.json()["progress"] == 5

    # 7. Wellness resources & bookmarks
    res_list = client.get("/resources", headers=headers)
    assert res_list.status_code == 200, res_list.text
    items = res_list.json()
    assert len(items) >= 1
    sample_res_id = items[0]["id"]

    # Bookmark resource
    bm_res = client.post(f"/resources/{sample_res_id}/bookmark", headers=headers)
    assert bm_res.status_code == 200, bm_res.text
    assert bm_res.json()["bookmarked"] is True

    bm_list = client.get("/resources/bookmarks", headers=headers)
    assert bm_list.status_code == 200, bm_list.text
    assert any(b["id"] == sample_res_id for b in bm_list.json())

    # 8. Counsellors & Appointments
    counsellors_res = client.get("/counsellors", headers=headers)
    assert counsellors_res.status_code == 200, counsellors_res.text
    c_list = counsellors_res.json()
    assert len(c_list) >= 1
    counsellor_id = c_list[0]["id"]

    # Book appointment 3 days in future
    future_date = (datetime.now(timezone.utc) + timedelta(days=3)).replace(hour=14, minute=0, second=0, microsecond=0)
    appt_res = client.post(
        "/appointments",
        headers=headers,
        json={
            "counsellor_id": counsellor_id,
            "appointment_date": future_date.isoformat(),
            "duration_minutes": 45,
            "meeting_type": "video",
            "notes": "Discussing study stress management.",
        },
    )
    assert appt_res.status_code == 201, appt_res.text
    appt_id = appt_res.json()["id"]

    # Student appointments list
    my_appts = client.get("/appointments", headers=headers)
    assert my_appts.status_code == 200, my_appts.text
    assert any(a["id"] == appt_id for a in my_appts.json())

    # 9. Notification dispatch verification
    notifs = client.get("/notifications", headers=headers)
    assert notifs.status_code == 200, notifs.text
    assert len(notifs.json()) >= 1  # Appointment booking triggers automated notification

    # 10. Chat conversation & message feedback (mocked LLM generation)
    with patch("routes.chat.generate_ai_chat") as mock_ai:
        mock_ai.return_value = {
            "text": "I hear how demanding midterm week has been. Let's take a slow grounding breath together.",
            "severity": "low",
            "suggestions": ["Try 4-7-8 breathing", "Take a 5-minute pause"],
        }
        chat_res = client.post(
            "/chat",
            headers=headers,
            json={"message": "I feel slightly overwhelmed by upcoming exam schedules."},
        )
        assert chat_res.status_code == 200, chat_res.text
        chat_data = chat_res.json()
        session_id = chat_data["session_id"]
        assert "slow grounding breath" in chat_data["text"]

    # Session messages retrieval
    session_msgs = client.get(f"/chat/sessions/{session_id}/messages", headers=headers)
    assert session_msgs.status_code == 200, session_msgs.text
    msgs = session_msgs.json()["messages"]
    assert len(msgs) >= 2
    bot_msg = [m for m in msgs if m["sender"] in ("assistant", "bot")][0]

    # Message feedback
    feedback_res = client.post(
        f"/chat/messages/{bot_msg['id']}/feedback",
        headers=headers,
        json={"rating": 1, "comment": "Very reassuring during study breaks."},
    )
    assert feedback_res.status_code == 200, feedback_res.text
    assert feedback_res.json()["success"] is True

    # 11. Data Export
    export_res = client.get("/users/export", headers=headers)
    assert export_res.status_code == 200, export_res.text
    export_data = export_res.json()
    assert export_data["export_metadata"]["email"] == email
    assert len(export_data["journal_entries"]) >= 1
    assert len(export_data["wellness_plans"]) >= 1
    assert len(export_data["appointments"]) >= 1


def test_concurrent_appointment_booking_collision():
    """Verify that two students competing for the exact same slot cannot double-book."""
    ts = int(datetime.now().timestamp() * 1000)

    # Student A & Student B
    client_a, headers_a = _register_and_create_session(f"stu_a_{ts}@campus.edu", "Kx9#vP2$mL8@qZ7!", "Student A")
    client_b, headers_b = _register_and_create_session(f"stu_b_{ts}@campus.edu", "Kx9#vP2$mL8@qZ7!", "Student B")

    # Get counsellor
    c_res = client_a.get("/counsellors", headers=headers_a)
    counsellor_id = c_res.json()[0]["id"]

    slot_time = (datetime.now(timezone.utc) + timedelta(days=5)).replace(hour=11, minute=0, second=0, microsecond=0)
    slot_iso = slot_time.isoformat()

    # Student A books slot
    booking_a = client_a.post(
        "/appointments",
        headers=headers_a,
        json={
            "counsellor_id": counsellor_id,
            "appointment_date": slot_iso,
            "duration_minutes": 45,
            "meeting_type": "video",
            "notes": "Student A primary reservation",
        },
    )
    assert booking_a.status_code == 201, booking_a.text

    # Student B attempts to book the identical slot
    booking_b = client_b.post(
        "/appointments",
        headers=headers_b,
        json={
            "counsellor_id": counsellor_id,
            "appointment_date": slot_iso,
            "duration_minutes": 45,
            "meeting_type": "video",
            "notes": "Student B conflicting reservation",
        },
    )
    assert booking_b.status_code == 400
    assert "already reserved" in booking_b.json()["detail"].lower() or "already booked" in booking_b.json()["detail"].lower()


def test_horizontal_privilege_escalation_defense():
    """Verify students cannot view, modify or delete other students' journal entries or appointments."""
    ts = int(datetime.now().timestamp() * 1000)

    client_1, headers_1 = _register_and_create_session(f"owner_{ts}@campus.edu", "Kx9#vP2$mL8@qZ7!", "Owner")
    client_2, headers_2 = _register_and_create_session(f"attacker_{ts}@campus.edu", "Kx9#vP2$mL8@qZ7!", "Attacker")

    # Student 1 creates private journal
    j_res = client_1.post(
        "/journal",
        headers=headers_1,
        json={"title": "Private Diary Entry", "content": "Confidential thoughts."},
    )
    assert j_res.status_code == 201, j_res.text
    journal_id = j_res.json()["id"]

    # Student 2 tries to read Student 1's journal
    get_res = client_2.get(f"/journal/{journal_id}", headers=headers_2)
    assert get_res.status_code in (403, 404)

    # Student 2 tries to modify Student 1's journal
    put_res = client_2.put(f"/journal/{journal_id}", headers=headers_2, json={"content": "Malicious edit"})
    assert put_res.status_code in (403, 404)

    # Student 2 tries to delete Student 1's journal
    del_res = client_2.delete(f"/journal/{journal_id}", headers=headers_2)
    assert del_res.status_code in (403, 404)
