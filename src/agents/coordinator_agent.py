from __future__ import annotations

from collections import Counter

from src.agents.base import BaseAgent
from src.state import WarRoomState


DECISION_RANK = {
    "PROCEED": 0,
    "PAUSE": 1,
    "ROLL_BACK": 2,
}


class CoordinatorAgent(BaseAgent):
    name = "coordinator"

    def run(self, state: WarRoomState) -> dict:
        agent_outputs = state["agent_outputs"]

        stances = {
            name: output["stance"] for name, output in agent_outputs.items() if name != self.name
        }
        stance_counts = Counter(stances.values())

        draft_decision = max(stances.values(), key=lambda s: DECISION_RANK[s])

        rationale = []
        if any(s == "ROLL_BACK" for s in stances.values()):
            rationale.append(
                "At least one function believes the launch should be rolled back due to guardrail severity."
            )
        if stance_counts["PAUSE"] >= 2:
            rationale.append("Multiple functions independently recommend pausing rollout.")
        if "data_analyst" in agent_outputs:
            rationale.append(agent_outputs["data_analyst"]["summary"])
        if "marketing_comms" in agent_outputs:
            rationale.append(agent_outputs["marketing_comms"]["summary"])
        if "risk_critic" in agent_outputs:
            rationale.append(agent_outputs["risk_critic"]["summary"])

        dissent = [
            {"agent": agent_name, "stance": stance}
            for agent_name, stance in stances.items()
            if stance != draft_decision
        ]

        avg_confidence = sum(output["confidence"] for output in agent_outputs.values()) / len(
            agent_outputs
        )
        disagreement_penalty = 0.08 if len(set(stances.values())) > 1 else 0.0
        confidence = self.clamp_confidence(avg_confidence - disagreement_penalty)

        summary = (
            f"Coordinator draft decision is {draft_decision}. "
            f"Consensus is based on agent stances={dict(stance_counts)}."
        )

        return {
            "agent": self.name,
            "draft_decision": draft_decision,
            "summary": summary,
            "stance_counts": dict(stance_counts),
            "dissent": dissent,
            "rationale": rationale,
            "confidence": confidence,
        }
