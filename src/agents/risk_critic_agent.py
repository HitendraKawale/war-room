from __future__ import annotations

from src.agents.base import BaseAgent
from src.state import WarRoomState


class RiskCriticAgent(BaseAgent):
    name = "risk_critic"

    def run(self, state: WarRoomState) -> dict:
        metrics_report = state["tool_outputs"]["metrics_report"]
        guardrails_report = state["tool_outputs"]["guardrails_report"]
        feedback_report = state["tool_outputs"]["feedback_report"]

        primary_risks = []

        for trigger in guardrails_report["rollback_triggers"]:
            primary_risks.append(
                {
                    "risk": trigger["reason"],
                    "severity": "critical",
                    "likelihood": "high",
                    "evidence": [
                        f"{trigger['metric']} on {trigger['date']} observed={trigger['observed']} threshold={trigger['threshold']}"
                    ],
                    "why_it_matters": "A rollback-level guardrail indicates material customer or business harm.",
                    "blocking": True,
                }
            )

        for trigger in guardrails_report["pause_triggers"]:
            primary_risks.append(
                {
                    "risk": trigger["reason"],
                    "severity": "high",
                    "likelihood": "high",
                    "evidence": [
                        f"{trigger['metric']} on {trigger['date']} observed={trigger['observed']} threshold={trigger['threshold']}"
                    ],
                    "why_it_matters": "Pause-level guardrails indicate rollout risk is ahead of acceptable launch tolerance.",
                    "blocking": True,
                }
            )

        for trust_risk in feedback_report["trust_risks"]:
            primary_risks.append(
                {
                    "risk": trust_risk,
                    "severity": "medium",
                    "likelihood": "medium",
                    "evidence": feedback_report["repeated_issues"] or ["feedback themes"],
                    "why_it_matters": "Trust damage can persist longer than the incident itself.",
                    "blocking": False,
                }
            )

        contradictions_found = []
        if any(
            item["metric"] == "feature_adoption_pct" and item["trend"] == "improving"
            for item in metrics_report["per_metric"]
        ):
            contradictions_found.append(
                "Adoption is improving while checkout reliability is deteriorating; growth does not equal launch readiness."
            )

        unsupported_claims = [
            "A strong adoption curve alone is not enough evidence to continue rollout.",
            "A few positive user comments do not offset repeated payment and stability issues.",
        ]

        required_before_proceeding = [
            "Payment success rate must recover above pause threshold and remain stable.",
            "Crash rate and p95 latency must return toward pre-launch levels.",
            "Support volume should normalize and severe outlier complaints should be investigated.",
        ]

        stance = guardrails_report["recommended_decision_floor"]
        summary = (
            "The strongest case against continuing rollout is that the feature appears appealing, "
            "but its operational reliability is not yet trustworthy enough to scale further."
        )

        confidence = 0.85
        if stance == "PAUSE":
            confidence += 0.03
        if stance == "ROLL_BACK":
            confidence += 0.05

        return {
            "agent": self.name,
            "stance": stance,
            "summary": summary,
            "primary_risks": primary_risks,
            "contradictions_found": contradictions_found,
            "unsupported_claims": unsupported_claims,
            "required_before_proceeding": required_before_proceeding,
            "confidence": self.clamp_confidence(confidence),
        }
