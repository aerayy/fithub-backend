"""Açılışta otomatik SQL migration.

Neden: migration'lar elle (psql/SSH) uygulanıyordu; deploy ile kod yeni,
DB eski kalabiliyordu ve uygulama adımı kişiye bağımlıydı. Artık her worker
açılışta `run_pending_migrations()` çağırır:

- `schema_migrations(filename, applied_at)` tablosu uygulananları tutar.
- Tablo YOKSA ve DB zaten kurulu ise (users tablosu var) mevcut tüm dosyalar
  "uygulanmış" kabul edilir (baseline) — hiçbir eski migration yeniden koşmaz.
  DB tamamen boşsa tüm dosyalar sırayla koşar.
- Uygulanmamış dosyalar numara sırasıyla koşar (dosya kendi BEGIN/COMMIT'ini
  içerebilir; autocommit bağlantıda çalışır).
- pg_advisory_lock ile 3 worker aynı anda koşmaz; kilidi alamayan bekler.
- Hata → exception (uygulama açılmaz → Render eski sürümü canlıda tutar).
- AUTO_MIGRATE=0 env ile kapatılabilir.
"""
import logging
import os
import time
import re
from pathlib import Path

import psycopg2

logger = logging.getLogger(__name__)

_LOCK_KEY = 72_119_001  # rastgele sabit; tüm worker'lar aynı kilidi kullanır
_FILE_RE = re.compile(r"^(\d{3,})_.*\.sql$")


def _migrations_dir() -> Path:
    # app/core/migrations.py → <repo>/migrations
    return Path(__file__).resolve().parents[2] / "migrations"


def _migration_files(directory: Path):
    files = []
    for p in sorted(directory.glob("*.sql")):
        m = _FILE_RE.match(p.name)
        if m:
            files.append((int(m.group(1)), p))
    files.sort(key=lambda t: (t[0], t[1].name))
    return [p for _, p in files]


def run_pending_migrations() -> dict:
    """Bekleyen migration'ları uygular. Özet dict döndürür."""
    if os.getenv("AUTO_MIGRATE", "1").strip() != "1":
        logger.info("migrations: AUTO_MIGRATE kapalı, atlandı")
        return {"skipped": True}

    from app.core.config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

    directory = _migrations_dir()
    files = _migration_files(directory)
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        host=DB_HOST, port=DB_PORT, connect_timeout=15,
    )
    conn.autocommit = True
    applied_now = []
    try:
        cur = conn.cursor()
        # Askıda kalan deploy'a karşı sigorta: kilit/ifade bekleme süreleri sınırlı.
        # Migration kilit alamazsa hızlıca hata verir → uygulama açılmaz → Render eski sürümü canlıda tutar.
        cur.execute("SET lock_timeout = '20s'")
        cur.execute("SET statement_timeout = '60s'")
        got_lock = False
        # Gunicorn worker boot zaman aşımı 120 sn: toplam bekleme bunun altında kalmalı.
        for _ in range(3):  # ~1 dk: başka bir instance migration çalıştırıyorsa bekle
            cur.execute("SELECT pg_try_advisory_lock(%s)", (_LOCK_KEY,))
            if cur.fetchone()[0]:
                got_lock = True
                break
            time.sleep(20)
        if not got_lock:
            raise RuntimeError("migrations: advisory lock alınamadı (başka bir migration askıda olabilir)")
        try:
            cur.execute("SELECT to_regclass('public.schema_migrations')")
            has_table = cur.fetchone()[0] is not None
            if not has_table:
                cur.execute(
                    """CREATE TABLE IF NOT EXISTS schema_migrations (
                         filename   TEXT PRIMARY KEY,
                         applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                       )"""
                )
                cur.execute("SELECT to_regclass('public.users')")
                db_initialized = cur.fetchone()[0] is not None
                if db_initialized:
                    # Mevcut DB: tüm dosyalar zaten elle uygulanmış kabul edilir.
                    for p in files:
                        cur.execute(
                            "INSERT INTO schema_migrations (filename) VALUES (%s) ON CONFLICT DO NOTHING",
                            (p.name,),
                        )
                    logger.warning(
                        "migrations: baseline — schema_migrations yoktu, %d mevcut dosya uygulanmış sayıldı",
                        len(files),
                    )
                    return {"baseline": len(files), "applied": []}

            cur.execute("SELECT filename FROM schema_migrations")
            done = {r[0] for r in cur.fetchall()}
            pending = [p for p in files if p.name not in done]
            for p in pending:
                if p.name.startswith("000_"):
                    # Başlangıç şeması: yalnızca boş DB'de çalışır. Kurulu DB'de (prod)
                    # tablolar zaten var → çalıştırmadan uygulanmış say.
                    cur.execute("SELECT to_regclass('public.users')")
                    if cur.fetchone()[0] is not None:
                        cur.execute("INSERT INTO schema_migrations (filename) VALUES (%s) ON CONFLICT DO NOTHING", (p.name,))
                        logger.info("migrations: %s atlandı (DB zaten kurulu), kayda alındı", p.name)
                        continue
                sql = p.read_text(encoding="utf-8")
                logger.info("migrations: uygulanıyor %s", p.name)
                cur.execute(sql)
                cur.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (p.name,))
                applied_now.append(p.name)
            if applied_now:
                logger.warning("migrations: %d dosya uygulandı: %s", len(applied_now), ", ".join(applied_now))
            else:
                logger.info("migrations: bekleyen yok (%d dosya kayıtlı)", len(done))
            return {"applied": applied_now}
        finally:
            try:
                cur.execute("SELECT pg_advisory_unlock(%s)", (_LOCK_KEY,))
            except Exception:
                pass
    finally:
        conn.close()
