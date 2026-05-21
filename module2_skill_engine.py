# module2_skill_engine.py
# Module 2: Skill Extraction & Trend Engine
# Team Member: Muhammad Mudasir (SP24-BAI-026)

import json
import numpy as np
import pandas as pd
from datetime import datetime
from collections import Counter

# ── Helper for section headers ───────────────────────────
def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

def divider():
    print(f"  {'-'*51}")

def info(label, value):
    print(f"  {label:<30} {value}")


# ── Load cleaned_jobs.json ───────────────────────────────
section("LOAD DATA")

try:
    with open("cleaned_jobs.json", "r", encoding="utf-8") as f:
        jobs = json.load(f)
    info("File", "cleaned_jobs.json")
    info("Records loaded", len(jobs))
except FileNotFoundError:
    print("\n  ERROR: cleaned_jobs.json not found.")
    print("  Run module1_parser.py first to generate it.")
    raise


# ── SkillIndex Class ──────────────────────────────────────
class SkillIndex:
    def __init__(self):
        self.categories = {
            "python":           "programming",
            "sql":              "programming",
            "machine learning": "ai_ml",
            "deep learning":    "ai_ml",
            "cloud":            "infrastructure",
        }

    def count_skills(self, jobs_list):
        all_skills = []
        for job in jobs_list:
            all_skills.extend(job.get("skills", []))
        total_mentions = Counter(all_skills)

        job_counts = Counter()
        for job in jobs_list:
            for skill in set(job.get("skills", [])):
                job_counts[skill] += 1

        return dict(total_mentions.most_common()), dict(job_counts.most_common())

    def compute_trends(self, jobs_list):
        rows = []
        for job in jobs_list:
            month = job.get("month", "")
            if not month or month in ("NaT", "nan", ""):
                continue
            for skill in set(job.get("skills", [])):
                rows.append({"month": month, "skill": skill})

        df_s   = pd.DataFrame(rows)
        months = sorted(df_s["month"].unique())
        skills = list(self.categories.keys())

        raw = {}
        for skill in skills:
            monthly_counts = [
                len(df_s[(df_s["month"] == m) & (df_s["skill"] == skill)])
                for m in months
            ]
            x     = np.arange(len(months))
            y     = np.array(monthly_counts, dtype=float)
            slope = float(np.polyfit(x, y, deg=1)[0]) if y.sum() > 0 else 0.0
            raw[skill] = {
                "slope":          round(slope, 6),
                "total_mentions": int(y.sum()),
                "monthly_avg":    round(float(y.mean()), 2),
            }

        slopes  = np.array([raw[s]["slope"]         for s in skills], dtype=float)
        demands = np.array([raw[s]["total_mentions"] for s in skills], dtype=float)

        def normalise(arr):
            rng = arr.max() - arr.min()
            return (arr - arr.min()) / rng if rng > 0 else np.zeros_like(arr)

        norm_slopes  = normalise(slopes)
        norm_demands = normalise(demands)
        combined     = 0.4 * norm_slopes + 0.6 * norm_demands

        ranked_skills = [skills[i] for i in np.argsort(combined)[::-1]]
        trend_results = {}
        for rank, skill in enumerate(ranked_skills):
            if rank < 2:
                classification = "hot"
            elif rank >= len(ranked_skills) - 1:
                classification = "declining"
            else:
                classification = "stable"

            trend_results[skill] = {
                "slope":          raw[skill]["slope"],
                "total_mentions": raw[skill]["total_mentions"],
                "monthly_avg":    raw[skill]["monthly_avg"],
                "combined_score": round(float(combined[skills.index(skill)]), 4),
                "classification": classification,
            }

        return trend_results

    def compute_gap(self, user_skills, job_counts, trend_data):
        user_lower     = [s.strip().lower() for s in user_skills if s.strip()]
        tier_weight    = {"hot": 3, "stable": 1, "declining": 0}
        points_lost    = 0
        max_points     = 0
        missing_hot    = []
        missing_stable = []

        for skill, info in trend_data.items():
            weight      = tier_weight[info["classification"]]
            max_points += weight
            if skill not in user_lower:
                points_lost += weight
                if info["classification"] == "hot":
                    missing_hot.append(skill)
                elif info["classification"] == "stable":
                    missing_stable.append(skill)

        missing_hot.sort(key=lambda s: job_counts.get(s, 0), reverse=True)
        missing_stable.sort(key=lambda s: job_counts.get(s, 0), reverse=True)

        user_hot       = [s for s in user_lower if trend_data.get(s, {}).get("classification") == "hot"]
        user_stable    = [s for s in user_lower if trend_data.get(s, {}).get("classification") == "stable"]
        user_declining = [s for s in user_lower if trend_data.get(s, {}).get("classification") == "declining"]

        gap_score = round((points_lost / max(max_points, 1)) * 100, 1)

        return {
            "user_skills":           user_lower,
            "missing_hot_skills":    missing_hot[:10],
            "missing_stable_skills": missing_stable[:10],
            "user_hot_skills":       user_hot,
            "user_stable_skills":    user_stable,
            "user_declining_skills": user_declining,
            "gap_score":             gap_score,
        }


# ── Instantiate ───────────────────────────────────────────
si = SkillIndex()
info("SkillIndex ready", f"{len(si.categories)} skills tracked")


# ══════════════════════════════════════════════════════════
# SECTION 1 — Skill Demand Counts
# ══════════════════════════════════════════════════════════
section("SECTION 1 — SKILL DEMAND COUNTS")

all_counts, job_counts = si.count_skills(jobs)
ranked_tuples = sorted(job_counts.items(), key=lambda t: t[1], reverse=True)

info("Total jobs analyzed", len(jobs))
print()

print(f"  {'Rank':<6} {'Skill':<22} {'Jobs':>6}  {'% of Market':>11}  Chart")
divider()
for rank, (skill, count) in enumerate(ranked_tuples, 1):
    pct = (count / len(jobs)) * 100
    bar = "█" * int(pct / 3)
    print(f"  #{rank:<5} {skill:<22} {count:>6}  ({pct:>5.1f}%)     {bar}")


# ══════════════════════════════════════════════════════════
# SECTION 2 — Trend Analysis
# ══════════════════════════════════════════════════════════
section("SECTION 2 — TREND ANALYSIS")

print("  Running linear regression on monthly data...")
trend_data = si.compute_trends(jobs)

hot      = [s for s, v in trend_data.items() if v["classification"] == "hot"]
stable   = [s for s, v in trend_data.items() if v["classification"] == "stable"]
declining= [s for s, v in trend_data.items() if v["classification"] == "declining"]

print()
info("Hot skills (rising)",    ", ".join(hot)      or "(none)")
info("Stable skills",          ", ".join(stable)   or "(none)")
info("Declining skills",       ", ".join(declining) or "(none)")

divider()
print(f"  {'Skill':<22} {'Slope':>10}  {'Total':>7}  {'Avg/mo':>7}  {'Score':>7}  Tier")
divider()

TIER_LABEL = {"hot": "🔥 HOT", "stable": "  stable", "declining": "📉 declining"}
for skill, v in sorted(trend_data.items(), key=lambda x: x[1]["combined_score"], reverse=True):
    tag = TIER_LABEL[v["classification"]]
    print(f"  {skill:<22} {v['slope']:>10.6f}  {v['total_mentions']:>7}  "
          f"{v['monthly_avg']:>7.1f}  {v['combined_score']:>7.4f}  {tag}")


# ══════════════════════════════════════════════════════════
# SECTION 3 — Interactive Skill Input & Gap Analysis
# ══════════════════════════════════════════════════════════
section("SECTION 3 — ENTER YOUR SKILLS")

VALID_SKILLS = list(si.categories.keys())
print(f"  Valid options: {', '.join(VALID_SKILLS)}")
print("  Press Enter with no input when done.\n")

my_skills = []
while True:
    skill = input("  Add skill (or press Enter to finish): ").strip().lower()
    if skill == "":
        if not my_skills:
            print("  No skills entered — gap will reflect a complete beginner.")
        break
    if skill in VALID_SKILLS:
        if skill not in my_skills:
            my_skills.append(skill)
            print(f"  ✓  Added: {skill}")
        else:
            print(f"  Already in list: {skill}")
    else:
        print(f"  ✗  Not recognised. Valid options: {', '.join(VALID_SKILLS)}")

gap = si.compute_gap(my_skills, job_counts, trend_data)

section("GAP ANALYSIS RESULTS")

info("Your skills",         ", ".join(my_skills) or "(none)")
divider()
info("Gap Score",           f"{gap['gap_score']}%")
divider()
info("Your HOT skills",     ", ".join(gap['user_hot_skills'])      or "(none yet)")
info("Your stable skills",  ", ".join(gap['user_stable_skills'])   or "(none)")
info("Deprioritize",        ", ".join(gap['user_declining_skills']) or "(none)")
divider()

print(f"\n  Priority skills to learn:\n")
for i, s in enumerate(gap['missing_hot_skills'], 1):
    count = job_counts.get(s, 0)
    pct   = (count / len(jobs)) * 100
    print(f"  {i}. 🔥 {s:<22}  in {count} jobs ({pct:.1f}%)  ← HOT")
for i, s in enumerate(gap['missing_stable_skills'], len(gap['missing_hot_skills']) + 1):
    count = job_counts.get(s, 0)
    pct   = (count / len(jobs)) * 100
    print(f"  {i}.    {s:<22}  in {count} jobs ({pct:.1f}%)")

if not gap['missing_hot_skills'] and not gap['missing_stable_skills']:
    print("  (none — great profile!)")

print()
if gap["gap_score"] == 0.0:
    print("  ✓  Perfect score — you have all hot and stable skills.")
elif gap["gap_score"] <= 25.0:
    print("  ✓  Strong profile. Small gap remaining.")
elif gap["gap_score"] <= 60.0:
    print("  !  Moderate gap. Focus on hot skills first.")
else:
    print("  ✗  Large gap. Prioritise hot skills immediately.")


# ══════════════════════════════════════════════════════════
# SECTION 4 — Save skill_report.json
# ══════════════════════════════════════════════════════════
section("SECTION 4 — SAVE OUTPUT")

report = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "total_jobs":   len(jobs),
    "job_counts":   job_counts,
    "trend_data":   trend_data,
    "gap_analysis": gap,
}

with open("skill_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

info("skill_report.json", "saved")

print(f"\n  ✓  Module 2 complete! Run module3_report.py next.")
<<<<<<< HEAD
print(f"{'='*55}\n")
=======
print(f"{'='*55}\n")
>>>>>>> 50cc318acdd3f983552b6179138fe6e4c7f90472
