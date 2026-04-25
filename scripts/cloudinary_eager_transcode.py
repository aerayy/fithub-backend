"""
Cloudinary EAGER TRANSCODE — kalıcı H.264 varyantları üretir.

Warmup script'in aksine bu, varyantı Cloudinary storage'a fiziksel olarak ekler.
Cache değil, gerçek dosya — eviction yok, sürekli hazır.

Her exercise video için cloudinary.uploader.explicit() çağrılır:
  eager=[{format: 'mp4', video_codec: 'h264'}]
  eager_async=False  (senkron — ne zaman bittiğini bilelim)

Kullanım:
    export CLOUDINARY_CLOUD_NAME=dxhvi9e1e
    export CLOUDINARY_API_KEY=...
    export CLOUDINARY_API_SECRET=...
    export DATABASE_URL=...
    python3 scripts/cloudinary_eager_transcode.py
"""
from __future__ import annotations

import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import cloudinary
import cloudinary.uploader
import psycopg2
from dotenv import load_dotenv

load_dotenv()

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "dxhvi9e1e")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")

if not all([API_KEY, API_SECRET, DATABASE_URL]):
    print("HATA: CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET, DATABASE_URL gerekli")
    sys.exit(1)

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET,
    secure=True,
)

CONCURRENCY = 4  # Cloudinary rate limit'e dikkat


def extract_public_id(url: str) -> str | None:
    """
    Cloudinary URL'inden public_id çıkar.
    Örnek: https://res.cloudinary.com/dxhvi9e1e/video/upload/v1772751299/exercises/Plank_Waist_.mp4
    → public_id = exercises/Plank_Waist_
    """
    if "/video/upload/" not in url:
        return None
    after = url.split("/video/upload/", 1)[1]
    # Strip version prefix v123456789/
    after = re.sub(r"^v\d+/", "", after)
    # Strip transformations (e.g. vc_h264/)
    while re.match(r"^[a-z0-9_,]+/", after) and not after.startswith(("exercises/", "fithub/", "user_")):
        after = after.split("/", 1)[1] if "/" in after else after
        break  # Sadece bir seviye atla
    # Strip extension
    if "." in after.rsplit("/", 1)[-1]:
        after = after.rsplit(".", 1)[0]
    return after


def eager_one(public_id: str) -> tuple[str, bool, str]:
    """Tek video için explicit + eager çağrı."""
    try:
        result = cloudinary.uploader.explicit(
            public_id,
            type="upload",
            resource_type="video",
            eager=[
                {"format": "mp4", "video_codec": "h264"},
            ],
            eager_async=False,
        )
        # Eager listesi var mı kontrol et
        eager_list = result.get("eager") or []
        if eager_list:
            return public_id, True, "ok"
        return public_id, True, "no_eager_in_response"
    except Exception as e:
        msg = str(e)[:120]
        return public_id, False, msg


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        """SELECT canonical_name, gif_url FROM exercise_library
           WHERE gif_url IS NOT NULL AND gif_url != ''
             AND gif_url LIKE '%/video/upload/%'"""
    )
    rows = cur.fetchall()
    conn.close()

    print(f"Toplam {len(rows)} Cloudinary video — eager transcode başlıyor")
    print(f"Concurrency: {CONCURRENCY}\n")

    success = 0
    failed = 0
    errors = []
    t_start = time.time()

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {}
        for name, url in rows:
            public_id = extract_public_id(url)
            if not public_id:
                continue
            futures[pool.submit(eager_one, public_id)] = (name, public_id)

        completed = 0
        for fut in as_completed(futures):
            name, pid = futures[fut]
            _, ok, msg = fut.result()
            completed += 1
            if ok:
                success += 1
            else:
                failed += 1
                errors.append((name, pid, msg))
                if len(errors) <= 10:
                    print(f"  ❌ {name} ({pid}): {msg}")
            if completed % 100 == 0:
                print(f"  ... {completed}/{len(rows)} tamamlandı (success={success}, failed={failed})")

    print(f"\n✅ Bitti — {time.time() - t_start:.1f}s")
    print(f"   Success: {success}/{len(rows)}")
    print(f"   Failed:  {failed}")
    if failed > 10:
        print(f"   (İlk 10 hata yukarıda gösterildi, toplam {failed})")


if __name__ == "__main__":
    sys.exit(main())
