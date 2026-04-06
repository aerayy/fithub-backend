"""Basic health check and config tests."""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_config_no_hardcoded_secrets():
    """Verify source code doesn't contain hardcoded secrets as defaults."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "app", "core", "config.py")
    with open(config_path) as f:
        source = f.read()

    # DB_PASSWORD default should not contain a real password
    assert 'Eray123!' not in source, \
        "DB_PASSWORD has hardcoded password in source code"

    # CORS should not default to wildcard
    assert "CORS_ORIGINS\", \"*\"" not in source, \
        "CORS_ORIGINS should not default to wildcard in source"

    # JWT_SECRET should not have guessable default
    assert "CHANGE_THIS" not in source, \
        "JWT_SECRET has guessable default in source code"


def test_google_client_id_not_hardcoded():
    """Google Client ID should come from env, not hardcoded."""
    from app.api.auth import GOOGLE_CLIENT_ID
    # If env not set, should be empty string, not hardcoded value
    if not os.getenv("GOOGLE_CLIENT_ID"):
        assert GOOGLE_CLIENT_ID == "", \
            "GOOGLE_CLIENT_ID should not be hardcoded in source"


def test_security_require_role_exists():
    """Verify require_role function is importable."""
    from app.core.security import require_role
    assert callable(require_role)


def test_onboarding_endpoint_has_auth():
    """Verify GET /onboarding/{user_id} requires authentication."""
    import inspect
    from app.api.onboarding import get_onboarding

    sig = inspect.signature(get_onboarding)
    param_names = list(sig.parameters.keys())
    assert "current_user" in param_names, \
        "GET /onboarding/{user_id} must have current_user (auth) parameter"


def test_debug_endpoint_has_auth():
    """Verify debug/db-info requires superadmin."""
    import inspect
    from app.api.subscriptions import debug_db_info

    sig = inspect.signature(debug_db_info)
    param_names = list(sig.parameters.keys())
    assert "current_user" in param_names, \
        "debug/db-info must have current_user (auth) parameter"
