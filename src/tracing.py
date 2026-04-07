from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def trace_event(
    step: str, event_type: str, summary: str, **extra: Any
) -> dict[str, Any]:
    payload = {
        "timestamp_utc": utc_now(),
        "step": step,
        "event_type": event_type,
        "summary": summary,
    }
    payload.update(extra)
    return payload
