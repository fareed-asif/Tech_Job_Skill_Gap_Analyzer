# module1_parser.py
# Module 1: Data Loader & Parser
# Team Member: Abdullah Amir (SP24-BAI-024)

import pandas as pd
import numpy as np
import json
import re                       # regex — built-in, no install needed
from datetime import datetime

print("Libraries ready!")
print("pandas:", pd.__version__)
print("numpy:", np.__version__)
print("re module:", re.__name__)


# ── SECTION 1: Load CSV ─────────────────────────────────
CSV_PATH = "AI_Job_Market_Trends_2026.csv"

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    print(f"ERROR: {CSV_PATH} not found.")
    print("Make sure the CSV is in the same folder as this script.")
    raise

print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
print("\nColumns:", list(df.columns))
print("\nFirst 3 rows:")
print(df.head(3).to_string())


# ── SECTION 2: Clean data (regex + exception handling) ──
rows_read    = len(df)
rows_skipped = 0

# Drop exact duplicates
before = len(df)
df = df.drop_duplicates()
print(f"Duplicates removed: {before - len(df)}")

# Regex cleaner — strips HTML tags, special chars, normalises whitespace
def clean_text(val):
    try:
        val = str(val)
        val = re.sub(r'<[^>]+>', '', val)       # remove HTML tags
        val = re.sub(r'[^\w\s,.-]', '', val)   # remove special chars
        val = re.sub(r'\s+', ' ', val).strip() # normalise whitespace
        return val.lower()
    except Exception:
        return ""   # malformed value → return empty string

# Apply regex cleaner to all text columns
for col in ["job_title", "company_size", "company_industry",
            "country", "remote_type", "experience_level",
            "education_level", "hiring_urgency"]:
    df[col] = df[col].apply(clean_text)

# Drop rows missing key fields
try:
    df = df.dropna(subset=["job_title", "salary", "job_posting_year"])
except KeyError as e:
    print(f"WARNING: Missing expected column {e} — check your CSV")
    raise

# Flag rows where job_title ended up empty after cleaning
bad_mask = df["job_title"] == ""
rows_skipped += bad_mask.sum()
df = df[~bad_mask].reset_index(drop=True)
print(f"Rows skipped (empty after cleaning): {rows_skipped}")

# Build a YYYY-MM month string for trend analysis
try:
    df["month"] = (
        df["job_posting_year"].astype(int).astype(str) + "-" +
        df["job_posting_month"].astype(int).astype(str).str.zfill(2)
    )
except Exception as e:
    print(f"ERROR building month column: {e}")
    raise

print(f"\nCleaned shape: {df.shape}")
print(f"Date range: {df['month'].min()} → {df['month'].max()}")


# ── SECTION 3: Build skills list per job ────────────────
SKILL_COLS = ["skills_python", "skills_sql", "skills_ml",
              "skills_deep_learning", "skills_cloud"]

# Map column names → clean skill labels
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

# Keep only jobs that require at least one skill
df = df[df["skills"].map(len) > 0].reset_index(drop=True)

print(f"Jobs with at least one skill: {len(df)}")
print("Sample skills list:", df["skills"].iloc[0])


# ── SECTION 4: Save cleaned_jobs.json + log ─────────────
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

# Save the cleaned JSON
with open("cleaned_jobs.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"Saved {len(records)} records to cleaned_jobs.json")

# ── Write processing log ──────────────────────────────────
log_lines = [
    f"Module 1 Processing Log — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    f"Rows read from CSV:      {rows_read}",
    f"Rows skipped (bad data): {rows_skipped}",
    f"Rows saved to JSON:      {len(records)}",
]
with open("module1_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))
for line in log_lines: print(line)
print("\nModule 1 complete! Run module2_skill_engine.py next.")