"""DB'li smoke testler — gerçek Postgres gerekir (CI'da servis; lokalde fithub_ci_test).

Boş DB'de açılış migration zinciri (000_baseline + 001..N) koşar; sonra uçtan uca
kayıt → giriş → yenileme → profil → dışa aktarma → koç kaydı → webhook → hesap silme.
DB yoksa modül atlanır.
"""
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("AUTO_MIGRATE", "1")
os.environ["SENTRY_DSN"] = ""
os.environ["RESEND_API_KEY"] = ""          # testte gerçek e-posta gitmesin
os.environ.setdefault("ADMIN_API_KEY", "ci-admin-key")
os.environ.setdefault("REVENUECAT_WEBHOOK_AUTH", "ci-webhook-auth")


def _db_reachable() -> bool:
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        c = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "fithub"), user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""), host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5433")), connect_timeout=3,
        )
        c.close()
        return True
    except Exception:
        return False


if not _db_reachable():
    pytest.skip("Postgres erişilemiyor — DB'li smoke testler atlandı", allow_module_level=True)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _register_user(client):
    tag = uuid.uuid4().hex[:10]
    email = f"smoke-{tag}@fithubpoint-test.com"
    phone = "05" + str(int(tag[:8], 16))[-9:].rjust(9, "1")
    password = "Smoke12345!"
    r = client.post("/auth/register", json={
        "full_name": "Smoke Kullanıcı", "email": email, "phone": phone,
        "password": password, "password_confirm": password,
        "birthdate": "1995-05-05", "accepted_terms": True,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True and body.get("token")
    return {"email": email, "password": password, "token": body["token"], "refresh": body.get("refresh_token")}


@pytest.fixture(scope="module")
def user(client):
    return _register_user(client)


def test_health_touches_db(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["db"] == "ok"


def test_migration_chain_recorded(client):
    from app.core.database import _get_pool
    pool = _get_pool(); conn = pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM schema_migrations")
        assert cur.fetchone()["c"] >= 60
        for t in ("users", "clients", "subscriptions", "workout_days", "messages", "revenuecat_events", "ai_usage_log"):
            cur.execute("SELECT to_regclass(%s) AS r", (f"public.{t}",))
            assert cur.fetchone()["r"] is not None, t
    finally:
        conn.rollback(); pool.putconn(conn)


def test_login_refresh_me_export(client, user):
    r = client.post("/auth/login", json={"identifier": user["email"], "password": user["password"], "remember_me": True})
    assert r.status_code == 200, r.text
    tok, refresh = r.json()["token"], r.json().get("refresh_token")
    assert tok and refresh
    r = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200 and r.json().get("token")
    h = {"Authorization": f"Bearer {tok}"}
    r = client.get("/client/me", headers=h)
    assert r.status_code == 200, r.text
    r = client.get("/auth/me/export", headers=h)
    assert r.status_code == 200 and r.json()["table_count"] >= 10
    assert "attachment" in r.headers.get("content-disposition", "")
    r = client.get("/client/notifications?limit=5", headers=h)
    assert r.status_code == 200 and r.json()["limit"] == 5


def test_wrong_password_then_rate_limit(client, user):
    codes = []
    for _ in range(10):
        r = client.post("/auth/login", json={"identifier": user["email"], "password": "yanlis-sifre"})
        codes.append(r.status_code)
    assert 401 in codes and codes[-1] == 429, codes


def test_coach_signup_and_admin_guards(client):
    email = f"smoke-coach-{uuid.uuid4().hex[:8]}@fithubpoint-test.com"
    r = client.post("/auth/coach-signup", json={"full_name": "Smoke Koç", "email": email, "password": "Sifre12345"})
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "coach" and r.json()["token"]
    coach_h = {"Authorization": f"Bearer {r.json()['token']}"}
    assert client.get("/admin/refunds/pending").status_code == 401
    assert client.get("/admin/refunds/pending", headers=coach_h).status_code == 403
    r = client.get("/admin/refunds/pending", headers={"X-Admin-Key": os.environ["ADMIN_API_KEY"]})
    assert r.status_code == 200 and "refunds" in r.json()
    assert client.get("/_openai_ping").status_code in (401, 422)
    assert client.get("/superadmin/ai-usage").status_code == 401


def test_revenuecat_webhook_dedup(client):
    ev = {"event": {"id": f"evt-{uuid.uuid4().hex[:12]}", "type": "INITIAL_PURCHASE",
                    "app_user_id": "999999", "product_id": "not-our-product"}}
    auth = {"Authorization": os.environ["REVENUECAT_WEBHOOK_AUTH"]}
    assert client.post("/webhooks/revenuecat", json=ev).status_code == 401
    r1 = client.post("/webhooks/revenuecat", json=ev, headers=auth)
    assert r1.status_code == 200 and "skipped" in r1.json()["result"]
    r2 = client.post("/webhooks/revenuecat", json=ev, headers=auth)
    assert r2.status_code == 200 and "duplicate" in r2.json()["result"]


def test_upload_rejects_non_image(client, user):
    h = {"Authorization": f"Bearer {user['token']}"}
    r = client.post("/upload/image", headers=h, files={"file": ("x.jpg", b"not-an-image", "image/jpeg")})
    # Cloudinary yoksa 500 "not configured", varsa magic-byte reddi 400
    assert r.status_code in (400, 500)


def test_delete_account_then_login_fails(client, user):
    h = {"Authorization": f"Bearer {user['token']}"}
    r = client.delete("/auth/me", headers=h)
    assert r.status_code == 200, r.text
    r = client.post("/auth/login", json={"identifier": user["email"], "password": user["password"]})
    assert r.status_code in (401, 404, 429)


def test_workout_set_logs_and_history(client):
    user = _register_user(client)  # hesap silme testinden bağımsız taze kullanıcı
    h = {"Authorization": f"Bearer {user['token']}"}
    body = {"exercise_name": "Bench Press", "library_id": 42, "day_key": "mon",
            "sets": [{"set_index": 1, "weight_kg": 60, "reps": 8}, {"set_index": 2, "weight_kg": 62.5, "reps": 6}]}
    r = client.put("/client/workout-sets", json=body, headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["saved"] == 2 and j["exercise_key"] == "lib:42" and j["pr"] is None  # ilk oturum: rekor yok
    # dün için daha hafif bir oturum ekle → bugünkü oturum rekor olmalı
    r = client.put("/client/workout-sets", json={**body, "session_date": "2020-01-01",
                                                 "sets": [{"set_index": 1, "weight_kg": 50, "reps": 8}]}, headers=h)
    assert r.status_code == 200 and r.json()["saved"] == 1
    r = client.put("/client/workout-sets", json={**body, "sets": [{"set_index": 3, "weight_kg": 65, "reps": 5}]}, headers=h)
    assert r.status_code == 200 and r.json()["pr"] is not None and r.json()["pr"]["weight_kg"] == 65
    r = client.get("/client/workout-sets/history?library_id=42", headers=h)
    assert r.status_code == 200, r.text
    hist = r.json()
    assert len(hist["today"]) == 3 and hist["last"]["date"] == "2020-01-01"
    assert hist["best"]["est_1rm"] == 76.0 and len(hist["sessions"]) == 2  # Epley: 60×8 > 65×5
    r = client.put("/client/workout-sets", json={"sets": []}, headers=h)
    assert r.status_code == 422


def test_exercise_alternatives_and_swap(client):
    from app.core.database import _get_pool
    user = _register_user(client)
    h = {"Authorization": f"Bearer {user['token']}"}
    pool = _get_pool(); conn = pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s", (user["email"],))
        uid = cur.fetchone()["id"]
        rows = [
            ("Barbell Bench Press", "horizontal_press", "barbell", ["chest"], 2, "g1"),
            ("Dumbbell Bench Press", "horizontal_press", "dumbbell", ["chest"], 2, "g2"),
            ("Machine Chest Press", "horizontal_press", "machine", ["chest"], 1, None),
            ("Barbell Row", "horizontal_pull", "barbell", ["middle back"], 2, "g4"),
        ]
        ids = []
        for name, pat, eq, mus, cx, gif in rows:
            cur.execute(
                """INSERT INTO exercise_library (external_id, canonical_name, movement_pattern, equipment_type, primary_muscles, complexity, gif_url, level, category)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'beginner', 'strength') RETURNING id""",
                (f"smoke-{uuid.uuid4().hex[:8]}", name, pat, eq, mus, cx, gif),
            )
            ids.append(cur.fetchone()["id"])
        cur.execute("INSERT INTO workout_programs (client_user_id, title, is_active, created_at, updated_at) VALUES (%s, 'Smoke', TRUE, NOW(), NOW()) RETURNING id", (uid,))
        pid = cur.fetchone()["id"]
        payload = {"title": "Gün", "blocks": [{"title": "A", "items": [
            {"type": "exercise", "name": "Barbell Bench Press", "sets": 4, "reps": "8", "library_id": ids[0]},
            {"type": "exercise", "name": "Barbell Row", "sets": 4, "reps": "8", "library_id": ids[3]},
        ]}]}
        import json as _json
        cur.execute("INSERT INTO workout_days (workout_program_id, day_of_week, order_index, week_index, day_payload, created_at, updated_at) VALUES (%s, 'mon', 0, 1, %s, NOW(), NOW()) RETURNING id",
                    (pid, _json.dumps(payload)))
        did = cur.fetchone()["id"]
        cur.execute("INSERT INTO workout_exercises (workout_day_id, exercise_name, sets, reps, order_index, exercise_library_id, created_at, updated_at) VALUES (%s, 'Barbell Bench Press', 4, '8', 0, %s, NOW(), NOW())", (did, ids[0]))
        conn.commit()
    finally:
        pool.putconn(conn)

    r = client.get(f"/client/exercise-alternatives?library_id={ids[0]}", headers=h)
    assert r.status_code == 200, r.text
    alts = r.json()["alternatives"]
    assert [a["name"] for a in alts] == ["Dumbbell Bench Press", "Machine Chest Press"]  # aynı kalıp; farklı kalıp (row) yok
    r = client.get(f"/client/exercise-alternatives?library_id={ids[0]}&equipment=machine", headers=h)
    assert [a["name"] for a in r.json()["alternatives"]] == ["Machine Chest Press"]

    r = client.post("/client/workout-exercises/swap", json={"day_key": "mon", "old_library_id": ids[0], "new_library_id": ids[1]}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["replaced_rows"] == 1 and r.json()["replaced_days"] == 1
    conn = pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT exercise_name, exercise_library_id FROM workout_exercises WHERE workout_day_id = %s", (did,))
        row = cur.fetchone()
        assert row["exercise_name"] == "Dumbbell Bench Press" and row["exercise_library_id"] == ids[1]
        cur.execute("SELECT day_payload FROM workout_days WHERE id = %s", (did,))
        dp = cur.fetchone()["day_payload"]
        dp = dp if isinstance(dp, dict) else _json.loads(dp)
        names = [i["name"] for i in dp["blocks"][0]["items"]]
        assert names == ["Dumbbell Bench Press", "Barbell Row"]
    finally:
        conn.rollback(); pool.putconn(conn)
    r = client.post("/client/workout-exercises/swap", json={"day_key": "tue", "old_library_id": ids[0], "new_library_id": ids[1]}, headers=h)
    assert r.status_code == 404
