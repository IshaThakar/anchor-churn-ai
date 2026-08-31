import uuid
from datetime import datetime, timezone
from typing import Tuple
from ..models import Account, PredictionResult, RiskLevel


class ClosedLoopLearningEngine:
    """
    Closed-Loop Learning Engine:
    - Captures post-intervention behavioral shifts (e.g. discount accepted, CSM call completed).
    - Dynamically updates account telemetry and recalibrates risk scores.
    - Feeds outcome data back into model metrics and tracks saved ARR.
    """

    def apply_intervention_feedback(
        self,
        account: Account,
        outcome: str = "Accepted & Retained"
    ) -> Tuple[Account, float]:
        """
        Simulates the closed-loop recovery of an account following a successful retention action.
        Returns the updated account and the risk reduction delta.
        """
        old_score = account.latest_prediction.risk_score if account.latest_prediction else 50.0

        if outcome == "Accepted & Retained":
            # Account positively responded to intervention
            # 1. API recovery
            account.telemetry.api_calls_30d_pct_change = 18.0

            # 2. Core feature adoption renewed & session active
            account.telemetry.core_feature_utilization_pct = 88.0
            account.telemetry.session_duration_decay_pct = 0.0
            account.telemetry.login_recency_days = 1
            account.telemetry.unread_onboarding_emails = 0

            # 3. Billing & downgrade intent cleared
            account.telemetry.billing_cycle_failures = 0
            account.telemetry.downgrade_clicks_30d = 0
            account.telemetry.competitor_pricing_signals = False

            # 4. Sentiment restored
            account.telemetry.consecutive_negative_tickets = 0
            account.telemetry.recent_ticket_sentiment_score = 0.85
            account.telemetry.executive_sponsor_active = True

            # 5. Clear global at-risk flag & resume upsell
            account.is_at_risk_flag = False
            account.upsell_marketing_paused = False
            account.sla_tier_override = None

        # Re-run ML prediction
        from .churn_model import ml_engine
        from .clustering import cluster_engine
        from .sentiment_nlp import sentiment_engine
        from ..orchestration.nba_engine import nba_engine
        from ..orchestration.governance import governance_engine

        gov_mode = governance_engine.get_settings().current_mode
        new_score, new_level = ml_engine.predict_risk(account.telemetry, account.contract_renewal_days)
        shap_values = ml_engine.calculate_shap_attributions(account.telemetry, account.contract_renewal_days)
        survival_curve, ttc = ml_engine.calculate_survival_curve(new_score)
        cluster, conf = cluster_engine.classify_cluster(account.telemetry, new_score)
        sentiment = sentiment_engine.analyze_sentiment(account.telemetry)

        nba, account = nba_engine.evaluate_and_route(
            account=account,
            risk_score=new_score,
            cluster=cluster,
            shap_values=shap_values,
            sentiment_analysis=sentiment,
            current_mode=gov_mode
        )

        account.latest_prediction = PredictionResult(
            risk_score=new_score,
            risk_level=new_level,
            estimated_ttc_days=ttc,
            cluster=cluster,
            cluster_confidence=conf,
            shap_attributions=shap_values,
            survival_curve=survival_curve,
            sentiment_analysis=sentiment,
            next_best_action=nba,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        # Log to intervention record
        risk_delta = round(old_score - new_score, 1)

        if account.intervention_history:
            latest_record = account.intervention_history[0]
            latest_record.status = "Completed"
            latest_record.outcome_status = outcome
            latest_record.post_intervention_risk_delta = risk_delta

        return account, risk_delta


closed_loop_engine = ClosedLoopLearningEngine()
