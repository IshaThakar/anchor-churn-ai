import hashlib
from typing import Dict, Any
from ..models import GovernanceSettings, DeploymentMode, Account


class GovernanceEngine:
    """
    Implementation & Governance Strategy (Slide 5):
    - Phased Deployment Matrix Management (Day 1-30 Heuristic, Day 30-60 Shadow, Day 90+ Autonomous)
    - PII Tokenization & Anonymization Layer for GDPR/CCPA Compliance
    """

    def __init__(self):
        self.settings = GovernanceSettings()

    def set_mode(self, mode: DeploymentMode) -> GovernanceSettings:
        self.settings.current_mode = mode
        return self.settings

    def toggle_pii_masking(self, enabled: bool) -> GovernanceSettings:
        self.settings.pii_masking_enabled = enabled
        return self.settings

    def get_settings(self) -> GovernanceSettings:
        return self.settings

    @staticmethod
    def generate_token(value: str) -> str:
        """Generates anonymized SHA-256 token."""
        return "tok_" + hashlib.sha256(value.encode()).hexdigest()[:12]

    def anonymize_account(self, account: Account) -> Dict[str, Any]:
        """Returns PII-masked view if PII masking is enabled."""
        acc_dict = account.dict()
        if self.settings.pii_masking_enabled:
            acc_dict["name"] = f"Account #{account.anonymized_token[:8]}"
            acc_dict["domain"] = f"org_{account.anonymized_token[:6]}.internal"
            acc_dict["csm_assigned"] = "CSM-Agent-ID"
        return acc_dict


governance_engine = GovernanceEngine()
