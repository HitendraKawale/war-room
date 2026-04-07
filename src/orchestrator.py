from __future__ import annotations

from src.state import WarRoomState
from src.tools.feedback_tools import analyze_feedback
from src.tools.metrics_tools import analyze_metric_trends, evaluate_guardrails
from src.tracing import trace_event


class WarRoomOrchestrator:
    def run(self, state: WarRoomState) -> WarRoomState:
        trace = state.setdefault("trace", [])
        trace.append(
            trace_event(
                step="orchestrator",
                event_type="start",
                summary="Initialized war room run with loaded dashboard inputs.",
            )
        )

        metrics = state["metrics"]
        feedback = state["feedback"]
        thresholds = state["thresholds"]

        trace.append(
            trace_event(
                step="metrics_tools",
                event_type="start",
                summary="Running metric trend analysis.",
            )
        )
        metrics_report = analyze_metric_trends(
            metrics=metrics,
            metric_direction=thresholds["metric_direction"],
            launch_date=thresholds["launch"]["launch_date"],
        )
        trace.append(
            trace_event(
                step="metrics_tools",
                event_type="end",
                summary=f"Metric trend analysis completed with overall health={metrics_report['overall_health']}.",
            )
        )

        trace.append(
            trace_event(
                step="guardrail_tools",
                event_type="start",
                summary="Evaluating launch guardrails.",
            )
        )
        guardrails_report = evaluate_guardrails(metrics=metrics, thresholds=thresholds)
        trace.append(
            trace_event(
                step="guardrail_tools",
                event_type="end",
                summary=(
                    "Guardrail evaluation completed with "
                    f"decision floor={guardrails_report['recommended_decision_floor']}."
                ),
            )
        )

        trace.append(
            trace_event(
                step="feedback_tools",
                event_type="start",
                summary="Running feedback sentiment and theme analysis.",
            )
        )
        feedback_report = analyze_feedback(feedback)
        trace.append(
            trace_event(
                step="feedback_tools",
                event_type="end",
                summary=(
                    "Feedback analysis completed with "
                    f"{feedback_report['sentiment_counts']['negative']} negative entries."
                ),
            )
        )

        state["tool_outputs"] = {
            "metrics_report": metrics_report,
            "guardrails_report": guardrails_report,
            "feedback_report": feedback_report,
        }
        state["agent_outputs"] = {}
        state["final_output"] = {
            "status": "tools_complete_agents_pending",
            "message": "Deterministic tool layer completed successfully.",
            "metrics_overall_health": metrics_report["overall_health"],
            "recommended_decision_floor": guardrails_report["recommended_decision_floor"],
            "negative_feedback_count": feedback_report["sentiment_counts"]["negative"],
            "repeated_issues": feedback_report["repeated_issues"],
        }

        trace.append(
            trace_event(
                step="orchestrator",
                event_type="end",
                summary="Tool layer run completed successfully.",
            )
        )
        return state

