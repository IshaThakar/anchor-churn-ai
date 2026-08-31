# Anchor Platform — Complete Technical Architecture & ML Specification

> **Platform Overview:** Anchor is an enterprise-grade AI/ML customer retention platform engineered to ingest multi-dimensional behavioral telemetry, compute real-time calibrated churn propensity scores, explain risk drivers via TreeSHAP, model Time-to-Churn (TTC) using Parametric Weibull survival analysis, and orchestrate automated, hyper-personalized retention workflows before attrition occurs.

---

## 1. Technology Stack Breakdown

| Architecture Layer | Core Technologies | Primary Functions & Capabilities | Engineering & Business Rationale |
| :--- | :--- | :--- | :--- |
| **Data Infrastructure & Feature Store** | Python, Pandas, NumPy, In-Memory Store, Snowflake/Kafka paradigms | Continuous ingestion of Transactional, 60–90d Behavioral, and Contextual NLP telemetry. 90-day daily decay curves. | Enables scalable, sub-second aggregation of clickstream, API volumes, and billing signals. |
| **ML & AI Predictive Engine** | Scikit-learn (Gradient Boosting Ensemble), TreeSHAP, SciPy | Dynamic 0–100 Propensity scoring, TreeSHAP feature attribution waterfall, Weibull Parametric Survival Analysis (TTC), Dissatisfaction Clustering. | High accuracy, interpretability (explains *why* an account is at risk), and non-linear hazard modeling. |
| **Application & API Layer** | FastAPI (Python), Uvicorn (ASGI), Pydantic v2 | High-throughput asynchronous REST endpoints, simulation engine, webhook routing, PII tokenization layer. | Decoupled microservices architecture with strict data validation and sub-50ms API response times. |
| **Orchestration & Integration** | REST Webhook Dispatchers, Closed-Loop Recalibration Engine | Omnichannel routing to Salesforce CRM, Pendo In-App Guides, SendGrid Email Drip, Twilio SMS, Zendesk Priority Support. | Ensures detection maps directly to operational next-best actions with closed-loop feedback tracking ARR saved. |
| **Frontend & Visualization** | HTML5, Custom Glassmorphic CSS, Vanilla JS, Chart.js, Lucide Icons | Interactive account risk matrix, live SHAP waterfall chart, 90-day survival curves, drift simulator sandbox, ROI calculator. | Zero-build-step deployment; runs instantly in any modern browser served directly from FastAPI static files. |

---

## 2. Detailed End-to-End System Workflow

1. **Multi-Dimensional Telemetry Ingestion**: Continuous event ingestion across 3 streams: Transactional (MRR, Plan Tier, Invoices), Behavioral (30d API shift %, session length decay %, core feature usage %), and Contextual (support ticket sentiment, executive sponsor departure signal).
2. **Unified Feature Store Aggregation (`backend/feature_store/store.py`)**: Stores telemetry with complete 90-day daily decay curves. Tokenizes sensitive customer PII using SHA-256 tokens.
3. **Ensemble ML Propensity Scoring (`backend/ml_engine/churn_model.py`)**: Gradient boosted decision trees evaluate the feature vector against calibrated enterprise distributions to output a dynamic **Risk Score (0.0 to 100.0)**.
4. **TreeSHAP Feature Attribution**: Computes exact marginal contributions for each feature against population baselines, isolating positive ($+$ risk accelerators) and negative ($-$ retention anchors) drivers.
5. **Parametric Weibull Survival Analysis**: Fits a non-linear hazard function $S(t) = \exp(-(t/\eta)^\beta)$ over 90 days to estimate the **Time-to-Churn (TTC in days)**.
6. **Dissatisfaction Root-Cause Clustering (`backend/ml_engine/clustering.py`)**: Computes multi-feature distance affinities to classify accounts into driver archetypes (*Price Sensitive*, *Adoption Friction*, *Executive Drift*, *API Degradation*).
7. **Contextual NLP Ticket Sentiment Analysis (`backend/ml_engine/sentiment_nlp.py`)**: Evaluates ticket sentiment. If consecutive negative tickets $\ge 2$, it triggers an immediate Tier 3 SLA override.
8. **Next-Best-Action (NBA) Evaluation (`backend/orchestration/nba_engine.py`)**: Matches the customer segment and ML root cause to the optimal intervention playbook from Slide 6.
9. **Phased Deployment Dispatch Gate (`backend/orchestration/governance.py`)**: Governs outward execution (**Day 1–30 Heuristic Rules**, **Day 30–60 Shadow Mode** where actions are logged but suppressed, **Day 90+ Full Autonomous Orchestration**).
10. **Closed-Loop Feedback & Recalibration (`backend/ml_engine/closed_loop.py`)**: Simulates post-intervention recovery, drops risk score, and updates ARR preserved metrics.

---

## 3. Dataset, Feature Engineering, ML Models & Training Methodology

### A. Synthetic Enterprise B2B SaaS Dataset (1,500 Accounts)
The model is trained on a synthetic dataset of 1,500 multi-dimensional enterprise B2B SaaS accounts generated using realistic non-linear statistical distributions:
- **30-Day API Telemetry Shift (%):** $\mathcal{N}(\mu=5.0, \sigma=35.0)$ clipped between $-95\%$ and $+100\%$.
- **Session Duration Decay (%):** $\text{Exp}(\lambda=0.05)$ modeling silent drift.
- **Core Feature Utilization (%):** $\text{Beta}(\alpha=5, \beta=2) \times 100$ modeling engagement curves.
- **Login Inactivity Interval (Days):** $\text{Exp}(\lambda=0.25)$ representing recency drift.
- **Billing Failures & Downgrade Clicks:** Categorical distributions modeling payment friction and cancellation portal hits.
- **Executive Sponsor Status:** Bernoulli trial ($p=0.88$ active, $0.12$ departed) capturing organizational turnover.
- **NLP Ticket Sentiment Score:** $\mathcal{N}(\mu=0.4, \sigma=0.45)$ mapped from $-1.0$ (severe frustration) to $+1.0$ (positive).

### B. Mathematical Ground Truth Churn Logit
$$\text{logit}(z) = -2.40 - 0.035(\text{API}_\Delta) + 0.028(\text{Session}_{\text{decay}}) - 0.032(\text{CoreUtil} - 50) + 0.06(\text{LoginRecency}) + 0.45(\text{BillingFailures}) + 0.85(\text{DowngradeClicks}) + 1.35(1 - \text{ExecSponsor}) + 0.95(\text{NegTickets}) - 1.20(\text{SentimentScore}) + 0.65(\text{CompetitorQuery}) - 0.003(\text{RenewalDays})$$

$$P(\text{Churn}) = \frac{1}{1 + e^{-z}}$$

### C. TreeSHAP Marginal Feature Attribution
$$\phi_i(x) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f(S \cup \{i\}) - f(S) \right]$$

### D. Parametric Weibull Survival Modeling & Time-to-Churn (TTC)
$$S(t) = \exp\left(-\left(\frac{t}{\eta}\right)^\beta\right), \quad \text{where } \eta = \max\left(12, 160 \cdot e^{-0.028 \cdot \text{RiskScore}}\right), \quad \beta = 1.35$$
The estimated **Time-to-Churn (TTC)** is the median survival horizon where $S(t) \le 0.50$:
$$t_{50} = \eta \cdot (\ln 2)^{1/\beta}$$

---

## 4. Dynamic Intervention & Outreach Routing Matrix (Slide 6)

| Customer Segment | ML Predictive Trigger | Optimal Channel | Automated Action & Orchestration |
| :--- | :--- | :--- | :--- |
| **Enterprise VIP** *(Highest LTV / Strategic)* | Severe drop in API utilization coupled with executive sponsor departure signal. | `RM / CSM Call` | Auto-generates high-priority Salesforce task; routes SHAP values to CSM dashboard; pauses all automated upsell marketing until account health stabilizes. |
| **Mid-Market** *(Core Revenue Base)* | Abandonment of a sticky 'core' feature after initial onboarding sequence. | `In-App / Email` | Triggers a contextual guided-tour UI overlay via Pendo; initiates personalized drip email campaign focused strictly on value realization for that specific feature. |
| **PLG / Self-Serve** *(Volume Driven)* | Clustered as "Price Sensitive" following a recent billing cycle failure or downgrade click. | `SMS / Email` | Injects dynamic, single-use 15% discount code valid for 48 hours; prompts a frictionless "downgrade to free tier" option as a safety net over hard cancellation. |
| **All Tiers** *(Universal Risk)* | Consecutive negative sentiment NLP scores identified via Zendesk ticket integration. | `Priority Support` | Temporarily overrides standard SLA routing to push tickets to Tier 3 support; flags account as 'At-Risk' globally across all Go-To-Market systems. |

---

## 5. Codebase Component Responsibilities

| File Path | Role & Exact Responsibility |
| :--- | :--- |
| `backend/ml_engine/churn_model.py` | Implements synthetic training dataset generation, GradientBoosting ensemble training, calibrated 0–100 risk scoring, TreeSHAP feature attributions, and Weibull Survival Analysis. |
| `backend/ml_engine/clustering.py` | Calculates distance affinities to segment at-risk accounts into dissatisfaction driver archetypes (*Price Sensitive*, *Adoption Friction*, *Executive Drift*, *API Degradation*). |
| `backend/ml_engine/sentiment_nlp.py` | Contextual NLP ticket sentiment engine; analyzes ticket snippets and triggers instant Tier 3 SLA overrides upon consecutive negative interactions. |
| `backend/ml_engine/closed_loop.py` | Captures post-intervention customer responses, simulates telemetry recovery, recalibrates risk scores, and updates prevented ARR metrics. |
| `backend/feature_store/store.py` | Feature Store aggregating Transactional, Behavioral (90-day decay histories), and Contextual telemetry for all accounts with preloaded SaaS enterprise profiles. |
| `backend/orchestration/nba_engine.py` | Executes the Slide 6 Intervention Matrix and routes actions based on customer tier, ML triggers, and governance deployment phase. |
| `backend/orchestration/dispatchers.py` | Omnichannel webhook dispatcher delivering payloads to Salesforce, Pendo, SendGrid, Twilio, and Zendesk. |
| `backend/orchestration/governance.py` | Phased deployment manager (Heuristic, Shadow Mode, Autonomous) and SHA-256 PII tokenization layer. |
| `backend/api/routes.py` | REST API endpoints for KPIs (`/api/overview`), account matrix (`/api/accounts`), dispatching (`/api/orchestration/dispatch`), simulation (`/api/simulation/decay-event`), and ROI (`/api/roi-calculator`). |
| `backend/main.py` | FastAPI application entrypoint with CORS, route mounts, and frontend static file serving. |
| `frontend/index.html & style.css & app.js` | Enterprise Single-Page Dashboard featuring real-time risk gauges, Chart.js SHAP waterfall plots, Survival curves, Drift Simulator sandbox, and ROI model. |
| `test_anchor.py` | Automated test suite validating ML scoring, SHAP attributions, survival curves, clustering, NBA routing, and closed-loop feedback. |
| `run.py` | One-click turnkey startup runner that checks dependencies, starts Uvicorn, and automatically opens `http://127.0.0.1:8000` in the browser. |
| `generate_pdf_report.py` | Generates the official publication-grade PDF technical architecture and ML report. |
