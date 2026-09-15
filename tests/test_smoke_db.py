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


@pytest.fixture(scope="module")
def user(client):
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
