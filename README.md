# Tech Job Skill-Gap Analyzer

An AI-powered Python desktop tool that ingests real-world tech job market data, extracts and ranks in-demand skills using trend regression analysis, and generates a personalized learning gap report.

---

## Team

| Member | ID | Module |
|---|---|---|
| Abdullah Amir | SP24-BAI-024 | Module 1 — Data Loader & Parser |
| Muhammad Mudasir | SP24-BAI-026 | Module 2 — Skill Extraction & Trend Engine |
| Fareed Asif | SP24-BAI-031 | Module 3 — Visualisation & Report Generator |

**Course:** Programming for Artificial Intelligence
**Institution:** COMSATS University Islamabad
**Submission:** Semester End Project — May 2026

---

## Overview

CS graduates and self-taught developers routinely invest time in skills that are fading from market demand while overlooking emerging ones. The Tech Job Skill-Gap Analyzer solves this by analyzing 10,345 real AI job postings across 7 years (2020–2026), applying linear regression to identify rising and declining skills, and comparing them against the user's self-reported skill set to produce a personalized, actionable gap report.

---

## Features

- Parses and cleans a 10,000+ row CSV dataset using Pandas and regex
- Extracts skill demand across 5 key tech skill categories
- Applies NumPy `polyfit()` linear regression per skill over monthly data
- Classifies each skill as **hot**, **stable**, or **declining** using a combined demand + trend score
- Accepts interactive user skill input at runtime
- Computes a weighted gap score across all skill tiers
- Generates 3 professional Matplotlib charts saved as PNG files
- Writes a plain-text personalized gap report
- Full Git workflow with per-member branches and a clean merged main

---

## Dataset

**File:** `AI_Job_Market_Trends_2026.csv`
**Rows:** 10,345 job postings
**Period:** January 2020 – December 2026

| Column | Description |
|---|---|
| `job_id` | Unique row identifier |
| `job_title` | e.g. AI Engineer, Data Scientist |
| `company_size` | Startup, SME, MNC |
| `company_industry` | Tech, Finance, Healthcare, etc. |
| `country` | USA, UK, India, Canada, etc. |
| `remote_type` | Remote / Hybrid / Onsite |
| `experience_level` | Entry / Mid / Senior |
| `years_experience` | Years of experience required |
| `education_level` | Bachelor / Master / PhD |
| `skills_python` | Binary flag — 1 = required |
| `skills_sql` | Binary flag — 1 = required |
| `skills_ml` | Binary flag — 1 = required |
| `skills_deep_learning` | Binary flag — 1 = required |
| `skills_cloud` | Binary flag — 1 = required |
| `salary` | Annual salary in USD |
| `job_posting_month` | Month (1–12) |
| `job_posting_year` | Year (2020–2026) |
| `hiring_urgency` | Low / Medium / High |
| `job_openings` | Number of open positions |

---

## Project Structure

```
TechJobSkillGapAnalyzer/
│
├── AI_Job_Market_Trends_2026.csv   # Dataset — place here before running
│
├── module1_parser.py               # Module 1: Data Loader & Parser
├── module2_skill_engine.py         # Module 2: Skill Extraction & Trend Engine
├── module3_report.py               # Module 3: Visualisation & Report Generator
│
├── cleaned_jobs.json               # Output of Module 1 → input of Module 2
├── skill_report.json               # Output of Module 2 → input of Module 3
│
├── module1_log.txt                 # Processing log (rows read / skipped / saved)
├── gap_report.txt                  # Personalized plain-text gap report
│
├── skills_demand_chart.png         # Chart 1: skill demand bar chart
├── gap_chart.png                   # Chart 2: your skills vs market demand
└── trend_chart.png                 # Chart 3: monthly trend lines
```

---

## Pipeline

The project is a three-stage pipeline. Each module produces a file the next one reads.

```
AI_Job_Market_Trends_2026.csv
        │
        ▼
module1_parser.py          →  cleaned_jobs.json  +  module1_log.txt
        │
        ▼
module2_skill_engine.py    →  skill_report.json
        │
        ▼
module3_report.py          →  3 PNG charts  +  gap_report.txt
```

---

## Setup

### Requirements

- Python 3.10 or higher
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/TechJobSkillGapAnalyzer.git
cd TechJobSkillGapAnalyzer

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install pandas numpy matplotlib
```

### Place the dataset

Copy `AI_Job_Market_Trends_2026.csv` into the `TechJobSkillGapAnalyzer/` folder before running any module.

---

## Usage

Run all three modules in order from the project folder with the virtual environment active.

### Step 1 — Run Module 1

```bash
python module1_parser.py
```

Reads the CSV, cleans all text fields using regex, reshapes binary skill columns into skill lists per job, and saves `cleaned_jobs.json` and `module1_log.txt`.

### Step 2 — Run Module 2

```bash
python module2_skill_engine.py
```

Loads `cleaned_jobs.json`, counts skill demand, applies monthly regression analysis, then prompts you to enter your skills interactively:

```
SKILL GAP ANALYZER — Enter Your Skills
==================================================
Valid options: python, sql, machine learning, deep learning, cloud
Press Enter with no input when done.

  Add skill (or press Enter to finish): python
  + Added: python
  Add skill (or press Enter to finish): sql
  + Added: sql
  Add skill (or press Enter to finish):

GAP ANALYSIS RESULTS
==================================================
  Gap Score            : 57.1%
  Your strengths (hot) : []
  Your stable skills   : ['python', 'sql']
  Hot to learn         : ['machine learning', 'cloud']
  Stable to learn      : []
  Deprioritize         : []
```

Saves `skill_report.json`.

### Step 3 — Run Module 3

```bash
python module3_report.py
```

Reads `skill_report.json`, generates 3 charts (each opens in a window — close it to continue), and writes `gap_report.txt`.

---

## Outputs

| File | Description |
|---|---|
| `cleaned_jobs.json` | Structured JSON of all cleaned job records |
| `skill_report.json` | Ranked skills, trend data, and gap analysis |
| `module1_log.txt` | Processing log: rows read, skipped, saved |
| `gap_report.txt` | Plain-text personalized gap report |
| `skills_demand_chart.png` | Top skills bar chart color-coded by tier |
| `gap_chart.png` | Your skills vs market demand comparison |
| `trend_chart.png` | Monthly demand trend lines (2020–2026) |

---

## Module Details

### Module 1 — Data Loader & Parser

**File:** `module1_parser.py`
**Owner:** Abdullah Amir (SP24-BAI-024)

- Reads `AI_Job_Market_Trends_2026.csv` using Pandas
- Cleans text fields with `re` (regex) — strips HTML tags, special characters, normalizes whitespace
- Handles missing fields and malformed rows using `try/except` blocks
- Maps binary skill columns to labeled skill lists per job
- Builds a `YYYY-MM` month string for trend analysis
- Saves `cleaned_jobs.json` and writes `module1_log.txt`

**Course topics covered:** File Handling, Regex, Dictionaries, Exception Handling, Loops & Control Structures

---

### Module 2 — Skill Extraction & Trend Engine

**File:** `module2_skill_engine.py`
**Owner:** Muhammad Mudasir (SP24-BAI-026)

- Defines a `SkillIndex` OOP class with three methods: `count_skills`, `compute_trends`, `compute_gap`
- Counts skill demand using `Counter` — returns `(skill, count)` tuple lists via `.most_common()`
- Groups jobs by month using Pandas, counts each skill per month, applies `np.polyfit()` regression
- Normalizes slope and demand scores to `[0, 1]`, computes a weighted combined score, and classifies:
  - **Hot** — top 2 skills by combined score
  - **Stable** — middle skills
  - **Declining** — bottom skill
- Accepts user skill input interactively at runtime
- Computes a weighted gap score: missing hot skill = 3 pts, missing stable = 1 pt, missing declining = 0 pts
- Saves `skill_report.json`

**Course topics covered:** OOP Classes, Pandas, NumPy, Regression Analysis, Data Structures, Tuples, Dicts

---

### Module 3 — Visualisation & Report Generator

**File:** `module3_report.py`
**Owner:** Fareed Asif (SP24-BAI-031)

- Reads `skill_report.json` and `cleaned_jobs.json`
- Generates 3 Matplotlib charts saved as high-resolution PNGs:
  - **Chart 1:** Horizontal bar chart of all skills color-coded by tier (hot/stable/declining)
  - **Chart 2:** Grouped bar chart comparing your skills vs market demand
  - **Chart 3:** Monthly trend lines for all skills (2020–2026), your skills shown as dashed lines
- Writes a plain-text `gap_report.txt` with overall gap score, strengths, and priority learning list
- Manages the team Git repository — branching strategy, PR merges, and final merge into main

**Course topics covered:** Matplotlib, Pandas, Functions, File Output, Debugging, Git & Version Control

---

## Course Topic Coverage

| Topic | Implementation |
|---|---|
| Python Basics & Operators | Arithmetic for score computation; logical operators for tier classification |
| Regular Expressions | Strips HTML tags, special characters, normalizes whitespace in Module 1 |
| Loops & Control Structures | Iterates over 10,000+ records; conditional branching for error handling |
| Functions | Modular functions across all 3 modules; report generator built as reusable functions |
| File Handling | CSV reading, JSON serialization, PNG output, plain-text report writing |
| Exception Handling | `try/except` for missing fields, encoding errors, file-not-found scenarios |
| Strings, Lists, Tuples, Dicts | Skill keyword lists, per-record dicts, frequency tuples, sorted string output |
| OOP | `SkillIndex` class encapsulates keyword list, scoring logic, and gap methods |
| NumPy | `polyfit()` regression per skill; array normalization for combined scoring |
| Pandas | DataFrame ingestion of CSV; `groupby` month for trend computation |
| Matplotlib | Bar, line, and comparison charts; color-coded tier visualization; PNG export |
| Regression Analysis | Linear regression slope computed per skill over monthly demand |
| Git & Version Control | Branching per module, pull request workflow, conflict resolution, merged main |

---

## Git Workflow

```bash
# Each member works on their own branch
git checkout module1/data-parser      # Abdullah
git checkout module2/skill-engine     # Mudasir
git checkout module3/report-generator # Fareed

# After completing work, push your branch
git add <your_module_file>.py
git commit -m "Complete Module X: description"
git push origin <your-branch>

# Fareed merges all branches into main
git checkout main
git merge module1/data-parser
git merge module2/skill-engine
git merge module3/report-generator
git push origin main
```

---

## License

This project was developed for academic purposes as part of the Programming for Artificial Intelligence course at COMSATS University Islamabad. Not licensed for commercial use.
