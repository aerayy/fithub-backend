"""
Cloudinary video warmup script — vc_h264 transformation cache'i ısıtır.

Sorun: Cloudinary `/video/upload/vc_h264/` URL'i ilk istekte cold transcode yapar
(5-30 saniye gecikme), kullanıcı uygulamada video yerine "GORSEL HENUZ EKLENMEDI"
görür. İkinci girişte transcode edilmiş versiyon cache'ten geldiği için anında oynar.

Bu script tüm exercise_library video URL'lerine vc_h264 ile bir kerelik HEAD/GET
isteği atar — Cloudinary tarafında transcode tetiklenir ve cache'e alınır.
Sonraki tüm gerçek kullanıcı istekleri anında sunulur.

Kullanım:
    cd fithub-backend
    python3 scripts/cloudinary_warmup_videos.py

DB ENV gerekli: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
veya tek seferlik DATABASE_URL ile.

Süre: ~10-15 dakika (2112 video, paralel 8 thread).
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}"
    )

CONCURRENCY = 8
TIMEOUT_SEC = 60  # ilk transcode 30+ sn olabilir


def to_h264_url(url: str) -> str:
    """Cloudinary video URL'ine vc_h264 transformation injecte eder."""
    if "/video/upload/" not in url:
        return url
    if "vc_h264" in url:
        return url
    return url.replace("/video/upload/", "/video/upload/vc_h264/", 1)


def warmup(url: str) -> tuple[str, int, float]:
    """URL'e GET at, status + süre döndür. Cloudinary'nin transcode'u tetiklenir."""
    h264 = to_h264_url(url)
    if h264 == url:
        return url, 0, 0.0  # Cloudinary değil, atlа
    t0 = time.time()
    try:
        # Range header ile sadece ilk birkaç KB iste — full download gereksiz,
        # sadece transcode'un başlamasını ve cache'lenmesini istiyoruz
        r = requests.get(
            h264,
            headers={"Range": "bytes=0-65535", "User-Agent": "FithubWarmup/1.0"},
            timeout=TIMEOUT_SEC,
            stream=True,
        )
        # Body'i okumadan kapat
        r.close()
        return h264, r.status_code, time.time() - t0
    except requests.RequestException as e:
        return h264, -1, time.time() - t0


def main():
    print(f"DB: {DATABASE_URL[:60]}...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        """SELECT canonical_name, gif_url FROM exercise_library
           WHERE gif_url IS NOT NULL AND gif_url != ''
             AND gif_url LIKE '%/video/upload/%'"""
    )
    rows = cur.fetchall()
    conn.close()

    print(f"Toplam {len(rows)} Cloudinary video — warmup başlıyor")
    print(f"Concurrency: {CONCURRENCY}, timeout: {TIMEOUT_SEC}s\n")

    success = 0
    failed = 0
    slow = []  # transcode süresi 5+ saniye olanlar
    t_start = time.time()

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {pool.submit(warmup, url): name for (name, url) in rows}
        completed = 0
        for fut in as_completed(futures):
            name = futures[fut]
            url, status, took = fut.result()
            completed += 1
            if status == 200 or status == 206:
                success += 1
                if took > 5:
                    slow.append((name, took))
            else:
                failed += 1
                print(f"  ❌ {name}: status={status}, {took:.1f}s")
            if completed % 100 == 0:
                print(f"  ... {completed}/{len(rows)} tamamlandı (success={success}, failed={failed})")

    print(f"\n✅ Bitti — {time.time() - t_start:.1f}s")
    print(f"   Success: {success}/{len(rows)}")
    print(f"   Failed:  {failed}")
    print(f"   Slow (>5s, ilk transcode):  {len(slow)}")
    if slow[:5]:
        print("\n   En yavaş 5:")
        for n, t in sorted(slow, key=lambda x: -x[1])[:5]:
            print(f"     {t:5.1f}s — {n}")


if __name__ == "__main__":
    sys.exit(main())
