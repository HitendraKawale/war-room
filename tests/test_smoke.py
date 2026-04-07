from src.data_loader import load_feedback, load_metrics, load_yaml


def test_mock_data_loads():
    metrics = load_metrics("data/metrics.csv")
    feedback = load_feedback("data/feedback.jsonl")
    thresholds = load_yaml("data/thresholds.yaml")

    assert len(metrics) == 10
    assert len(feedback) == 30
    assert "decision_rules" in thresholds
