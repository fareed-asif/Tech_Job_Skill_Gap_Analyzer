# module1_parser.py
# Module 1: Data Loader & Parser
# Team Member: Abdullah Amir (SP24-BAI-024)

import pandas as pd
import numpy as np
import json
import re
from datetime import datetime

# ── Helper for section headers ───────────────────────────
def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

def divider():
    print(f"  {'-'*51}")

def info(label, value):
    print(f"  {label:<30} {value}")


# ── Startup ──────────────────────────────────────────────
section("LIBRARIES")
info("pandas",    pd.__version__)
info("numpy",     np.__version__)
info("re module", re.__name__)


# ── SECTION 1: Load CSV ─────────────────────────────────
section("SECTION 1 — LOAD CSV")

CSV_PATH = "AI_Job_Market_Trends_2026.csv"

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    print(f"\n  ERROR: '{CSV_PATH}' not found.")
    print("  Make sure the CSV is in the same folder as this script.")
    raise

info("File loaded",   CSV_PATH)
info("Total rows",    df.shape[0])
info("Total columns", df.shape[1])
divider()
print(f"  Columns:")
for i, col in enumerate(df.columns, 1):
    print(f"    {i:>2}. {col}")
divider()
print(f"  First 3 rows preview:")
print()
print(df.head(3).to_string(index=False))


# ── SECTION 2: Clean Data ────────────────────────────────
section("SECTION 2 — CLEAN DATA")

rows_read    = len(df)
rows_skipped = 0

# Drop exact duplicates
before = len(df)
df = df.drop_duplicates()
dupes_removed = before - len(df)
info("Duplicate rows removed", dupes_removed)

# Regex cleaner
def clean_text(val):
    try:
        val = str(val)
        val = re.sub(r'<[^>]+>', '', val)
        val = re.sub(r'[^\w\s,.-]', '', val)
        val = re.sub(r'\s+', ' ', val).strip()
        return val.lower()
    except Exception:
        return ""

TEXT_COLS = ["job_title", "company_size", "company_industry",
             "country", "remote_type", "experience_level",
             "education_level", "hiring_urgency"]

print(f"\n  Applying regex cleaner to {len(TEXT_COLS)} text columns...")
for col in TEXT_COLS:
    df[col] = df[col].apply(clean_text)
    print(f"    ✓  {col}")

# Drop rows with missing key fields
try:
    df = df.dropna(subset=["job_title", "salary", "job_posting_year"])
except KeyError as e:
    print(f"\n  WARNING: Missing expected column {e} — check your CSV")
    raise

# Remove rows where job_title became empty after cleaning
bad_mask      = df["job_title"] == ""
rows_skipped += bad_mask.sum()
df            = df[~bad_mask].reset_index(drop=True)

# Build YYYY-MM month string
try:
    df["month"] = (
        df["job_posting_year"].astype(int).astype(str) + "-" +
        df["job_posting_month"].astype(int).astype(str).str.zfill(2)
    )
except Exception as e:
    print(f"\n  ERROR building month column: {e}")
    raise

divider()
info("Rows read from CSV",        rows_read)
info("Rows skipped (bad data)",   rows_skipped)
info("Rows remaining after clean",len(df))
info("Date range",                f"{df['month'].min()}  →  {df['month'].max()}")


# ── SECTION 3: Build Skills List ─────────────────────────
section("SECTION 3 — BUILD SKILL LISTS")

SKILL_COLS = ["skills_python", "skills_sql", "skills_ml",
              "skills_deep_learning", "skills_cloud"]

SKILL_LABELS = {
    "skills_python":        "python",
    "skills_sql":           "sql",
    "skills_ml":            "machine learning",
    "skills_deep_learning": "deep learning",
    "skills_cloud":         "cloud"
}

def row_to_skills(row):
    return [SKILL_LABELS[c] for c in SKILL_COLS if row[c] == 1]

df["skills"] = df.apply(row_to_skills, axis=1)
df = df[df["skills"].map(len) > 0].reset_index(drop=True)

info("Jobs with at least one skill", len(df))

divider()
print(f"  Skill demand breakdown:\n")
all_skills_flat = [s for skills in df["skills"] for s in skills]
from collections import Counter
skill_counts = Counter(all_skills_flat)
for skill, count in skill_counts.most_common():
    pct = (count / len(df)) * 100
    bar = "█" * int(pct / 3)
    print(f"    {skill:<20}  {count:>5} jobs  ({pct:5.1f}%)  {bar}")

divider()
print(f"  Sample — first job skill list:")
print(f"    {df['skills'].iloc[0]}")


# ── SECTION 4: Save JSON + Log ───────────────────────────
section("SECTION 4 — SAVE OUTPUT FILES")

records = []
for _, row in df.iterrows():
    records.append({
        "job_id":           int(row["job_id"]),
        "job_title":        row["job_title"],
        "company_industry": row["company_industry"],
        "company_size":     row["company_size"],
        "country":          row["country"],
        "remote_type":      row["remote_type"],
        "experience_level": row["experience_level"],
        "education_level":  row["education_level"],
        "salary":           int(row["salary"]),
        "hiring_urgency":   row["hiring_urgency"],
        "month":            row["month"],
        "skills":           row["skills"]
    })

with open("cleaned_jobs.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

log_lines = [
    f"Module 1 Processing Log — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    f"Rows read from CSV:       {rows_read}",
    f"Rows skipped (bad data):  {rows_skipped}",
    f"Rows saved to JSON:       {len(records)}",
]
with open("module1_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

info("cleaned_jobs.json", f"{len(records)} records saved")
info("module1_log.txt",   "processing log saved")


# ── Summary ──────────────────────────────────────────────
section("SUMMARY")
info("Started with",  f"{rows_read} rows")
info("Skipped",       f"{rows_skipped} rows (bad/empty data)")
info("Duplicates",    f"{dupes_removed} removed")
info("Saved",         f"{len(records)} clean job records")
info("Output files",  "cleaned_jobs.json, module1_log.txt")
print(f"\n  ✓  Module 1 complete! Run module2_skill_engine.py next.")
print(f"{'='*55}\n")