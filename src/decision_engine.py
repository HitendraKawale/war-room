from __future__ import annotations

from src.agents.base import BaseAgent
from src.state import WarRoomState


class PMAgent(BaseAgent):
    name = "pm"

    def run(self, state: WarRoomState) -> dict:
        metrics_report = state["tool_outputs"]["metrics_report"]
        guardrails_report = state["tool_outputs"]["guardrails_report"]
        feedback_report = state["tool_outputs"]["feedback_report"]

        metric_lookup = {item["metric"]: item for item in metrics_report["per_metric"]}

        adoption = metric_lookup["feature_adoption_pct"]
        dau = metric_lookup["dau"]
        conversion = metric_lookup["signup_conversion_pct"]
        retention = metric_lookup["d1_retention_pct"]
        payment = metric_lookup["payment_success_pct"]
        crash = metric_lookup["crash_rate_pct"]

        positive_signals = []
        negative_signals = []

        if adoption["trend"] == "improving":
            positive_signals.append("Feature adoption is climbing post-launch.")
        if dau["trend"] == "improving":
            positive_signals.append("DAU increased during rollout.")
        if conversion["status"] == "green":
            positive_signals.append("Signup conversion remains healthy or improved.")

        if payment["status"] in {"yellow", "red"}:
            negative_signals.append("Payment reliability degraded during rollout.")
        if crash["status"] in {"yellow", "red"}:
            negative_signals.append("Crash rate worsened after launch.")
        if retention["status"] in {"yellow", "red"}:
            negative_signals.append("Early retention softened, suggesting launch friction.")
        if feedback_report["repeated_issues"]:
            negative_signals.append(
                "Repeated user complaints were detected: "
                + ", ".join(feedback_report["repeated_issues"])
                + "."
            )

        floor = guardrails_report["recommended_decision_floor"]
        stance = floor if floor in {"PAUSE", "ROLL_BACK"} else "PROCEED"

        customer_impact = {
            "value_delivered": (
                "Users appear to like recommendations and easier discovery, and feature adoption is rising."
            ),
            "harm_or_friction": (
                "Checkout reliability issues are undermining the value of the new flow."
            ),
            "blast_radius": "moderate"
            if stance == "PAUSE"
            else "broad"
            if stance == "ROLL_BACK"
            else "localized",
        }

        recommended_actions = [
            "Hold rollout expansion until reliability metrics return inside acceptable guardrails.",
            "Prioritize fixes in payment confirmation, crash stability, and slow checkout rendering.",
            "Re-evaluate launch readiness after 24 hours of stabilized metrics.",
        ]

        open_questions = [
            "Are failures concentrated on specific devices, OS versions, or traffic cohorts?",
            "Can recommendation calls be degraded gracefully without breaking checkout?",
            "Is payment failure driven by UI state, backend latency, or confirmation polling?",
        ]

        key_product_signals = [
            {
                "signal": "Feature adoption increased after launch",
                "direction": "positive",
                "evidence": [f"latest_adoption={adoption['latest_value']}"],
            },
            {
                "signal": "User reach and usage expanded during rollout",
                "direction": "positive",
                "evidence": [f"latest_dau={dau['latest_value']}"],
            },
            {
                "signal": "Core checkout reliability degraded",
                "direction": "negative",
                "evidence": [
                    f"payment_status={payment['status']}",
                    f"crash_status={crash['status']}",
                ],
            },
        ]

        summary = (
            "The launch is delivering visible product value through adoption and usage growth, "
            "but that value is currently offset by reliability and payment friction in the core checkout journey."
        )

        confidence = 0.74
        if stance == "PAUSE":
            confidence += 0.04
        if (
            feedback_report["sentiment_counts"]["negative"]
            > feedback_report["sentiment_counts"]["positive"]
        ):
            confidence += 0.03

        return {
            "agent": self.name,
            "stance": stance,
            "summary": summary,
            "key_product_signals": key_product_signals,
            "customer_impact_assessment": customer_impact,
            "positive_signals": positive_signals,
            "negative_signals": negative_signals,
            "recommended_actions": recommended_actions,
            "open_questions": open_questions,
            "confidence": self.clamp_confidence(confidence),
        }
