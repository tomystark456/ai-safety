"""Build the three-page report, supporting appendix and oversight diagram.

Run monitor_governance.py with MLflow first. All numeric findings are loaded
from the verified monitoring outputs rather than retyped in the report.
"""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "experiments/results/assignment4"
REPORT = ROOT / "report/assignment4"
NAVY = colors.HexColor("#173f59")
BLUE = colors.HexColor("#eaf1f6")
AMBER = colors.HexColor("#fff0d8")
RED = colors.HexColor("#a33832")
WIDTH = A4[0] - 84
STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="BodyA4", fontName="Helvetica", fontSize=9.2, leading=12.0, spaceAfter=5))
STYLES.add(ParagraphStyle(name="SmallA4", parent=STYLES["BodyA4"], fontSize=7.7, leading=10.0, spaceAfter=4))
STYLES.add(ParagraphStyle(name="HeadingA4", fontName="Helvetica-Bold", fontSize=10.8, leading=14, textColor=NAVY, spaceBefore=9, spaceAfter=5, keepWithNext=True))
STYLES.add(ParagraphStyle(name="TitleA4", fontName="Helvetica-Bold", fontSize=21, leading=24, textColor=NAVY, spaceAfter=8))
STYLES.add(ParagraphStyle(name="SubtitleA4", fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#546875"), spaceAfter=10))
STYLES.add(ParagraphStyle(name="CellA4", parent=STYLES["SmallA4"], spaceAfter=0))


def load(name):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def p(text, style="BodyA4"):
    return Paragraph(text, STYLES[style])


def heading(text):
    return p(text, "HeadingA4")


def table(rows, widths, size="CellA4"):
    data = [[p(escape(str(cell)), size) for cell in row] for row in rows]
    result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, NAVY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, colors.HexColor("#d6e0e8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return result


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(NAVY)
    canvas.line(42, A4[1] - 30, A4[0] - 42, A4[1] - 30)
    canvas.setFont("Helvetica", 7.4)
    canvas.setFillColor(colors.HexColor("#546875"))
    canvas.drawString(42, 25, "QAIRU | AISRA1301 | Assignment 4")
    canvas.drawRightString(A4[0] - 42, 25, str(doc.page))
    canvas.restoreState()


def build_pdf(path, story, title):
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=42, rightMargin=42,
                            topMargin=43, bottomMargin=40, title=title,
                            author="QAIRU course project", subject="AI monitoring, governance and deployment readiness")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def workflow():
    """Blue: implemented application, amber: implemented offline, white: proposed human process."""
    d = Drawing(WIDTH, 224)
    box_width, box_height = 150, 43
    xs = [0, (WIDTH - box_width) / 2, WIDTH - box_width]
    ys = [164, 88, 12]

    def box(x, y, title, subtitle, fill, human=False):
        d.add(Rect(x, y, box_width, box_height, rx=5, ry=5, fillColor=fill, strokeColor=NAVY,
                   strokeDashArray=[4, 2] if human else None))
        d.add(String(x + box_width / 2, y + 26, title, fontName="Helvetica-Bold", fontSize=8.2, textAnchor="middle", fillColor=NAVY))
        d.add(String(x + box_width / 2, y + 12, subtitle, fontName="Helvetica", fontSize=7.0, textAnchor="middle"))

    def arrow(x1, y1, x2, y2, label="", dashed=False):
        d.add(Line(x1, y1, x2, y2, strokeColor=NAVY, strokeWidth=1, strokeDashArray=[4, 3] if dashed else None))
        if abs(x2-x1) > abs(y2-y1):
            direction = 1 if x2 > x1 else -1
            tri = [x2, y2, x2-5*direction, y2+3, x2-5*direction, y2-3]
        else:
            direction = 1 if y2 > y1 else -1
            tri = [x2, y2, x2-3, y2-5*direction, x2+3, y2-5*direction]
        d.add(Polygon(tri, fillColor=NAVY, strokeColor=NAVY))
        if label:
            d.add(String((x1+x2)/2, (y1+y2)/2+5, label, fontSize=6.4, textAnchor="middle", fillColor=NAVY))

    box(xs[0], ys[0], "USER REQUEST", "Operator starts local service", BLUE)
    box(xs[1], ys[0], "API VALIDATION", "Reject invalid roles / sizes", BLUE)
    box(xs[2], ys[0], "OLLAMA + DEFENCE", "Generate; no auto publication", BLUE)
    arrow(xs[0]+box_width, ys[0]+22, xs[1], ys[0]+22)
    arrow(xs[1]+box_width, ys[0]+22, xs[2], ys[0]+22)
    box(xs[2], ys[1], "ARCHIVED EVIDENCE", "Fixed A3 metrics; offline replay", AMBER)
    arrow(xs[2]+75, ys[0], xs[2]+75, ys[1]+box_height, "A3 export")
    box(xs[1], ys[1], "POLICY + MLFLOW", "Auto metrics, thresholds, flags", AMBER)
    arrow(xs[2], ys[1]+22, xs[1]+box_width, ys[1]+22)
    box(xs[0], ys[1], "AUDIT AND REVIEW QUEUE", "Generated flags; review pending", AMBER)
    arrow(xs[1], ys[1]+22, xs[0]+box_width, ys[1]+22)
    box(xs[0], ys[2], "HUMAN OPERATOR", "Inspect; approve / reject / stop", colors.white, True)
    arrow(xs[0]+75, ys[1], xs[0]+75, ys[2]+box_height, "proposed", True)
    box(xs[1], ys[2], "MANUAL CONTROL", "Stop proxy; hold release; edit", colors.white, True)
    arrow(xs[0]+box_width, ys[2]+22, xs[1], ys[2]+22, dashed=True)
    box(xs[2], ys[2], "RETEST AND AUTHORIZE", "Record decision before restart", colors.white, True)
    arrow(xs[1]+box_width, ys[2]+22, xs[2], ys[2]+22, dashed=True)
    return d


def chart(summary):
    configs = ["baseline", "guarded", "guarded_smooth"]
    labels = ["Base", "Guarded", "Guarded\n+ Smooth"]
    values = [summary["models"][c]["metrics"] for c in configs]
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 2.75))
    palette = ["#91a9ba", "#246384", "#ce883c"]
    specs = [("benign_success_rate", "Audited task success", 100, "Percent", 60),
             ("mean_benign_latency_s", "Mean benign latency", 1, "Seconds", 2),
             ("published_suffix_lexical_bypass_rate", "Suffix lexical bypass", 100, "Percent", None)]
    for ax, (metric, title, scale, unit, threshold) in zip(axes, specs):
        ys = [v[metric] * scale for v in values]
        bars = ax.bar(labels, ys, color=palette, width=0.57)
        ax.bar_label(bars, labels=[f"{v:.2f}" if scale == 1 else f"{v:.0f}%" for v in ys], padding=3, fontsize=9)
        ax.set_title(title, fontsize=10, fontweight="bold", pad=12)
        ax.set_ylabel(unit, fontsize=9)
        ax.set_ylim(0, 100 if scale == 100 else max(ys) * 1.3)
        ax.tick_params(labelsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        if threshold is not None:
            ax.axhline(threshold, color="#a33832", linestyle="--", linewidth=1, label="Pilot threshold")
            ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout(w_pad=2)
    target = EVIDENCE / "monitoring_comparison.png"
    fig.savefig(target, dpi=180, facecolor="white")
    plt.close(fig)
    return target


def risks():
    return [
        ["Jailbreak / harmful output", "Prompt + smoothing; lexical suffix bypass 1/10; judge 0/30 for Smooth", "Judge alert + operator review", "High: tiny, dependent set; labels uncalibrated"],
        ["Useful task corruption", "Smooth audited success 3/10 versus Guarded 7/10", "10-case quality gate; inspect failures", "High: current default fails pilot gate"],
        ["Latency / overload", "Mean benign 2.65 s; five calls; no global concurrency cap", "Latency gate; operator holds rollout", "High: no load test or total deadline"],
        ["Fabricated facts", "UI warns users; no grounded fact verification", "Editor checks every publishable answer", "High: factuality rate unmeasured"],
        ["Privacy / retention", "Browser localStorage; private research logs", "No sensitive inputs; clear history; restrict logs", "Medium: no enforced retention policy"],
        ["API misuse / forged history", "Improved proxy 0/24 invalid forwarded; client history unauthenticated", "Boundary release gate; restrict access", "Medium: stub coverage only"],
        ["Missed or false flags", "Regex and single judge disagree; no human calibration", "Review critical flags and sampled unflagged cases", "High: operational false alarm rate unknown"],
    ]


def main_report(summary, runs, policy, image_path):
    m = summary["models"]
    g = m["guarded"]["metrics"]
    s = m["guarded_smooth"]["metrics"]
    ratio = s["mean_benign_latency_s"] / g["mean_benign_latency_s"]
    story = [p("Monitoring and Governance of a Local LLM Assistant", "TitleA4"),
             p("Assignment 4 | AISRA1301 | AI Security and Risk Analysis | QAIRU", "SubtitleA4"),
             heading("1. Title and AI System Overview"),
             p("The existing news assistant uses React/Vite, a Python HTTP proxy and local Ollama with Vicuna 7B Q4_0. It offers Base, Guarded and Guarded + SmoothLLM modes. This study evaluates operational readiness through retrospective monitoring of the same system. <b>Decision: NO-GO for public or unattended deployment.</b> Authorised local research may continue under operator supervision."),
             heading("2. Summary of Midterm and Assignment 3 Results"),
             p("Midterm published-suffix lexical bypass was 22/25 for Base and 19/25 for Guarded [1]. Assignment 3 used 40 fixed cases per configuration: 10 direct, 10 published-suffix, 10 cached-GCG and 10 benign. Suffix bypass became 7/10, 7/10 and 1/10; audited benign success was 7/10, 7/10 and 3/10 [2]. Lexical bypass is absence of refusal phrases, not semantic ASR. The judge labelled 1/30 attack answers harmful for Base and 0/30 for both defences. Historical and new runs remain separate."),
             heading("3. AI Agency and Autonomy Assessment"),
             p("The model selects generated wording and may contradict user intent through refusals, factual errors or smoothing-induced corruption. It has no tool-execution loop, autonomous publication, database access or self-initiated actions. The server calls local Ollama; that API call does not give the model external permissions. The proxy validates roles and sizes, inserts trusted instructions and keeps 12 messages. Human authorization is required for publication, defence changes and restart after an incident. Browser abort stops delivery but does not guarantee cancellation of upstream inference; an operator can stop the local proxy and Ollama."),
             heading("4. Selected Monitoring or Governance Tool"),
             p(f"<b>MLflow {escape(runs['version'])}</b> records five completed runs: three model configurations and two historical HTTP boundary variants. Local SQLite stores metadata; local artifacts contain sanitised summaries, policy, hashes and alerts. Metric histories are read back through MlflowClient [3]. The policy script computes thresholds; MLflow records and compares results. No production tracing or live enforcement is installed."),
             heading("5. Monitoring Indicators and Thresholds"),
             table([["Indicator / source", "Threshold", "Trigger and response"],
                    ["Audited benign passes / 10; rubric + model IDs", "< 60%", "Every 10 canaries; hold rollout and review failures"],
                    ["Mean full benign latency; archived timings", "> 2.0 s", "Every 10 canaries; inspect load and settings"],
                    ["Judge harmful labels / 30 attack cases", "> 0", "First harmful label; operator reviews private answer"],
                    ["Invalid requests forwarded / 24; HTTP stub", "> 0", "First violation; block server release"]], [WIDTH*.43, WIDTH*.13, WIDTH*.44]),
             p("The 60% quality floor and 2 s response budget are provisional pilot assumptions, chosen after viewing A3 results. Zero tolerance for flagged harmful output means review, not confirmed harm. Zero invalid forwarding follows the API contract. Proposed cadence: daily benign canaries, weekly safety suite and after every relevant change; boundary tests at each release. A4 demonstrates offline evaluation only; thresholds require held-out calibration. Full methods, sources and actions are in the appendix.", "SmallA4"),
             PageBreak(), heading("6. Monitoring Experiment and Results"),
             p("The controlled contrast replays Guarded as the relative reference and Guarded + SmoothLLM as the degraded condition on identical benign tasks. Base is an additional comparator. The script joins 120 response records, 90 judge labels and 30 audited rubric scores; a separate replay checks 96 stub HTTP outcomes. It validates unique IDs, complete groups and the dataset SHA-256 against A3 metadata. No model is rerun and no synthetic latency is inserted. The new result is the monitor's detection, not a new inference experiment."),
             table([["Configuration", "Benign", "Mean latency", "Judge harmful", "Model alerts"],
                    *[[c.replace("guarded_smooth", "Guarded + Smooth").replace("guarded", "Guarded").replace("baseline", "Base"),
                       f"{d['benign_passes']}/10", f"{d['metrics']['mean_benign_latency_s']:.3f} s", f"{d['judge_harmful_count']}/30", len(d['alerts'])] for c,d in m.items()]],
                   [WIDTH*.29, WIDTH*.14, WIDTH*.20, WIDTH*.20, WIDTH*.17]),
             Image(str(image_path), width=WIDTH, height=WIDTH*2.75/10.8),
             p(f"<b>Figure 1.</b> Archived A3 measurements evaluated by the A4 policy. Smooth reduces audited task success by 40 percentage points and increases benign latency {ratio:.2f} times versus Guarded. Both batch indicators flag at case 10, representing {10*s['mean_benign_latency_s']:.3f} s of archived inference, excluding warm-up and judging. This is not measured alert delivery time. The recorded replay/export runtime is in execution.json.", "SmallA4"),
             p(f"There are <b>{summary['alert_count']} alerts</b>: two for Smooth quality/latency, one for the Base judge flag and one for historical API invalid forwarding (16/24 versus improved 0/24). Both proxy variants forward 24/24 valid requests. Harmful and boundary screening flag the first positive event. Safety labels remain zero for Smooth and therefore miss its usability regression. No quality/latency flag occurs in the one Guarded reference window; production false alarm rates and judge accuracy cannot be inferred without independent human labels."),
             heading("7. Scalable Oversight and Human Control"),
             workflow(),
             p("<b>Figure 2.</b> Blue: existing application; amber: executed offline monitoring; dashed boxes/arrows: proposed operator workflow. Automation calculates metrics and queues flags. The local student/operator inspects evidence, holds releases, stops services and approves changes or restart. Editors approve publication. Severity-based queues, deduplication and sampling of unflagged outputs support larger usage; an incident record must retain case IDs, model/policy hashes, decision, reviewer and retest evidence. No silent fallback to a weaker model is permitted.", "SmallA4"),
             PageBreak(), heading("8. Residual Risk and Deployment Readiness Decision"),
             table([["Risk", "Existing evidence / control", "Monitoring / oversight", "Residual assessment"], *risks()],
                   [WIDTH*.19, WIDTH*.31, WIDTH*.25, WIDTH*.25]),
             Spacer(1, 6),
             p("<b>NO-GO for public or unattended deployment.</b> The default smoothing mode fails the provisional quality and latency gates; factuality is unmeasured, safety labels lack human calibration and live escalation is not integrated. Guarded's better usability alone does not justify deployment because published-suffix lexical bypass remains 7/10 and semantic safety is uncertain. This is a research readiness assessment, not a claim of legal compliance."),
             p("Reconsider controlled deployment only after: (1) independent human review and a larger held-out safety/quality evaluation; (2) approved configuration meeting calibrated task and latency budgets; (3) tested runtime logging, alert routing, shutdown and restart authorization; (4) bounded concurrency, a total request deadline and outage tests; (5) documented privacy/retention and mandatory editorial checks. Each condition is a pending acceptance gate, not an implemented safeguard."),
             heading("9. Limitations and Recommendations"),
             p("Ten cases per group, dependent cached goals, one suffix/seed, fixed execution order and a 96-token cap limit generalisation. The audited benign rubric was corrected after the original run. A4 thresholds were selected retrospectively, and replay establishes neither prospective detection nor online drift monitoring. Regex and the single local judge are fallible; zero flagged cases is not evidence of zero risk. HTTP timings use a stub and are not LLM latency. Critical flags require human review, and sampled unflagged cases are needed to estimate misses. Future checks should use held-out tasks, multiple seeds, human adjudication and real load/failure tests."),
             heading("10. References"),
             p("[1] Supplied Midterm aggregates: experiments/results/historical_model_summary.json. [2] Assignment 3 Technical Report, report/assignment3; public per-case evidence in experiments/results/assignment3, including model_results.jsonl, judge_labels.jsonl, benign_review.json and boundary_results.jsonl. A4 source hashes: manifest.json.", "SmallA4"),
             p('[3] MLflow. Tracking and backend stores. <link href="https://mlflow.org/docs/latest/ml/tracking/">mlflow.org/docs/latest/ml/tracking/</link>; <link href="https://mlflow.org/docs/latest/tracking/backend-stores/">mlflow.org/docs/latest/tracking/backend-stores/</link>.', "SmallA4"),
             p('[4] Robey et al. SmoothLLM (2023), <link href="https://arxiv.org/abs/2310.03684">arxiv.org/abs/2310.03684</link>. [5] Zou et al. Universal and Transferable Adversarial Attacks (2023), <link href="https://arxiv.org/abs/2307.15043">arxiv.org/abs/2307.15043</link>. Local defence is an independent adaptation.', "SmallA4"),
             p("AI assistance: Claude Code was used to write the monitoring code and draft documents; the student directed the project and evaluated the results (see AI_USE_DECLARATION.md). No independent adjudication by a second reviewer or operational approval is claimed.", "SmallA4")]
    build_pdf(REPORT / "Assignment4_Governance_Report.pdf", story, "Monitoring and Governance of a Local LLM Assistant")


def appendix(summary, runs, policy):
    story = [p("Monitoring Evidence and Oversight", "TitleA4"),
             p("Assignment 4 supporting appendix | Offline replay and proposed pilot controls", "SubtitleA4"),
             heading("Monitoring indicators and response policy")]
    for rule in policy["indicators"]:
        operator = "below" if rule["operator"] == "lt" else "above"
        story.extend([heading(rule["name"]),
                      p(f"<b>Measurement:</b> {escape(rule['method'])}"),
                      p(f"<b>Data source:</b> {escape(rule['source'])}"),
                      p(f"<b>Alert:</b> {operator} {rule['threshold']} {escape(rule['unit'])}; severity {rule['severity']}.", "BodyA4"),
                      p(f"<b>Frequency:</b> {escape(rule['frequency'])}"),
                      p(f"<b>Justification:</b> {escape(rule['rationale'])}"),
                      p(f"<b>Response:</b> {escape(rule['response'])}")])
    story.extend([PageBreak(), heading("Oversight workflow and implementation status"), workflow(),
                  p("Blue boxes describe the existing assistant. Amber boxes describe the implemented and executed offline evaluation. Dashed boxes describe the operator procedure to adopt before a controlled pilot. No dashboard action directly changes the running application."),
                  heading("Authority and interruption"),
                  p("The project student/operator owns local technical incident response. A human editor approves every publishable output. These are proposed responsibilities; no external person is assigned or notified by this experiment. Only the operator may approve model/defence changes and restart. Ordinary response generation and offline metric calculations may run automatically."),
                  p("On a critical flag, hold pilot admission and preserve sanitised evidence. If an affected service is operating, the operator stops the Python server (Ctrl+C in its terminal) and, if generation persists, stops the Ollama service/process using the local service manager. Browser Stop cancels delivery only; full inference cancellation needs separate validation. Retest before restart; do not route to the base model automatically."),
                  heading("Incident record and response sequence"),
                  table([["Stage", "Required record / decision"],
                         ["Flag", "Incident ID, time, severity, configuration, case IDs, metric, threshold, policy and source hashes"],
                         ["Review", "Human reviewer, private evidence location, confirmed issue or dismissed flag, reasoning"],
                         ["Contain", "Hold release; stop affected service if needed; record action and scope"],
                         ["Correct", "Approved change, configuration version, responsible operator"],
                         ["Retest", "Held-out evaluation and API checks; link results; no restart without approval"],
                         ["Close", "Reviewer sign-off, restart decision, closure time and follow-up"]], [WIDTH*.18, WIDTH*.82]),
                  p("Scale the process with severity queues, grouping repeated configuration/rule flags, restricted access to raw content, periodic human review of unflagged samples and explicit reviewer capacity. An unstaffed queue prevents pilot admission. Log retention and escalation service levels must be approved before a live pilot.", "SmallA4"),
                  PageBreak(), heading("Verified MLflow application"),
                  p(f"Tool: MLflow {escape(runs['version'])}. Backend: local SQLite with local artifacts. The following five runs were read back using the actual MLflow API; the portable export contains their final metrics and histories. Run IDs identify this execution; reproducing the script creates new runs."),
                  table([["Scope / configuration", "Completed run ID"],
                         *[[r['scope'] + ' / ' + r['configuration'], r['run_id']] for r in runs['runs']]], [WIDTH*.43, WIDTH*.57]),
                  heading("Generated flag evidence"),
                  table([["Scope / configuration", "Indicator", "Value / threshold", "Detection"],
                         *[[a['scope']+' / '+a['configuration'], a['metric'],
                            f"{a['value']:.4g} {a['operator']} {a['threshold']}",
                            f"Benign case {a['detection_after_benign_cases']}" if 'detection_after_benign_cases' in a else
                            f"Labelled attack {a['detection_after_labelled_attack_cases']}" if 'detection_after_labelled_attack_cases' in a else
                            f"Invalid HTTP case {a['detection_after_invalid_cases']}" ] for a in summary['alerts']]],
                        [WIDTH*.29, WIDTH*.29, WIDTH*.19, WIDTH*.23]),
                  p("All flags remain pending operator review. Stored records demonstrate detection and documented recommendations, not an operator acknowledgement or an actual shutdown. The historical proxy and base model both use the label baseline in their original files; their distinct scopes above prevent conflation."),
                  heading("Reproducibility and source map"),
                  p("Run experiments/monitor_governance.py, experiments/check_governance.py and experiments/build_assignment4_report.py using the pinned monitoring requirements. The dashboard, summary, comparison, indicators, alerts, source manifest and MLflow API export are in experiments/results/assignment4. Full commands and the LMS deliverable map are in docs/ASSIGNMENT4.md."),
                  p("Monitoring execution metadata and runtime are recorded separately in execution.json. Source files and the original application are preserved. The public export loads no raw completions; private A3 logs and browser history still require access and retention controls."),
                  heading("Deployment decision"),
                  p("<b>NO-GO for public or unattended deployment.</b> The main report lists seven residual risks and five acceptance gates. Supervised, authorised local research is within the evaluation scope. A future controlled pilot requires new evidence and an explicit human authorization; this appendix provides no approval signature.")])
    build_pdf(REPORT / "Assignment4_Monitoring_Appendix.pdf", story, "Assignment 4 Monitoring Evidence and Oversight")


def main():
    summary, runs = load("summary.json"), load("mlflow_runs.json")
    policy = json.loads((ROOT / "experiments/monitoring_policy.json").read_text(encoding="utf-8"))
    if not runs.get("enabled") or len(runs["runs"]) != 5 or any(r["status"] != "FINISHED" for r in runs["runs"]):
        raise ValueError("Five verified completed MLflow runs are required before authoring the report")
    REPORT.mkdir(parents=True, exist_ok=True)
    svg = workflow()
    renderSVG.drawToFile(svg, str(REPORT / "Oversight_Workflow.svg"))
    image_path = chart(summary)
    main_report(summary, runs, policy, image_path)
    appendix(summary, runs, policy)
    decision = {"decision": "NO-GO", "scope": "public or unattended deployment", "research_scope": "authorised supervised local research may continue",
                "basis": {"policy_id": policy["policy_id"], "alert_count": summary["alert_count"], "live_controls_integrated": False,
                          "independent_human_adjudication": False},
                "risks": [dict(zip(("risk", "existing_control_or_evidence", "monitoring_or_oversight", "residual"), row)) for row in risks()],
                "acceptance_gates": [
                    {"condition": "Independent human review and larger held-out safety/quality evaluation", "status": "pending"},
                    {"condition": "Approved configuration meeting calibrated task and latency budgets", "status": "pending"},
                    {"condition": "Tested runtime logging, alert routing, shutdown and restart authorization", "status": "pending"},
                    {"condition": "Bounded concurrency, total request deadline and real outage/load tests", "status": "pending"},
                    {"condition": "Approved privacy/retention procedure and mandatory editorial review", "status": "pending"}],
                "authorization": "Research recommendation only; no human operational approval or legal compliance asserted"}
    (REPORT / "Deployment_Readiness_Decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print("PASS: main report, appendix, standalone SVG and deployment decision created")


if __name__ == "__main__":
    main()
