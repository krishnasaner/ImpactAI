import os
import sys
import tempfile
from pathlib import Path

os.environ["DATABASE_PATH"] = str(Path(tempfile.gettempdir()) / "impactai_phase1_verify.db")
os.environ["COOKIE_SECURE"] = "false"
os.environ["COOKIE_SAMESITE"] = "lax"

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient

import routes.chat as chat_routes
from main import app

chat_routes.generate_ai_chat = lambda message, history: {
    "text": f"Support response for: {message}",
    "severity": "medium",
    "suggestions": ["Take a breath", "Reach out to a friend"],
}
chat_routes.is_model_available = lambda: True
chat_routes.predict_severity = lambda message: ("medium", 0.91)


def csrf_headers(client: TestClient):
    token = client.cookies.get("csrf_token")
    return {"X-CSRF-Token": token} if token else {}


with TestClient(app) as client:
    signup = client.post(
        "/auth/signup",
        json={
            "email": "student@impactai.com",
            "password": "Student@ImpactAI1!",
            "confirm_password": "Student@ImpactAI1!",
            "role": "student",
            "remember_me": True,
        },
    )
    assert signup.status_code == 200, signup.text
    assert signup.json()["user"]["email"] == "student@impactai.com"
    assert signup.json()["token"] is None

    me = client.get("/auth/me")
    assert me.status_code == 200, me.text

    mood = client.post("/mood", json={"mood": "4", "note": "steady"}, headers=csrf_headers(client))
    assert mood.status_code == 200, mood.text

    chat = client.post(
        "/chat",
        json={"message": "I am feeling stressed today"},
        headers=csrf_headers(client),
    )
    assert chat.status_code == 200, chat.text
    session_id = chat.json()["session_id"]

    history = client.get(f"/chat/history?session_id={session_id}")
    assert history.status_code == 200, history.text
    assert history.json()["count"] == 2, history.text

    logout = client.post("/auth/logout", headers=csrf_headers(client))
    assert logout.status_code == 200, logout.text

    relogin = client.post(
        "/auth/login",
        json={
            "email": "student@impactai.com",
            "password": "Student@ImpactAI1!",
            "role": "student",
            "remember_me": True,
        },
    )
    assert relogin.status_code == 200, relogin.text

    second_client = TestClient(app)
    second_login = second_client.post(
        "/auth/login",
        json={
            "email": "student@impactai.com",
            "password": "Student@ImpactAI1!",
            "role": "student",
            "remember_me": True,
        },
    )
    assert second_login.status_code == 200, second_login.text

    logout_all = client.post("/auth/logout/all", headers=csrf_headers(client))
    assert logout_all.status_code == 200, logout_all.text
    second_me = second_client.get("/auth/me")
    assert second_me.status_code == 401, second_me.text
    second_client.close()

    admin_signup = client.post(
        "/auth/signup",
        json={
            "email": "admin@impactai.com",
            "password": "Admin@ImpactAI1!",
            "confirm_password": "Admin@ImpactAI1!",
            "role": "admin",
            "remember_me": True,
        },
    )
    assert admin_signup.status_code == 200, admin_signup.text

    db_stats = client.get("/analytics/db-stats")
    assert db_stats.status_code == 200, db_stats.text
    assert "total_users" in db_stats.json(), db_stats.text

    google_status = client.get("/auth/google/status")
    assert google_status.status_code == 200, google_status.text

    google_redirect = client.get("/auth/google?role=student&next=login", follow_redirects=False)
    assert google_redirect.status_code in {307, 302}, google_redirect.text

print("Phase 1 verification passed.")
