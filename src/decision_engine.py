from __future__ import annotations

from collections import Counter
from typing import Any

from src.models import ActionItem, FinalDecision, RiskItem


DECISION_RANK = {
    "PROCEED": 0,
    "PAUSE": 1,
    "ROLL_BACK": 2,
}


def _max_decision(a: str, b: str) -> str:
    return a if DECISION_RANK[a] >= DECISION_RANK[b] else b


def _latest_metric_lookup(tool_outputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["metric"]: item for item in tool_outputs["metrics_report"]["per_metric"]}


def compute_confidence(
    tool_outputs: dict[str, Any],
    agent_outputs: dict[str, Any],
    final_decision: str,
) -> float:
    metrics_report = tool_outputs["metrics_report"]
    feedback_report = tool_outputs["feedback_report"]
    guardrails_report = tool_outputs["guardrails_report"]

    agent_confidences = [
        output["confidence"]
        for name, output in agent_outputs.items()
        if name != "coordinator" and "confidence" in output
    ]
    avg_agent_conf = sum(agent_confidences) / len(agent_confidences)

    stance_values = [
        output["stance"]
        for name, output in agent_outputs.items()
        if name != "coordinator" and "stance" in output
    ]
    disagreement_penalty = 0.05 if len(set(stance_values)) > 1 else 0.0

    evidence_bonus = 0.0
    if metrics_report["status_counts"]["red"] >= 1:
        evidence_bonus += 0.03
    if feedback_report["repeated_issues"]:
        evidence_bonus += 0.03
    if final_decision == guardrails_report["recommended_decision_floor"]:
        evidence_bonus += 0.03
    if len(guardrails_report["rollback_triggers"]) > 0:
        evidence_bonus += 0.02
    elif len(guardrails_report["pause_triggers"]) > 0:
        evidence_bonus += 0.02

    confidence = avg_agent_conf - disagreement_penalty + evidence_bonus

    # Cap confidence lower so mixed-signal launch decisions do not look overconfident
    return round(max(0.05, min(0.90, confidence)), 2)


def build_rationale(
    tool_outputs: dict[str, Any],
    agent_outputs: dict[str, Any],
    final_decision: str,
) -> list[str]:
    feedback_report = tool_outputs["feedback_report"]
    guardrails_report = tool_outputs["guardrails_report"]

    metric_lookup = _latest_metric_lookup(tool_outputs)

    rationale = [
        f"Final decision is {final_decision} based on quantitative guardrails, repeated feedback patterns, and cross-functional agent review.",
        f"Guardrail decision floor was {guardrails_report['recommended_decision_floor']}.",
    ]

    for metric_name in [
        "payment_success_pct",
        "crash_rate_pct",
        "p95_latency_ms",
        "support_tickets",
    ]:
        item = metric_lookup[metric_name]
        rationale.append(
            f"{metric_name}: status={item['status']}, trend={item['trend']}, latest={item['latest_value']}, baseline={item['baseline_mean']}."
        )

    rationale.append(
        "Feedback summary: "
        f"positive={feedback_report['sentiment_counts']['positive']}, "
        f"neutral={feedback_report['sentiment_counts']['neutral']}, "
        f"negative={feedback_report['sentiment_counts']['negative']}."
    )

    if feedback_report["repeated_issues"]:
        rationale.append(
            "Repeated issues detected: " + ", ".join(feedback_report["repeated_issues"]) + "."
        )

    stance_counts = Counter(
        output["stance"]
        for name, output in agent_outputs.items()
        if name != "coordinator" and "stance" in output
    )
    rationale.append(f"Agent stance distribution: {dict(stance_counts)}.")

    return rationale


def build_risk_register(tool_outputs: dict[str, Any]) -> list[dict[str, Any]]:
    guardrails_report = tool_outputs["guardrails_report"]
    feedback_report = tool_outputs["feedback_report"]

    risks: list[RiskItem] = []
    seen_titles: set[str] = set()

    for idx, trigger in enumerate(guardrails_report["rollback_triggers"], start=1):
        title = trigger["reason"]
        if title in seen_titles:
            continue
        seen_titles.add(title)
        risks.append(
            RiskItem(
                risk_id=f"risk_rb_{idx}",
                title=title,
                severity="critical",
                likelihood="high",
                blocking=True,
                owner="Engineering",
                mitigation="Roll back the affected launch components and validate recovery metrics.",
                evidence=[
                    f"{trigger['metric']} on {trigger['date']} observed={trigger['observed']} threshold={trigger['threshold']}"
                ],
            )
        )

    offset = len(risks)
    for idx, trigger in enumerate(guardrails_report["pause_triggers"], start=1):
        title = trigger["reason"]
        if title in seen_titles:
            continue
        seen_titles.add(title)
        owner = "Engineering" if trigger["metric"] != "support_tickets" else "Support"
        mitigation = (
            "Stabilize the affected metric before expanding rollout."
            if trigger["metric"] != "support_tickets"
            else "Prepare support operations and reduce user-facing incident load."
        )
        risks.append(
            RiskItem(
                risk_id=f"risk_p_{offset + idx}",
                title=title,
                severity="high",
                likelihood="high",
                blocking=True,
                owner=owner,
                mitigation=mitigation,
                evidence=[
                    f"{trigger['metric']} on {trigger['date']} observed={trigger['observed']} threshold={trigger['threshold']}"
                ],
            )
        )

    if feedback_report["repeated_issues"]:
        risks.append(
            RiskItem(
                risk_id=f"risk_feedback_{len(risks) + 1}",
                title="Repeated user complaints indicate customer trust risk.",
                severity="medium",
                likelihood="high",
                blocking=False,
                owner="Product",
                mitigation="Investigate complaint clusters, confirm blast radius, and communicate clearly to affected teams.",
                evidence=feedback_report["repeated_issues"],
            )
        )

    if feedback_report["outliers"]:
        risks.append(
            RiskItem(
                risk_id=f"risk_outlier_{len(risks) + 1}",
                title="Severe outlier complaints require targeted investigation.",
                severity="medium",
                likelihood="medium",
                blocking=False,
                owner="Support",
                mitigation="Review account-level logs and verify whether these reports are isolated or systemic.",
                evidence=feedback_report["outliers"][:3],
            )
        )

    return [risk.model_dump() for risk in risks[:6]]


def build_action_plan(
    final_decision: str,
    tool_outputs: dict[str, Any],
) -> list[dict[str, Any]]:
    latest_date = tool_outputs["guardrails_report"]["latest_date"]

    actions = [
        ActionItem(
            action_id="act_1",
            priority="P0",
            owner="Engineering",
            deadline_utc=f"{latest_date}T12:00:00Z",
            task="Investigate payment confirmation failures and validate the full checkout path end-to-end.",
            success_criteria="Payment success rate recovers above pause threshold and holds steady across two monitoring intervals.",
        ),
        ActionItem(
            action_id="act_2",
            priority="P0",
            owner="Engineering",
            deadline_utc=f"{latest_date}T16:00:00Z",
            task="Profile crash and latency hotspots introduced by checkout rendering and recommendation fetch calls.",
            success_criteria="Crash rate and p95 latency trend back toward pre-launch baseline.",
        ),
        ActionItem(
            action_id="act_3",
            priority="P1",
            owner="Support",
            deadline_utc=f"{latest_date}T18:00:00Z",
            task="Prepare a support brief with known issues, workarounds, and escalation triggers.",
            success_criteria="Support team has a standardized response and escalation path for affected customers.",
        ),
        ActionItem(
            action_id="act_4",
            priority="P1",
            owner="Product",
            deadline_utc=f"{latest_date}T20:00:00Z",
            task="Review rollout status after 24 hours of stabilized metrics and decide whether to resume, hold, or roll back.",
            success_criteria="A follow-up decision is made using refreshed metrics and updated complaint volume.",
        ),
    ]

    if final_decision == "ROLL_BACK":
        actions.insert(
            0,
            ActionItem(
                action_id="act_0",
                priority="P0",
                owner="Engineering",
                deadline_utc=f"{latest_date}T10:00:00Z",
                task="Trigger rollback to legacy checkout experience for impacted traffic.",
                success_criteria="Affected users are routed to a stable checkout flow and severe guardrail breaches stop worsening.",
            ),
        )
    elif final_decision == "PAUSE":
        actions.insert(
            0,
            ActionItem(
                action_id="act_0",
                priority="P0",
                owner="Product",
                deadline_utc=f"{latest_date}T10:00:00Z",
                task="Pause rollout expansion and hold traffic at the current exposure level.",
                success_criteria="No further rollout increase occurs until blocking metrics recover.",
            ),
        )

    return [action.model_dump() for action in actions]


def build_communication_plan(
    final_decision: str,
    tool_outputs: dict[str, Any],
) -> dict[str, Any]:
    feedback_report = tool_outputs["feedback_report"]

    internal_message = (
        f"Launch decision: {final_decision}. Adoption is promising, but rollout is gated by reliability issues "
        "in checkout, including payment friction and performance instability."
    )

    support_message = (
        "Customers may report slow checkout, freezing, delayed confirmation, or failed payment attempts. "
        "Use approved workaround language and escalate severe account-impacting cases."
    )

    external_required = final_decision in {"PAUSE", "ROLL_BACK"}
    customer_required = final_decision in {"PAUSE", "ROLL_BACK"}

    external_message = None
    customer_message = None

    if external_required:
        external_message = (
            "We are investigating intermittent checkout issues affecting a subset of users. "
            "Our team is actively working on mitigations and will share updates as reliability improves."
        )

    if customer_required:
        customer_message = (
            "We are aware of intermittent checkout issues that may impact payment completion or responsiveness. "
            "We are actively working on a fix and recommend retrying shortly if you encounter a delay."
        )

    if feedback_report["outliers"]:
        support_message += (
            " Review severe outlier complaints individually to confirm whether they are isolated."
        )

    return {
        "internal_slack_update": {
            "required": True,
            "audience": "#launch-war-room",
            "message": internal_message,
        },
        "external_status_page": {
            "required": external_required,
            "message": external_message,
        },
        "customer_email": {
            "required": customer_required,
            "segment": "affected_users" if customer_required else None,
            "message": customer_message,
        },
        "support_brief": {
            "required": True,
            "message": support_message,
        },
    }


def confidence_increase_factors(tool_outputs: dict[str, Any]) -> list[str]:
    feedback_report = tool_outputs["feedback_report"]

    items = [
        "Another 24 hours of stable post-fix payment and performance metrics.",
        "Cohort-level analysis showing whether failures are localized to specific platforms or user segments.",
        "Validation that severe outlier complaints are either resolved or not broadly reproducible.",
        "Fresh support volume data confirming whether incident pressure is declining.",
    ]

    if feedback_report["repeated_issues"]:
        items.append("Evidence that repeated complaint themes materially decline after mitigation.")

    return items


def build_final_decision(
    tool_outputs: dict[str, Any],
    agent_outputs: dict[str, Any],
) -> dict[str, Any]:
    coordinator_draft = agent_outputs["coordinator"]["draft_decision"]
    guardrail_floor = tool_outputs["guardrails_report"]["recommended_decision_floor"]

    final_decision = _max_decision(coordinator_draft, guardrail_floor)
    confidence = compute_confidence(tool_outputs, agent_outputs, final_decision)

    payload = FinalDecision(
        decision=final_decision,
        confidence=confidence,
        rationale=build_rationale(tool_outputs, agent_outputs, final_decision),
        risk_register=build_risk_register(tool_outputs),
        action_plan_24_48h=build_action_plan(final_decision, tool_outputs),
        communication_plan=build_communication_plan(final_decision, tool_outputs),
        confidence_increase_factors=confidence_increase_factors(tool_outputs),
    )

    return payload.model_dump()

