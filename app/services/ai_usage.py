"""OpenAI token kullanımı kaydı — maliyet görünürlüğü.

Her üretim/analiz çağrısından sonra `record_usage(...)` çağrılır; kendi havuz
bağlantısını kullanır, ASLA hata fırlatmaz (üretim akışını bozmaz).
Superadmin `/superadmin/ai-usage` ile özet + tahmini USD görür.
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# USD / 1M token (giriş, çıkış) — Eylül 2026 liste fiyatları; tahmin amaçlı.
_PRICES = {
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
}


def _tok(usage: Any, name: str) -> Optional[int]:
    if usage is None:
        return None
    if isinstance(usage, dict):
        v = usage.get(name)
    else:
        v = getattr(usage, name, None)
    try:
        return int(v) if v is not None else None
    except Exception:
        return None


def record_usage(feature: str, model: Optional[str], usage: Any,
                 user_id: Optional[int] = None, duration_ms: Optional[int] = None) -> None:
    pt, ct, tt = _tok(usage, "prompt_tokens"), _tok(usage, "completion_tokens"), _tok(usage, "total_tokens")
    if tt is None and (pt is not None or ct is not None):
        tt = (pt or 0) + (ct or 0)
    conn = None
    pool = None
    try:
        from app.core.database import _get_pool
        pool = _get_pool()
        conn = pool.getconn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO ai_usage_log
               (user_id, feature, model, prompt_tokens, completion_tokens, total_tokens, duration_ms)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, feature[:64], (model or "")[:64] or None, pt, ct, tt, duration_ms),
        )
        conn.commit()
    except Exception as e:
        logger.warning("ai_usage: kayıt yazılamadı feature=%s: %s", feature, e)
        try:
            if conn is not None:
                conn.rollback()
        except Exception:
            pass
    finally:
        if pool is not None and conn is not None:
            try:
                pool.putconn(conn)
            except Exception:
                pass


def usage_summary(conn, days: int = 30) -> Dict[str, Any]:
    days = max(1, min(int(days or 30), 365))
    cur = conn.cursor()
    cur.execute(
        """SELECT feature, model, COUNT(*) AS calls,
                  COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
                  COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                  COALESCE(SUM(total_tokens), 0) AS total_tokens,
                  ROUND(AVG(duration_ms)) AS avg_duration_ms
           FROM ai_usage_log
           WHERE created_at > NOW() - make_interval(days => %s)
           GROUP BY feature, model
           ORDER BY total_tokens DESC""",
        (days,),
    )
    rows = [dict(r) for r in (cur.fetchall() or [])]
    total_usd = 0.0
    for r in rows:
        inp, outp = _PRICES.get(r.get("model") or "", (0.0, 0.0))
        usd = (float(r["prompt_tokens"] or 0) / 1e6) * inp + (float(r["completion_tokens"] or 0) / 1e6) * outp
        r["estimated_usd"] = round(usd, 4)
        r["avg_duration_ms"] = int(r["avg_duration_ms"]) if r.get("avg_duration_ms") is not None else None
        total_usd += usd
    return {"days": days, "rows": rows, "estimated_total_usd": round(total_usd, 2),
            "note": "Tahmini maliyet liste fiyatlarıyla hesaplanır; OpenAI faturası esastır."}
