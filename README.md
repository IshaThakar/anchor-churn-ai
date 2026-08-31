# Anchor: Predictive Intelligence for Customer Retention

> **Enterprise-grade AI/ML retention platform engineered to ingest multi-dimensional behavioral data, calculate real-time churn propensity scores, and orchestrate automated, hyper-personalized retention workflows before attrition occurs.**

Built strictly in accordance with the **Anchor Architectural Specification and Product Deck**.

---

## 🎯 Paradigm Shift: Reactive to Predictive (Slide 2)

| Legacy Reactive Approach | Anchor Predictive Engine |
| :--- | :--- |
| **Lagging Indicators**: Relying on NPS drops, cancellation tickets, or expired renewal dates guarantees revenue loss (70% of churn happens silently). | **Continuous Multi-Dimensional Ingestion**: Ingests API usage drift, session duration decay, and core feature abandonment over 60–90 day windows. |
| **Black-box Gut Instinct**: Guesswork on why accounts are unhappy. | **SHAP Explainability**: Calibrated TreeSHAP feature attributions explaining *why* an account is at risk. |
| **Static Retention Plays**: Generic "blast" email surveys. | **Omnichannel Next-Best-Action (NBA)**: Dynamic routing to Salesforce, Pendo in-app guides, SendGrid dynamic promo codes, Twilio SMS, and Zendesk SLA overrides. |
| **Open-loop Action**: No tracking if outreach succeeded. | **Closed-Loop Recalibration**: Post-intervention behavioral shifts feed back into model weights and ARR preserved metrics. |

---

## 🏛️ System Architecture (Slide 3 & 4)

```
anchor-platform/
├── backend/
│   ├── api/
│   │   └── routes.py              # REST API: Accounts, Predictions, SHAP, Survival, Dispatches, Governance, ROI
│   ├── feature_store/
│   │   └── store.py               # Ingestion & Feature Store with 90-day decay histories & PII tokenization
│   ├── ml_engine/
│   │   ├── churn_model.py         # Ensemble Gradient Boosting (0-100 score), SHAP attributions, Weibull Survival Analysis (TTC)
│   │   ├── clustering.py          # Root-cause Driver Clustering (Price Sensitive, Adoption Friction, Executive Drift, API Drop)
│   │   ├── sentiment_nlp.py       # Contextual Ticket NLP Sentiment Analyzer & Consecutive Negative Tracker
│   │   └── closed_loop.py         # Closed-loop Feedback Engine & ARR Saved Tracker
│   ├── orchestration/
│   │   ├── nba_engine.py          # Slide 6 Next-Best-Action Intervention Matrix
│   │   ├── dispatchers.py         # Omnichannel Webhook Dispatchers (Salesforce, Pendo, SendGrid, Twilio, Zendesk)
│   │   └── governance.py          # Phased Deployment Matrix (Heuristic, Shadow Mode, Autonomous) & PII Tokenizer
│   ├── config.py                  # Server configuration
│   ├── models.py                  # Complete Pydantic schemas and enums
│   └── main.py                    # FastAPI application & static server
├── frontend/
│   ├── index.html                 # Enterprise Dark UI Dashboard with interactive charts
│   ├── style.css                  # Custom Glassmorphic CSS with responsive grid
│   └── app.js                     # Real-time state management, Chart.js integrations, Simulation sandbox
├── test_anchor.py                 # Automated test suite (100% passing)
├── run.py                         # One-click startup runner
├── start.bat                      # Windows Batch launcher
├── start.ps1                      # Windows PowerShell launcher
└── requirements.txt               # Backend dependencies
```

---

## ⚡ Dynamic Intervention & Outreach Routing Matrix (Slide 6)

| Customer Segment | ML Predictive Trigger | Optimal Channel | Automated Action & Orchestration |
| :--- | :--- | :--- | :--- |
| **Enterprise VIP** *(Highest LTV / Strategic)* | Severe drop in API utilization coupled with executive sponsor departure. | `RM / CSM Call` | Auto-generates high-priority Salesforce task; routes SHAP values to CSM dashboard; pauses all automated upsell marketing until account stabilizes. |
| **Mid-Market** *(Core Revenue Base)* | Abandonment of a sticky 'core' feature after initial onboarding sequence. | `In-App / Email` | Triggers a contextual guided-tour UI overlay via Pendo; initiates personalized drip email campaign focused strictly on value realization for that specific feature. |
| **PLG / Self-Serve** *(Volume Driven)* | Clustered as "Price Sensitive" following a recent billing cycle failure or downgrade click. | `SMS / Email` | Injects dynamic, single-use 15% discount code valid for 48 hours; prompts a frictionless "downgrade to free tier" option as a safety net over hard cancellation. |
| **All Tiers** *(Universal Risk)* | Consecutive negative sentiment NLP scores identified via Zendesk ticket integration. | `Priority Support` | Temporarily overrides standard SLA routing to push tickets to Tier 3 support; flags account as 'At-Risk' globally across all Go-To-Market systems. |

---

## 🚀 How to Run in VS Code / Terminal

### Option 1: Quick Run with Python
```powershell
# 1. Clone the repo and navigate to the project directory
git clone https://github.com/YOUR_USERNAME/anchor-platform.git
cd anchor-platform

# 2. Run the platform (automatically installs packages if needed)
python run.py
# or
py -3.13 run.py
```

### Option 2: Windows Batch / PowerShell
Double-click `start.bat` or run:
```powershell
.\start.ps1
```

Once running:
- **Interactive UI Dashboard**: Open `http://localhost:8000` in your web browser.
- **Interactive Swagger API Docs**: Open `http://localhost:8000/docs`.

---

## 🧪 Verification & Testing

To execute the unit test suite covering ML propensity scoring, SHAP explainability, Weibull survival curve, clustering, NBA intervention matrix, governance modes, and closed-loop learning:

```powershell
py -3.13 test_anchor.py
```

All 6 test suites execute with `OK` status.

---

## 🎮 Interactive Features in the Dashboard

1. **Phased Deployment Matrix Toggle (Top Bar)**:
   - **Day 1–30: Heuristic Rules**: Rule-based alerts.
   - **Day 30–60: V1 ML Shadow Mode**: ML predictions run in the background; outward dispatches are suppressed and logged for validation.
   - **Day 90+: Full Autonomous**: Deep behavioral ML scoring with automated instantaneous dispatch.
2. **PII Masking Toggle (GDPR / CCPA)**:
   - Instantly hashes and masks sensitive customer domain and account names into `Account #tok_...` tokens.
3. **Deep Retention Inspector (Click "Inspect" on any account)**:
   - **0–100 Dynamic Risk Gauge** and **Estimated Time-to-Churn (TTC)**.
   - **Interactive SHAP Waterfall Chart**: Visually breaks down feature contributions (+ / -).
   - **Parametric Weibull Survival Curve**: Plots survival probability decay $S(t)$ over 90 days.
   - **60–90 Day Multi-Dimensional Telemetry Chart**: Tracks API calls, Core Feature usage, and Session Duration.
   - **1-Click Omnichannel Dispatch & Closed-Loop Simulator**.
4. **Behavioral Decay Simulator (Sandbox Tab)**:
   - Inject real-time scenarios (e.g. *-70% API Decay*, *Executive Sponsor Departure*, *Billing Failure*, *Negative Zendesk Tickets*) and watch the entire ML model re-score the account and update the UI in real time.
5. **Proof of Value & ROI Model (Slide 7 Tab)**:
   - Dynamic financial calculator projecting ARR saved, Net ROI multiple (e.g. 4.0x–8.2x), and Payback Period in months.
