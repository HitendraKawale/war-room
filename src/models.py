from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DecisionLabel = Literal["PROCEED", "PAUSE", "ROLL_BACK"]
Severity = Literal["low", "medium", "high", "critical"]
Likelihood = Literal["low", "medium", "high"]
Priority = Literal["P0", "P1", "P2"]


class MetricRow(BaseModel):
    date: str
    signup_conversion_pct: float
    dau: int
    wau: int
    d1_retention_pct: float
    crash_rate_pct: float
    p95_latency_ms: int
    payment_success_pct: float
    support_tickets: int
    feature_adoption_pct: float
    churn_pct: float


class FeedbackEntry(BaseModel):
    id: str
    date: str
    channel: str
    segment: str
    text: str


class AgentOutput(BaseModel):
    agent: str
    stance: DecisionLabel
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)


class RiskItem(BaseModel):
    risk_id: str
    title: str
    severity: Severity
    likelihood: Likelihood
    blocking: bool
    owner: str
    mitigation: str
    evidence: list[str]


class ActionItem(BaseModel):
    action_id: str
    priority: Priority
    owner: str
    deadline_utc: str
    task: str
    success_criteria: str


class FinalDecision(BaseModel):
    decision: DecisionLabel
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: list[str]
    risk_register: list[RiskItem]
    action_plan_24_48h: list[ActionItem]
    communication_plan: dict
    confidence_increase_factors: list[str]

