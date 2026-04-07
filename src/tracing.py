from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id(prefix: str = "wr") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def trace_event(
    *,
    run_id: str,
    step: str,
    event_type: str,
    summary: str,
    status: str = "ok",
    duration_ms: int | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "timestamp_utc": utc_now(),
        "run_id": run_id,
        "step": step,
        "event_type": event_type,
        "status": status,
        "summary": summary,
    }
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    payload.update(extra)
    return payload


class TraceRecorder:
    def __init__(self, run_id: str, trace: list[dict[str, Any]] | None = None) -> None:
        self.run_id = run_id
        self.trace = trace if trace is not None else []

    def add(
        self,
        *,
        step: str,
        event_type: str,
        summary: str,
        status: str = "ok",
        duration_ms: int | None = None,
        **extra: Any,
    ) -> None:
        self.trace.append(
            trace_event(
                run_id=self.run_id,
                step=step,
                event_type=event_type,
                summary=summary,
                status=status,
                duration_ms=duration_ms,
                **extra,
            )
        )

    @contextmanager
    def span(self, step: str, start_summary: str, end_summary: str) -> Iterator[None]:
        self.add(step=step, event_type="start", summary=start_summary)
        started = time.perf_counter()
        try:
            yield
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            self.add(
                step=step,
                event_type="end",
                summary=f"{end_summary} FAILED: {exc}",
                status="error",
                duration_ms=duration_ms,
                error=str(exc),
            )
            raise
        else:
            duration_ms = int((time.perf_counter() - started) * 1000)
            self.add(
                step=step,
                event_type="end",
                summary=end_summary,
                status="ok",
                duration_ms=duration_ms,
            )

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.trace, indent=2), encoding="utf-8")

    def save_jsonl(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for item in self.trace:
                f.write(json.dumps(item) + "\n")

