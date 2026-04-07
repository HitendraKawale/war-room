from src.data_loader import load_feedback, load_metrics, load_text, load_yaml
from src.orchestrator import WarRoomOrchestrator
from src.state import WarRoomState


def build_state() -> WarRoomState:
    return {
        "metrics": load_metrics("data/metrics.csv"),
        "feedback": load_feedback("data/feedback.jsonl"),
        "release_notes": load_text("data/release_notes.md"),
        "thresholds": load_yaml("data/thresholds.yaml"),
        "trace": [],
        "errors": [],
    }


def test_trace_contains_run_id_and_status():
    result = WarRoomOrchestrator().run(build_state())
    trace = result["trace"]

    assert len(trace) > 0
    assert all("run_id" in item for item in trace)
    assert all("status" in item for item in trace)


def test_trace_contains_decision_engine_step():
    result = WarRoomOrchestrator().run(build_state())
    steps = [item["step"] for item in result["trace"]]

    assert "decision_engine" in steps
    assert "metrics_tools" in steps
    assert "feedback_tools" in steps
