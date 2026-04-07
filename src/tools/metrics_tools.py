from __future__ import annotations

from statistics import mean
from typing import Any


def _safe_mean(values: list[float]) -> float:
    return round(mean(values), 4) if values else 0.0


def _delta_pct(baseline: float, current: float) -> float | None:
    if baseline == 0:
        return None
    return round(((current - baseline) / baseline) * 100.0, 2)


def _metric_trend(direction: str, first_post: float, latest: float) -> str:
    if abs(latest - first_post) < 1e-9:
        return "flat"

    if direction == "higher_is_better":
        return "improving" if latest > first_post else "worsening"

    return "improving" if latest < first_post else "worsening"


def _heuristic_status(metric: str, direction: str, baseline: float, latest: float) -> str:
    if metric == "feature_adoption_pct":
        return "green" if latest > 0 else "yellow"

    delta = _delta_pct(baseline, latest)
    if delta is None:
        return "green"

    if direction == "higher_is_better":
        if delta <= -10:
            return "red"
        if delta <= -3:
            return "yellow"
        return "green"

    deterioration = delta
    if deterioration >= 50:
        return "red"
    if deterioration >= 15:
        return "yellow"
    return "green"


def split_baseline_post_launch(
    metrics: list[dict[str, Any]],
    launch_date: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baseline_rows = [row for row in metrics if row["date"] < launch_date]
    post_launch_rows = [row for row in metrics if row["date"] >= launch_date]
    return baseline_rows, post_launch_rows


def analyze_metric_trends(
    metrics: list[dict[str, Any]],
    metric_direction: dict[str, str],
    launch_date: str,
) -> dict[str, Any]:
    baseline_rows, post_launch_rows = split_baseline_post_launch(metrics, launch_date)

    if not baseline_rows:
        raise ValueError("No baseline rows found before launch_date.")
    if not post_launch_rows:
        raise ValueError("No post-launch rows found on/after launch_date.")

    latest = post_launch_rows[-1]
    first_post = post_launch_rows[0]

    per_metric: list[dict[str, Any]] = []

    for metric, direction in metric_direction.items():
        baseline_values = [float(row[metric]) for row in baseline_rows]
        baseline_mean = _safe_mean(baseline_values)
        latest_value = float(latest[metric])
        first_post_value = float(first_post[metric])

        delta_pct = _delta_pct(baseline_mean, latest_value)
        trend = _metric_trend(direction, first_post_value, latest_value)
        status = _heuristic_status(metric, direction, baseline_mean, latest_value)

        evidence = [
            f"baseline_mean={baseline_mean}",
            f"first_post={first_post_value}",
            f"latest={latest_value}",
            f"trend={trend}",
            f"delta_pct={delta_pct}",
        ]

        per_metric.append(
            {
                "metric": metric,
                "directionality": direction,
                "baseline_mean": baseline_mean,
                "first_post_value": first_post_value,
                "latest_value": latest_value,
                "delta_pct_vs_baseline": delta_pct,
                "trend": trend,
                "status": status,
                "evidence": evidence,
            }
        )

    status_counts = {
        "green": sum(1 for item in per_metric if item["status"] == "green"),
        "yellow": sum(1 for item in per_metric if item["status"] == "yellow"),
        "red": sum(1 for item in per_metric if item["status"] == "red"),
    }

    overall_health = "green"
    if status_counts["red"] >= 2:
        overall_health = "red"
    elif status_counts["red"] >= 1 or status_counts["yellow"] >= 2:
        overall_health = "mixed"

    key_findings = []
    for item in per_metric:
        metric = item["metric"]
        if metric in {"crash_rate_pct", "p95_latency_ms", "payment_success_pct", "support_tickets"}:
            key_findings.append(
                f"{metric}: {item['status']} ({item['trend']}, latest={item['latest_value']}, baseline={item['baseline_mean']})"
            )
        elif metric in {"signup_conversion_pct", "feature_adoption_pct", "dau"}:
            key_findings.append(
                f"{metric}: {item['status']} ({item['trend']}, latest={item['latest_value']})"
            )

    return {
        "launch_date": launch_date,
        "baseline_days": len(baseline_rows),
        "post_launch_days": len(post_launch_rows),
        "latest_date": latest["date"],
        "overall_health": overall_health,
        "status_counts": status_counts,
        "per_metric": per_metric,
        "key_findings": key_findings,
    }


def evaluate_guardrails(
    metrics: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    launch_date = thresholds["launch"]["launch_date"]
    rules = thresholds["decision_rules"]

    baseline_rows, post_launch_rows = split_baseline_post_launch(metrics, launch_date)
    if not baseline_rows or not post_launch_rows:
        raise ValueError("Guardrail evaluation requires both baseline and post-launch rows.")

    baseline_support_mean = _safe_mean([float(row["support_tickets"]) for row in baseline_rows])
    latest_row = post_launch_rows[-1]

    rollback_triggers: list[dict[str, Any]] = []
    pause_triggers: list[dict[str, Any]] = []

    for row in post_launch_rows:
        if float(row["payment_success_pct"]) < float(
            rules["rollback"]["payment_success_pct_below"]
        ):
            rollback_triggers.append(
                {
                    "rule_id": "rollback_payment_success",
                    "metric": "payment_success_pct",
                    "date": row["date"],
                    "observed": float(row["payment_success_pct"]),
                    "threshold": float(rules["rollback"]["payment_success_pct_below"]),
                    "reason": "Payment success dropped below rollback threshold.",
                }
            )

        if float(row["crash_rate_pct"]) > float(rules["rollback"]["crash_rate_pct_above"]):
            rollback_triggers.append(
                {
                    "rule_id": "rollback_crash_rate",
                    "metric": "crash_rate_pct",
                    "date": row["date"],
                    "observed": float(row["crash_rate_pct"]),
                    "threshold": float(rules["rollback"]["crash_rate_pct_above"]),
                    "reason": "Crash rate exceeded rollback threshold.",
                }
            )

        if float(row["p95_latency_ms"]) > float(rules["rollback"]["p95_latency_ms_above"]):
            rollback_triggers.append(
                {
                    "rule_id": "rollback_latency",
                    "metric": "p95_latency_ms",
                    "date": row["date"],
                    "observed": float(row["p95_latency_ms"]),
                    "threshold": float(rules["rollback"]["p95_latency_ms_above"]),
                    "reason": "Latency exceeded rollback threshold.",
                }
            )

        if float(row["payment_success_pct"]) < float(rules["pause"]["payment_success_pct_below"]):
            pause_triggers.append(
                {
                    "rule_id": "pause_payment_success",
                    "metric": "payment_success_pct",
                    "date": row["date"],
                    "observed": float(row["payment_success_pct"]),
                    "threshold": float(rules["pause"]["payment_success_pct_below"]),
                    "reason": "Payment success dropped below pause threshold.",
                }
            )

        if float(row["crash_rate_pct"]) > float(rules["pause"]["crash_rate_pct_above"]):
            pause_triggers.append(
                {
                    "rule_id": "pause_crash_rate",
                    "metric": "crash_rate_pct",
                    "date": row["date"],
                    "observed": float(row["crash_rate_pct"]),
                    "threshold": float(rules["pause"]["crash_rate_pct_above"]),
                    "reason": "Crash rate exceeded pause threshold.",
                }
            )

        if float(row["p95_latency_ms"]) > float(rules["pause"]["p95_latency_ms_above"]):
            pause_triggers.append(
                {
                    "rule_id": "pause_latency",
                    "metric": "p95_latency_ms",
                    "date": row["date"],
                    "observed": float(row["p95_latency_ms"]),
                    "threshold": float(rules["pause"]["p95_latency_ms_above"]),
                    "reason": "Latency exceeded pause threshold.",
                }
            )

    latest_support = float(latest_row["support_tickets"])
    support_multiplier = (
        round(latest_support / baseline_support_mean, 2) if baseline_support_mean else 0.0
    )
    support_threshold = float(rules["pause"]["support_ticket_multiplier_above"])

    if support_multiplier > support_threshold:
        pause_triggers.append(
            {
                "rule_id": "pause_support_ticket_multiplier",
                "metric": "support_tickets",
                "date": latest_row["date"],
                "observed": support_multiplier,
                "threshold": support_threshold,
                "reason": "Support tickets are materially above baseline.",
            }
        )

    recommended_decision_floor = "PROCEED"
    if rollback_triggers:
        recommended_decision_floor = "ROLL_BACK"
    elif pause_triggers:
        recommended_decision_floor = "PAUSE"

    return {
        "launch_date": launch_date,
        "latest_date": latest_row["date"],
        "baseline_support_mean": baseline_support_mean,
        "latest_support_tickets": latest_support,
        "support_ticket_multiplier": support_multiplier,
        "rollback_triggers": rollback_triggers,
        "pause_triggers": pause_triggers,
        "recommended_decision_floor": recommended_decision_floor,
    }
