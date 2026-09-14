"""Cloudinary varlık temizliği (hesap silme, KVKK).

Neden: DELETE /auth/me kişisel satırları siliyordu ama Cloudinary'deki profil,
vücut formu, öğün ve sohbet görselleri kalıyordu. Bu modül URL'lerden public_id
çıkarır ve en iyi çaba ile siler; hata akışı bozmaz, yalnızca loglanır.
"""
import logging
import re
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"^https?://res\.cloudinary\.com/[^/]+/(image|video|raw)/upload/(.+)$")
_VERSION_RE = re.compile(r"^v\d+$")
_TRANSFORM_RE = re.compile(r"^[a-z]{1,3}_[^/]*$")


def cloudinary_public_id(url: Optional[str]) -> Optional[Tuple[str, str]]:
    """Cloudinary teslim URL'sinden (public_id, resource_type) çıkarır.

    Örnek: https://res.cloudinary.com/x/image/upload/c_limit,w_1200/v17/fithub/chat/ab.jpg
           → ("fithub/chat/ab", "image")
    Bilinmeyen/başka host → None.
    """
    m = _URL_RE.match((url or "").strip())
    if not m:
        return None
    rtype, rest = m.group(1), m.group(2)
    rest = rest.split("?", 1)[0].split("#", 1)[0]
    segs = [s for s in rest.split("/") if s]
    # Transformasyon (c_limit,w_1200 / q_auto) ve versiyon (v123) segmentlerini at
    while segs and (_VERSION_RE.match(segs[0]) or "," in segs[0] or _TRANSFORM_RE.match(segs[0])):
        segs.pop(0)
    if not segs:
        return None
    public_id = "/".join(segs)
    if rtype != "raw":
        public_id = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", public_id)
    return public_id, rtype


def delete_cloudinary_assets(urls: Iterable[str]) -> Dict[str, int]:
    """URL listesindeki Cloudinary varlıklarını siler (100'lük partiler). En iyi çaba."""
    grouped: Dict[str, List[str]] = {}
    for u in urls or []:
        parsed = cloudinary_public_id(u)
        if not parsed:
            continue
        pid, rtype = parsed
        grouped.setdefault(rtype, [])
        if pid not in grouped[rtype]:
            grouped[rtype].append(pid)
    if not grouped:
        return {}

    try:
        import cloudinary
        import cloudinary.api
        from app.core.config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
        if not CLOUDINARY_CLOUD_NAME:
            logger.warning("media_cleanup: Cloudinary yapılandırılmamış, %s varlık atlandı",
                           sum(len(v) for v in grouped.values()))
            return {}
        cloudinary.config(cloud_name=CLOUDINARY_CLOUD_NAME, api_key=CLOUDINARY_API_KEY,
                          api_secret=CLOUDINARY_API_SECRET)
    except Exception as e:  # pragma: no cover
        logger.warning("media_cleanup: cloudinary import/config hatası: %s", e)
        return {}

    deleted: Dict[str, int] = {}
    for rtype, ids in grouped.items():
        for i in range(0, len(ids), 100):
            chunk = ids[i:i + 100]
            try:
                cloudinary.api.delete_resources(chunk, resource_type=rtype, invalidate=True)
                deleted[rtype] = deleted.get(rtype, 0) + len(chunk)
            except Exception as e:
                logger.warning("media_cleanup: %s silinemedi (%d id): %s", rtype, len(chunk), e)
    logger.info("media_cleanup: silindi %s", deleted)
    return deleted
