# module4_skill_card.py
# Module 4: OpenCV Skill Profile Card Generator
# Reads skill_report.json (output of Module 2) and generates
# a personalized skill profile card saved as skill_card.png

import cv2
import numpy as np
import json
from datetime import datetime

# ── Load skill_report.json from Module 2 ─────────────────
try:
    with open("skill_report.json", "r", encoding="utf-8") as f:
        report = json.load(f)
    print("Loaded skill_report.json successfully")
except FileNotFoundError:
    print("ERROR: skill_report.json not found.")
    print("Run module2_skill_engine.py first to generate it.")
    raise

# ── Extract data from report ──────────────────────────────
job_counts  = report["job_counts"]
trend_data  = report["trend_data"]
gap         = report["gap_analysis"]
total_jobs  = report["total_jobs"]
gap_score   = gap["gap_score"]
user_skills = gap["user_skills"]
missing_hot = gap["missing_hot_skills"]

# ── Get user name at runtime ──────────────────────────────
print("\nEnter your name for the skill card:")
user_name = input("  Full name: ").strip()
if not user_name:
    user_name = "Anonymous"

student_id = input("  Student ID (e.g. SP24-BAI-026): ").strip()
if not student_id:
    student_id = "COMSATS University"

print(f"\nGenerating skill card for: {user_name}")


# ════════════════════════════════════════════════════════════
# CARD DESIGN CONSTANTS
# ════════════════════════════════════════════════════════════

# Card dimensions
CARD_W = 900
CARD_H = 620

# ── Colours (BGR format — OpenCV uses BGR not RGB) ────────
C_BG          = (28,  28,  32)    # near-black background
C_PANEL       = (40,  40,  48)    # slightly lighter panel
C_BORDER      = (80,  80,  95)    # card border
C_WHITE       = (240, 238, 232)   # primary text
C_SUBTEXT     = (150, 148, 140)   # secondary text
C_ACCENT      = (255, 180,  60)   # gold accent (title bar)
C_HOT         = (80,  200, 100)   # green  — hot skill
C_STABLE      = (100, 160, 240)   # blue   — stable skill
C_DECLINING   = (80,  80,  200)   # purple — declining skill
C_MISSING     = (60,  60,  70)    # dark grey — missing skill bar
C_GAP_FILL    = (60,  130, 220)   # gap score bar fill
C_GAP_EMPTY   = (55,  55,  65)    # gap score bar empty

# Font
FONT       = cv2.FONT_HERSHEY_SIMPLEX
FONT_BOLD  = cv2.FONT_HERSHEY_DUPLEX

# Skill order — sorted by combined score descending
ALL_SKILLS = sorted(trend_data.keys(),
                    key=lambda s: trend_data[s]["combined_score"],
                    reverse=True)


# ════════════════════════════════════════════════════════════
# HELPER DRAWING FUNCTIONS
# ════════════════════════════════════════════════════════════

def draw_rounded_rect(img, x1, y1, x2, y2, radius, color, thickness=-1):
    """
    Draw a rectangle with rounded corners.
    Uses cv2.rectangle + cv2.circle at each corner.
    thickness=-1 fills the shape.
    """
    # Fill the main body
    cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
    cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
    # Round each corner with a filled circle
    for cx, cy in [(x1+radius, y1+radius), (x2-radius, y1+radius),
                   (x1+radius, y2-radius), (x2-radius, y2-radius)]:
        cv2.circle(img, (cx, cy), radius, color, thickness)


def draw_skill_bar(img, x, y, skill, bar_w=340, bar_h=22):
    """
    Draw one skill row:
      [bullet] skill name   [████████░░░] TIER BADGE  demand%
    Uses cv2.circle, cv2.rectangle, cv2.putText, cv2.line.
    """
    tier   = trend_data[skill]["classification"]
    owned  = skill in user_skills
    demand = job_counts.get(skill, 0)
    pct    = demand / max(total_jobs, 1)

    # Choose bar colour based on tier and ownership
    if owned:
        bar_color = C_HOT if tier == "hot" else (C_STABLE if tier == "stable" else C_DECLINING)
    else:
        bar_color = C_MISSING

    # Bullet circle
    cv2.circle(img, (x - 14, y + bar_h // 2), 5,
               bar_color if owned else C_BORDER, -1)

    # Skill name
    label = skill.title()
    cv2.putText(img, label, (x, y + 16),
                FONT, 0.48, C_WHITE if owned else C_SUBTEXT, 1, cv2.LINE_AA)

    # Bar background (empty track)
    bx = x + 160
    cv2.rectangle(img, (bx, y + 4), (bx + bar_w, y + bar_h), C_GAP_EMPTY, -1)

    # Bar fill — width proportional to market demand %
    fill_w = int(bar_w * pct)
    if fill_w > 0:
        fill_color = bar_color if owned else (40, 40, 50)
        cv2.rectangle(img, (bx, y + 4), (bx + fill_w, y + bar_h), fill_color, -1)

    # Thin bar border line
    cv2.rectangle(img, (bx, y + 4), (bx + bar_w, y + bar_h), C_BORDER, 1)

    # Tier badge
    badge_map = {
        "hot":      ("HOT",       C_HOT),
        "stable":   ("STABLE",    C_STABLE),
        "declining":("DECLINING", C_DECLINING),
    }
    badge_text, badge_color = badge_map[tier]
    if not owned:
        badge_text  = "MISSING " + badge_text
        badge_color = (120, 120, 140)

    bx2 = bx + bar_w + 10
    cv2.putText(img, badge_text, (bx2, y + 16),
                FONT, 0.38, badge_color, 1, cv2.LINE_AA)

    # Demand percentage on the right
    pct_text = f"{pct*100:.0f}% of jobs"
    cv2.putText(img, pct_text, (bx2 + 115, y + 16),
                FONT, 0.36, C_SUBTEXT, 1, cv2.LINE_AA)

    # Separator line below each skill row
    cv2.line(img, (x - 20, y + bar_h + 6),
             (CARD_W - 30, y + bar_h + 6), C_BORDER, 1)


def draw_gap_bar(img, x, y, w, h, score):
    """
    Draw the overall gap score progress bar.
    score = 0 means no gap (full bar green).
    score = 100 means complete gap (empty bar).
    Fill = 100 - score so a low gap = mostly filled.
    """
    filled = int(w * (1 - score / 100))
    cv2.rectangle(img, (x, y), (x + w, y + h), C_GAP_EMPTY, -1)
    if filled > 0:
        cv2.rectangle(img, (x, y), (x + filled, y + h), C_GAP_FILL, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), C_BORDER, 1)
    # Score text centred inside the bar
    label = f"{100 - score:.0f}% covered"
    (tw, th), _ = cv2.getTextSize(label, FONT, 0.45, 1)
    cv2.putText(img, label, (x + w // 2 - tw // 2, y + h // 2 + th // 2),
                FONT, 0.45, C_WHITE, 1, cv2.LINE_AA)


# ════════════════════════════════════════════════════════════
# BUILD THE CARD
# ════════════════════════════════════════════════════════════

# Step 1 — Create blank canvas using np.zeros()
card = np.zeros((CARD_H, CARD_W, 3), dtype=np.uint8)
card[:] = C_BG   # fill with background colour

# Step 2 — Outer card border (rounded rectangle)
draw_rounded_rect(card, 10, 10, CARD_W - 10, CARD_H - 10, 12, C_BORDER, 1)

# ── HEADER SECTION ────────────────────────────────────────
# Gold accent header bar
draw_rounded_rect(card, 10, 10, CARD_W - 10, 80, 12, C_ACCENT, -1)
# Cover bottom corners of header (make it flush)
cv2.rectangle(card, (10, 60), (CARD_W - 10, 80), C_ACCENT, -1)

# Title text on header
cv2.putText(card, "TECH JOB SKILL-GAP ANALYZER",
            (30, 45), FONT_BOLD, 0.75, C_BG, 2, cv2.LINE_AA)
cv2.putText(card, "AI Job Market Report  |  2020 - 2026",
            (30, 70), FONT, 0.42, C_BG, 1, cv2.LINE_AA)

# Dataset info top-right
info_text = f"{total_jobs:,} job postings"
(tw, _), _ = cv2.getTextSize(info_text, FONT, 0.38, 1)
cv2.putText(card, info_text,
            (CARD_W - tw - 25, 70), FONT, 0.38, C_BG, 1, cv2.LINE_AA)

# ── USER IDENTITY PANEL ───────────────────────────────────
panel_y = 92
draw_rounded_rect(card, 20, panel_y, CARD_W - 20, panel_y + 72, 8, C_PANEL, -1)

# User icon circle
cv2.circle(card, (58, panel_y + 36), 22, C_ACCENT, -1)
cv2.putText(card, user_name[0].upper(),
            (50, panel_y + 44), FONT_BOLD, 0.8, C_BG, 2, cv2.LINE_AA)

# Name and ID
cv2.putText(card, user_name,
            (90, panel_y + 28), FONT_BOLD, 0.65, C_WHITE, 1, cv2.LINE_AA)
cv2.putText(card, student_id + "  |  COMSATS University Islamabad",
            (90, panel_y + 52), FONT, 0.38, C_SUBTEXT, 1, cv2.LINE_AA)

# Generated date — right side of panel
date_str = datetime.now().strftime("%d %b %Y")
(tw, _), _ = cv2.getTextSize(date_str, FONT, 0.38, 1)
cv2.putText(card, date_str,
            (CARD_W - tw - 35, panel_y + 52), FONT, 0.38, C_SUBTEXT, 1, cv2.LINE_AA)

# Divider line inside panel
cv2.line(card, (85, panel_y + 8), (85, panel_y + 64), C_BORDER, 1)

# ── GAP SCORE SECTION ─────────────────────────────────────
gap_y = panel_y + 84

cv2.putText(card, "OVERALL GAP SCORE",
            (30, gap_y), FONT_BOLD, 0.48, C_SUBTEXT, 1, cv2.LINE_AA)

# Big gap score number
score_color = C_HOT if gap_score <= 30 else (C_ACCENT if gap_score <= 60 else (80, 80, 220))
cv2.putText(card, f"{gap_score:.1f}%",
            (30, gap_y + 44), FONT_BOLD, 1.4, score_color, 2, cv2.LINE_AA)

# Gap bar — drawn to the right of the number
draw_gap_bar(card, 160, gap_y + 14, 440, 28, gap_score)

# Interpretation label
if gap_score == 0:
    interp = "Perfect — all hot and stable skills covered"
elif gap_score <= 25:
    interp = "Strong profile — small gap remaining"
elif gap_score <= 60:
    interp = "Moderate gap — focus on hot skills next"
else:
    interp = "Large gap — prioritise hot skills immediately"

cv2.putText(card, interp,
            (160, gap_y + 58), FONT, 0.38, C_SUBTEXT, 1, cv2.LINE_AA)

# Priority recommendation
if missing_hot:
    rec = f"Start with:  {missing_hot[0].title()}"
    cv2.putText(card, rec,
                (620, gap_y + 58), FONT, 0.38, C_HOT, 1, cv2.LINE_AA)

# Divider line
div_y = gap_y + 70
cv2.line(card, (20, div_y), (CARD_W - 20, div_y), C_BORDER, 1)

# ── SKILL BREAKDOWN SECTION ───────────────────────────────
skills_y = div_y + 20

cv2.putText(card, "SKILL BREAKDOWN",
            (30, skills_y), FONT_BOLD, 0.48, C_SUBTEXT, 1, cv2.LINE_AA)

# Legend
legend_items = [
    (C_HOT,      "You have (hot)"),
    (C_STABLE,   "You have (stable)"),
    (C_DECLINING,"You have (declining)"),
    (C_MISSING,  "Missing"),
]
lx = 200
for lcolor, ltext in legend_items:
    cv2.rectangle(card, (lx, skills_y - 10), (lx + 12, skills_y + 2), lcolor, -1)
    cv2.putText(card, ltext, (lx + 16, skills_y),
                FONT, 0.33, C_SUBTEXT, 1, cv2.LINE_AA)
    lx += 130

# Draw one row per skill
row_y = skills_y + 18
for skill in ALL_SKILLS:
    draw_skill_bar(card, 40, row_y, skill)
    row_y += 40

# ── FOOTER ────────────────────────────────────────────────
footer_y = CARD_H - 28
cv2.line(card, (20, footer_y - 12), (CARD_W - 20, footer_y - 12), C_BORDER, 1)

footer_left  = "Programming for Artificial Intelligence  |  Semester End Project  |  May 2026"
footer_right = "Generated by Tech Job Skill-Gap Analyzer"
cv2.putText(card, footer_left,
            (25, footer_y + 4), FONT, 0.32, C_SUBTEXT, 1, cv2.LINE_AA)
(tw, _), _ = cv2.getTextSize(footer_right, FONT, 0.32, 1)
cv2.putText(card, footer_right,
            (CARD_W - tw - 25, footer_y + 4), FONT, 0.32, C_SUBTEXT, 1, cv2.LINE_AA)


# ════════════════════════════════════════════════════════════
# SAVE AND DISPLAY
# ════════════════════════════════════════════════════════════

# cv2.imwrite() saves the card as a PNG file
output_path = "skill_card.png"
success = cv2.imwrite(output_path, card)

if success:
    print(f"\nSkill card saved: {output_path}")
else:
    print("\nERROR: Failed to save skill_card.png")
    raise RuntimeError("cv2.imwrite failed — check that opencv-python is installed correctly")

# Print a summary of what was drawn
print("\nCard summary:")
print(f"  Name        : {user_name}")
print(f"  Student ID  : {student_id}")
print(f"  Gap Score   : {gap_score}%")
print(f"  Skills you have  : {user_skills or '(none)'}")
print(f"  Hot to learn     : {missing_hot or '(none)'}")
print(f"  Canvas size : {CARD_W} x {CARD_H} px  (np.zeros — {CARD_W*CARD_H*3:,} bytes)")

# cv2.imshow() — display the card in a window
# Press any key to close the window
print("\nDisplaying card — press any key to close the window...")
cv2.imshow("Skill Profile Card", card)
cv2.waitKey(0)
cv2.destroyAllWindows()

print("Module 4 complete.")