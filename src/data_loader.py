from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from src.models import FeedbackEntry, MetricRow


def load_metrics(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = MetricRow(
                date=row["date"],
                signup_conversion_pct=float(row["signup_conversion_pct"]),
                dau=int(row["dau"]),
                wau=int(row["wau"]),
                d1_retention_pct=float(row["d1_retention_pct"]),
                crash_rate_pct=float(row["crash_rate_pct"]),
                p95_latency_ms=int(row["p95_latency_ms"]),
                payment_success_pct=float(row["payment_success_pct"]),
                support_tickets=int(row["support_tickets"]),
                feature_adoption_pct=float(row["feature_adoption_pct"]),
                churn_pct=float(row["churn_pct"]),
            )
            rows.append(parsed.model_dump())
    return rows


def load_feedback(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            payload = json.loads(line)
            parsed = FeedbackEntry(**payload)
            rows.append(parsed.model_dump())
    return rows


def load_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
