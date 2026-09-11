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
from typing import Optional

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


_UPSERT_SQL = """
INSERT INTO rate_limit_buckets (key, window_start, count)
VALUES (%(key)s, NOW(), 1)
ON CONFLICT (key) DO UPDATE SET
  count = CASE
            WHEN rate_limit_buckets.window_start < NOW() - make_interval(secs => %(win)s) THEN 1
            ELSE rate_limit_buckets.count + 1
          END,
  window_start = CASE
            WHEN rate_limit_buckets.window_start < NOW() - make_interval(secs => %(win)s) THEN NOW()
            ELSE rate_limit_buckets.window_start
          END
RETURNING count
"""

_db_unavailable_logged = False


def allow_db(conn, key: str, limit: int, window_sec: int) -> Optional[bool]:
    """DB destekli sabit pencere sayacı (migration 057 `rate_limit_buckets`).

    Tüm worker'lar aynı sayacı görür. Tablo yoksa / DB hatasında None döner
    (çağıran bellek yedeğine düşer) — auth asla rate limit yüzünden kırılmaz.
    """
    global _db_unavailable_logged
    try:
        cur = conn.cursor()
        cur.execute(_UPSERT_SQL, {"key": key, "win": window_sec})
        row = cur.fetchone()
        conn.commit()
        # Havuz bağlantıları RealDictCursor kullanıyor → satır dict gelir;
        # düz cursor'da tuple. İkisini de destekle (row[0] KeyError veriyordu →
        # sessizce bellek yedeğine düşüyor, DB sayacı hiç çalışmıyordu).
        if row is None:
            count = 0
        elif isinstance(row, dict):
            count = int(row.get("count", 0))
        else:
            count = int(row[0])
        return count <= limit
    except Exception as e:  # tablo yok, bağlantı sorunu vb.
        try:
            conn.rollback()
        except Exception:
            pass
        if not _db_unavailable_logged:
            _db_unavailable_logged = True
            import logging
            logging.getLogger(__name__).warning(
                "rate_limit: DB sayacı kullanılamıyor (migration 057 uygulandı mı?), bellek yedeği: %s", e
            )
        return None


def check(scope: str, key: str, limit: int, window_sec: int, db=None) -> None:
    """Fonksiyon içinden (ör. identifier bazlı) kullanım; aşımda 429.
    `db` verilirse önce DB sayacı denenir, olmazsa bellek."""
    full_key = f"{scope}:{key}"
    ok = allow_db(db, full_key, limit, window_sec) if db is not None else None
    if ok is None:
        ok = allow(full_key, limit, window_sec)
    if not ok:
        raise HTTPException(status_code=429, detail=RATE_LIMIT_DETAIL)


def rate_limited(scope: str, limit: int, window_sec: int):
    """IP bazlı FastAPI bağımlılığı (DB sayacı, yedek: bellek)."""
    from app.core.database import get_db

    async def _dep(request: Request, db=Depends(get_db)):
        check(scope, client_ip(request), limit, window_sec, db=db)

    return Depends(_dep)
