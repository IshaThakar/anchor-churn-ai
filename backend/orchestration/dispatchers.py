import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from ..models import InterventionRecord, DeploymentMode


class OmnichannelDispatcher:
    """
    Omnichannel Dispatcher for Anchor:
    Communicates with external systems of record:
    - Salesforce: Task generation, CSM alerts, upsell pausing
    - Pendo: In-App guided tour triggers
    - SendGrid: Hyper-personalized dynamic retention/drip emails
    - Twilio: SMS retention alerts
    - Zendesk: Priority Tier 3 SLA routing overrides
    """

    def __init__(self):
        self.dispatch_log = []

    def dispatch(
        self,
        account_id: str,
        account_name: str,
        channel: str,
        target_destination: str,
        action_title: str,
        payload: Dict[str, Any],
        mode: DeploymentMode
    ) -> InterventionRecord:
        record_id = f"disp_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Check if Shadow Mode suppresses the outward dispatch
        is_shadow_mode = (mode == DeploymentMode.SHADOW_MODE)
        
        status = "Suppressed (Shadow Mode Logged)" if is_shadow_mode else "Dispatched & Active"

        record = InterventionRecord(
            id=record_id,
            timestamp=timestamp,
            channel=channel,
            target_destination=target_destination,
            action_taken=action_title,
            mode=mode,
            payload=payload,
            status=status,
            outcome_status="Pending Response" if not is_shadow_mode else "Shadow Recorded",
            post_intervention_risk_delta=0.0
        )

        self.dispatch_log.insert(0, record)
        return record

    def get_recent_dispatches(self, limit: int = 20):
        return self.dispatch_log[:limit]


dispatcher = OmnichannelDispatcher()
