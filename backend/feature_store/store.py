import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from ..models import (
    Account,
    AccountSegment,
    Telemetry,
    DailyTelemetryPoint,
    PredictionResult,
    InterventionRecord,
    DeploymentMode,
    DissatisfactionCluster
)
from ..ml_engine.churn_model import ml_engine
from ..ml_engine.clustering import cluster_engine
from ..ml_engine.sentiment_nlp import sentiment_engine
from ..orchestration.nba_engine import nba_engine
from ..orchestration.governance import governance_engine
from ..orchestration.dispatchers import dispatcher


class FeatureStore:
    """
    Unified Ingestion & Feature Store:
    Aggregates Transactional, Behavioral, and Contextual telemetry.
    Pre-populates enterprise accounts and manages live scoring.
    """

    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self._initialize_sample_accounts()
        self.recompute_all_predictions()

    def _generate_90d_curve(self, base_api: int, trend: str) -> List[DailyTelemetryPoint]:
        """Generates realistic 90-day daily telemetry curves."""
        curve = []
        for d in range(90, -1, -5):
            day_idx = 90 - d
            if trend == "severe_decay":
                factor = max(0.15, 1.0 - (day_idx / 90.0) * 0.75)
            elif trend == "mild_decay":
                factor = max(0.45, 1.0 - (day_idx / 90.0) * 0.40)
            elif trend == "abandonment":
                factor = max(0.10, 1.0 - (day_idx / 90.0) * 0.85)
            else:  # healthy
                factor = 1.0 + (day_idx / 90.0) * 0.15

            curve.append(DailyTelemetryPoint(
                day=d,
                api_calls=int(base_api * factor),
                session_minutes=round(max(5.0, 45.0 * factor), 1),
                core_feature_events=int(max(2, 35 * factor)),
                active_users=int(max(1, 20 * factor))
            ))
        return curve

    def _initialize_sample_accounts(self):
        # 1. Enterprise VIP - High Churn Risk (Severe API Drop + Sponsor Departure)
        acc1_id = "acc_ent_001"
        self.accounts[acc1_id] = Account(
            id=acc1_id,
            name="Apex Global Cloud",
            domain="apexcloud.io",
            tier=AccountSegment.ENTERPRISE_VIP,
            mrr=24500.0,
            arr=294000.0,
            contract_renewal_days=45,
            csm_assigned="Sarah Jenkins (Principal CSM)",
            is_at_risk_flag=True,
            upsell_marketing_paused=True,
            sla_tier_override=None,
            anonymized_token=governance_engine.generate_token(acc1_id),
            telemetry=Telemetry(
                mrr=24500.0,
                plan_tier="Enterprise Platinum",
                billing_frequency="Annual",
                billing_cycle_failures=0,
                downgrade_clicks_30d=0,
                api_calls_30d_pct_change=-68.5,
                session_duration_decay_pct=52.0,
                core_feature_utilization_pct=34.0,
                login_recency_days=9,
                unread_onboarding_emails=4,
                executive_sponsor_active=False,  # Sponsor Left!
                consecutive_negative_tickets=1,
                recent_ticket_sentiment_score=-0.25,
                competitor_pricing_signals=True,
                historical_90d_decay=self._generate_90d_curve(120000, "severe_decay")
            )
        )

        # 2. Enterprise VIP - Healthy / Anchor Account
        acc2_id = "acc_ent_002"
        self.accounts[acc2_id] = Account(
            id=acc2_id,
            name="Nexus BioPharma",
            domain="nexusbio.com",
            tier=AccountSegment.ENTERPRISE_VIP,
            mrr=38000.0,
            arr=456000.0,
            contract_renewal_days=210,
            csm_assigned="Michael Chen (Enterprise Director)",
            is_at_risk_flag=False,
            upsell_marketing_paused=False,
            sla_tier_override=None,
            anonymized_token=governance_engine.generate_token(acc2_id),
            telemetry=Telemetry(
                mrr=38000.0,
                plan_tier="Enterprise Custom",
                billing_frequency="Annual",
                billing_cycle_failures=0,
                downgrade_clicks_30d=0,
                api_calls_30d_pct_change=14.2,
                session_duration_decay_pct=0.0,
                core_feature_utilization_pct=92.0,
                login_recency_days=1,
                unread_onboarding_emails=0,
                executive_sponsor_active=True,
                consecutive_negative_tickets=0,
                recent_ticket_sentiment_score=0.85,
                competitor_pricing_signals=False,
                historical_90d_decay=self._generate_90d_curve(250000, "healthy")
            )
        )

        # 3. Mid-Market - Core Feature Abandonment (Sticky Feature Dropped Post-Onboarding)
        acc3_id = "acc_mid_001"
        self.accounts[acc3_id] = Account(
            id=acc3_id,
            name="FinPulse Analytics",
            domain="finpulse.ai",
            tier=AccountSegment.MID_MARKET,
            mrr=4800.0,
            arr=57600.0,
            contract_renewal_days=78,
            csm_assigned="David Ross",
            is_at_risk_flag=True,
            upsell_marketing_paused=False,
            sla_tier_override=None,
            anonymized_token=governance_engine.generate_token(acc3_id),
            telemetry=Telemetry(
                mrr=4800.0,
                plan_tier="Mid-Market Growth",
                billing_frequency="Annual",
                billing_cycle_failures=0,
                downgrade_clicks_30d=1,
                api_calls_30d_pct_change=-22.0,
                session_duration_decay_pct=44.0,
                core_feature_utilization_pct=18.5,  # Severe core feature drop
                login_recency_days=6,
                unread_onboarding_emails=3,
                executive_sponsor_active=True,
                consecutive_negative_tickets=0,
                recent_ticket_sentiment_score=0.10,
                competitor_pricing_signals=False,
                historical_90d_decay=self._generate_90d_curve(45000, "abandonment")
            )
        )

        # 4. Mid-Market - Universal Risk (Consecutive Negative Zendesk Tickets)
        acc4_id = "acc_mid_002"
        self.accounts[acc4_id] = Account(
            id=acc4_id,
            name="RetailFlow Omnichannel",
            domain="retailflow.net",
            tier=AccountSegment.MID_MARKET,
            mrr=6200.0,
            arr=74400.0,
            contract_renewal_days=115,
            csm_assigned="Emily Thorne",
            is_at_risk_flag=True,
            upsell_marketing_paused=False,
            sla_tier_override="Tier 3 Priority Support (Instant Override)",
            anonymized_token=governance_engine.generate_token(acc4_id),
            telemetry=Telemetry(
                mrr=6200.0,
                plan_tier="Mid-Market Pro",
                billing_frequency="Annual",
                billing_cycle_failures=0,
                downgrade_clicks_30d=0,
                api_calls_30d_pct_change=-15.0,
                session_duration_decay_pct=28.0,
                core_feature_utilization_pct=65.0,
                login_recency_days=2,
                unread_onboarding_emails=1,
                executive_sponsor_active=True,
                consecutive_negative_tickets=3,  # 3 consecutive negative tickets!
                recent_ticket_sentiment_score=-0.78,
                competitor_pricing_signals=False,
                historical_90d_decay=self._generate_90d_curve(60000, "mild_decay")
            )
        )

        # 5. PLG / Self-Serve - Price Sensitive (Billing Failure + Downgrade Click)
        acc5_id = "acc_plg_001"
        self.accounts[acc5_id] = Account(
            id=acc5_id,
            name="DevCraft Studio",
            domain="devcraft.io",
            tier=AccountSegment.PLG_SELF_SERVE,
            mrr=499.0,
            arr=5988.0,
            contract_renewal_days=12,
            csm_assigned="Self-Serve Automated Queue",
            is_at_risk_flag=True,
            upsell_marketing_paused=False,
            sla_tier_override=None,
            anonymized_token=governance_engine.generate_token(acc5_id),
            telemetry=Telemetry(
                mrr=499.0,
                plan_tier="Pro Team",
                billing_frequency="Monthly",
                billing_cycle_failures=2,  # 2 Invoice failures
                downgrade_clicks_30d=3,    # Downgrade page views
                api_calls_30d_pct_change=-42.0,
                session_duration_decay_pct=60.0,
                core_feature_utilization_pct=40.0,
                login_recency_days=14,
                unread_onboarding_emails=5,
                executive_sponsor_active=True,
                consecutive_negative_tickets=0,
                recent_ticket_sentiment_score=-0.15,
                competitor_pricing_signals=True,
                historical_90d_decay=self._generate_90d_curve(15000, "severe_decay")
            )
        )

        # 6. PLG / Self-Serve - Healthy High-Velocity
        acc6_id = "acc_plg_002"
        self.accounts[acc6_id] = Account(
            id=acc6_id,
            name="QuickStack Micro",
            domain="quickstack.dev",
            tier=AccountSegment.PLG_SELF_SERVE,
            mrr=299.0,
            arr=3588.0,
            contract_renewal_days=290,
            csm_assigned="Self-Serve Automated Queue",
            is_at_risk_flag=False,
            upsell_marketing_paused=False,
            sla_tier_override=None,
            anonymized_token=governance_engine.generate_token(acc6_id),
            telemetry=Telemetry(
                mrr=299.0,
                plan_tier="Team Starter",
                billing_frequency="Monthly",
                billing_cycle_failures=0,
                downgrade_clicks_30d=0,
                api_calls_30d_pct_change=28.0,
                session_duration_decay_pct=0.0,
                core_feature_utilization_pct=88.0,
                login_recency_days=1,
                unread_onboarding_emails=0,
                executive_sponsor_active=True,
                consecutive_negative_tickets=0,
                recent_ticket_sentiment_score=0.90,
                competitor_pricing_signals=False,
                historical_90d_decay=self._generate_90d_curve(12000, "healthy")
            )
        )

        # 7. Enterprise VIP - High Telemetry Decay
        acc7_id = "acc_ent_003"
        self.accounts[acc7_id] = Account(
            id=acc7_id,
            name="Strata Logistics",
            domain="stratalogistics.com",
            tier=AccountSegment.ENTERPRISE_VIP,
            mrr=19500.0,
            arr=234000.0,
            contract_renewal_days=95,
            csm_assigned="Sarah Jenkins",
            is_at_risk_flag=True,
            upsell_marketing_paused=False,
            sla_tier_override=None,
            anonymized_token=governance_engine.generate_token(acc7_id),
            telemetry=Telemetry(
                mrr=19500.0,
                plan_tier="Enterprise Scale",
                billing_frequency="Annual",
                billing_cycle_failures=0,
                downgrade_clicks_30d=0,
                api_calls_30d_pct_change=-48.0,
                session_duration_decay_pct=39.0,
                core_feature_utilization_pct=52.0,
                login_recency_days=7,
                unread_onboarding_emails=2,
                executive_sponsor_active=False,
                consecutive_negative_tickets=1,
                recent_ticket_sentiment_score=-0.10,
                competitor_pricing_signals=False,
                historical_90d_decay=self._generate_90d_curve(95000, "severe_decay")
            )
        )

        # 8. Mid-Market - Stable Growth
        acc8_id = "acc_mid_003"
        self.accounts[acc8_id] = Account(
            id=acc8_id,
            name="DataVanguard Corp",
            domain="datavanguard.io",
            tier=AccountSegment.MID_MARKET,
            mrr=5500.0,
            arr=66000.0,
            contract_renewal_days=180,
            csm_assigned="David Ross",
            is_at_risk_flag=False,
            upsell_marketing_paused=False,
            sla_tier_override=None,
            anonymized_token=governance_engine.generate_token(acc8_id),
            telemetry=Telemetry(
                mrr=5500.0,
                plan_tier="Growth Plus",
                billing_frequency="Annual",
                billing_cycle_failures=0,
                downgrade_clicks_30d=0,
                api_calls_30d_pct_change=8.5,
                session_duration_decay_pct=5.0,
                core_feature_utilization_pct=78.0,
                login_recency_days=2,
                unread_onboarding_emails=0,
                executive_sponsor_active=True,
                consecutive_negative_tickets=0,
                recent_ticket_sentiment_score=0.60,
                competitor_pricing_signals=False,
                historical_90d_decay=self._generate_90d_curve(50000, "healthy")
            )
        )

    def score_account(self, account: Account) -> Account:
        """Runs the complete ML + Explainability + Survival + NBA pipeline on an account."""
        t = account.telemetry
        gov_mode = governance_engine.get_settings().current_mode

        # 1. Propensity ML Score
        risk_score, risk_level = ml_engine.predict_risk(t, account.contract_renewal_days)

        # 2. SHAP Feature Attribution
        shap_values = ml_engine.calculate_shap_attributions(t, account.contract_renewal_days)

        # 3. Survival Analysis & TTC
        survival_curve, ttc_days = ml_engine.calculate_survival_curve(risk_score)

        # 4. Dissatisfaction Driver Clustering
        cluster, cluster_conf = cluster_engine.classify_cluster(t, risk_score)

        # 5. NLP Sentiment & Support SLA Engine
        sentiment_analysis = sentiment_engine.analyze_sentiment(t)

        # 6. Next-Best-Action Omnichannel Routing
        nba, updated_account = nba_engine.evaluate_and_route(
            account=account,
            risk_score=risk_score,
            cluster=cluster,
            shap_values=shap_values,
            sentiment_analysis=sentiment_analysis,
            current_mode=gov_mode
        )

        # Compile full prediction
        updated_account.latest_prediction = PredictionResult(
            risk_score=risk_score,
            risk_level=risk_level,
            estimated_ttc_days=ttc_days,
            cluster=cluster,
            cluster_confidence=cluster_conf,
            shap_attributions=shap_values,
            survival_curve=survival_curve,
            sentiment_analysis=sentiment_analysis,
            next_best_action=nba,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        return updated_account

    def recompute_all_predictions(self):
        for acc_id in list(self.accounts.keys()):
            self.accounts[acc_id] = self.score_account(self.accounts[acc_id])

    def get_account(self, account_id: str) -> Optional[Account]:
        return self.accounts.get(account_id)

    def get_all_accounts(self) -> List[Account]:
        return list(self.accounts.values())

    def update_telemetry(self, account_id: str, new_telemetry: Telemetry) -> Account:
        if account_id in self.accounts:
            self.accounts[account_id].telemetry = new_telemetry
            self.accounts[account_id] = self.score_account(self.accounts[account_id])
            return self.accounts[account_id]
        raise ValueError(f"Account {account_id} not found.")


feature_store = FeatureStore()
