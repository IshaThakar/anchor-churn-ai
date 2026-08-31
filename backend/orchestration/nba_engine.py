import uuid
from typing import Tuple, Dict, Any, List
from ..models import (
    Account,
    AccountSegment,
    NextBestAction,
    DeploymentMode,
    DissatisfactionCluster,
    ShapAttribution,
    NLPSentimentAnalysis
)
from .dispatchers import dispatcher


class NextBestActionEngine:
    """
    Dynamic Intervention & Outreach Routing Engine (Slide 6 & Slide 5):
    Maps predictive ML signals & root causes to omnichannel Next-Best-Actions.
    """

    def evaluate_and_route(
        self,
        account: Account,
        risk_score: float,
        cluster: DissatisfactionCluster,
        shap_values: List[ShapAttribution],
        sentiment_analysis: NLPSentimentAnalysis,
        current_mode: DeploymentMode
    ) -> Tuple[NextBestAction, Account]:
        """
        Determines the Next-Best-Action based on Customer Segment, ML Predictive Triggers,
        and current Phased Deployment Mode.
        """
        t = account.telemetry

        # 1. Check UNIVERSAL RULE (All Tiers): Consecutive negative sentiment NLP scores
        if sentiment_analysis.consecutive_negative_count >= 2 or sentiment_analysis.sla_tier_override_needed:
            nba = self._build_universal_support_nba(account, sentiment_analysis)
            account.sla_tier_override = "Tier 3 Priority Support (Instant Override)"
            account.is_at_risk_flag = True

        # 2. Check ENTERPRISE VIP RULE: Severe API drop + executive sponsor departure
        elif account.tier == AccountSegment.ENTERPRISE_VIP and (
            not t.executive_sponsor_active or t.api_calls_30d_pct_change <= -35.0 or risk_score >= 60.0
        ):
            nba = self._build_enterprise_vip_nba(account, shap_values)
            account.upsell_marketing_paused = True
            account.is_at_risk_flag = True

        # 3. Check MID-MARKET RULE: Core feature abandonment
        elif account.tier == AccountSegment.MID_MARKET and (
            t.core_feature_utilization_pct < 40.0 or cluster == DissatisfactionCluster.ADOPTION_FRICTION or risk_score >= 50.0
        ):
            nba = self._build_mid_market_nba(account)
            account.is_at_risk_flag = True

        # 4. Check PLG / SELF-SERVE RULE: Price Sensitive after billing failure or downgrade click
        elif account.tier == AccountSegment.PLG_SELF_SERVE and (
            cluster == DissatisfactionCluster.PRICE_SENSITIVE or t.billing_cycle_failures > 0 or t.downgrade_clicks_30d > 0 or risk_score >= 45.0
        ):
            nba = self._build_plg_nba(account)
            account.is_at_risk_flag = True

        # 5. Fallback or Low Risk
        else:
            nba = NextBestAction(
                channel="Automated Monitoring",
                action_title="Standard Account Health Monitoring",
                action_description="Telemetry is within nominal bounds. No immediate intervention required.",
                recommended_payload={"status": "nominal", "retention_score": round(100.0 - risk_score, 1)},
                target_destination="Internal Telemetry",
                auto_dispatched=False,
                status="Healthy"
            )
            account.is_at_risk_flag = False

        # Apply Phased Deployment Mode Logic (Slide 5)
        if current_mode == DeploymentMode.SHADOW_MODE:
            nba.status = "Suppressed (Shadow Mode)"
            nba.suppression_reason = "V1 ML model running in shadow mode (Day 30-60). Predictions validated without triggering outward actions."
            nba.auto_dispatched = False
        elif current_mode == DeploymentMode.HEURISTIC_RULES:
            nba.action_title = f"[Heuristic] {nba.action_title}"
            nba.status = "Dispatched (Rule-Based)"
            nba.auto_dispatched = True
        else:  # AUTONOMOUS_MODE (Day 90+)
            nba.status = "Auto-Dispatched (Autonomous)"
            nba.auto_dispatched = True

        return nba, account

    def _build_enterprise_vip_nba(self, account: Account, shap_values: List[ShapAttribution]) -> NextBestAction:
        """Enterprise VIP: RM / CSM Call + Salesforce Task + Pause Upsell + Route SHAP."""
        top_reasons = [f"{s.feature_name} ({'+' if s.impact_score > 0 else ''}{s.impact_score})" for s in shap_values[:3]]
        
        payload = {
            "salesforce_task": {
                "priority": "HIGH_P0",
                "assigned_to": account.csm_assigned,
                "due_date": "Within 4 Hours",
                "subject": f"URGENT: Executive Sponsor Drift & API Decay at {account.name}",
                "account_arr": f"${account.arr:,.0f}",
                "shap_root_causes": top_reasons,
                "recommended_talking_points": [
                    "Acknowledge leadership change / new stakeholder alignment.",
                    "Review recent API integration telemetry and offer direct solutions engineering pairing.",
                    "Confirm contract value proposition prior to upcoming renewal cycle."
                ]
            },
            "marketing_automation": {
                "action": "PAUSE_ALL_UPSELL_CAMPAIGNS",
                "reason": "Account flagged in Retention Emergency state."
            }
        }

        return NextBestAction(
            channel="RM / CSM Call",
            action_title=f"High-Priority Salesforce Task & CSM Briefing for {account.name}",
            action_description="Auto-generates P0 Salesforce task, routes SHAP explainability insights to CSM dashboard, and pauses automated upsell marketing until account health stabilizes.",
            recommended_payload=payload,
            target_destination="Salesforce CRM + CSM Dashboard",
            auto_dispatched=True,
            status="Ready to Dispatch"
        )

    def _build_mid_market_nba(self, account: Account) -> NextBestAction:
        """Mid-Market: Pendo Guided Tour Overlay + Targeted Drip Email."""
        payload = {
            "pendo_guide": {
                "guide_id": "guide_core_feature_adoption_v2",
                "target_role": "Workspace Admins & Power Users",
                "trigger_type": "Contextual UI Overlay on Next Login",
                "tour_steps": 3,
                "goal": "Re-engage user on Sticky Workflow automation"
            },
            "sendgrid_drip": {
                "template_id": "drip_value_realization_series",
                "sequence": [
                    {"day": 0, "subject": "Unlocking 3x faster workflows with our core tools"},
                    {"day": 3, "subject": "How leading teams in your industry automate reporting"},
                    {"day": 7, "subject": "Quick 15-min strategy session with our product specialist"}
                ]
            }
        }

        return NextBestAction(
            channel="In-App / Email",
            action_title="Pendo Contextual Guided-Tour Overlay & Targeted Value Drip",
            action_description="Triggers a contextual guided-tour UI overlay via Pendo and initiates a personalized 3-part email campaign focused strictly on value realization for the abandoned core feature.",
            recommended_payload=payload,
            target_destination="Pendo In-App + SendGrid",
            auto_dispatched=True,
            status="Ready to Dispatch"
        )

    def _build_plg_nba(self, account: Account) -> NextBestAction:
        """PLG / Self-Serve: Dynamic 15% Discount Code (48h) + Downgrade to Free Tier prompt."""
        promo_code = f"ANCHOR-SAVE15-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "discount_injection": {
                "promo_code": promo_code,
                "discount_percentage": 15,
                "validity_window": "48 Hours",
                "dynamic_link": f"https://app.{account.domain}/billing/redeem?code={promo_code}"
            },
            "safety_net_prompt": {
                "action": "OFFER_FRICTIONLESS_FREE_TIER_DOWNGRADE",
                "message": "Prefer to pause? Keep your projects safe on our Free Tier instead of losing your workflow configuration."
            },
            "delivery_channels": ["Twilio SMS (if enabled)", "SendGrid Instant Email"]
        }

        return NextBestAction(
            channel="SMS / Email",
            action_title="Dynamic 15% Retention Promo Code & Free-Tier Safety Net",
            action_description="Injects a dynamic, single-use 15% discount code valid for 48 hours and prompts a frictionless 'downgrade to free tier' option as a safety net over hard cancellation.",
            recommended_payload=payload,
            target_destination="SendGrid + Twilio SMS",
            auto_dispatched=True,
            status="Ready to Dispatch"
        )

    def _build_universal_support_nba(self, account: Account, sentiment_analysis: NLPSentimentAnalysis) -> NextBestAction:
        """All Tiers: Priority Support Tier 3 SLA Override + Global 'At-Risk' Flag."""
        payload = {
            "zendesk_sla_override": {
                "action": "ROUTE_TO_TIER_3_ESCALATIONS",
                "new_sla_response_time": "15 Minutes (Down from 4 Hours)",
                "sentiment_trigger": f"{sentiment_analysis.consecutive_negative_count} Consecutive Negative NLP interactions",
                "ticket_excerpts": sentiment_analysis.ticket_snippets
            },
            "global_gtm_flag": {
                "status": "AT_RISK_CUSTOMER_EMERGENCY",
                "broadcast_targets": ["Slack #cs-escalations", "Salesforce Account Banner", "HubSpot Deal Stage"]
            }
        }

        return NextBestAction(
            channel="Priority Support",
            action_title="Instant Tier-3 Support SLA Override & Global 'At-Risk' Escalation",
            action_description="Temporarily overrides standard SLA routing to push open tickets directly to Tier 3 senior engineers; flags the account as 'At-Risk' globally across all Go-To-Market systems.",
            recommended_payload=payload,
            target_destination="Zendesk + Slack Escalations",
            auto_dispatched=True,
            status="Ready to Dispatch"
        )


nba_engine = NextBestActionEngine()
