# module3_report.py
# Module 3: Visualisation & Report Generator
# Team Member: Fareed Asif (SP24-BAI-031)

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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


# ── Load Data ────────────────────────────────────────────
section("LOAD DATA")

try:
    with open("skill_report.json", "r") as f:
        report = json.load(f)
    info("File", "skill_report.json")
except FileNotFoundError:
    print("\n  ERROR: skill_report.json not found.")
    print("  Run module2_skill_engine.py first to generate it.")
    raise

job_counts = report["job_counts"]
trend_data = report["trend_data"]
gap        = report["gap_analysis"]
total_jobs = report["total_jobs"]

info("Total jobs",      total_jobs)
info("Skills tracked",  ", ".join(job_counts.keys()))
info("Generated at",    report.get("generated_at", "—"))


# ── CHART 1: Skill Demand Bar Chart ─────────────────────
section("CHART 1 — SKILL DEMAND")

skills_list = list(job_counts.keys())
counts_list = [job_counts[s] for s in skills_list]

color_map = {"hot": "#1D9E75", "stable": "#378ADD", "declining": "#D85A30"}
colors = [color_map.get(trend_data.get(s, {}).get("classification", "stable"), "#378ADD")
          for s in skills_list]

print()
for skill, count in zip(skills_list, counts_list):
    tier  = trend_data.get(skill, {}).get("classification", "stable")
    pct   = round((count / total_jobs) * 100, 1)
    label = {"hot": "HOT", "stable": "stable", "declining": "declining"}[tier]
    print(f"  {skill:<22}  {count:>6} jobs  ({pct:>5.1f}%)  [{label}]")

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(skills_list, counts_list, color=colors, height=0.55, edgecolor="white")
for bar, count in zip(bars, counts_list):
    pct = round((count / total_jobs) * 100, 1)
    ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height() / 2,
            f"{count} ({pct}%)", va="center", fontsize=10)
legend = [
    mpatches.Patch(color="#1D9E75", label="Hot — rising"),
    mpatches.Patch(color="#378ADD", label="Stable"),
    mpatches.Patch(color="#D85A30", label="Declining")
]
ax.legend(handles=legend, loc="lower right", fontsize=10)
ax.set_title("AI Job Market — Skill Demand (2020–2026)", fontsize=13, fontweight="bold")
ax.invert_yaxis()
ax.grid(axis="x", alpha=0.4)
plt.tight_layout()
plt.savefig("skills_demand_chart.png", dpi=150)
plt.show()

divider()
info("Saved", "skills_demand_chart.png")


# ── CHART 2: Gap Comparison Chart ───────────────────────
section("CHART 2 — YOUR SKILLS VS MARKET")

user_skills = gap.get("user_skills", [])
missing_hot = gap.get("missing_hot_skills", [])
user_hot    = gap.get("user_hot_skills", [])
gap_score   = gap.get("gap_score", 0)

show_skills = list(dict.fromkeys(user_hot + missing_hot + list(job_counts.keys())))[:8]

print()
info("Your skills",  ", ".join(user_skills) or "(none)")
info("Gap score",    f"{gap_score}%")
print()

if show_skills:
    print(f"  {'Skill':<22}  {'Market':>7}  {'Yours':>7}  {'Difference':>10}")
    divider()
    market_vals = [job_counts.get(s, 0) for s in show_skills]
    user_vals   = [job_counts.get(s, 0) if s in user_skills else 0 for s in show_skills]
    for skill, mv, uv in zip(show_skills, market_vals, user_vals):
        diff = mv - uv
        print(f"  {skill:<22}  {mv:>7}  {uv:>7}  {diff:>+10}")

    x     = np.arange(len(show_skills))
    width = 0.38

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - width/2, market_vals, width, label="Market demand", color="#378ADD", alpha=0.85)
    ax.bar(x + width/2, user_vals,   width, label="Your skills",   color="#1D9E75", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(show_skills, rotation=30, ha="right", fontsize=10)
    ax.set_title(f"Your Skills vs Market Demand — Gap Score: {gap_score}%",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.4)
    plt.tight_layout()
    plt.savefig("gap_chart.png", dpi=150)
    plt.show()

divider()
info("Saved", "gap_chart.png")


# ── CHART 3: Monthly Trend Lines ─────────────────────────
section("CHART 3 — MONTHLY TREND LINES")

try:
    with open("cleaned_jobs.json", "r") as f:
        jobs_raw = json.load(f)
    info("File", "cleaned_jobs.json")

    rows = []
    for job in jobs_raw:
        month = job.get("month", "")
        if not month or month in ("NaT", "nan", ""):
            continue
        for skill in set(job.get("skills", [])):
            rows.append({"month": month, "skill": skill})

    import pandas as pd
    df_s   = pd.DataFrame(rows)
    months = sorted(df_s["month"].unique())

    info("Months in dataset",  len(months))
    info("Date range",         f"{months[0]}  →  {months[-1]}")

    user_skills_list = gap.get("user_skills", [])
    top_market       = list(job_counts.keys())
    all_to_plot      = list(dict.fromkeys(top_market + user_skills_list))

    print()
    print(f"  Plotting {len(all_to_plot)} skill line(s):")
    for skill in all_to_plot:
        tag = " (yours — dashed)" if skill in user_skills_list else ""
        print(f"    • {skill}{tag}")

    colors_market = ["#185FA5", "#1D9E75", "#D85A30", "#854F0B", "#534AB7"]

    fig, ax = plt.subplots(figsize=(13, 5))
    for i, skill in enumerate(all_to_plot):
        monthly = [len(df_s[(df_s["month"] == m) & (df_s["skill"] == skill)]) for m in months]
        is_user = skill in user_skills_list
        is_top  = skill in top_market
        color   = colors_market[top_market.index(skill) % len(colors_market)] if is_top else "#999"
        style   = "--" if is_user and not is_top else "-"
        lw      = 2.5 if is_user else 1.8
        label   = f"{skill} (yours)" if is_user else skill
        ax.plot(months, monthly, marker="o", label=label,
                color=color, linewidth=lw, linestyle=style, markersize=4)

    ax.set_title("Monthly Demand: Your Skills vs Market Top Skills (2020–2026)",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=9, ncol=2)
    ax.grid(alpha=0.4)
    plt.xticks(rotation=40, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig("trend_chart.png", dpi=150)
    plt.show()

    divider()
    info("Saved", "trend_chart.png")

except Exception as e:
    print(f"\n  WARNING: Trend chart skipped — {e}")


# ── Write gap_report.txt ─────────────────────────────────
section("GAP REPORT — gap_report.txt")

lines = []
lines.append("=" * 62)
lines.append("   AI JOB MARKET — PERSONALIZED SKILL GAP REPORT")
lines.append("=" * 62)
lines.append(f"  Generated:   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
lines.append(f"  Dataset:     {total_jobs} AI/tech job postings (2020–2026)")
lines.append("")
lines.append(f"  YOUR OVERALL GAP SCORE: {gap['gap_score']}%")
lines.append("")
lines.append("  " + "-" * 58)
lines.append("  YOUR STRENGTHS (hot skills you already have):")
lines.append("  " + "-" * 58)
for s in gap["user_hot_skills"]:
    count = job_counts.get(s, 0)
    pct   = round((count / total_jobs) * 100, 1)
    lines.append(f"    + {s:<28} in {count} jobs ({pct}%)")
if not gap["user_hot_skills"]:
    lines.append("    (none of your skills are classified as hot yet)")
lines.append("")
lines.append("  " + "-" * 58)
lines.append("  PRIORITY SKILLS TO LEARN:")
lines.append("  " + "-" * 58)
for i, s in enumerate(gap["missing_hot_skills"], 1):
    count = job_counts.get(s, 0)
    pct   = round((count / total_jobs) * 100, 1)
    lines.append(f"    {i}. {s:<28} in {count} jobs ({pct}%)  <- HOT")
lines.append("")
lines.append("  " + "-" * 58)
lines.append("  SKILLS TO DEPRIORITIZE (declining demand):")
lines.append("  " + "-" * 58)
for s in gap["user_declining_skills"]:
    lines.append(f"    - {s}")
if not gap["user_declining_skills"]:
    lines.append("    (none)")
lines.append("")
lines.append("=" * 62)

with open("gap_report.txt", "w") as f:
    f.write("\n".join(lines))

for line in lines:
    print(line)

divider()
info("Saved", "gap_report.txt")

# ── Summary ──────────────────────────────────────────────
section("SUMMARY — ALL OUTPUTS")

info("skills_demand_chart.png", "Chart 1 — skill demand by tier")
info("gap_chart.png",           "Chart 2 — your skills vs market")
info("trend_chart.png",         "Chart 3 — monthly trend lines")
info("gap_report.txt",          "plain-text personalized report")

print(f"\n  ✓  Module 3 complete!")
print(f"{'='*55}\n")