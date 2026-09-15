"""Ham baseline (scripts/gen_baseline_schema.py çıktısı, prod kataloğu) → migrations/000_baseline_schema.sql

Lokal migration dosyalarına bakarak: migration'ların eklediği kolon/kısıt/indeksleri atar,
RENAME COLUMN'ları tersine uygular (baseline = migration ÖNCESİ durum). Kullanım:
  ssh <render> "cd /app && python3 -" < scripts/gen_baseline_schema.py > baseline_raw.sql   (üretici stdout'a yazar)
  .venv/bin/python scripts/filter_baseline_schema.py baseline_raw.sql
"""
import re, glob, os, sys
S = sys.argv[1] if len(sys.argv) > 1 else "baseline_raw.sql"
BASE = ("users","clients","coaches","client_onboarding","coach_packages","exercise_library","subscriptions","workout_programs","workout_days","workout_exercises","nutrition_programs","nutrition_meals")
raw = open(S, encoding="utf-8").read()
mig_text = ""
for f in sorted(glob.glob("migrations/*.sql")):
    if os.path.basename(f).startswith("000_"): continue
    mig_text += open(f, encoding="utf-8", errors="ignore").read() + "\n"
added_cols = set()
# Her ALTER TABLE ... ; ifadesi içinde tüm ADD [COLUMN] [IF NOT EXISTS] <kolon> geçişleri
for m in re.finditer(r"ALTER TABLE\s+(?:IF EXISTS\s+)?(?:ONLY\s+)?(?:public\.)?\"?(\w+)\"?\s+(.*?);", mig_text, re.I | re.S):
    t = m.group(1).lower()
    for mm in re.finditer(r"\bADD\s+(?:COLUMN\s+)?(?:IF NOT EXISTS\s+)?\"?(\w+)\"?", m.group(2), re.I):
        col = mm.group(1)
        if col.upper() in ("CONSTRAINT", "PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "COLUMN"): continue
        added_cols.add((t, col.lower()))
def named(n): return re.search(r"\b%s\b" % re.escape(n), mig_text) is not None
renames = {}  # (tablo, yeni_ad) -> eski_ad ; baseline migration ÖNCESİ durumu yansıtmalı
for m in re.finditer(r"ALTER TABLE\s+(?:public\.)?(\w+)\s+RENAME COLUMN\s+(\w+)\s+TO\s+(\w+)", mig_text, re.I):
    renames[(m.group(1).lower(), m.group(3).lower())] = m.group(2)
header, body = raw.split("\n\n", 1)
blocks = body.split("\n\n")
out, skipped_cols, skipped_cons = [], [], []
for b in blocks:
    b = b.strip("\n")
    if not b: continue
    m = re.match(r"CREATE TABLE IF NOT EXISTS (\w+) \(\n(.*)\n\);$", b, re.S)
    if m:
        t = m.group(1); lines = m.group(2).split("\n"); keep = []
        for l in lines:
            ls = l.strip().rstrip(",")
            if ls.startswith("CONSTRAINT "):
                name = ls.split()[1]
                tokens = {tok.lower() for tok in re.findall(r"[A-Za-z_]\w*", ls[len("CONSTRAINT ")+len(name):])}
                if (not ls.split()[2].startswith("PRIMARY") and named(name)) or any((t, tok) in added_cols for tok in tokens):
                    skipped_cons.append(name); continue
            else:
                col = ls.split()[0]
                if (t, col.lower()) in added_cols:
                    skipped_cols.append(f"{t}.{col}"); continue
                if (t, col.lower()) in renames:
                    l = l.replace(col, renames[(t, col.lower())], 1)
                    skipped_cols.append(f"{t}.{col}->{renames[(t, col.lower())]}")
            keep.append(l.rstrip(","))
        out.append("CREATE TABLE IF NOT EXISTS %s (\n%s\n);" % (t, ",\n".join(keep)))
        continue
    m = re.search(r"conname = '(\w+)'", b)
    if b.startswith("DO $$") and m:
        name = m.group(1)
        ref = re.search(r"REFERENCES\s+(\w+)", b)
        fkcols = re.search(r"FOREIGN KEY \((.*?)\)", b)
        t = re.search(r"ALTER TABLE (\w+)", b).group(1).lower()
        if named(name) or (ref and ref.group(1).lower() not in BASE) or (fkcols and any((t, c.strip().lower()) in added_cols for c in fkcols.group(1).split(","))):
            skipped_cons.append(name); continue
        out.append(b); continue
    m = re.match(r"CREATE (?:UNIQUE )?INDEX IF NOT EXISTS (\w+) ON (?:public\.)?(\w+)\b.*\((.*)\)", b)
    if m:
        iname, t, cols = m.group(1), m.group(2), m.group(3)
        if named(iname) or any((t, cc.strip().split(" ")[0].strip('"').lower()) in added_cols for cc in cols.split(",")):
            skipped_cons.append(iname); continue
        out.append(b); continue
    out.append(b)
header = header.replace("-- Kaynak: lokal DB pg_catalog (12 tablo), idempotent (IF NOT EXISTS / DO bloğu).", "-- Kaynak: PROD DB pg_catalog (salt okunur SSH, /app) + lokal migration dosyalarına göre filtre; idempotent.")
open("migrations/000_baseline_schema.sql", "w", encoding="utf-8").write(header + "\n\n" + "\n\n".join(out) + "\n")
print("filtrelenmiş baseline | atlanan kolon:", len(skipped_cols), "| atlanan kısıt/indeks:", len(skipped_cons))
