from __future__ import annotations

from src.agents.coordinator_agent import CoordinatorAgent
from src.agents.data_analyst_agent import DataAnalystAgent
from src.agents.marketing_agent import MarketingAgent
from src.agents.pm_agent import PMAgent
from src.agents.risk_critic_agent import RiskCriticAgent
from src.decision_engine import build_final_decision
from src.state import WarRoomState
from src.tools.feedback_tools import analyze_feedback
from src.tools.metrics_tools import analyze_metric_trends, evaluate_guardrails
from src.tracing import TraceRecorder, new_run_id


class WarRoomOrchestrator:
    def run(self, state: WarRoomState) -> WarRoomState:
        run_id = state.get("run_id") or new_run_id()
        state["run_id"] = run_id

        recorder = TraceRecorder(run_id=run_id, trace=state.setdefault("trace", []))
        recorder.add(
            step="orchestrator",
            event_type="start",
            summary="Initialized war room run with loaded dashboard inputs.",
        )

        metrics = state["metrics"]
        feedback = state["feedback"]
        thresholds = state["thresholds"]

        with recorder.span(
            "metrics_tools",
            "Running metric trend analysis.",
            "Metric trend analysis completed.",
        ):
            metrics_report = analyze_metric_trends(
                metrics=metrics,
                metric_direction=thresholds["metric_direction"],
                launch_date=thresholds["launch"]["launch_date"],
            )

        recorder.add(
            step="metrics_tools",
            event_type="info",
            summary="Metric health summary recorded.",
            overall_health=metrics_report["overall_health"],
            red_metrics=metrics_report["status_counts"]["red"],
            yellow_metrics=metrics_report["status_counts"]["yellow"],
        )

        with recorder.span(
            "guardrail_tools",
            "Evaluating launch guardrails.",
            "Guardrail evaluation completed.",
        ):
            guardrails_report = evaluate_guardrails(metrics=metrics, thresholds=thresholds)

        recorder.add(
            step="guardrail_tools",
            event_type="info",
            summary="Guardrail decision floor recorded.",
            recommended_decision_floor=guardrails_report["recommended_decision_floor"],
            pause_trigger_count=len(guardrails_report["pause_triggers"]),
            rollback_trigger_count=len(guardrails_report["rollback_triggers"]),
        )

        with recorder.span(
            "feedback_tools",
            "Running feedback sentiment and theme analysis.",
            "Feedback analysis completed.",
        ):
            feedback_report = analyze_feedback(feedback)

        recorder.add(
            step="feedback_tools",
            event_type="info",
            summary="Feedback summary recorded.",
            negative_feedback=feedback_report["sentiment_counts"]["negative"],
            repeated_issue_count=len(feedback_report["repeated_issues"]),
            outlier_count=len(feedback_report["outliers"]),
        )

        state["tool_outputs"] = {
            "metrics_report": metrics_report,
            "guardrails_report": guardrails_report,
            "feedback_report": feedback_report,
        }

        state["agent_outputs"] = {}

        agents = [
            PMAgent(),
            DataAnalystAgent(),
            MarketingAgent(),
            RiskCriticAgent(),
        ]

        for agent in agents:
            with recorder.span(
                agent.name,
                f"Running {agent.name} analysis.",
                f"{agent.name} analysis completed.",
            ):
                output = agent.run(state)
                state["agent_outputs"][agent.name] = output

            recorder.add(
                step=agent.name,
                event_type="info",
                summary=f"{agent.name} stance recorded.",
                stance=output["stance"],
                confidence=output["confidence"],
            )

        coordinator = CoordinatorAgent()
        with recorder.span(
            coordinator.name,
            "Running coordinator synthesis.",
            "Coordinator synthesis completed.",
        ):
            coordinator_output = coordinator.run(state)
            state["agent_outputs"][coordinator.name] = coordinator_output

        recorder.add(
            step=coordinator.name,
            event_type="info",
            summary="Coordinator draft decision recorded.",
            draft_decision=coordinator_output["draft_decision"],
            confidence=coordinator_output["confidence"],
        )

        with recorder.span(
            "decision_engine",
            "Building final structured launch decision.",
            "Final structured decision completed.",
        ):
            final_output = build_final_decision(
                tool_outputs=state["tool_outputs"],
                agent_outputs=state["agent_outputs"],
            )
            state["final_output"] = final_output

        recorder.add(
            step="decision_engine",
            event_type="info",
            summary="Final decision recorded.",
            decision=final_output["decision"],
            confidence=final_output["confidence"],
            risk_count=len(final_output["risk_register"]),
            action_count=len(final_output["action_plan_24_48h"]),
        )

        recorder.add(
            step="orchestrator",
            event_type="end",
            summary="End-to-end war room run completed successfully.",
        )
        return state

