"""migrations/000_baseline_schema.sql üretici (15 Eyl 2026).

Lokal DB'nin pg_catalog'undan, hiçbir migration dosyasında CREATE TABLE'ı olmayan
12 temel tablonun DDL'ini üretir. Sonraki migration'ların eklediği kolon/indeks/
kısıtlar baseline'a ALINMAZ (zincir onları kendisi ekler); NOT NULL kısıtları
(PG18 'n' contype) satır içi yazılmaz (PG16 uyumu).

Kullanım (prod kataloğu, salt okunur):
  ssh srv-...@ssh.frankfurt.render.com "cd /app && python3 -" < scripts/gen_baseline_schema.py > baseline_raw.sql
  .venv/bin/python scripts/filter_baseline_schema.py baseline_raw.sql   # → migrations/000_baseline_schema.sql
"""
import glob
import os
import re

import psycopg2
from dotenv import load_dotenv

load_dotenv(".env")  # Render'da .env yok, env zaten dolu
TABLES = ["users", "clients", "coaches", "client_onboarding", "coach_packages", "exercise_library",
          "subscriptions", "workout_programs", "workout_days", "workout_exercises",
          "nutrition_programs", "nutrition_meals"]

mig_text = ""
for f in sorted(glob.glob("migrations/*.sql")):
    if os.path.basename(f).startswith("000_"):
        continue
    mig_text += open(f, encoding="utf-8", errors="ignore").read() + "\n"
added_cols = set()
for m in re.finditer(r"ALTER TABLE\s+(?:IF EXISTS\s+)?(?:public\.)?(\w+)\s+ADD COLUMN\s+(?:IF NOT EXISTS\s+)?(\w+)", mig_text, re.I):
    added_cols.add((m.group(1).lower(), m.group(2).lower()))
# Aynı ALTER içinde virgülle birden fazla ADD COLUMN
for m in re.finditer(r"ALTER TABLE\s+(?:IF EXISTS\s+)?(?:public\.)?(\w+)\s+((?:ADD COLUMN[^;]*?,\s*)+ADD COLUMN[^;]*);", mig_text, re.I | re.S):
    for mm in re.finditer(r"ADD COLUMN\s+(?:IF NOT EXISTS\s+)?(\w+)", m.group(2), re.I):
        added_cols.add((m.group(1).lower(), mm.group(1).lower()))

def named_in_migrations(name: str) -> bool:
    return re.search(r"\b%s\b" % re.escape(name), mig_text) is not None

c = psycopg2.connect(dbname=os.getenv("DB_NAME", "fithub"), user=os.getenv("DB_USER", "postgres"),
                     password=os.getenv("DB_PASSWORD", ""), host=os.getenv("DB_HOST", "localhost"),
                     port=int(os.getenv("DB_PORT", "5433")))
cur = c.cursor()
out, fks, indexes = [], [], []
skipped_cols, skipped_cons = [], []
for t in TABLES:
    cur.execute("""SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod), a.attnotnull,
                          pg_get_expr(d.adbin, d.adrelid), a.attidentity
                   FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
                   WHERE a.attrelid=('public.'||%s)::regclass AND a.attnum>0 AND NOT a.attisdropped
                   ORDER BY a.attnum""", (t,))
    cols = []
    for name, typ, notnull, default, ident in cur.fetchall():
        if (t, name.lower()) in added_cols:
            skipped_cols.append(f"{t}.{name}")
            continue
        d = ""
        if ident in ("a", "d"):
            typ_out = typ
            d = " GENERATED %s AS IDENTITY" % ("ALWAYS" if ident == "a" else "BY DEFAULT")
        elif default and re.match(r"nextval\('", default):
            typ_out = "BIGSERIAL" if typ == "bigint" else "SERIAL"
        else:
            typ_out = typ
            if default is not None:
                d = " DEFAULT " + default
        cols.append("    %s %s%s%s" % (name, typ_out, " NOT NULL" if notnull else "", d))
    cur.execute("SELECT conname, contype, pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid=('public.'||%s)::regclass ORDER BY contype, conname", (t,))
    cons_inline, con_index_names = [], set()
    for conname, contype, condef in cur.fetchall():
        if contype == "n":  # PG18 named NOT NULL — attnotnull ile zaten yazıldı
            continue
        if contype != "p" and named_in_migrations(conname):
            skipped_cons.append(conname)  # zincir kendisi ekler
            continue
        if contype == "f":
            ref = re.search(r"REFERENCES\s+(?:public\.)?(\w+)", condef)
            if not ref or ref.group(1).lower() not in TABLES:
                skipped_cons.append(conname)
                continue
            fks.append((t, conname, condef))
        else:
            # Kısıt, migration'la eklenen bir kolona dayanıyorsa atla (kolon listesi veya CHECK ifadesi)
            tokens = {tok.lower() for tok in re.findall(r"[A-Za-z_]\w*", condef)}
            if any((t, tok) in added_cols for tok in tokens):
                skipped_cons.append(conname)
                continue
            cons_inline.append("    CONSTRAINT %s %s" % (conname, condef))
            if contype in ("p", "u"):
                con_index_names.add(conname)
    out.append("CREATE TABLE IF NOT EXISTS %s (\n%s\n);" % (t, ",\n".join(cols + cons_inline)))
    cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename=%s", (t,))
    for iname, idef in cur.fetchall():
        if iname in con_index_names or named_in_migrations(iname):
            continue
        m = re.search(r"\((.*)\)", idef)
        if m and any((t, cc.strip().split(" ")[0].strip('"').lower()) in added_cols for cc in m.group(1).split(",")):
            continue
        indexes.append(re.sub(r"^CREATE (UNIQUE )?INDEX ", lambda mm: "CREATE %sINDEX IF NOT EXISTS " % (mm.group(1) or ""), idef) + ";")
for t, conname, condef in fks:
    stmt = "ALTER TABLE %s ADD CONSTRAINT %s %s" % (t, conname, condef)
    out.append("DO $$ BEGIN\n  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '%s') THEN\n    EXECUTE '%s';\n  END IF;\nEND $$;" % (conname, stmt.replace("'", "''")))
out.extend(indexes)
header = """-- 000_baseline_schema.sql — BAŞLANGIÇ ŞEMASI (15 Eyl 2026, scripts/gen_baseline_schema.py ile üretildi)
-- Neden: users/clients/coaches/... tabloları hiçbir migration dosyasında yoktu (elle kurulmuştu);
-- boş bir veritabanına 001'den itibaren kurulum imkânsızdı (staging + CI DB testleri).
-- Sonraki migration'ların eklediği kolon/indeks/kısıtlar burada YOK, zincir onları ekler.
-- Çalıştırıcı kuralı (app/core/migrations.py): "000_" önekli dosyalar YALNIZCA users tablosu yoksa çalışır;
-- kurulu DB'de (prod/lokal) çalıştırılmadan 'uygulandı' olarak kaydedilir.

"""
import sys
sys.stdout.write(header + "\n\n".join(out) + "\n")
print("ham baseline üretildi | tablo", len(TABLES), "| FK", len(fks), "| indeks", len(indexes), file=sys.stderr)
print("atlanan kolonlar:", skipped_cols, file=sys.stderr)
print("atlanan kısıtlar:", skipped_cons, file=sys.stderr)
