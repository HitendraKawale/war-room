from src.data_loader import load_feedback, load_metrics, load_text, load_yaml
from src.orchestrator import WarRoomOrchestrator
from src.state import WarRoomState


def test_agents_produce_outputs():
    state: WarRoomState = {
        "metrics": load_metrics("data/metrics.csv"),
        "feedback": load_feedback("data/feedback.jsonl"),
        "release_notes": load_text("data/release_notes.md"),
        "thresholds": load_yaml("data/thresholds.yaml"),
        "trace": [],
        "errors": [],
    }

    result = WarRoomOrchestrator().run(state)

    assert "pm" in result["agent_outputs"]
    assert "data_analyst" in result["agent_outputs"]
    assert "marketing_comms" in result["agent_outputs"]
    assert "risk_critic" in result["agent_outputs"]
    assert "coordinator" in result["agent_outputs"]


def test_coordinator_produces_draft_decision():
    state: WarRoomState = {
        "metrics": load_metrics("data/metrics.csv"),
        "feedback": load_feedback("data/feedback.jsonl"),
        "release_notes": load_text("data/release_notes.md"),
        "thresholds": load_yaml("data/thresholds.yaml"),
        "trace": [],
        "errors": [],
    }

    result = WarRoomOrchestrator().run(state)
    decision = result["final_output"]["draft_decision"]

    assert result["final_output"]["decision"] in {"PROCEED", "PAUSE", "ROLL_BACK"}
