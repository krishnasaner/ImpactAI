"""
ImpactAI — Seed the database with demo users.

Run:
    cd Backend
    python scripts/seed_db.py
"""

from pathlib import Path
import sys

# Allow running from the scripts directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import init_db, SessionLocal, UserRow
from services.security import hash_password
from datetime import datetime, timezone


DEMO_USERS = [
    {"email": "student@impactai.com",   "password": "Student@ImpactAI1!",   "role": "student",   "name": "Demo Student"},
    {"email": "counselor@impactai.com", "password": "Counselor@ImpactAI1!", "role": "counselor", "name": "Demo Counselor"},
    {"email": "admin@impactai.com",     "password": "Admin@ImpactAI1!",     "role": "admin",     "name": "Demo Admin"},
]


def main():
    init_db()
    db = SessionLocal()
    try:
        for user_data in DEMO_USERS:
            existing = db.query(UserRow).filter(UserRow.email == user_data["email"]).first()
            if existing:
                print(f"  SKIP: {user_data['email']} already exists")
                continue
            user = UserRow(
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                name=user_data["name"],
                created_at=datetime.now(timezone.utc),
            )
            db.add(user)
            db.commit()
            print(f"  OK: Created {user_data['role']:>10s} -> {user_data['email']}")
        print("\nDone! Demo users are ready.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
