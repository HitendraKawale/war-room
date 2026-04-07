from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from src.config import settings
from src.data_loader import load_feedback, load_metrics, load_text, load_yaml
from src.orchestrator import WarRoomOrchestrator
from src.state import WarRoomState
from src.tracing import TraceRecorder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PurpleMerit launch war room simulator")
    parser.add_argument("--metrics", default="data/metrics.csv")
    parser.add_argument("--feedback", default="data/feedback.jsonl")
    parser.add_argument("--release-notes", default="data/release_notes.md")
    parser.add_argument("--thresholds", default="data/thresholds.yaml")
    parser.add_argument("--output-dir", default=settings.outputs_dir)
    parser.add_argument(
        "--export-format",
        choices=["json", "yaml", "both"],
        default="both",
    )
    return parser.parse_args()


def display_model_info() -> tuple[str, str]:
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return provider, settings.ollama_model
    return provider, settings.openai_model


def main() -> None:
    args = parse_args()

    metrics = load_metrics(args.metrics)
    feedback = load_feedback(args.feedback)
    release_notes = load_text(args.release_notes)
    thresholds = load_yaml(args.thresholds)

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

    provider, model_name = display_model_info()

    print("\n=== PurpleMerit War Room ===")
    print(f"Run ID: {run_id}")
    print(f"Loaded metrics rows: {len(metrics)}")
    print(f"Loaded feedback entries: {len(feedback)}")
    print(f"Configured feature: {thresholds['launch']['feature_name']}")
    print(f"LLM provider: {provider}")
    print(f"Model: {model_name}")

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

    outputs_dir = Path(args.output_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    (outputs_dir / "tool_outputs.json").write_text(
        json.dumps(final_state["tool_outputs"], indent=2),
        encoding="utf-8",
    )
    (outputs_dir / "agent_outputs.json").write_text(
        json.dumps(final_state["agent_outputs"], indent=2),
        encoding="utf-8",
    )

    if args.export_format in {"json", "both"}:
        (outputs_dir / "final_decision.json").write_text(
            json.dumps(final_output, indent=2),
            encoding="utf-8",
        )

    if args.export_format in {"yaml", "both"}:
        (outputs_dir / "final_decision.yaml").write_text(
            yaml.safe_dump(final_output, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    recorder = TraceRecorder(run_id=run_id, trace=trace)
    recorder.save_json(outputs_dir / "trace.json")
    recorder.save_jsonl(outputs_dir / "trace.jsonl")

    print("\nSaved outputs:")
    if args.export_format in {"json", "both"}:
        print(f"- {outputs_dir / 'final_decision.json'}")
    if args.export_format in {"yaml", "both"}:
        print(f"- {outputs_dir / 'final_decision.yaml'}")
    print(f"- {outputs_dir / 'trace.json'}")
    print(f"- {outputs_dir / 'trace.jsonl'}")


if __name__ == "__main__":
    main()
