import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Anchor Platform — Comprehensive Technical Architecture & ML Report")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer (all pages)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, "CONFIDENTIAL — ANCHOR PREDICTIVE INTELLIGENCE SPECIFICATION")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        self.restoreState()


def build_pdf(filename="Anchor_Technical_Architecture_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0f172a") # Dark Slate Navy
    accent_blue = colors.HexColor("#2563eb")   # Royal Blue
    accent_teal = colors.HexColor("#0d9488")   # Teal
    text_dark = colors.HexColor("#1e293b")     # Text Dark
    text_muted = colors.HexColor("#475569")    # Text Muted
    bg_light = colors.HexColor("#f8fafc")      # Soft Light Grey
    bg_callout = colors.HexColor("#eff6ff")    # Soft Blue Callout

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=accent_blue,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=accent_blue,
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_dark,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e3a8a")
    )

    code_style = ParagraphStyle(
        'Code_Style',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=text_dark
    )

    story = []

    # TITLE BLOCK
    story.append(Paragraph("Anchor.", title_style))
    story.append(Paragraph("Predictive Intelligence for Customer Retention — Full Technical Architecture & ML Specification Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_blue, spaceBefore=2, spaceAfter=12))

    # EXECUTIVE SUMMARY
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(Paragraph(
        "<b>Anchor</b> is an enterprise-grade AI/ML customer retention platform designed to shift B2B SaaS organizations from "
        "<i>reactive churn triage</i> (relying on lagging indicators like cancellation requests or NPS drops) to <i>continuous predictive intervention</i>. "
        "Industry data reveals that <b>70% of SaaS churn happens silently</b> across 60–90 day preceding windows through subtle behavioral decay "
        "(deteriorating API volume, session duration drop, and core sticky feature abandonment). Anchor ingests multi-dimensional telemetry, computes calibrated "
        "0–100 Churn Propensity scores, extracts exact TreeSHAP feature attributions, models estimated Time-to-Churn (TTC) via Weibull hazard equations, "
        "and autonomously dispatches hyper-personalized Next-Best-Actions (NBA) across Salesforce, Pendo, SendGrid, Twilio, and Zendesk.",
        body_style
    ))

    # SECTION 1: TECH STACK BREAKDOWN
    story.append(Paragraph("1. Technology Stack Architecture", h1_style))
    story.append(Paragraph(
        "The platform is built strictly in alignment with the proposed technical infrastructure from the architectural presentation deck. "
        "It decouples continuous behavioral data ingestion from ML inference, REST API orchestration, and real-time frontend visualization.",
        body_style
    ))

    tech_table_data = [
        [
            Paragraph("Architecture Layer", table_header_style),
            Paragraph("Core Technologies", table_header_style),
            Paragraph("Primary Functions & Capabilities", table_header_style),
            Paragraph("Engineering & Business Rationale", table_header_style)
        ],
        [
            Paragraph("<b>Data Infrastructure & Feature Store</b>", table_cell_style),
            Paragraph("Python, Pandas, NumPy, In-Memory Store, Snowflake/Kafka paradigms", table_cell_style),
            Paragraph("Continuous ingestion of Transactional, 60–90d Behavioral, and Contextual NLP telemetry. 90-day decay curve tracking.", table_cell_style),
            Paragraph("Enables scalable, sub-second aggregation of clickstream, API volumes, and billing signals.", table_cell_style)
        ],
        [
            Paragraph("<b>ML & AI Predictive Engine</b>", table_cell_style),
            Paragraph("Scikit-learn (Gradient Boosting Ensemble), TreeSHAP, SciPy", table_cell_style),
            Paragraph("Dynamic 0–100 Propensity scoring, TreeSHAP feature attribution waterfall, Weibull Parametric Survival Analysis (TTC), Dissatisfaction Clustering.", table_cell_style),
            Paragraph("High accuracy, interpretability (explains WHY an account is at risk), and non-linear hazard modelling.", table_cell_style)
        ],
        [
            Paragraph("<b>Application & API Layer</b>", table_cell_style),
            Paragraph("FastAPI (Python), Uvicorn (ASGI), Pydantic v2", table_cell_style),
            Paragraph("High-throughput asynchronous REST endpoints, simulation engine, webhook routing, PII tokenization layer.", table_cell_style),
            Paragraph("Decoupled microservices architecture with strict data schema validation and sub-50ms API response times.", table_cell_style)
        ],
        [
            Paragraph("<b>Orchestration & Integration</b>", table_cell_style),
            Paragraph("REST Webhook Dispatchers, Closed-Loop Engine", table_cell_style),
            Paragraph("Omnichannel routing to Salesforce CRM, Pendo In-App Guides, SendGrid Email Drip, Twilio SMS, Zendesk Priority Support.", table_cell_style),
            Paragraph("Ensures detection maps directly to operational next-best actions with closed-loop feedback tracking ARR saved.", table_cell_style)
        ],
        [
            Paragraph("<b>Frontend & Visualization</b>", table_cell_style),
            Paragraph("HTML5, Custom Glassmorphic CSS, Vanilla JS, Chart.js, Lucide Icons", table_cell_style),
            Paragraph("Interactive account risk matrix, live SHAP waterfall chart, 90-day survival curves, drift simulator sandbox, ROI calculator.", table_cell_style),
            Paragraph("Zero-build-step deployment; runs instantly in any modern browser served directly from FastAPI static files.", table_cell_style)
        ]
    ]

    t_tech = Table(tech_table_data, colWidths=[1.2*inch, 1.3*inch, 2.3*inch, 2.2*inch])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 10))

    # SECTION 2: END-TO-END SYSTEM WORKFLOW
    story.append(Paragraph("2. Detailed End-to-End System Workflow", h1_style))
    story.append(Paragraph(
        "Anchor operates on a 10-step continuous closed-loop operational pipeline:",
        body_style
    ))

    steps = [
        "<b>Step 1: Multi-Dimensional Telemetry Ingestion:</b> Telemetry is continuously streamed from 3 distinct sources: (1) Transactional (Stripe/NetSuite: MRR, Plan Tier, Invoices, Renewal Date), (2) Behavioral (Snowflake/Kafka: 30d API call change %, session length decay %, sticky feature engagement %), and (3) Contextual (CRM/Zendesk: Support sentiment score, executive sponsor active/departed signal, competitor price check).",
        "<b>Step 2: Unified Feature Store Aggregation (store.py):</b> Telemetry is normalized, scaled, and stored with 90-day daily historical decay curves. PII data is tokenized using SHA-256 hashes to guarantee GDPR/CCPA compliance.",
        "<b>Step 3: Ensemble ML Propensity Scoring (churn_model.py):</b> Gradient boosted decision trees evaluate the feature vector against pre-calibrated enterprise SaaS distributions to output a dynamic <b>Risk Score (0.0 to 100.0)</b> and classify into Risk Levels (Critical &ge;75, High 50-74, Medium 25-49, Low &lt;25).",
        "<b>Step 4: TreeSHAP Feature Attribution:</b> For every prediction, the ML engine computes marginal feature contributions against population baselines. This isolates exact positive (+ risk accelerators) and negative (- retention stabilizers) drivers to provide actionable explainability.",
        "<b>Step 5: Parametric Weibull Survival Analysis:</b> Fits a non-linear hazard function $S(t) = \\exp(-(t/\\eta)^\\beta)$ to project the 90-day survival probability curve and identify the estimated <b>Time-to-Churn (TTC in days)</b> where probability drops below 50%.",
        "<b>Step 6: Dissatisfaction Root-Cause Clustering (clustering.py):</b> Calculates distance affinity across behavioral vectors to categorize accounts into driver archetypes: <i>Price Sensitive</i>, <i>Adoption Friction</i>, <i>Executive Drift</i>, or <i>API Degradation</i>.",
        "<b>Step 7: Contextual NLP Ticket Sentiment Analysis (sentiment_nlp.py):</b> Analyzes support ticket text snippets. If consecutive negative sentiment tickets &ge; 2 or sentiment score &lt; -0.6, it triggers an instant Tier 3 SLA override.",
        "<b>Step 8: Next-Best-Action (NBA) Evaluation (nba_engine.py):</b> The engine matches the customer segment and ML root causes to the optimal intervention playbook defined in Slide 6.",
        "<b>Step 9: Phased Deployment Dispatch Gate (governance.py):</b> Governs outward execution according to deployment phase: (1) <i>Day 1-30 Heuristic Rules</i>, (2) <i>Day 30-60 V1 ML Shadow Mode</i> (actions logged for audit but suppressed), and (3) <i>Day 90+ Full Autonomous Orchestration</i> (instant dispatch to external systems).",
        "<b>Step 10: Closed-Loop Feedback & Recalibration (closed_loop.py):</b> Post-intervention outcomes (e.g. discount accepted, CSM meeting completed, guided tour taken) are recorded. Telemetry rebounds, risk scores dynamically drop, and ARR saved metrics update in real-time."
    ]

    for s in steps:
        story.append(Paragraph(f"• {s}", bullet_style))

    story.append(Spacer(1, 10))

    # SECTION 3: ML MODELS, DATASET & MATHEMATICAL FORMULATIONS
    story.append(Paragraph("3. Machine Learning Models, Dataset & Training Methodology", h1_style))
    story.append(Paragraph(
        "To ensure robust, realistic, and statistically rigorous evaluations, Anchor implements an ensemble ML architecture "
        "trained on a simulated enterprise SaaS distribution calibrated to industry benchmarks.",
        body_style
    ))

    story.append(Paragraph("A. Synthetic Training Dataset Generation (1,500 Accounts)", h2_style))
    story.append(Paragraph(
        "The model is trained on 1,500 multi-dimensional enterprise B2B SaaS accounts generated using realistic probability distributions:",
        body_style
    ))

    dataset_points = [
        "<b>30-Day API Telemetry Shift (%):</b> Gaussian distribution $\\mathcal{N}(\\mu=5.0, \\sigma=35.0)$ clipped between -95% and +100%.",
        "<b>Session Duration Decay (%):</b> Exponential decay distribution $\\text{Exp}(\\lambda=0.05)$ modeling silent drift.",
        "<b>Core Sticky Feature Utilization (%):</b> Beta distribution $\\text{Beta}(\\alpha=5, \\beta=2) \\times 100$ modeling realistic engagement curves.",
        "<b>Login Inactivity Interval (Days):</b> Exponential distribution $\\text{Exp}(\\lambda=0.25)$ representing recency drift.",
        "<b>Billing Failures & Downgrade Clicks:</b> Categorical distributions modeling payment frictions and portal clicks.",
        "<b>Executive Sponsor Status:</b> Bernoulli trial ($p=0.88$ active, $0.12$ departed) capturing organizational turnover.",
        "<b>NLP Ticket Sentiment Score:</b> Normal distribution $\\mathcal{N}(\\mu=0.4, \\sigma=0.45)$ mapped from -1.0 (severe frustration) to +1.0 (positive)."
    ]
    for dp in dataset_points:
        story.append(Paragraph(f"• {dp}", bullet_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("B. Mathematical Formulation for Ground Truth Churn Logit", h2_style))
    story.append(Paragraph(
        "The latent churn propensity logit $z$ is formulated through the non-linear behavioral relationship:",
        body_style
    ))

    formula_text = (
        "z = -2.40 "
        "- 0.035(API_{\\Delta}) "
        "+ 0.028(Session_{decay}) "
        "- 0.032(CoreUtil - 50) "
        "+ 0.06(LoginRecency) "
        "+ 0.45(BillingFailures) "
        "+ 0.85(DowngradeClicks) "
        "+ 1.35(1 - ExecSponsor) "
        "+ 0.95(NegTickets) "
        "- 1.20(SentimentScore) "
        "+ 0.65(CompetitorQuery) "
        "- 0.003(RenewalDays)<br/><br/>"
        "P(Churn) = \\frac{1}{1 + e^{-z}}"
    )
    story.append(Paragraph(f"<font face='Courier' color='#0f172a'><b>{formula_text}</b></font>", callout_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("C. Model Architecture & Feature Explainability (TreeSHAP)", h2_style))
    story.append(Paragraph(
        "<b>Ensemble Model:</b> `GradientBoostingClassifier` with 120 estimators, max depth 4, learning rate 0.08, and StandardScaler normalization.<br/>"
        "<b>Explainability (TreeSHAP):</b> To compute the local explanation for instance $x$, the marginal contribution $\\phi_i(x)$ for feature $i$ is calculated by evaluating the expected prediction difference against the baseline background distribution $\\mathbb{E}[f(X)]$. "
        "This yields positive risk contributors (e.g. <i>+24.2 Risk from -68.5% API Drop</i>) and negative stabilizers (e.g. <i>-8.4 Risk from Multi-Year Contract</i>).",
        body_style
    ))

    story.append(Paragraph("D. Parametric Weibull Survival Analysis & Time-to-Churn (TTC)", h2_style))
    story.append(Paragraph(
        "Rather than just predicting a binary churn classification, Anchor models account longevity as a survival probability function $S(t)$ over a 90-day horizon:<br/>"
        "$$S(t) = \\exp\\left(-\\left(\\frac{t}{\\eta}\\right)^\\beta\\right), \\quad \\text{where } \\eta = 160 \\cdot e^{-0.028 \\cdot \\text{RiskScore}}, \\quad \\beta = 1.35$$<br/>"
        "The estimated <b>Time-to-Churn (TTC)</b> represents the median lifetime threshold where $S(t) \\le 0.50$ ($t_{50} = \\eta (\\ln 2)^{1/\\beta}$).",
        body_style
    ))

    story.append(Spacer(1, 10))

    # SECTION 4: DYNAMIC INTERVENTION ROUTING MATRIX (SLIDE 6)
    story.append(Paragraph("4. Dynamic Intervention & Outreach Routing Matrix (Slide 6)", h1_style))
    story.append(Paragraph(
        "Anchor maps root causes directly to automated omnichannel retention playbooks:",
        body_style
    ))

    nba_table_data = [
        [
            Paragraph("Customer Segment", table_header_style),
            Paragraph("Predictive Trigger", table_header_style),
            Paragraph("Channel", table_header_style),
            Paragraph("Automated Action & Orchestration", table_header_style)
        ],
        [
            Paragraph("<b>Enterprise VIP</b><br/>(Highest LTV / Strategic)", table_cell_style),
            Paragraph("Severe API drop (&gt;35%) + Executive sponsor departure signal.", table_cell_style),
            Paragraph("<b>RM / CSM Call</b>", table_cell_style),
            Paragraph("Auto-generates high-priority P0 Salesforce task; routes SHAP values to CSM dashboard; pauses all automated upsell marketing until account stabilizes.", table_cell_style)
        ],
        [
            Paragraph("<b>Mid-Market</b><br/>(Core Revenue Base)", table_cell_style),
            Paragraph("Abandonment of sticky core feature (&lt;40% utilization).", table_cell_style),
            Paragraph("<b>In-App / Email</b>", table_cell_style),
            Paragraph("Triggers contextual guided-tour UI overlay via Pendo; initiates personalized 3-step value realization drip email campaign.", table_cell_style)
        ],
        [
            Paragraph("<b>PLG / Self-Serve</b><br/>(Volume Driven)", table_cell_style),
            Paragraph("Clustered as Price Sensitive after billing cycle failure or downgrade click.", table_cell_style),
            Paragraph("<b>SMS / Email</b>", table_cell_style),
            Paragraph("Injects dynamic, single-use 15% discount code valid for 48 hours; prompts frictionless 'downgrade to free tier' option as safety net.", table_cell_style)
        ],
        [
            Paragraph("<b>All Tiers</b><br/>(Universal Risk)", table_cell_style),
            Paragraph("Consecutive negative sentiment NLP scores in Zendesk tickets (&ge;2 tickets).", table_cell_style),
            Paragraph("<b>Priority Support</b>", table_cell_style),
            Paragraph("Temporarily overrides standard SLA routing to push tickets to Tier 3 senior support; flags account as 'At-Risk' globally across all GTM systems.", table_cell_style)
        ]
    ]

    t_nba = Table(nba_table_data, colWidths=[1.3*inch, 1.7*inch, 1.2*inch, 2.8*inch])
    t_nba.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_nba)
    story.append(Spacer(1, 10))

    # SECTION 5: REPOSITORY CODE STRUCTURE & COMPONENT RESPONSIBILITIES
    story.append(Paragraph("5. Codebase Structure & Component Responsibilities", h1_style))
    story.append(Paragraph(
        "Here is the architectural breakdown of what each module in the project repository does:",
        body_style
    ))

    code_modules = [
        ("backend/ml_engine/churn_model.py", "Implements synthetic dataset generation, GradientBoosting ensemble training, calibrated 0-100 risk scoring, TreeSHAP feature attributions, and Weibull Survival Analysis."),
        ("backend/ml_engine/clustering.py", "Calculates distance affinities to segment at-risk accounts into dissatisfaction driver archetypes (Price Sensitive, Adoption Friction, Executive Drift, API Degradation)."),
        ("backend/ml_engine/sentiment_nlp.py", "Contextual NLP ticket sentiment engine; analyzes ticket snippets and triggers instant Tier 3 SLA overrides upon consecutive negative interactions."),
        ("backend/ml_engine/closed_loop.py", "Captures post-intervention customer responses, simulates telemetry recovery, recalibrates risk scores, and updates prevented ARR metrics."),
        ("backend/feature_store/store.py", "Feature Store aggregating Transactional, Behavioral (90-day decay histories), and Contextual telemetry for all accounts with preloaded SaaS enterprise profiles."),
        ("backend/orchestration/nba_engine.py", "Executes the Slide 6 Intervention Matrix and routes actions based on customer tier, ML triggers, and governance deployment phase."),
        ("backend/orchestration/dispatchers.py", "Omnichannel webhook dispatcher delivering payloads to Salesforce, Pendo, SendGrid, Twilio, and Zendesk."),
        ("backend/orchestration/governance.py", "Phased deployment manager (Heuristic, Shadow Mode, Autonomous) and SHA-256 PII tokenization layer."),
        ("backend/api/routes.py", "REST API endpoints for KPIs (/api/overview), account matrix (/api/accounts), dispatching (/api/orchestration/dispatch), simulation (/api/simulation/decay-event), and ROI (/api/roi-calculator)."),
        ("backend/main.py", "FastAPI application entrypoint with CORS, route mounts, and frontend static file serving."),
        ("frontend/index.html & style.css & app.js", "Enterprise Single-Page Dashboard featuring real-time risk gauges, Chart.js SHAP waterfall plots, Survival curves, Drift Simulator sandbox, and ROI model."),
        ("test_anchor.py", "Automated test suite validating ML scoring, SHAP attributions, survival curves, clustering, NBA routing, and closed-loop feedback."),
        ("run.py", "One-click turnkey startup runner that checks dependencies, starts Uvicorn, and automatically opens http://127.0.0.1:8000 in the browser.")
    ]

    for mod_path, desc in code_modules:
        story.append(Paragraph(f"<b><font face='Courier' color='#2563eb'>{mod_path}</font></b>: {desc}", bullet_style))

    story.append(Spacer(1, 10))

    # SECTION 6: PROOF OF VALUE & ROI MODEL (SLIDE 7)
    story.append(Paragraph("6. Proof of Value & ROI Model (Slide 7)", h1_style))
    story.append(Paragraph(
        "Anchor includes a real-time financial ROI calculator that quantifies value preservation for executive leadership review:<br/>"
        "• <b>Monitored ARR:</b> Total customer base multiplied by average ARR per account.<br/>"
        "• <b>Baseline Churned ARR:</b> Baseline annual gross churn percentage (e.g. 12%).<br/>"
        "• <b>Projected ARR Saved:</b> Churned ARR $\\times$ Anchor Retention Lift % (typically +18.4% to +25%).<br/>"
        "• <b>Net ROI Multiple:</b> Projected Annual ARR Saved divided by platform investment (delivering <b>4.0x to 8.2x ROI</b> with a <b>2.5 to 3.5 month payback period</b>).",
        body_style
    ))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] Successfully generated PDF report: {filename}")


if __name__ == "__main__":
    out_file = "Anchor_Technical_Architecture_Report.pdf"
    if len(sys.argv) > 1 and sys.argv[1].endswith(".pdf"):
        out_file = sys.argv[1]
    build_pdf(out_file)
