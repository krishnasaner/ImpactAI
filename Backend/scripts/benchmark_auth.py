"""
Phase B.4 — Authentication Performance Benchmarks.

Measures p50, p95, p99 latency for signup, login, /auth/me, and /auth/refresh
at 1, 10, 25, and 50 concurrent requests using threading.
"""

import hashlib
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup before importing app
sys.path.insert(0, ".")
from main import app
from database import Base, get_db, UserRow, SessionRow, RefreshTokenRow
from services.security import hash_password, create_access_token, create_refresh_token


# ── In-memory test DB ──────────────────────────────────────────────────────────
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def percentile(data, pct):
    """Calculate percentile from a sorted list."""
    if not data:
        return 0
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * pct / 100)
    return sorted_data[min(idx, len(sorted_data) - 1)]


def benchmark(func, concurrency, iterations_per_thread=1):
    """Run func with given concurrency and return latency stats."""
    latencies = []

    def timed_call():
        start = time.perf_counter()
        try:
            result = func()
            elapsed = time.perf_counter() - start
            return elapsed, result
        except Exception as e:
            elapsed = time.perf_counter() - start
            return elapsed, None

    if concurrency == 1:
        for _ in range(max(iterations_per_thread, 3)):
            elapsed, _ = timed_call()
            latencies.append(elapsed)
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(timed_call) for _ in range(concurrency)]
            for f in as_completed(futures):
                elapsed, _ = f.result()
                latencies.append(elapsed)

    return {
        "count": len(latencies),
        "p50_ms": round(percentile(latencies, 50) * 1000, 1),
        "p95_ms": round(percentile(latencies, 95) * 1000, 1),
        "p99_ms": round(percentile(latencies, 99) * 1000, 1),
        "mean_ms": round(statistics.mean(latencies) * 1000, 1),
        "min_ms": round(min(latencies) * 1000, 1),
        "max_ms": round(max(latencies) * 1000, 1),
    }


def main():
    print("=" * 70)
    print("PHASE B.4 — AUTHENTICATION PERFORMANCE BENCHMARKS")
    print("=" * 70)

    Base.metadata.create_all(bind=test_engine)
    client = TestClient(app)

    # Pre-create a test user for login benchmarks
    db = TestingSessionLocal()
    test_user = UserRow(
        email="benchuser@test.com",
        hashed_password=hash_password("BenchPass123!@"),
        role="student",
        name="Bench User",
        created_at=datetime.now(timezone.utc),
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    user_id = test_user.id
    db.close()

    concurrency_levels = [1, 10, 25, 50]

    # ── Signup Benchmark ───────────────────────────────────────────────────
    print("\n── Signup Benchmark ──")
    counter = [0]

    for c in concurrency_levels:
        def signup_call():
            counter[0] += 1
            email = f"signup_{counter[0]}_{uuid4().hex[:6]}@test.com"
            return client.post("/auth/signup", json={
                "email": email,
                "password": "BenchPass123!@",
                "confirm_password": "BenchPass123!@",
                "role": "student",
            })

        stats = benchmark(signup_call, c)
        print(f"  Concurrency {c:3d}: p50={stats['p50_ms']:7.1f}ms  p95={stats['p95_ms']:7.1f}ms  p99={stats['p99_ms']:7.1f}ms  mean={stats['mean_ms']:7.1f}ms")

    # ── Login Benchmark ────────────────────────────────────────────────────
    print("\n── Login Benchmark ──")
    for c in concurrency_levels:
        def login_call():
            return client.post("/auth/login", json={
                "email": "benchuser@test.com",
                "password": "BenchPass123!@",
                "role": "student",
            })

        stats = benchmark(login_call, c)
        print(f"  Concurrency {c:3d}: p50={stats['p50_ms']:7.1f}ms  p95={stats['p95_ms']:7.1f}ms  p99={stats['p99_ms']:7.1f}ms  mean={stats['mean_ms']:7.1f}ms")

    # ── /auth/me Benchmark ─────────────────────────────────────────────────
    print("\n── /auth/me Benchmark ──")
    token = create_access_token({
        "sub": str(user_id),
        "email": "benchuser@test.com",
        "role": "student",
    })
    for c in concurrency_levels:
        def me_call():
            return client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        stats = benchmark(me_call, c)
        print(f"  Concurrency {c:3d}: p50={stats['p50_ms']:7.1f}ms  p95={stats['p95_ms']:7.1f}ms  p99={stats['p99_ms']:7.1f}ms  mean={stats['mean_ms']:7.1f}ms")

    # ── /auth/refresh Benchmark ────────────────────────────────────────────
    print("\n── /auth/refresh Benchmark (single request) ──")

    # Create a session + refresh token for each refresh attempt
    def setup_and_refresh():
        db = TestingSessionLocal()
        session_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        db_session = SessionRow(
            user_id=user_id,
            session_id=session_id,
            expires_at=expires_at,
            is_active=1,
            remember_me=1,
        )
        db.add(db_session)
        db.commit()

        refresh_tok = create_refresh_token(
            {"sub": str(user_id), "session_id": session_id},
            timedelta(days=7),
        )
        token_hash = hashlib.sha256(refresh_tok.encode("utf-8")).hexdigest()
        db.add(RefreshTokenRow(
            user_id=user_id,
            session_id=session_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=0,
        ))
        db.commit()
        db.close()

        client.cookies.set("refresh_token", refresh_tok)
        return client.post("/auth/refresh")

    stats = benchmark(setup_and_refresh, 1, 3)
    print(f"  Single request: p50={stats['p50_ms']:7.1f}ms  p95={stats['p95_ms']:7.1f}ms  p99={stats['p99_ms']:7.1f}ms  mean={stats['mean_ms']:7.1f}ms")

    # ── bcrypt standalone benchmark ────────────────────────────────────────
    print("\n── bcrypt Operation Latency ──")
    import bcrypt
    pwd = b"BenchPass123!@"

    hash_times = []
    for _ in range(5):
        start = time.perf_counter()
        hashed = bcrypt.hashpw(pwd, bcrypt.gensalt(rounds=12))
        hash_times.append(time.perf_counter() - start)

    verify_times = []
    for _ in range(5):
        start = time.perf_counter()
        bcrypt.checkpw(pwd, hashed)
        verify_times.append(time.perf_counter() - start)

    print(f"  Hash (rounds=12):  mean={statistics.mean(hash_times)*1000:.1f}ms  p50={percentile(hash_times, 50)*1000:.1f}ms")
    print(f"  Verify:            mean={statistics.mean(verify_times)*1000:.1f}ms  p50={percentile(verify_times, 50)*1000:.1f}ms")
    print(f"\n  Note: bcrypt operations are offloaded via asyncio.to_thread()")
    print(f"  to prevent blocking the FastAPI event loop.")

    print("\n" + "=" * 70)
    print("PHASE B.4 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
