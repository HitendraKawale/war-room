from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.state import WarRoomState


class DataAnalystAgent(BaseAgent):
    name = "data_analyst"

    KEY_METRICS = {
        "signup_conversion_pct",
        "dau",
        "d1_retention_pct",
        "crash_rate_pct",
        "p95_latency_ms",
        "payment_success_pct",
        "support_tickets",
        "feature_adoption_pct",
        "churn_pct",
    }

    def run(self, state: WarRoomState) -> dict[str, Any]:
        metrics_report = state["tool_outputs"]["metrics_report"]
        guardrails_report = state["tool_outputs"]["guardrails_report"]

        metric_findings = []
        blocking_metrics = []

        for item in metrics_report["per_metric"]:
            if item["metric"] not in self.KEY_METRICS:
                continue

            finding = {
                "metric": item["metric"],
                "status": item["status"],
                "trend": item["trend"],
                "baseline_value": item["baseline_mean"],
                "current_value": item["latest_value"],
                "delta_pct": item["delta_pct_vs_baseline"],
                "threshold_breached": item["metric"]
                in {
                    trigger["metric"]
                    for trigger in (
                        guardrails_report["pause_triggers"] + guardrails_report["rollback_triggers"]
                    )
                },
                "evidence": item["evidence"],
            }
            metric_findings.append(finding)

            if finding["status"] == "red" or finding["threshold_breached"]:
                blocking_metrics.append(item["metric"])

        floor = guardrails_report["recommended_decision_floor"]
        stance = floor

        summary_parts = [
            f"Overall metric health is {metrics_report['overall_health']}.",
            f"Decision floor from guardrails is {floor}.",
        ]

        if blocking_metrics:
            summary_parts.append(
                "Primary blocking metrics: " + ", ".join(sorted(set(blocking_metrics))) + "."
            )

        recommended_actions = []
        if "payment_success_pct" in blocking_metrics:
            recommended_actions.append(
                "Investigate checkout and payment confirmation flow immediately."
            )
        if "crash_rate_pct" in blocking_metrics or "p95_latency_ms" in blocking_metrics:
            recommended_actions.append(
                "Stabilize client and backend performance before expanding rollout."
            )
        if "support_tickets" in blocking_metrics:
            recommended_actions.append(
                "Prepare support team with workaround guidance and known issue scripts."
            )

        confidence = 0.82
        if floor == "ROLL_BACK":
            confidence += 0.05
        if metrics_report["overall_health"] == "mixed":
            confidence -= 0.05

        return {
            "agent": self.name,
            "stance": stance,
            "summary": " ".join(summary_parts),
            "metric_findings": metric_findings,
            "blocking_metrics": sorted(set(blocking_metrics)),
            "recommended_actions": recommended_actions,
            "confidence": self.clamp_confidence(confidence),
        }
