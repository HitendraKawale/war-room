from __future__ import annotations

from src.agents.coordinator_agent import CoordinatorAgent
from src.agents.data_analyst_agent import DataAnalystAgent
from src.agents.marketing_agent import MarketingAgent
from src.agents.pm_agent import PMAgent
from src.agents.risk_critic_agent import RiskCriticAgent
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

        agents = [
            PMAgent(),
            DataAnalystAgent(),
            MarketingAgent(),
            RiskCriticAgent(),
        ]

        for agent in agents:
            trace.append(
                trace_event(
                    step=agent.name,
                    event_type="start",
                    summary=f"Running {agent.name} analysis.",
                )
            )
            output = agent.run(state)
            state["agent_outputs"][agent.name] = output
            trace.append(
                trace_event(
                    step=agent.name,
                    event_type="end",
                    summary=f"{agent.name} completed with stance={output['stance']}.",
                )
            )

        coordinator = CoordinatorAgent()
        trace.append(
            trace_event(
                step=coordinator.name,
                event_type="start",
                summary="Running coordinator synthesis.",
            )
        )
        coordinator_output = coordinator.run(state)
        state["agent_outputs"][coordinator.name] = coordinator_output
        trace.append(
            trace_event(
                step=coordinator.name,
                event_type="end",
                summary=f"Coordinator produced draft decision={coordinator_output['draft_decision']}.",
            )
        )

        state["final_output"] = {
            "status": "agents_complete_decision_engine_pending",
            "message": "Cross-functional agents completed successfully.",
            "draft_decision": coordinator_output["draft_decision"],
            "coordinator_confidence": coordinator_output["confidence"],
            "agent_stances": {
                name: output["stance"]
                for name, output in state["agent_outputs"].items()
                if "stance" in output
            },
            "rationale": coordinator_output["rationale"],
            "dissent": coordinator_output["dissent"],
        }

        trace.append(
            trace_event(
                step="orchestrator",
                event_type="end",
                summary="Agent layer run completed successfully.",
            )
        )
        return state

