# app/services/app_settings.py
"""Sunucu tarafı özellik bayrakları (app_settings tablosu, key='features').

Uygulama /config/app ve /client/state üzerinden okur; superadmin /superadmin/features ile değiştirir.
Kısa süreli süreç içi önbellek: her istekte DB'ye gitmemek için 60 sn.
"""
import json
import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)

DEFAULT_FEATURES: Dict[str, Any] = {
    "real_coaches_enabled": False,   # gerçek (insan) koç keşif + satın alma akışları
    "ai_coach_trial_days": 7,        # paywall metni için; asıl deneme süresi mağaza teklifinden gelir
    "ai_coach_name": "FitHub AI Coach",
}
_ALLOWED_TYPES = {"real_coaches_enabled": bool, "ai_coach_trial_days": int, "ai_coach_name": str}
_CACHE: Dict[str, Any] = {"features": None, "ts": 0.0}
CACHE_TTL_SECONDS = 60


def _row_value(row):
    if row is None:
        return None
    val = row["value"] if hasattr(row, "keys") else row[0]
    if isinstance(val, (bytes, str)):
        val = json.loads(val)
    return val


def get_features(db, force: bool = False) -> Dict[str, Any]:
    now = time.time()
    if not force and _CACHE["features"] is not None and now - _CACHE["ts"] < CACHE_TTL_SECONDS:
        return dict(_CACHE["features"])
    feats = dict(DEFAULT_FEATURES)
    try:
        cur = db.cursor()
        cur.execute("SELECT value FROM app_settings WHERE key = 'features'")
        val = _row_value(cur.fetchone())
        if isinstance(val, dict):
            feats.update(val)
    except Exception as e:  # tablo yoksa / DB hatası → varsayılanlar
        logger.warning("app_settings okunamadı, varsayılanlar kullanılıyor: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
    _CACHE["features"] = feats
    _CACHE["ts"] = now
    return dict(feats)


def set_features(db, patch: Dict[str, Any]) -> Dict[str, Any]:
    """Yalnızca bilinen anahtarları, doğru tipte kabul eder; ValueError fırlatır."""
    clean: Dict[str, Any] = {}
    for k, v in (patch or {}).items():
        if k not in _ALLOWED_TYPES:
            raise ValueError(f"Bilinmeyen ayar: {k}")
        t = _ALLOWED_TYPES[k]
        if t is bool and not isinstance(v, bool):
            raise ValueError(f"{k} true/false olmalı")
        if t is int and (isinstance(v, bool) or not isinstance(v, int) or v < 0 or v > 90):
            raise ValueError(f"{k} 0-90 arası tam sayı olmalı")
        if t is str and (not isinstance(v, str) or not v.strip() or len(v) > 60):
            raise ValueError(f"{k} 1-60 karakter metin olmalı")
        clean[k] = v.strip() if t is str else v
    merged = {**get_features(db, force=True), **clean}
    cur = db.cursor()
    cur.execute(
        """INSERT INTO app_settings (key, value, updated_at) VALUES ('features', %s, NOW())
           ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()""",
        (json.dumps(merged),),
    )
    db.commit()
    _CACHE["features"] = merged
    _CACHE["ts"] = time.time()
    return dict(merged)


def public_config(db) -> Dict[str, Any]:
    feats = get_features(db)
    return {
        "features": feats,
        "ai_coach": {"name": feats["ai_coach_name"], "trial_days": feats["ai_coach_trial_days"]},
    }
