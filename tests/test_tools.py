from src.data_loader import load_feedback, load_metrics, load_yaml
from src.tools.feedback_tools import analyze_feedback
from src.tools.metrics_tools import analyze_metric_trends, evaluate_guardrails


def test_metric_tools_detect_mixed_or_red_health():
    metrics = load_metrics("data/metrics.csv")
    thresholds = load_yaml("data/thresholds.yaml")

    report = analyze_metric_trends(
        metrics=metrics,
        metric_direction=thresholds["metric_direction"],
        launch_date=thresholds["launch"]["launch_date"],
    )

    assert report["overall_health"] in {"mixed", "red"}
    assert len(report["per_metric"]) >= 6


def test_guardrails_recommend_pause_or_rollback():
    metrics = load_metrics("data/metrics.csv")
    thresholds = load_yaml("data/thresholds.yaml")

    report = evaluate_guardrails(metrics, thresholds)

    assert report["recommended_decision_floor"] in {"PAUSE", "ROLL_BACK"}
    assert len(report["pause_triggers"]) >= 1


def test_feedback_tools_detect_negative_signals():
    feedback = load_feedback("data/feedback.jsonl")
    report = analyze_feedback(feedback)

    assert report["sentiment_counts"]["negative"] >= 8
    assert (
        "payment_failure" in report["repeated_issues"]
        or "crash_freeze" in report["repeated_issues"]
    )
