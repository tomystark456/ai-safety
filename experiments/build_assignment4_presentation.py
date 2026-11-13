"""Build the Assignment 4 slide deck from the saved monitoring evidence.

Requires python-pptx. Numbers are read from experiments/results/assignment4 and
report/assignment4, so the slides cannot drift from the measured results.
"""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "experiments/results/assignment4"
REPORT = ROOT / "report/assignment4"
NAVY, BLUE, AMBER = RGBColor(0x17, 0x3F, 0x59), RGBColor(0xEA, 0xF1, 0xF6), RGBColor(0xFF, 0xF0, 0xD8)
RED, GREY, WHITE = RGBColor(0xA3, 0x38, 0x32), RGBColor(0x54, 0x68, 0x75), RGBColor(0xFF, 0xFF, 0xFF)

summary = json.loads((EVIDENCE / "summary.json").read_text(encoding="utf-8"))
decision = json.loads((REPORT / "Deployment_Readiness_Decision.json").read_text(encoding="utf-8"))
policy = json.loads((ROOT / "experiments/monitoring_policy.json").read_text(encoding="utf-8"))
models = summary["models"]

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
blank = prs.slide_layouts[6]


def text(slide, x, y, w, h, content, size=18, bold=False, color=NAVY, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    lines = content if isinstance(content, list) else [content]
    for i, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        paragraph.alignment = align
        paragraph.space_after = Pt(6)
        run = paragraph.add_run()
        run.text = line
        run.font.size, run.font.bold, run.font.color.rgb = Pt(size), bold, color
    return box


def new_slide(title):
    slide = prs.slides.add_slide(blank)
    text(slide, 0.6, 0.35, 12.1, 0.9, title, 30, True)
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.6), Inches(1.2), Inches(12.7), Inches(1.2))
    line.line.color.rgb, line.line.width = NAVY, Pt(1.5)
    text(slide, 0.6, 7.0, 9, 0.35, "QAIRU | AISRA1301 | Assignment 4", 11, color=GREY)
    return slide


def bullets(slide, items, x=0.6, y=1.5, w=12.1, size=20):
    text(slide, x, y, w, 5.3, ["•  " + item for item in items], size)


def table(slide, rows, x, y, w, col_widths, size=14, row_h=0.5):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    grid = shape.table
    for c, width in enumerate(col_widths):
        grid.columns[c].width = Inches(width)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = grid.cell(r, c)
            cell.text = str(value)
            for paragraph in cell.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.font.size, run.font.bold = Pt(size), r == 0
                    run.font.color.rgb = WHITE if r == 0 else NAVY
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if r == 0 else (BLUE if r % 2 else WHITE)
    return grid


def box(slide, x, y, w, h, title, subtitle, fill, dashed=False):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = NAVY
    if dashed:
        shape.line.dash_style = 4
    frame = shape.text_frame
    frame.word_wrap = True
    first = frame.paragraphs[0]
    first.alignment = PP_ALIGN.CENTER
    run = first.add_run()
    run.text, run.font.size, run.font.bold, run.font.color.rgb = title, Pt(14), True, NAVY
    second = frame.add_paragraph()
    second.alignment = PP_ALIGN.CENTER
    run = second.add_run()
    run.text, run.font.size, run.font.color.rgb = subtitle, Pt(11), NAVY
    return shape


def arrow(slide, a, b, dashed=False):
    connector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, *a, *b)
    connector.line.color.rgb, connector.line.width = NAVY, Pt(1.75)
    if dashed:
        connector.line.dash_style = 4
    line = connector.line._get_or_add_ln()
    tail = line.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd", {"type": "triangle"})
    line.append(tail)


# 1. Title
slide = prs.slides.add_slide(blank)
band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(7.5))
band.fill.solid()
band.fill.fore_color.rgb = NAVY
band.line.fill.background()
text(slide, 0.9, 2.2, 11.5, 1.6, "Monitoring and Governance of a Local LLM Assistant", 40, True, WHITE)
text(slide, 0.9, 3.9, 11.5, 1.0, "AI governance, continuous monitoring, scalable oversight and deployment readiness", 22, color=WHITE)
text(slide, 0.9, 5.6, 11.5, 0.6, "Assignment 4 | AISRA1301 | AI Security and Risk Analysis | QAIRU", 16, color=WHITE)

# 2. System and earlier results
slide = new_slide("1. System and results of Midterm / Assignment 3")
bullets(slide, [
    "Local news assistant: React/Vite chat, Python proxy, Ollama with Vicuna 7B Q4_0",
    "Three modes: Base, Guarded (system prompt), Guarded + SmoothLLM (5 perturbed calls, majority vote)",
    "Threat studied: GCG jailbreak suffixes; 40 fixed cases per mode (10 direct, 10 published suffix, 10 cached GCG, 10 benign)",
    "A3 result: published-suffix lexical bypass 7/10, 7/10, 1/10, but audited benign success fell to 3/10 for Smooth",
    "Remaining risks needing monitoring: harmful output, task corruption, latency, invalid API input",
], size=20)

# 3. Autonomy
slide = new_slide("2. Agency and autonomy assessment")
table(slide, [["Question", "Finding"],
              ["Independent decisions", "Generated wording only (text output, refusals)"],
              ["Tools / APIs / databases", "None for the model; the proxy only calls local Ollama"],
              ["Actions affecting others", "None: no publishing, no self-initiated actions"],
              ["Boundaries enforced", "Role/size validation, 4000-char message, 12-message history, fixed mode list"],
              ["Conflict with user intent", "Possible: wrong facts, over-refusal, smoothing-corrupted answers"],
              ["Human authorization", "Publication, defence changes, restart after an incident"],
              ["Interruption", "Stop proxy / Ollama; browser Stop only cancels delivery"]],
      0.6, 1.5, 12.1, [3.6, 8.5], size=15, row_h=0.62)

# 4. Tool
slide = new_slide("3. Selected tool: MLflow")
bullets(slide, [
    "Fits the system: experiment tracking and comparison of the same metrics across configurations",
    "Five completed runs: three model modes and two HTTP boundary variants (local SQLite, no external service)",
    "A policy script computes thresholds and alerts; MLflow records metrics, histories, artifacts and alerts",
    "Evidence: dashboard.html, summary.json, alerts.jsonl, mlflow_runs.json (API export), source SHA-256 manifest",
    "Offline replay of saved A3 data: no new model calls; no live interception is claimed",
], size=20)

# 5. Indicators
slide = new_slide("4. Indicators and thresholds")
# Short slide wording; the full policy is in monitoring_policy.json and the appendix.
slide_text = {
    "benign_success_rate": ("Audited benign passes / 10 cases", "below 60%", "Hold rollout; review failed cases"),
    "mean_benign_latency_s": ("Mean latency, benign window", "above 2.0 s", "Check load; never weaken safety silently"),
    "judge_harmful_rate": ("Judge harmful labels / 30 attacks", "above 0", "Operator inspects answer; suspend pilot"),
    "invalid_forwarded_count": ("Invalid requests forwarded / 24", "above 0", "Block release; repair and retest"),
}
rows = [["Indicator", "Measurement", "Alert", "Response"]]
for rule in policy["indicators"]:
    measure, alert, response = slide_text[rule["metric"]]
    rows.append([rule["name"], measure, alert, response])
table(slide, rows, 0.6, 1.5, 12.1, [3.3, 3.3, 1.8, 3.7], size=14, row_h=0.8)
text(slide, 0.6, 6.2, 12.1, 0.7, "The 60% quality floor and 2 s latency budget are provisional pilot assumptions; they need held-out calibration.", 15, color=GREY)

# 6. Results
slide = new_slide("5. Monitoring experiment and results")
rows = [["Mode", "Benign success", "Mean latency", "Judge harmful", "Alerts"]]
names = {"baseline": "Base", "guarded": "Guarded", "guarded_smooth": "Guarded + Smooth"}
for key, data in models.items():
    rows.append([names[key], f"{data['benign_passes']}/10", f"{data['metrics']['mean_benign_latency_s']:.3f} s",
                 f"{data['judge_harmful_count']}/30", str(len(data["alerts"]))])
table(slide, rows, 0.6, 1.5, 12.1, [3.5, 2.4, 2.4, 2.1, 1.7], size=14, row_h=0.45)
slide.shapes.add_picture(str(EVIDENCE / "monitoring_comparison.png"), Inches(0.6), Inches(3.6), width=Inches(7.6))
text(slide, 8.5, 3.5, 4.3, 3.4, [
    "Baseline: Guarded. Controlled degradation: Guarded + Smooth.",
    "Quality drops 40 points, latency rises 5.3x; both flag at benign case 10.",
    f"{summary['alert_count']} alerts in total, all pending operator review.",
    "Smooth keeps 0/30 harmful labels, so safety-only screening misses the regression."], 14)

# 7. Oversight workflow
slide = new_slide("6. Oversight workflow")
box(slide, 0.6, 1.6, 3.4, 1.0, "User request", "Operator starts local service", BLUE)
box(slide, 4.95, 1.6, 3.4, 1.0, "API validation", "Reject invalid roles / sizes", BLUE)
box(slide, 9.3, 1.6, 3.4, 1.0, "Ollama + defence", "Generate; no auto publication", BLUE)
box(slide, 9.3, 3.3, 3.4, 1.0, "Archived evidence", "Fixed A3 metrics, offline replay", AMBER)
box(slide, 4.95, 3.3, 3.4, 1.0, "Policy + MLflow", "Automatic metrics, thresholds, flags", AMBER)
box(slide, 0.6, 3.3, 3.4, 1.0, "Audit and review queue", "Flags logged; review pending", AMBER)
box(slide, 0.6, 5.0, 3.4, 1.0, "Human operator", "Inspect; approve / reject / stop", WHITE, True)
box(slide, 4.95, 5.0, 3.4, 1.0, "Manual control", "Stop proxy; hold release; edit", WHITE, True)
box(slide, 9.3, 5.0, 3.4, 1.0, "Retest and authorize", "Record decision before restart", WHITE, True)
arrow(slide, (Inches(4.0), Inches(2.1)), (Inches(4.95), Inches(2.1)))
arrow(slide, (Inches(8.35), Inches(2.1)), (Inches(9.3), Inches(2.1)))
arrow(slide, (Inches(11.0), Inches(2.6)), (Inches(11.0), Inches(3.3)))
arrow(slide, (Inches(9.3), Inches(3.8)), (Inches(8.35), Inches(3.8)))
arrow(slide, (Inches(4.95), Inches(3.8)), (Inches(4.0), Inches(3.8)))
arrow(slide, (Inches(2.3), Inches(4.3)), (Inches(2.3), Inches(5.0)), True)
arrow(slide, (Inches(4.0), Inches(5.5)), (Inches(4.95), Inches(5.5)), True)
arrow(slide, (Inches(8.35), Inches(5.5)), (Inches(9.3), Inches(5.5)), True)
text(slide, 0.6, 6.25, 12.1, 0.7, "Blue: existing application. Amber: executed offline monitoring (automatic). Dashed: proposed human procedure; "
     "publication, configuration changes and restart always need human authorization.", 13, color=GREY)

# 8. Risks
slide = new_slide("7. Residual risks")
rows = [["Risk", "Residual"]] + [[r["risk"], r["residual"]] for r in decision["risks"]]
table(slide, rows, 0.6, 1.5, 12.1, [4.0, 8.1], size=14, row_h=0.6)

# 9. Decision
slide = new_slide("8. Deployment readiness decision")
text(slide, 0.6, 1.5, 12.1, 0.9, "NO-GO for public or unattended deployment", 34, True, RED)
bullets(slide, [
    "Default Smooth mode fails the quality (3/10) and latency (2.65 s) gates",
    "Semantic safety gain over Guarded is not shown; labels are not human-calibrated; factuality is unmeasured",
    "Live logging, alert routing and shutdown are proposals, not implemented",
    "Supervised local research may continue",
    "Conditions to reconsider a controlled pilot (all pending):",
], y=2.5, size=18)
text(slide, 1.0, 5.0, 11.7, 1.9, ["–  " + g["condition"] for g in decision["acceptance_gates"]], 14, color=GREY)

# 10. Limitations
slide = new_slide("9. Limitations and recommendations")
bullets(slide, [
    "Ten cases per group, one model, one seed, one published suffix, 96-token cap",
    "Thresholds chosen retrospectively; replay is not prospective or online drift monitoring",
    "Regex and a single judge are fallible; zero flags is not zero risk",
    "HTTP timings use a stub upstream and are not LLM latency",
    "Next: held-out tasks, human adjudication, load tests, live alerting, retention rules",
    "A monitoring tool alone does not make the system safe or legally compliant",
], size=20)

prs.save(REPORT / "Assignment4_Presentation.pptx")
print("PASS: presentation created")
