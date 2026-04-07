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


def test_final_output_has_required_fields():
    result = WarRoomOrchestrator().run(build_state())
    final_output = result["final_output"]

    assert "decision" in final_output
    assert "confidence" in final_output
    assert "rationale" in final_output
    assert "risk_register" in final_output
    assert "action_plan_24_48h" in final_output
    assert "communication_plan" in final_output
    assert "confidence_increase_factors" in final_output


def test_final_decision_is_valid_enum():
    result = WarRoomOrchestrator().run(build_state())
    assert result["final_output"]["decision"] in {"PROCEED", "PAUSE", "ROLL_BACK"}


def test_action_plan_is_non_empty():
    result = WarRoomOrchestrator().run(build_state())
    actions = result["final_output"]["action_plan_24_48h"]

    assert len(actions) >= 3
    assert all("owner" in item for item in actions)
    assert all("task" in item for item in actions)


def test_confidence_is_reasonable():
    result = WarRoomOrchestrator().run(build_state())
    confidence = result["final_output"]["confidence"]

    assert 0.5 <= confidence <= 0.9

