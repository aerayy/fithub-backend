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
        # Lokal test DB'de art arda koşularda register/login hız sınırı (DB kovası) dolmasın.
        try:
            from app.core.database import _get_pool
            conn = _get_pool().getconn()
            try:
                cur = conn.cursor()
                cur.execute("UPDATE rate_limit_buckets SET count = 0 WHERE key LIKE '%%testclient%%'")
                conn.commit()
            finally:
                _get_pool().putconn(conn)
        except Exception:
            pass
        yield c


def _reset_rate_limits():
    """Aynı süreçte çok sayıda kayıt/giriş yapan testler DB hız sınırı kovasını doldurmasın."""
    try:
        from app.core.database import _get_pool
        conn = _get_pool().getconn()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE rate_limit_buckets SET count = 0 WHERE key LIKE '%%testclient%%'")
            conn.commit()
        finally:
            _get_pool().putconn(conn)
    except Exception:
        pass


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
        # Kas adı koşuya özel: lokal test DB'de önceki koşuların satırları alternatif listesine
        # karışmasın (movement_pattern v3 pipeline enum'unda kalmalı, o yüzden kalıp değişmez).
        tag = uuid.uuid4().hex[:6]
        rows = [
            ("Barbell Bench Press", "horizontal_press", "barbell", [f"chest-{tag}"], 2, "g1"),
            ("Dumbbell Bench Press", "horizontal_press", "dumbbell", [f"chest-{tag}"], 2, "g2"),
            ("Machine Chest Press", "horizontal_press", "machine", [f"chest-{tag}"], 1, None),
            ("Barbell Row", "horizontal_pull", "barbell", [f"middle back-{tag}"], 2, "g4"),
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
    # Lokal test DB'de önceki koşulardan kalan aynı isimli satırlar olabilir → bu koşunun id'leriyle süz.
    def _mine(items):
        return [a["name"] for a in items if a.get("library_id") in ids]
    alts = r.json()["alternatives"]
    assert _mine(alts) == ["Dumbbell Bench Press", "Machine Chest Press"]  # aynı kalıp; farklı kalıp (row) yok
    assert ids[0] not in [a.get("library_id") for a in alts]  # kaynağın kendisi listelenmez
    r = client.get(f"/client/exercise-alternatives?library_id={ids[0]}&equipment=machine", headers=h)
    assert _mine(r.json()["alternatives"]) == ["Machine Chest Press"]

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


# ─── 28. gün akışı (program döngüsü) ─────────────────────────────────────────

def _insert_multiweek_program(conn, uid, coach_id, weeks, days_ago, title="Döngü Testi"):
    import json as _json
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO workout_programs (client_user_id, coach_user_id, title, is_active, created_at, updated_at)
           VALUES (%s, %s, %s, TRUE, (CURRENT_DATE - %s) + TIME '10:00', NOW()) RETURNING id""",
        (uid, coach_id, title, days_ago),
    )
    pid = cur.fetchone()["id"]
    payload = {"title": "Gün", "blocks": [{"title": "A", "items": [{"type": "exercise", "name": "Squat", "sets": 3, "reps": "8"}]}]}
    for w in range(1, weeks + 1):
        cur.execute(
            """INSERT INTO workout_days (workout_program_id, day_of_week, order_index, week_index, day_payload, created_at, updated_at)
               VALUES (%s, 'mon', 0, %s, %s, NOW(), NOW())""",
            (pid, w, _json.dumps(payload)),
        )
    conn.commit()
    return pid


def _user_id(conn, email):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    return cur.fetchone()["id"]


def _ensure_ai_coach_user(conn):
    """Prod'da Fit AI Koç users.id=60'tır; boş test DB'sinde FK için oluştur."""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO users (id, email, role, full_name, created_at, updated_at)
           VALUES (60, 'ai-coach@fithubpoint-test.com', 'coach', 'Fit AI Koç', NOW(), NOW())
           ON CONFLICT (id) DO NOTHING"""
    )
    cur.execute("SELECT setval('users_id_seq', GREATEST((SELECT COALESCE(MAX(id), 1) FROM users), 60))")
    conn.commit()


def test_program_cycle_fields_and_ai_renew_guards(client):
    from app.core.database import _get_pool
    from app.services import ai_subscription_service as ai_sub
    user = _register_user(client)
    h = {"Authorization": f"Bearer {user['token']}"}
    pool = _get_pool(); conn = pool.getconn()
    try:
        uid = _user_id(conn, user["email"])
        _ensure_ai_coach_user(conn)
        assert client.get("/client/workouts/active", headers=h).status_code == 404
        # abonelik yok → 402
        r = client.post("/ai-coach/renew-cycle", headers=h)
        assert r.status_code == 402 and r.json()["detail"]["code"] == "no_subscription"
        ai_sub.create_mock_subscription(conn, uid, "starter")  # Starter'da da döngü yenileme var
        # program yok → 404
        assert client.post("/ai-coach/renew-cycle", headers=h).status_code == 404
        pid = _insert_multiweek_program(conn, uid, 60, weeks=4, days_ago=10)
        r = client.get("/client/workouts/active", headers=h)
        assert r.status_code == 200, r.text
        p = r.json()["program"]
        assert p["coach_kind"] == "ai" and p["can_renew"] is False and p["total_weeks"] == 4
        cyc = p["cycle"]
        assert cyc["has_cycle_end"] and cyc["day_index"] in (11, 12) and cyc["days_left"] in (17, 18)
        assert not cyc["ending_soon"] and not cyc["is_finished"] and p["current_week_index"] == 2
        # bitmemiş döngü → 409
        r = client.post("/ai-coach/renew-cycle", headers=h)
        assert r.status_code == 409 and r.json()["detail"]["code"] == "cycle_not_finished"
        # bitmiş döngü → can_renew, son hafta tekrar, bildirim işareti (arka plan) atılır
        cur = conn.cursor()
        cur.execute("UPDATE workout_programs SET created_at = (CURRENT_DATE - 30) + TIME '10:00' WHERE id = %s", (pid,))
        conn.commit()
        r = client.get("/client/workouts/active", headers=h)
        p = r.json()["program"]
        assert p["cycle"]["is_finished"] and p["cycle"]["days_left"] == 0 and p["can_renew"] is True
        assert p["current_week_index"] == 4 and r.json()["week"]  # 28. günden sonra 4. hafta
        # tek haftalık şablon: bitiş yok, yenileme yok
        cur.execute("UPDATE workout_programs SET is_active = FALSE WHERE id = %s", (pid,)); conn.commit()
        _insert_multiweek_program(conn, uid, 60, weeks=1, days_ago=90)
        r = client.get("/client/workouts/active", headers=h)
        p = r.json()["program"]
        assert p["cycle"]["has_cycle_end"] is False and p["can_renew"] is False and p["current_week_index"] == 1
        r = client.post("/ai-coach/renew-cycle", headers=h)
        assert r.status_code == 409 and r.json()["detail"]["code"] == "no_cycle"
    finally:
        pool.putconn(conn)


def test_program_cycle_end_coach_side_and_maintenance(client):
    from app.core.database import _get_pool
    coach_email = f"smoke-coach-{uuid.uuid4().hex[:8]}@fithubpoint-test.com"
    r = client.post("/auth/coach-signup", json={"full_name": "Döngü Koçu", "email": coach_email, "password": "Sifre12345"})
    assert r.status_code == 200, r.text
    coach_h = {"Authorization": f"Bearer {r.json()['token']}"}
    user = _register_user(client)
    student_h = {"Authorization": f"Bearer {user['token']}"}
    pool = _get_pool(); conn = pool.getconn()
    try:
        coach_id = _user_id(conn, coach_email)
        uid = _user_id(conn, user["email"])
        cur = conn.cursor()
        cur.execute("UPDATE clients SET assigned_coach_id = %s WHERE user_id = %s", (coach_id, uid))
        conn.commit()
        pid = _insert_multiweek_program(conn, uid, coach_id, weeks=4, days_ago=26)  # 27. gün → son 2 gün

        # Koç panosu: canlı liste + sayaç
        r = client.get("/coach/dashboard/summary", headers=coach_h)
        assert r.status_code == 200, r.text
        ending = r.json()["needed"]["program_ending"]
        me = next(x for x in ending if x["student_id"] == uid)
        assert me["program_id"] == pid and me["program_days_left"] in (1, 2) and me["program_finished"] is False
        assert r.json()["kpi"]["program_ending_count"] >= 1
        # Öğrenci listesi: program_days_left / program_finished
        r = client.get("/coach/students/active", headers=coach_h)
        row = next(x for x in r.json()["students"] if x["student_id"] == uid)
        assert row["program_days_left"] in (1, 2) and row["program_finished"] is False

        # Bakım: dry-run listeler, gerçek koşu bir kez bildirir, tekrar koşu boş
        ah = {"X-Admin-Key": os.environ["ADMIN_API_KEY"]}
        assert client.post("/admin/maintenance/notify-program-endings").status_code == 401
        r = client.post("/admin/maintenance/notify-program-endings?dry_run=1", headers=ah)
        assert r.status_code == 200 and r.json()["dry_run"] is True
        cand = next(c for c in r.json()["candidates"] if c["program_id"] == pid)
        assert cand["kind"] == "coach" and cand["is_finished"] is False
        r = client.post("/admin/maintenance/notify-program-endings", headers=ah)
        assert r.status_code == 200, r.text
        done = next(n for n in r.json()["notified"] if n["program_id"] == pid)
        assert done["kind"] == "coach" and done["coach_email_sent"] is False  # Resend kapalı → no-op
        r = client.post("/admin/maintenance/notify-program-endings", headers=ah)
        assert pid not in [n["program_id"] for n in r.json()["notified"]]
        cur.execute("SELECT cycle_end_notified_at FROM workout_programs WHERE id = %s", (pid,))
        assert cur.fetchone()["cycle_end_notified_at"] is not None
        cur.execute("SELECT action_type FROM activity_log WHERE client_user_id = %s ORDER BY id DESC LIMIT 1", (uid,))
        assert cur.fetchone()["action_type"] == "program_cycle_end"

        # Öğrenci tarafı: gerçek koç → yenileme yok, "bitmek üzere"
        r = client.get("/client/workouts/active", headers=student_h)
        p = r.json()["program"]
        assert p["coach_kind"] == "coach" and p["can_renew"] is False and p["cycle"]["ending_soon"]
        r = client.post("/ai-coach/renew-cycle", headers=student_h)
        assert r.status_code == 402  # AI aboneliği yok
    finally:
        pool.putconn(conn)


def test_push_token_lookup_returns_registered_tokens(client):
    """Havuz RealDictCursor → eski row[0] KeyError veriyordu; token'lı kullanıcıda push hiç gitmiyordu."""
    from app.services.push_notification import _get_user_tokens, _remove_token
    from app.core.database import _get_pool
    user = _register_user(client)
    h = {"Authorization": f"Bearer {user['token']}"}
    tok = f"smoke-fcm-{uuid.uuid4().hex}"
    r = client.post("/client/fcm-token", json={"fcm_token": tok, "platform": "android"}, headers=h)
    assert r.status_code == 200, r.text
    pool = _get_pool(); conn = pool.getconn()
    try:
        uid = _user_id(conn, user["email"])
    finally:
        pool.putconn(conn)
    assert tok in _get_user_tokens(uid)
    _remove_token(tok)
    assert tok not in _get_user_tokens(uid)


# ─── Koç: çok haftalı program, taslak atama, v3 üretim koruması ─────────────

def _coach_and_student(client):
    """Yeni koç + ona atanmış yeni öğrenci; (coach_h, student_h, coach_id, uid)."""
    from app.core.database import _get_pool
    coach_email = f"smoke-coach-{uuid.uuid4().hex[:8]}@fithubpoint-test.com"
    r = client.post("/auth/coach-signup", json={"full_name": "Program Koçu", "email": coach_email, "password": "Sifre12345"})
    assert r.status_code == 200, r.text
    coach_h = {"Authorization": f"Bearer {r.json()['token']}"}
    user = _register_user(client)
    student_h = {"Authorization": f"Bearer {user['token']}"}
    pool = _get_pool(); conn = pool.getconn()
    try:
        coach_id = _user_id(conn, coach_email); uid = _user_id(conn, user["email"])
        cur = conn.cursor()
        cur.execute("UPDATE clients SET assigned_coach_id = %s WHERE user_id = %s", (coach_id, uid))
        conn.commit()
    finally:
        pool.putconn(conn)
    return coach_h, student_h, coach_id, uid


def _day(title, *names):
    return {"title": title, "kcal": "", "coach_note": "", "warmup": {"duration_min": "5", "items": []},
            "blocks": [{"title": "Ana Blok", "items": [{"type": "exercise", "name": n, "sets": 3, "reps": "10", "notes": ""} for n in names]}]}


def test_coach_multiweek_program_save_latest_assign(client):
    coach_h, student_h, coach_id, uid = _coach_and_student(client)
    sid = uid
    # Tek haftalık kayıt (eski biçim) hâlâ çalışır
    r = client.post(f"/coach/students/{sid}/workout-programs", json={"week": {"mon": _day("Upper", "Push-up")}}, headers=coach_h)
    assert r.status_code == 200 and r.json()["total_weeks"] == 1, r.text
    # İki haftalık kayıt (admin hafta sekmeleri)
    weeks = {"1": {"mon": _day("Upper A", "Push-up", "Row"), "thu": _day("Lower A", "Squat")},
             "2": {"mon": _day("Upper B", "Dip"), "thu": _day("Lower B", "Lunge")}}
    r = client.post(f"/coach/students/{sid}/workout-programs", json={"weeks": weeks, "title": "İki Hafta"}, headers=coach_h)
    assert r.status_code == 200 and r.json()["total_weeks"] == 2, r.text
    pid = r.json()["program_id"]
    r = client.get(f"/coach/students/{sid}/workout-programs/latest", headers=coach_h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["program_id"] == pid and j["total_weeks"] == 2 and j["is_active"] is False and j["title"] == "İki Hafta"
    assert j["weeks"]["2"]["thu"]["title"] == "Lower B" and j["weeks"]["1"]["mon"]["blocks"][0]["items"][1]["name"] == "Row"
    # Düz liste kütüphane eşleşmesiyle kanonik ada çözülür (test DB'de bulanık eşleşme) → sadece sayı
    assert len(j["week"]["mon"]) == 2 and j["weeks"]["1"]["tue"] is None
    # Ata → öğrenci tarafında 2 haftalık döngü (14 gün)
    r = client.post(f"/coach/students/{sid}/workout-programs/assign", headers=coach_h)
    assert r.status_code == 200, r.text
    r = client.get("/client/workouts/active", headers=student_h)
    assert r.status_code == 200, r.text
    p = r.json()["program"]
    assert p["id"] == pid and p["total_weeks"] == 2 and p["coach_kind"] == "coach"
    assert p["cycle"]["has_cycle_end"] and p["cycle"]["total_days"] == 14 and p["cycle"]["day_index"] == 1
    assert r.json()["weeks"]["2"]["mon"]["title"] == "Upper B"
    # v3 üretimi: atanmamış öğrenci → 403 (pipeline'a hiç girmez)
    other = _register_user(client)
    from app.core.database import _get_pool
    pool = _get_pool(); conn = pool.getconn()
    try:
        other_id = _user_id(conn, other["email"])
    finally:
        pool.putconn(conn)
    r = client.post(f"/coach/students/{other_id}/workout-programs/generate-v3", headers=coach_h)
    assert r.status_code == 403


def test_coach_drafts_assign_writes_real_rows(client):
    """Taslak atama eskiden var olmayan kolonlara INSERT atıp 500 veriyordu."""
    coach_h, student_h, coach_id, uid = _coach_and_student(client)
    sid = uid
    payload = {"mon": _day("Taslak Günü", "Plank"), "wed": _day("Orta", "Squat")}
    r = client.post(f"/coach/students/{sid}/workout-drafts", json={"name": "Taslak A", "payload": payload}, headers=coach_h)
    assert r.status_code == 200, r.text
    draft_id = r.json()["draft"]["id"]
    r = client.post(f"/coach/students/{sid}/workout-drafts/{draft_id}/assign", headers=coach_h)
    assert r.status_code == 200, r.text
    pid = r.json()["program_id"]
    r = client.get("/client/workouts/active", headers=student_h)
    assert r.status_code == 200 and r.json()["program"]["id"] == pid
    assert r.json()["week"]["wed"]["title"] == "Orta" and r.json()["program"]["title"] == "Taslak A"
    # Çok haftalı taslak payload'ı da kabul edilir
    r = client.post(f"/coach/students/{sid}/workout-drafts", json={"name": "Taslak B", "payload": {"weeks": {"1": {"mon": _day("W1", "Row")}, "2": {"mon": _day("W2", "Dip")}}}}, headers=coach_h)
    assert r.status_code == 200, r.text
    r = client.post(f"/coach/students/{sid}/workout-drafts/{r.json()['draft']['id']}/assign", headers=coach_h)
    assert r.status_code == 200, r.text
    r = client.get("/client/workouts/active", headers=student_h)
    assert r.json()["program"]["total_weeks"] == 2 and r.json()["weeks"]["2"]["mon"]["title"] == "W2"
    # Beslenme taslağı atama
    meals = {"mon": [{"time": "08:00", "items": [{"name": "Yulaf", "amount": "60 g"}]}, {"time": "13:00", "items": [{"name": "Tavuk", "amount": "150 g"}]}]}
    r = client.post(f"/coach/students/{sid}/nutrition-drafts", json={"name": "Beslenme A", "payload": {"week": meals, "supplements": ["Kreatin"]}}, headers=coach_h)
    assert r.status_code == 200, r.text
    r = client.post(f"/coach/students/{sid}/nutrition-drafts/{r.json()['draft']['id']}/assign", headers=coach_h)
    assert r.status_code == 200, r.text
    r = client.get("/client/nutrition/active", headers=student_h)
    assert r.status_code == 200, r.text


def test_coach_detail_has_real_student_count(client):
    coach_h, student_h, coach_id, uid = _coach_and_student(client)
    r = client.get(f"/client/coaches/{coach_id}", headers=student_h)
    assert r.status_code == 200, r.text
    assert r.json()["coach"]["student_count"] == 1


def test_hidden_library_entries_excluded(client):
    """Migration 066: is_hidden=TRUE kayıtlar arama / isimle detay / alternatiflerde çıkmaz,
    id ile detay (eski programlar) çalışmaya devam eder."""
    if not _db_reachable():
        pytest.skip("DB yok")
    from app.core.database import _get_pool
    from psycopg2.extras import RealDictCursor
    _reset_rate_limits()
    user = _register_user(client)
    h = {"Authorization": f"Bearer {user['token']}"}
    tag = uuid.uuid4().hex[:6]
    pool = _get_pool()
    conn = pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        ids = {}
        for key, name, hidden in (("vis", f"Visible Press {tag}", False), ("hid", f"Hidden Demo {tag}", True)):
            cur.execute(
                """INSERT INTO exercise_library (external_id, canonical_name, movement_pattern, equipment_type,
                                                 primary_muscles, complexity, gif_url, level, category, is_hidden)
                   VALUES (%s, %s, 'horizontal_press', 'barbell', %s, 2, 'g', 'beginner', 'strength', %s) RETURNING id""",
                (f"hid-{tag}-{key}", name, [f"chest-{tag}"], hidden),
            )
            ids[key] = cur.fetchone()["id"]
        conn.commit()
    finally:
        pool.putconn(conn)

    r = client.get(f"/exercises/search?q={tag}", headers=h)
    assert r.status_code == 200, r.text
    names = [e["name"] for e in r.json()["exercises"]]
    assert f"Visible Press {tag}" in names and f"Hidden Demo {tag}" not in names

    r = client.get(f"/exercises/detail?id={ids['hid']}", headers=h)
    assert r.status_code == 200 and r.json().get("found") is True

    r = client.get(f"/exercises/detail?name=Hidden Demo {tag}", headers=h)
    assert r.status_code == 200 and not r.json().get("found")

    r = client.get(f"/client/exercise-alternatives?library_id={ids['vis']}", headers=h)
    assert r.status_code == 200, r.text
    alt_ids = {a["id"] for a in (r.json().get("alternatives") or r.json().get("items") or [])}
    assert ids["hid"] not in alt_ids


def test_app_config_and_state_features(client):
    """Migration 067: /config/app herkese açık bayraklar; /client/state 'features' taşır."""
    if not _db_reachable():
        pytest.skip("DB yok")
    r = client.get("/config/app")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["features"]["real_coaches_enabled"] is False
    assert body["ai_coach"]["name"] == "FitHub AI Coach" and body["ai_coach"]["trial_days"] == 7
    _reset_rate_limits()
    user = _register_user(client)
    h = {"Authorization": f"Bearer {user['token']}"}
    r = client.get("/client/state", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "NO_COACH" and r.json()["features"]["real_coaches_enabled"] is False
    # superadmin olmayan değiştiremez
    assert client.patch("/superadmin/features", json={"real_coaches_enabled": True}, headers=h).status_code == 403


def test_coach_waitlist_join_idempotent(client):
    if not _db_reachable():
        pytest.skip("DB yok")
    _reset_rate_limits()
    user = _register_user(client)
    h = {"Authorization": f"Bearer {user['token']}"}
    assert client.get("/client/coach-waitlist", headers=h).json() == {"joined": False}
    assert client.post("/client/coach-waitlist", json={"source": "home_card"}, headers=h).json() == {"joined": True}
    assert client.post("/client/coach-waitlist", json={}, headers=h).json() == {"joined": True}
    assert client.get("/client/coach-waitlist", headers=h).json() == {"joined": True}
