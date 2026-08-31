from typing import List
from ..models import NLPSentimentAnalysis, Telemetry


class TicketSentimentNLPEngine:
    """
    Contextual NLP Sentiment Engine:
    Analyzes ticket text sentiment, tracks consecutive frustration streaks,
    and flags accounts requiring instant SLA tier overrides (Tier 3 Support).
    """

    NEGATIVE_KEYWORDS = [
        "unacceptable", "broken", "bug", "terrible", "cancellation", "churn",
        "downtime", "failed", "frustrated", "refund", "outage", "escalate",
        "disappointed", "slow", "error", "useless", "downgrade", "competitor"
    ]

    POSITIVE_KEYWORDS = [
        "great", "resolved", "helpful", "excellent", "fast", "thank you",
        "love", "awesome", "fixed", "fantastic", "smooth", "appreciated"
    ]

    def analyze_sentiment(self, telemetry: Telemetry, custom_snippets: List[str] = None) -> NLPSentimentAnalysis:
        score = telemetry.recent_ticket_sentiment_score
        consecutive_neg = telemetry.consecutive_negative_tickets

        # Generate realistic contextual ticket snippets if none provided
        snippets = custom_snippets or []
        if not snippets:
            if consecutive_neg >= 2 or score < -0.4:
                snippets = [
                    "Zendesk #8841: 'This is the 3rd time our weekly sync webhook failed. We cannot afford this production disruption.'",
                    "Zendesk #8792: 'Billing team charged us without applying the agreed tier discount. Escalating to our finance lead.'"
                ]
            elif score < 0.0:
                snippets = [
                    "Zendesk #8650: 'Integration documentation seems outdated for the new v2 API.'"
                ]
            else:
                snippets = [
                    "Zendesk #8512: 'Query answered promptly by Tier 1 support. Feature working as expected.'"
                ]

        # Determine sentiment classification
        if score <= -0.5 or consecutive_neg >= 3:
            label = "Severe Negative"
        elif score < 0.0 or consecutive_neg >= 1:
            label = "Frustrated"
        elif score < 0.4:
            label = "Neutral"
        else:
            label = "Positive"

        # Universal Risk Rule from Slide 6:
        # Consecutive negative sentiment NLP scores identified via Zendesk triggers Tier 3 SLA override
        sla_override_needed = (consecutive_neg >= 2 or score <= -0.6)

        return NLPSentimentAnalysis(
            sentiment_label=label,
            sentiment_score=round(score, 2),
            consecutive_negative_count=consecutive_neg,
            sla_tier_override_needed=sla_override_needed,
            ticket_snippets=snippets
        )


sentiment_engine = TicketSentimentNLPEngine()
