import numpy as np
import math
from datetime import datetime
from typing import List, Tuple, Dict, Any
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from ..models import (
    Telemetry,
    ShapAttribution,
    SurvivalPoint,
    RiskLevel,
    DissatisfactionCluster,
    AccountSegment
)


class PredictiveMLEngine:
    """
    Enterprise-grade ML Engine for Anchor:
    - Ensemble Propensity Modeling (Gradient Boosting)
    - SHAP-style Feature Explainability
    - Parametric Survival Analysis & Time-To-Churn (TTC)
    """

    FEATURE_NAMES = [
        "api_calls_30d_pct_change",      # 0: -100 to +100
        "session_duration_decay_pct",    # 1: 0 to 100
        "core_feature_utilization_pct",  # 2: 0 to 100
        "login_recency_days",            # 3: 0 to 60
        "unread_onboarding_emails",      # 4: 0 to 20
        "billing_cycle_failures",        # 5: 0 to 5
        "downgrade_clicks_30d",          # 6: 0 to 10
        "executive_sponsor_active",      # 7: 1 (True) or 0 (False)
        "consecutive_negative_tickets",  # 8: 0 to 5
        "recent_ticket_sentiment_score", # 9: -1.0 to +1.0
        "competitor_pricing_signals",    # 10: 1 or 0
        "contract_renewal_days",         # 11: 1 to 365
    ]

    FEATURE_LABELS = {
        "api_calls_30d_pct_change": "30-Day API Telemetry Decay",
        "session_duration_decay_pct": "Session Duration Drift",
        "core_feature_utilization_pct": "Sticky Core Feature Utilization",
        "login_recency_days": "Login Inactivity Interval",
        "unread_onboarding_emails": "Unopened Onboarding / Lifecycle Comms",
        "billing_cycle_failures": "Billing & Invoice Payment Failures",
        "downgrade_clicks_30d": "Downgrade / Cancellation Portal Hits",
        "executive_sponsor_active": "Executive Sponsor Departure Signal",
        "consecutive_negative_tickets": "Consecutive Negative Zendesk Sentiment",
        "recent_ticket_sentiment_score": "NLP Support Ticket Sentiment",
        "competitor_pricing_signals": "Competitor Benchmarking & Pricing Query",
        "contract_renewal_days": "Days Remaining Until Contract Renewal",
    }

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = GradientBoostingClassifier(
            n_estimators=120,
            learning_rate=0.08,
            max_depth=4,
            random_state=42
        )
        self.baseline_feature_means = {}
        self.is_trained = False
        self._train_initial_model()

    def _generate_synthetic_training_data(self, n_samples: int = 1500) -> Tuple[np.ndarray, np.ndarray]:
        """Generates realistic enterprise SaaS behavioral telemetry distributions."""
        np.random.seed(42)
        X = np.zeros((n_samples, len(self.FEATURE_NAMES)))

        # Feature generation
        # 0: API change %
        api_change = np.random.normal(loc=5.0, scale=35.0, size=n_samples)
        X[:, 0] = np.clip(api_change, -95.0, 100.0)

        # 1: Session decay %
        session_decay = np.random.exponential(scale=20.0, size=n_samples)
        X[:, 1] = np.clip(session_decay, 0.0, 95.0)

        # 2: Core feature utilization %
        core_util = np.random.beta(a=5, b=2, size=n_samples) * 100.0
        X[:, 2] = np.clip(core_util, 5.0, 100.0)

        # 3: Login recency days
        login_recency = np.random.exponential(scale=4.0, size=n_samples)
        X[:, 3] = np.clip(login_recency, 0, 60)

        # 4: Unread onboarding emails
        X[:, 4] = np.random.poisson(lam=1.5, size=n_samples)

        # 5: Billing failures
        X[:, 5] = np.random.choice([0, 1, 2, 3], size=n_samples, p=[0.82, 0.12, 0.04, 0.02])

        # 6: Downgrade clicks
        X[:, 6] = np.random.choice([0, 1, 2, 4], size=n_samples, p=[0.85, 0.09, 0.04, 0.02])

        # 7: Executive sponsor active (1 = active, 0 = departed)
        X[:, 7] = np.random.choice([1, 0], size=n_samples, p=[0.88, 0.12])

        # 8: Consecutive negative tickets
        X[:, 8] = np.random.choice([0, 1, 2, 3, 4], size=n_samples, p=[0.75, 0.15, 0.06, 0.03, 0.01])

        # 9: Recent ticket sentiment (-1.0 to 1.0)
        sentiment = np.random.normal(loc=0.4, scale=0.45, size=n_samples)
        X[:, 9] = np.clip(sentiment, -1.0, 1.0)

        # 10: Competitor pricing signals
        X[:, 10] = np.random.choice([0, 1], size=n_samples, p=[0.85, 0.15])

        # 11: Contract renewal days
        X[:, 11] = np.random.uniform(10, 365, size=n_samples)

        # Calculate ground truth churn probability based on non-linear behavioral decay equations
        logit = (
            -2.4
            + (-0.035 * X[:, 0])             # API drop increases churn
            + (0.028 * X[:, 1])              # Session decay increases churn
            + (-0.032 * (X[:, 2] - 50.0))    # Core feature abandonment increases churn
            + (0.06 * X[:, 3])               # Login recency
            + (0.45 * X[:, 5])               # Billing failure
            + (0.85 * X[:, 6])               # Downgrade clicks
            + (1.35 * (1 - X[:, 7]))         # Executive departure
            + (0.95 * X[:, 8])               # Negative tickets
            + (-1.20 * X[:, 9])              # Sentiment
            + (0.65 * X[:, 10])              # Competitor signals
            + (-0.003 * X[:, 11])            # Near renewal date slight pressure
        )

        probs = 1.0 / (1.0 + np.exp(-logit))
        y = (np.random.rand(n_samples) < probs).astype(int)

        return X, y

    def _train_initial_model(self):
        """Fits the initial gradient boosted model on SaaS telemetry."""
        X, y = self._generate_synthetic_training_data(1500)
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        self.model.fit(X_scaled, y)
        self.baseline_feature_means = {
            self.FEATURE_NAMES[i]: float(np.mean(X[:, i])) for i in range(len(self.FEATURE_NAMES))
        }
        self.is_trained = True

    def extract_features(self, telemetry: Telemetry, renewal_days: int = 180) -> np.ndarray:
        """Extracts numerical vector for ML inference."""
        return np.array([[
            float(telemetry.api_calls_30d_pct_change),
            float(telemetry.session_duration_decay_pct),
            float(telemetry.core_feature_utilization_pct),
            float(telemetry.login_recency_days),
            float(telemetry.unread_onboarding_emails),
            float(telemetry.billing_cycle_failures),
            float(telemetry.downgrade_clicks_30d),
            1.0 if telemetry.executive_sponsor_active else 0.0,
            float(telemetry.consecutive_negative_tickets),
            float(telemetry.recent_ticket_sentiment_score),
            1.0 if telemetry.competitor_pricing_signals else 0.0,
            float(renewal_days)
        ]])

    def predict_risk(self, telemetry: Telemetry, renewal_days: int = 180) -> Tuple[float, RiskLevel]:
        """Calculates dynamic Risk Score (0 to 100) using calibrated gradient boosted trees."""
        feat = self.extract_features(telemetry, renewal_days)
        feat_scaled = self.scaler.transform(feat)
        prob = self.model.predict_proba(feat_scaled)[0, 1]
        
        # Risk score scaled to 0-100 with precision
        score = float(np.clip(prob * 100.0, 1.0, 99.0))
        score = round(score, 1)

        if score >= 75.0:
            level = RiskLevel.CRITICAL
        elif score >= 50.0:
            level = RiskLevel.HIGH
        elif score >= 25.0:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return score, level

    def calculate_shap_attributions(self, telemetry: Telemetry, renewal_days: int = 180) -> List[ShapAttribution]:
        """
        Computes exact marginal SHAP-style feature attribution values.
        Quantifies how each behavioral decay indicator drives risk upward or downward.
        """
        feat_raw = self.extract_features(telemetry, renewal_days)[0]
        base_score, _ = self.predict_risk(telemetry, renewal_days)

        attributions: List[ShapAttribution] = []

        # Perturbation-based marginal attribution against baseline distribution
        for idx, feat_name in enumerate(self.FEATURE_NAMES):
            observed_val = feat_raw[idx]
            baseline_val = self.baseline_feature_means[feat_name]

            # Create baseline replaced vector
            perturbed_feat = feat_raw.copy()
            perturbed_feat[idx] = baseline_val
            
            p_scaled = self.scaler.transform([perturbed_feat])
            perturbed_prob = self.model.predict_proba(p_scaled)[0, 1]
            perturbed_score = float(np.clip(perturbed_prob * 100.0, 1.0, 99.0))

            # Impact: positive means this feature increased churn risk above baseline
            impact = round(base_score - perturbed_score, 2)
            
            # Format explanation description
            label = self.FEATURE_LABELS[feat_name]
            direction = "risk_increase" if impact >= 0 else "risk_decrease"
            
            explanation = self._build_explanation_text(feat_name, observed_val, impact)

            attributions.append(ShapAttribution(
                feature_id=feat_name,
                feature_name=label,
                impact_score=impact,
                observed_value=float(observed_val) if isinstance(observed_val, (int, float, np.number)) else observed_val,
                baseline_value=round(baseline_val, 2),
                direction=direction,
                explanation=explanation
            ))

        # Sort attributions by absolute impact magnitude
        attributions.sort(key=lambda x: abs(x.impact_score), reverse=True)
        return attributions

    def _build_explanation_text(self, feat_name: str, val: float, impact: float) -> str:
        """Creates human-interpretable root cause description for CSM/Dashboard."""
        if feat_name == "api_calls_30d_pct_change":
            return f"API usage shifted by {val:+.1f}% over 30 days ({'+' if impact > 0 else ''}{impact:.1f} risk score impact)."
        elif feat_name == "executive_sponsor_active":
            return "Executive sponsor departure detected (+ risk signal)" if val == 0 else "Executive sponsor remains active (retention anchor)."
        elif feat_name == "core_feature_utilization_pct":
            return f"Core sticky feature engagement is at {val:.1f}% ({'+' if impact > 0 else ''}{impact:.1f} impact)."
        elif feat_name == "session_duration_decay_pct":
            return f"Session duration declined by {val:.1f}% vs historical 90-day baseline."
        elif feat_name == "consecutive_negative_tickets":
            return f"{int(val)} consecutive negative sentiment support tickets logged."
        elif feat_name == "billing_cycle_failures":
            return f"{int(val)} recent invoice or credit card payment failures recorded."
        elif feat_name == "downgrade_clicks_30d":
            return f"{int(val)} visits to account cancellation/downgrade settings."
        elif feat_name == "recent_ticket_sentiment_score":
            return f"NLP sentiment score of {val:+.2f} on recent communications."
        elif feat_name == "login_recency_days":
            return f"Last user session was {int(val)} days ago."
        elif feat_name == "unread_onboarding_emails":
            return f"{int(val)} unread onboarding / feature update emails."
        elif feat_name == "competitor_pricing_signals":
            return "Competitor price-check query triggered in sales/support notes."
        elif feat_name == "contract_renewal_days":
            return f"Contract renewal in {int(val)} days."
        return f"{feat_name}: {val}"

    def calculate_survival_curve(self, risk_score: float) -> Tuple[List[SurvivalPoint], int]:
        """
        Parametric Weibull Survival Analysis:
        Predicts S(t) = exp(-(t / eta)^beta) over 90 days.
        Calculates estimated Time-To-Churn (TTC in days) where S(t) <= 0.50.
        """
        # Base scale parameter eta decreases sharply as risk score increases
        normalized_risk = max(1.0, min(99.0, risk_score))
        
        # High risk -> fast decay (eta 20-35 days), Low risk -> slow decay (eta 180+ days)
        eta = max(12.0, 160.0 * math.exp(-0.028 * normalized_risk))
        beta = 1.35  # Accelerating hazard (typical of silent drift)

        survival_points: List[SurvivalPoint] = []
        ttc_days = 90
        found_ttc = False

        for day in range(0, 91, 5):
            t = float(day)
            if t == 0:
                s_t = 1.00
                hazard = 0.0
            else:
                hazard = (beta / eta) * ((t / eta) ** (beta - 1))
                s_t = math.exp(-((t / eta) ** beta))
                s_t = max(0.01, min(1.0, s_t))

            survival_points.append(SurvivalPoint(
                day=day,
                survival_probability=round(s_t, 3),
                hazard_rate=round(hazard, 4)
            ))

            if not found_ttc and s_t <= 0.50 and day > 0:
                ttc_days = day
                found_ttc = True

        if not found_ttc:
            # Extrapolate TTC if low risk
            ttc_days = int(eta * ((-math.log(0.5)) ** (1.0 / beta)))

        return survival_points, ttc_days


# Singleton ML Engine instance
ml_engine = PredictiveMLEngine()
