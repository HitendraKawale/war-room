from __future__ import annotations

from src.agents.base import BaseAgent
from src.state import WarRoomState


class MarketingAgent(BaseAgent):
    name = "marketing_comms"

    def run(self, state: WarRoomState) -> dict:
        feedback_report = state["tool_outputs"]["feedback_report"]
        guardrails_report = state["tool_outputs"]["guardrails_report"]

        sentiment_counts = feedback_report["sentiment_counts"]
        repeated_issues = feedback_report["repeated_issues"]
        outliers = feedback_report["outliers"]

        stance = "PROCEED"
        if guardrails_report["recommended_decision_floor"] == "ROLL_BACK":
            stance = "ROLL_BACK"
        elif repeated_issues or sentiment_counts["negative"] > sentiment_counts["positive"]:
            stance = "PAUSE"

        communication_recommendations = [
            {
                "audience": "internal",
                "message_goal": "Align product, engineering, support, and leadership on current launch status and next 24-hour priorities.",
                "urgency": "high",
            },
            {
                "audience": "support",
                "message_goal": "Provide agents with known issue language, workaround guidance, and escalation rules.",
                "urgency": "high",
            },
        ]

        if stance in {"PAUSE", "ROLL_BACK"}:
            communication_recommendations.append(
                {
                    "audience": "customers",
                    "message_goal": "Acknowledge intermittent checkout issues for affected users and set expectation for updates.",
                    "urgency": "medium",
                }
            )

        if outliers:
            communication_recommendations.append(
                {
                    "audience": "executives",
                    "message_goal": "Highlight severe complaints and explain whether they are corroborated or isolated.",
                    "urgency": "medium",
                }
            )

        summary = (
            "Customer perception is mixed: users like the new recommendations and streamlined design, "
            "but repeated complaints about slowness, freezing, and payment reliability are creating trust risk."
        )

        confidence = 0.76
        if repeated_issues:
            confidence += 0.04
        if outliers:
            confidence -= 0.03

        return {
            "agent": self.name,
            "stance": stance,
            "summary": summary,
            "sentiment_breakdown": sentiment_counts,
            "top_themes": feedback_report["top_themes"],
            "outliers": outliers,
            "trust_risks": feedback_report["trust_risks"],
            "communication_recommendations": communication_recommendations,
            "confidence": self.clamp_confidence(confidence),
        }
