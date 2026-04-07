from __future__ import annotations

from src.state import WarRoomState
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

        state["tool_outputs"] = {}
        state["agent_outputs"] = {}
        state["final_output"] = {
            "status": "not_implemented_yet",
            "message": "Commit 1 scaffold loaded successfully.",
        }

        trace.append(
            trace_event(
                step="orchestrator",
                event_type="end",
                summary="Scaffold run completed.",
            )
        )
        return state
