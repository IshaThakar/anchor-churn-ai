import sys
import unittest
from backend.models import (
    Telemetry,
    AccountSegment,
    RiskLevel,
    DissatisfactionCluster,
    DeploymentMode,
    SimulationDecayRequest
)
from backend.ml_engine.churn_model import ml_engine
from backend.ml_engine.clustering import cluster_engine
from backend.ml_engine.sentiment_nlp import sentiment_engine
from backend.ml_engine.closed_loop import closed_loop_engine
from backend.feature_store.store import feature_store
from backend.orchestration.nba_engine import nba_engine
from backend.orchestration.governance import governance_engine
from backend.orchestration.dispatchers import dispatcher


class TestAnchorPlatform(unittest.TestCase):

    def test_01_ml_propensity_and_shap(self):
        """Test ML ensemble scoring and SHAP explainability."""
        t_high_risk = Telemetry(
            mrr=25000.0,
            api_calls_30d_pct_change=-75.0,
            session_duration_decay_pct=60.0,
            core_feature_utilization_pct=20.0,
            login_recency_days=15,
            unread_onboarding_emails=5,
            billing_cycle_failures=2,
            downgrade_clicks_30d=2,
            executive_sponsor_active=False,
            consecutive_negative_tickets=3,
            recent_ticket_sentiment_score=-0.8,
            competitor_pricing_signals=True
        )

        score, level = ml_engine.predict_risk(t_high_risk, renewal_days=30)
        self.assertGreaterEqual(score, 70.0, "High risk telemetry should yield risk score >= 70")
        self.assertIn(level, [RiskLevel.CRITICAL, RiskLevel.HIGH])

        shap_values = ml_engine.calculate_shap_attributions(t_high_risk, renewal_days=30)
        self.assertGreater(len(shap_values), 5)
        top_shap = shap_values[0]
        self.assertGreater(top_shap.impact_score, 0, "Top risk driver should have positive impact score")

    def test_02_survival_analysis(self):
        """Test Weibull Survival Analysis and TTC curve."""
        curve_high, ttc_high = ml_engine.calculate_survival_curve(85.0)
        curve_low, ttc_low = ml_engine.calculate_survival_curve(15.0)

        self.assertLess(ttc_high, ttc_low, "High risk account should have significantly shorter TTC")
        self.assertEqual(curve_high[0].survival_probability, 1.0)
        self.assertLess(curve_high[-1].survival_probability, 0.40)

    def test_03_clustering_archetypes(self):
        """Test Dissatisfaction Driver clustering."""
        t_price = Telemetry(
            mrr=500.0,
            billing_cycle_failures=3,
            downgrade_clicks_30d=4,
            competitor_pricing_signals=True
        )
        cluster_p, conf_p = cluster_engine.classify_cluster(t_price, 65.0)
        self.assertEqual(cluster_p, DissatisfactionCluster.PRICE_SENSITIVE)

        t_adoption = Telemetry(
            mrr=5000.0,
            core_feature_utilization_pct=15.0,
            session_duration_decay_pct=50.0,
            unread_onboarding_emails=5
        )
        cluster_a, conf_a = cluster_engine.classify_cluster(t_adoption, 60.0)
        self.assertEqual(cluster_a, DissatisfactionCluster.ADOPTION_FRICTION)

    def test_04_nba_intervention_matrix(self):
        """Test Slide 6 Intervention Matrix rules."""
        accounts = feature_store.get_all_accounts()
        ent_acc = next(a for a in accounts if a.tier == AccountSegment.ENTERPRISE_VIP and a.id == "acc_ent_001")
        mid_acc = next(a for a in accounts if a.tier == AccountSegment.MID_MARKET and a.id == "acc_mid_001")
        plg_acc = next(a for a in accounts if a.tier == AccountSegment.PLG_SELF_SERVE and a.id == "acc_plg_001")
        sla_acc = next(a for a in accounts if a.id == "acc_mid_002")

        # Enterprise VIP should trigger CSM / Salesforce
        self.assertEqual(ent_acc.latest_prediction.next_best_action.channel, "RM / CSM Call")
        self.assertTrue(ent_acc.upsell_marketing_paused)

        # Mid-Market feature drop should trigger Pendo / In-App
        self.assertEqual(mid_acc.latest_prediction.next_best_action.channel, "In-App / Email")

        # PLG price sensitive should trigger Promo Code / SMS / Email
        self.assertEqual(plg_acc.latest_prediction.next_best_action.channel, "SMS / Email")
        self.assertIn("ANCHOR-SAVE15", str(plg_acc.latest_prediction.next_best_action.recommended_payload))

        # Universal consecutive negative tickets should trigger SLA Override
        self.assertEqual(sla_acc.latest_prediction.next_best_action.channel, "Priority Support")
        self.assertIsNotNone(sla_acc.sla_tier_override)

    def test_05_governance_modes(self):
        """Test Phased Deployment Modes (Heuristic vs Shadow vs Autonomous)."""
        # Shadow Mode
        governance_engine.set_mode(DeploymentMode.SHADOW_MODE)
        feature_store.recompute_all_predictions()
        acc = feature_store.get_account("acc_ent_001")
        self.assertEqual(acc.latest_prediction.next_best_action.status, "Suppressed (Shadow Mode)")

        # Autonomous Mode
        governance_engine.set_mode(DeploymentMode.AUTONOMOUS_MODE)
        feature_store.recompute_all_predictions()
        acc = feature_store.get_account("acc_ent_001")
        self.assertEqual(acc.latest_prediction.next_best_action.status, "Auto-Dispatched (Autonomous)")

    def test_06_closed_loop_feedback(self):
        """Test Closed-Loop learning and risk reduction."""
        acc = feature_store.get_account("acc_plg_001")
        initial_risk = acc.latest_prediction.risk_score
        
        updated_acc, delta = closed_loop_engine.apply_intervention_feedback(acc, "Accepted & Retained")
        self.assertGreater(delta, 10.0, "Risk score should drop significantly after retention acceptance")
        self.assertLess(updated_acc.latest_prediction.risk_score, initial_risk)


if __name__ == "__main__":
    unittest.main()
