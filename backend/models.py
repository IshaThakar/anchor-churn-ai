from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AccountSegment(str, Enum):
    ENTERPRISE_VIP = "Enterprise VIP"
    MID_MARKET = "Mid-Market"
    PLG_SELF_SERVE = "PLG / Self-Serve"


class RiskLevel(str, Enum):
    CRITICAL = "Critical"   # Risk >= 75
    HIGH = "High"           # Risk 50 - 74
    MEDIUM = "Medium"       # Risk 25 - 49
    LOW = "Low"             # Risk < 25


class DissatisfactionCluster(str, Enum):
    PRICE_SENSITIVE = "Price Sensitive"
    ADOPTION_FRICTION = "Adoption Friction"
    EXECUTIVE_DRIFT = "Executive Drift"
    API_DEGRADATION = "API Degradation"
    HEALTHY_STABLE = "Healthy & Stable"


class DeploymentMode(str, Enum):
    HEURISTIC_RULES = "Day 1-30: Heuristic Rules"
    SHADOW_MODE = "Day 30-60: V1 ML Shadow Mode"
    AUTONOMOUS_MODE = "Day 90+: Full Autonomous"


class DailyTelemetryPoint(BaseModel):
    day: int
    api_calls: int
    session_minutes: float
    core_feature_events: int
    active_users: int


class Telemetry(BaseModel):
    # Transactional
    mrr: float = Field(..., description="Monthly Recurring Revenue in USD")
    plan_tier: str = Field("Enterprise", description="Plan Tier")
    billing_frequency: str = Field("Annual", description="Annual or Monthly")
    billing_cycle_failures: int = Field(0, description="Recent payment or invoice failures")
    downgrade_clicks_30d: int = Field(0, description="Count of visits/clicks on cancel/downgrade pages")
    
    # Behavioral (60-90 day window)
    api_calls_30d_pct_change: float = Field(0.0, description="Percentage change in API volume over 30d (-100 to +100)")
    session_duration_decay_pct: float = Field(0.0, description="Percentage decay in average session length")
    core_feature_utilization_pct: float = Field(85.0, description="Percentage utilization of primary sticky feature (0-100)")
    login_recency_days: int = Field(1, description="Days since last user login")
    unread_onboarding_emails: int = Field(0, description="Unopened onboarding or product update emails")
    
    # Contextual
    executive_sponsor_active: bool = Field(True, description="Whether the original executive buyer/sponsor is still at company")
    consecutive_negative_tickets: int = Field(0, description="Consecutive Zendesk/support tickets with negative sentiment")
    recent_ticket_sentiment_score: float = Field(0.8, description="Sentiment score from -1.0 (very negative) to +1.0 (very positive)")
    competitor_pricing_signals: bool = Field(False, description="Whether user requested competitor parity or pricing match")
    
    # Historical 90-day curve
    historical_90d_decay: List[DailyTelemetryPoint] = Field(default_factory=list)


class ShapAttribution(BaseModel):
    feature_id: str
    feature_name: str
    impact_score: float       # Positive increases risk, negative decreases risk
    observed_value: Any
    baseline_value: Any
    direction: str            # 'risk_increase' or 'risk_decrease'
    explanation: str


class SurvivalPoint(BaseModel):
    day: int
    survival_probability: float  # 0.0 to 1.0
    hazard_rate: float


class NextBestAction(BaseModel):
    channel: str              # 'RM / CSM Call', 'In-App / Email', 'SMS / Email', 'Priority Support'
    action_title: str
    action_description: str
    recommended_payload: Dict[str, Any]
    target_destination: str    # 'Salesforce', 'Pendo', 'SendGrid', 'Twilio', 'Zendesk'
    auto_dispatched: bool
    status: str               # 'Pending', 'Dispatched', 'Suppressed (Shadow Mode)', 'Completed'
    suppression_reason: Optional[str] = None


class NLPSentimentAnalysis(BaseModel):
    sentiment_label: str       # 'Positive', 'Neutral', 'Frustrated', 'Severe Negative'
    sentiment_score: float     # -1.0 to 1.0
    consecutive_negative_count: int
    sla_tier_override_needed: bool
    ticket_snippets: List[str] = Field(default_factory=list)


class PredictionResult(BaseModel):
    risk_score: float          # 0.0 to 100.0
    risk_level: RiskLevel
    estimated_ttc_days: int    # Estimated Time-To-Churn in days
    cluster: DissatisfactionCluster
    cluster_confidence: float
    shap_attributions: List[ShapAttribution]
    survival_curve: List[SurvivalPoint]
    sentiment_analysis: NLPSentimentAnalysis
    next_best_action: NextBestAction
    generated_at: str


class InterventionRecord(BaseModel):
    id: str
    timestamp: str
    channel: str
    target_destination: str
    action_taken: str
    mode: DeploymentMode
    payload: Dict[str, Any]
    status: str
    outcome_status: str       # 'Pending Response', 'Accepted & Retained', 'Churn Mitigated', 'Ignored'
    post_intervention_risk_delta: float = 0.0


class Account(BaseModel):
    id: str
    name: str
    domain: str
    tier: AccountSegment
    mrr: float
    arr: float
    contract_renewal_days: int
    csm_assigned: str
    is_at_risk_flag: bool = False
    upsell_marketing_paused: bool = False
    sla_tier_override: Optional[str] = None
    telemetry: Telemetry
    latest_prediction: Optional[PredictionResult] = None
    intervention_history: List[InterventionRecord] = Field(default_factory=list)
    anonymized_token: str


class SimulationDecayRequest(BaseModel):
    account_id: str
    scenario_type: str  # 'api_drop_70', 'executive_departure', 'billing_failure_downgrade', 'consecutive_negative_tickets', 'core_feature_abandonment', 'intervention_success_rebound'


class GovernanceSettings(BaseModel):
    current_mode: DeploymentMode = DeploymentMode.AUTONOMOUS_MODE
    pii_masking_enabled: bool = False
    auto_dispatch_enabled: bool = True
    sla_override_enabled: bool = True
    shadow_mode_log_retention_days: int = 60


class OverviewMetrics(BaseModel):
    total_active_accounts: int
    total_arr_monitored: float
    total_arr_at_risk: float
    prevented_churn_arr: float
    avg_churn_risk_pct: float
    critical_risk_accounts: int
    high_risk_accounts: int
    medium_risk_accounts: int
    low_risk_accounts: int
    model_precision: float
    model_lift_pct: float
    cluster_breakdown: Dict[str, int]
    segment_breakdown: Dict[str, Dict[str, Any]]
    active_governance_mode: DeploymentMode
    recent_dispatches: List[InterventionRecord]
