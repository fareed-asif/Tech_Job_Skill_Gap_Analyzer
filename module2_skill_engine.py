# module2_skill_engine.py
# Module 2: Skill Extraction & Trend Engine
# Team Member: Muhammad Mudasir (SP24-BAI-026)

import json
import numpy as np
import pandas as pd
from datetime import datetime
from collections import Counter

# ── Load cleaned_jobs.json from Module 1 ─────────────────
try:
    with open("cleaned_jobs.json", "r", encoding="utf-8") as f:
        jobs = json.load(f)
    print(f"Loaded {len(jobs)} job records from cleaned_jobs.json")
except FileNotFoundError:
    print("ERROR: cleaned_jobs.json not found.")
    print("Run module1_parser.py first to generate it.")
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
        print(f"SkillIndex ready — {len(self.categories)} skills tracked")

    # ── Method 1: Count skill demand ─────────────────────
    def count_skills(self, jobs_list):
        """
        Count how many jobs require each skill.
        Returns:
          total_mentions : dict  — total times a skill appears across all jobs
          job_counts     : dict  — number of distinct jobs requiring each skill
        Both dicts are sorted highest to lowest by count.
        .most_common() returns a list of (skill, count) tuples — tuple data structure.
        """
        all_skills = []
        for job in jobs_list:
            all_skills.extend(job.get("skills", []))
        total_mentions = Counter(all_skills)

        # Count distinct jobs per skill (a skill mentioned twice in one job counts once)
        job_counts = Counter()
        for job in jobs_list:
            for skill in set(job.get("skills", [])):
                job_counts[skill] += 1

        # .most_common() returns list of (skill, count) tuples
        return dict(total_mentions.most_common()), dict(job_counts.most_common())

    # ── Method 2: Trend analysis via NumPy regression ────
    def compute_trends(self, jobs_list):
        """
        Groups job postings by month and counts each skill per month.
        Applies np.polyfit() linear regression (deg=1) to find the slope
        of demand over time for each skill.

        Classification uses a combined score of:
          - normalised slope  (direction of trend over time)
          - normalised demand (raw volume of jobs requiring the skill)
        The combined score ranks skills relative to each other, then:
          top 2    -> 'hot'
          bottom 1 -> 'declining'
          rest     -> 'stable'

        This approach is robust even when all slopes are small (e.g. a
        synthetically balanced dataset where every skill hovers near 50%).
        """
        # Build a flat row per (month, skill) occurrence
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

        # Step 1 — compute raw slope and total demand per skill
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

        # Step 2 — normalise slope and demand to [0, 1] across all skills
        slopes  = np.array([raw[s]["slope"]         for s in skills], dtype=float)
        demands = np.array([raw[s]["total_mentions"] for s in skills], dtype=float)

        def normalise(arr):
            rng = arr.max() - arr.min()
            return (arr - arr.min()) / rng if rng > 0 else np.zeros_like(arr)

        norm_slopes  = normalise(slopes)
        norm_demands = normalise(demands)

        # Combined score: 40% trend direction + 60% raw demand volume
        combined = 0.4 * norm_slopes + 0.6 * norm_demands

        # Step 3 — rank and classify relative to each other
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

    # ── Method 3: Personalised gap analysis ──────────────
    def compute_gap(self, user_skills, job_counts, trend_data):
        """
        Gap score is calculated across ALL skills weighted by tier:
          missing hot skill       = 3 penalty points  (most critical)
          missing stable skill    = 1 penalty point   (somewhat important)
          missing declining skill = 0 penalty points  (not penalised)

        Gap score = total penalty points / max possible points * 100

        This means having only hot skills but missing stable ones still
        produces a non-zero gap score, which is realistic and meaningful.
        """
        user_lower = [s.strip().lower() for s in user_skills if s.strip()]

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

        # Sort missing skills by raw job demand — highest priority first
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


# ══════════════════════════════════════════════════════════
# SECTION 1 — Skill demand counts
# ══════════════════════════════════════════════════════════
all_counts, job_counts = si.count_skills(jobs)

# sorted() on .items() produces (skill, count) tuples sorted by count
ranked_tuples = sorted(job_counts.items(), key=lambda t: t[1], reverse=True)

print(f"\nTotal jobs analyzed: {len(jobs)}")
print("\nSkill demand ranking — (skill, count) tuples:")
for skill, count in ranked_tuples:
    pct = (count / len(jobs)) * 100
    print(f"  {skill:<22} {count:>6} jobs  ({pct:.1f}%)")


# ══════════════════════════════════════════════════════════
# SECTION 2 — Trend analysis
# ══════════════════════════════════════════════════════════
trend_data = si.compute_trends(jobs)

hot       = [s for s, v in trend_data.items() if v["classification"] == "hot"]
stable    = [s for s, v in trend_data.items() if v["classification"] == "stable"]
declining = [s for s, v in trend_data.items() if v["classification"] == "declining"]

print("\nTrend Analysis Results:")
print(f"  Hot skills      : {hot}")
print(f"  Stable skills   : {stable}")
print(f"  Declining skills: {declining}")
print("\nDetailed breakdown:")
print(f"  {'Skill':<22} {'Slope':>10}  {'Total':>7}  {'Avg/mo':>7}  {'Score':>7}  Classification")
print("  " + "-" * 72)
for skill, info in sorted(trend_data.items(), key=lambda x: x[1]["combined_score"], reverse=True):
    tag = {"hot": "HOT", "stable": "stable", "declining": "declining"}[info["classification"]]
    print(f"  {skill:<22} {info['slope']:>10.6f}  {info['total_mentions']:>7}  "
          f"{info['monthly_avg']:>7.1f}  {info['combined_score']:>7.4f}  {tag}")


# ══════════════════════════════════════════════════════════
# SECTION 3 — Interactive skill input & gap analysis
# ══════════════════════════════════════════════════════════
VALID_SKILLS = list(si.categories.keys())

print("\n" + "=" * 50)
print("  SKILL GAP ANALYZER — Enter Your Skills")
print("=" * 50)
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
            print(f"  + Added: {skill}")
        else:
            print(f"  Already added: {skill}")
    else:
        print(f"  Not recognised. Valid options: {', '.join(VALID_SKILLS)}")

print(f"\n  Your skills: {my_skills}")

gap = si.compute_gap(my_skills, job_counts, trend_data)

print("\n" + "=" * 50)
print("  GAP ANALYSIS RESULTS")
print("=" * 50)
print(f"  Gap Score            : {gap['gap_score']}%")
print(f"  Your strengths (hot) : {gap['user_hot_skills']       or '(none yet)'}")
print(f"  Your stable skills   : {gap['user_stable_skills']    or '(none)'}")
print(f"  Deprioritize         : {gap['user_declining_skills']  or '(none)'}")
print(f"  Hot to learn         : {gap['missing_hot_skills']    or '(none)'}")
print(f"  Stable to learn      : {gap['missing_stable_skills'] or '(none)'}")

print()
if gap["gap_score"] == 0.0:
    print("  Perfect score — you have all hot and stable skills.")
elif gap["gap_score"] <= 25.0:
    print("  Strong profile. Small gap remaining.")
    if gap["missing_hot_skills"]:
        print(f"  One hot skill to add  : {gap['missing_hot_skills'][0]}")
    elif gap["missing_stable_skills"]:
        print(f"  Stable skill to add   : {gap['missing_stable_skills'][0]}")
elif gap["gap_score"] <= 60.0:
    print("  Moderate gap. Focus on hot skills first.")
    if gap["missing_hot_skills"]:
        print(f"  Start with: {gap['missing_hot_skills'][0]}")
else:
    print("  Large gap. Prioritise hot skills immediately.")
    if gap["missing_hot_skills"]:
        print(f"  Start with: {gap['missing_hot_skills'][0]}")


# ══════════════════════════════════════════════════════════
# SECTION 4 — Save skill_report.json
# ══════════════════════════════════════════════════════════
report = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "total_jobs":   len(jobs),
    "job_counts":   job_counts,
    "trend_data":   trend_data,
    "gap_analysis": gap,
}

with open("skill_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("\nSaved skill_report.json")
print("Module 2 complete — run module3_report.py next.")