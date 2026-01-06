from fastapi import APIRouter

router = APIRouter(prefix="/client", tags=["client"])

# sadece yeni client endpointlerini burada import edeceğiz
# (onboarding/auth'a dokunmuyoruz)
try:
    from . import purchases  # noqa: F401
except Exception:
    # purchases.py yoksa bile server ayağa kalksın
    pass

try:
    from . import me  # noqa: F401
except Exception:
    pass

try:
    from . import coaches  # noqa: F401
except Exception:
    pass
