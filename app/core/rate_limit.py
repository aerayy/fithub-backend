"""Basit, bağımlılıksız istek sınırlayıcı (sliding window, süreç içi bellek).

Neden: login / register / şifre sıfırlama / OTP endpoint'lerinde hiç sınır
yoktu → şifre deneme (brute force / credential stuffing) ve SMS/e-posta
spam'ine açıktı. Render'da tek instance çalıştığımız için süreç içi sayaç
yeterli; çoklu instance'a geçilirse Redis'e taşınmalı.

Kullanım (route dekoratöründe, imza değişmeden):
    @router.post("/login", dependencies=[Depends(rate_limited("login", 20, 600))])

İstemci IP'si: Cloudflare arkasındayız → CF-Connecting-IP, yoksa
X-Forwarded-For'un ilk adresi, yoksa bağlantı adresi.
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request

_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)
_MAX_KEYS = 50_000  # bellek koruması

RATE_LIMIT_DETAIL = "Çok fazla deneme yapıldı. Lütfen biraz bekleyip tekrar dene."


def client_ip(request: Request) -> str:
    h = request.headers
    ip = h.get("cf-connecting-ip") or ""
    if not ip:
        xff = h.get("x-forwarded-for") or ""
        ip = xff.split(",")[0].strip() if xff else ""
    if not ip and request.client:
        ip = request.client.host or ""
    return ip or "unknown"


def allow(key: str, limit: int, window_sec: int) -> bool:
    """`window_sec` içinde `limit`'ten fazla istek → False. Thread-safe."""
    now = time.monotonic()
    with _lock:
        if key not in _hits and len(_hits) >= _MAX_KEYS:
            _hits.clear()
        q = _hits[key]
        cutoff = now - window_sec
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


def check(scope: str, key: str, limit: int, window_sec: int) -> None:
    """Fonksiyon içinden (ör. identifier bazlı) kullanım; aşımda 429."""
    if not allow(f"{scope}:{key}", limit, window_sec):
        raise HTTPException(status_code=429, detail=RATE_LIMIT_DETAIL)


def rate_limited(scope: str, limit: int, window_sec: int):
    """IP bazlı FastAPI bağımlılığı."""

    async def _dep(request: Request):
        check(scope, client_ip(request), limit, window_sec)

    return Depends(_dep)
