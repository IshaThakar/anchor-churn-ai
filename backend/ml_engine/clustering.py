from typing import Tuple
from ..models import Telemetry, DissatisfactionCluster


class DissatisfactionClusterEngine:
    """
    Categorizes at-risk accounts into actionable root-cause clusters:
    - Price Sensitive: Billing failures, downgrade intent, pricing friction.
    - Adoption Friction: Feature abandonment, low onboarding completion, session decay.
    - Executive Drift: Key executive stakeholder departure, organizational shift.
    - API Degradation: API volume drop, technical integration decay.
    - Healthy & Stable: Normal telemetry.
    """

    def classify_cluster(self, telemetry: Telemetry, risk_score: float) -> Tuple[DissatisfactionCluster, float]:
        if risk_score < 30.0 and telemetry.executive_sponsor_active and telemetry.billing_cycle_failures == 0:
            return DissatisfactionCluster.HEALTHY_STABLE, 0.95

        # Calculate affinity weights for each driver archetype
        price_affinity = (
            (telemetry.billing_cycle_failures * 35.0)
            + (telemetry.downgrade_clicks_30d * 40.0)
            + (25.0 if telemetry.competitor_pricing_signals else 0.0)
        )

        adoption_affinity = (
            max(0.0, (70.0 - telemetry.core_feature_utilization_pct) * 1.2)
            + (telemetry.session_duration_decay_pct * 0.8)
            + (telemetry.unread_onboarding_emails * 5.0)
            + (telemetry.login_recency_days * 3.0)
        )

        exec_affinity = (
            (100.0 if not telemetry.executive_sponsor_active else 0.0)
            + (telemetry.login_recency_days * 2.0)
        )

        api_affinity = (
            max(0.0, -telemetry.api_calls_30d_pct_change * 1.5)
            + (20.0 if telemetry.api_calls_30d_pct_change < -30.0 else 0.0)
        )

        scores = {
            DissatisfactionCluster.EXECUTIVE_DRIFT: exec_affinity,
            DissatisfactionCluster.PRICE_SENSITIVE: price_affinity,
            DissatisfactionCluster.API_DEGRADATION: api_affinity,
            DissatisfactionCluster.ADOPTION_FRICTION: adoption_affinity,
        }

        # Select highest affinity driver
        sorted_clusters = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_cluster, top_score = sorted_clusters[0]

        if top_score < 15.0:
            return DissatisfactionCluster.HEALTHY_STABLE, 0.80

        total_score = sum(scores.values()) or 1.0
        confidence = round(min(0.99, max(0.55, top_score / total_score)), 2)

        return top_cluster, confidence


cluster_engine = DissatisfactionClusterEngine()
