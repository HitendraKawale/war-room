from __future__ import annotations

import json
from pathlib import Path

from src.config import settings
from src.data_loader import load_feedback, load_metrics, load_text, load_yaml
from src.orchestrator import WarRoomOrchestrator
from src.state import WarRoomState
from src.tracing import TraceRecorder


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

    run_id = final_state["run_id"]
    final_output = final_state["final_output"]
    trace = final_state["trace"]

    print("\n=== PurpleMerit War Room ===")
    print(f"Run ID: {run_id}")
    print(f"Loaded metrics rows: {len(metrics)}")
    print(f"Loaded feedback entries: {len(feedback)}")
    print(f"Configured feature: {thresholds['launch']['feature_name']}")
    print(f"Model configured: {settings.model_name}")

    print("\n=== Final Decision Summary ===")
    print(f"Decision: {final_output['decision']}")
    print(f"Confidence: {final_output['confidence']}")
    print(f"Risks: {len(final_output['risk_register'])}")
    print(f"Actions: {len(final_output['action_plan_24_48h'])}")

    print("\n=== Agent Stances ===")
    for agent_name, output in final_state["agent_outputs"].items():
        if "stance" in output:
            print(f"- {agent_name}: {output['stance']} (confidence={output['confidence']})")
        else:
            print(
                f"- {agent_name}: draft={output['draft_decision']} (confidence={output['confidence']})"
            )

    print("\n=== Final Structured Output ===")
    print(json.dumps(final_output, indent=2))

    print("\n=== Trace Preview ===")
    for event in trace[-8:]:
        print(json.dumps(event, indent=2))

    outputs_dir = Path(settings.outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    (outputs_dir / "tool_outputs.json").write_text(
        json.dumps(final_state["tool_outputs"], indent=2),
        encoding="utf-8",
    )
    (outputs_dir / "agent_outputs.json").write_text(
        json.dumps(final_state["agent_outputs"], indent=2),
        encoding="utf-8",
    )
    (outputs_dir / "final_decision.json").write_text(
        json.dumps(final_output, indent=2),
        encoding="utf-8",
    )

    recorder = TraceRecorder(run_id=run_id, trace=trace)
    recorder.save_json(outputs_dir / "trace.json")
    recorder.save_jsonl(outputs_dir / "trace.jsonl")

    print("\nSaved outputs:")
    print(f"- {outputs_dir / 'final_decision.json'}")
    print(f"- {outputs_dir / 'trace.json'}")
    print(f"- {outputs_dir / 'trace.jsonl'}")


if __name__ == "__main__":
    main()
