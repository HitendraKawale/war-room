from __future__ import annotations

from typing import Any, TypedDict


class WarRoomState(TypedDict, total=False):
    metrics: list[dict[str, Any]]
    feedback: list[dict[str, Any]]
    release_notes: str
    thresholds: dict[str, Any]

    tool_outputs: dict[str, Any]
    agent_outputs: dict[str, Any]
    final_output: dict[str, Any]

    trace: list[dict[str, Any]]
    errors: list[dict[str, Any]]
