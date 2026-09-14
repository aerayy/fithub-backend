"""15 Eylül sertleştirme testleri — DB gerektirmez (CI'da AUTO_MIGRATE=0)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("AUTO_MIGRATE", "0")
os.environ.setdefault("SENTRY_DSN", "")


def test_cloudinary_public_id_parser():
    from app.services.media_cleanup import cloudinary_public_id

    assert cloudinary_public_id(
        "https://res.cloudinary.com/demo/image/upload/v1712345/fithub/chat/abc.jpg"
    ) == ("fithub/chat/abc", "image")
    assert cloudinary_public_id(
        "https://res.cloudinary.com/demo/image/upload/c_limit,w_1200/q_auto/v17/fithub/profile-photos/x.png"
    ) == ("fithub/profile-photos/x", "image")
    assert cloudinary_public_id(
        "https://res.cloudinary.com/demo/video/upload/v1/fithub/chat-voice/n.m4a"
    ) == ("fithub/chat-voice/n", "video")
    assert cloudinary_public_id("https://example.com/a.jpg") is None
    assert cloudinary_public_id(None) is None


def test_rate_limit_sliding_window():
    from app.core import rate_limit

    key = "test-hardening-key"
    assert rate_limit.allow(key, 2, 60) is True
    assert rate_limit.allow(key, 2, 60) is True
    assert rate_limit.allow(key, 2, 60) is False


def test_security_headers_and_request_id_on_live():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        r = client.get("/health/live", headers={"X-Request-ID": "abc123"})
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.headers["X-Request-ID"] == "abc123"
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in r.headers


def test_admin_key_header_required_for_debug_routes():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        r = client.get("/_openai_ping")
        assert r.status_code in (401, 422)  # header yoksa reddedilir
