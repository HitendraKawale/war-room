from __future__ import annotations

import json
from pathlib import Path

from src.config import settings
from src.data_loader import load_feedback, load_metrics, load_text, load_yaml
from src.orchestrator import WarRoomOrchestrator
from src.state import WarRoomState


def main() -> None:
    metrics = load_metrics("data/metrics.csv")
    feedback = load_feedback("data/feedback.jsonl")
    release_notes = load_text("data/release_notes.md")
    thresholds = load_yaml("data/thresholds.yaml")

    state: WarRoomState = {
        "metrics": metrics,
        "feedback": feedback,
        "release_notes": release_notes,
        "thresholds": thresholds,
        "trace": [],
        "errors": [],
    }

    orchestrator = WarRoomOrchestrator()
    final_state = orchestrator.run(state)

    print("\n=== PurpleMerit War Room ===")
    print(f"Loaded metrics rows: {len(metrics)}")
    print(f"Loaded feedback entries: {len(feedback)}")
    print(f"Configured feature: {thresholds['launch']['feature_name']}")
    print(f"Model configured: {settings.model_name}")
    print("\nCurrent final output:")
    print(json.dumps(final_state["final_output"], indent=2))

    print("\nTrace:")
    for event in final_state["trace"]:
        print(json.dumps(event, indent=2))

    outputs_dir = Path(settings.outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    (outputs_dir / "scaffold_trace.json").write_text(
        json.dumps(final_state["trace"], indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
