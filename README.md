# war-room

A deterministic multi-agent system that simulates a cross-functional **launch war room** during a product rollout.

The system analyzes a mock product launch dashboard containing:
- time-series **metrics**
- short-form **user feedback**
- **release notes / known issues**
- **decision thresholds**

It then produces a structured launch decision:

- **PROCEED**
- **PAUSE**
- **ROLL_BACK**

along with:
- rationale
- risk register
- 24–48 hour action plan
- communication plan
- confidence score
- execution traces

---

## Overview

During a product launch, teams often need to make fast decisions under uncertainty. Some metrics improve, others worsen, and customer feedback is mixed. In practice, these decisions are rarely made by one person alone. Product, analytics, marketing, and risk stakeholders all contribute different perspectives.

This project simulates that process.

**war-room** is a deterministic multi-agent system that models a cross-functional launch review. It takes a mock launch dashboard as input, runs a set of programmatic analysis tools, routes the evidence through specialist agents, and produces a structured launch recommendation with clear operational next steps.

The result is a reproducible and explainable system that is easy to run, test, and inspect.

---

## Core Idea

The system follows this pipeline:

```text
Input files
→ Data loading
→ Deterministic tools
→ Specialist agents
→ Coordinator
→ Decision engine
→ Final structured output + traces
```

## Agents
The war room is modelled with the following agents 
- **PM Agent:** Evaluates product value, user impact, rollout readiness, and go/no-go framing.

- **Data Analyst Agent:** Interprets quantitative signals such as trends, threshold breaches, and blocking metrics.

- **Marketing / Comms Agent:** Assesses customer sentiment, repeated complaint patterns, and communication implications.

- **Risk / Critic Agent:** Challenges optimistic assumptions, highlights launch risks, and identifies blockers.

- **Coordinator Agent:** Aggregates the specialist positions into a draft recommendation before final resolution.

## Tooling

The system includes deterministic tools that agents rely on programmatically:

- **Metrics Tooling:** pre-launch vs post-launch comparison, trend assessment, metric health scoring, pause / rollback guardrail checks, Feedback Tooling

- **Feedback Tooling:** sentiment classification, theme detection, repeated issue identification, outlier complaint detection, trust risk summary

#### Why Determinsitic?
- Logic is easy to validate
- final decision is grounded in explicit tool outputs and threshold rules
- explainable

## Repo Structure

```
purplemerit-war-room/
├── README.md
├── .env.example
├── .gitignore
├── pyproject.toml
├── data/
│   ├── metrics.csv
│   ├── feedback.jsonl
│   ├── release_notes.md
│   └── thresholds.yaml
├── outputs/
│   └── .gitkeep
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── data_loader.py
│   ├── decision_engine.py
│   ├── main.py
│   ├── models.py
│   ├── orchestrator.py
│   ├── state.py
│   ├── tracing.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── coordinator_agent.py
│   │   ├── data_analyst_agent.py
│   │   ├── marketing_agent.py
│   │   ├── pm_agent.py
│   │   └── risk_critic_agent.py
│   └── tools/
│       ├── __init__.py
│       ├── feedback_tools.py
│       └── metrics_tools.py
└── tests/
    ├── test_agents.py
    ├── test_decision_engine.py
    ├── test_smoke.py
    ├── test_tools.py
    └── test_traceability.py
```
## Inputs

- Metrics: A realistic 10-day launch dataset including metrics such as signup conversion, DAU / WAU, D1 retention, crash rate, p95 latency, payment success rate, support ticket volume, feature adoption, churn

- User Feedback: A set of short feedback entries including positive comments, neutral comments, negative comments, repeated complaint themes, a few severe outliers

- Release Notes / Known Issues: A short rollout note describing, the feature change, rollout plan, success criteria, known risks, rollback options

- Threshold Rules: A compact YAML config defining pause thresholds, rollback thresholds, and metric directionality

## Setup
#### Requirements
- Python 3.12+
- ```uv``` recommended
#### Install dependencies
```bash
uv sync --dev
```

If you prefer pip:
```bash
python -n venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```
## Running the Project 
#### Run tests
```bash
uv run pytest
```
#### Run the full simulation
```bash
uv run python -m src.main
```
#### if you wanna use explicit paths
```bash
uv run python -m src.main \
  --metrics data/metrics.csv \
  --feedback data/feedback.jsonl \
  --release-notes data/release_notes.md \
  --thresholds data/thresholds.yaml
```
## Output Files
After a successful run, the following files are generated in ```outputs/```:
- ```final_decision.json```
- ```trace.json```
- ```trace.jsonl```
- ```tool_outputs.json```
- ```agent_outputs.json```

The final output contains sections such as; final_decision.json, trace.json, trace.jsonl, tool_outputs.json, agent_outputs.json

## Traceability
Traceability is implementted through ```src/tracing.py```: Each record has a unique run_id, step names, start/end events, status, timing and summary metadata.

## Environment Variables
No env variables are required for the current version
an example is included in ```.env.example``` for future extensions with llm based agents.

## Running the UI
A small Streamlit UI is included:
```bash
uv run streamlit run ui/app.py
```
The ui lets you:
- view the final decision
- ispect agent stances
- inspect the final json output
- inspect the execution trace

## Future improvements
- LLM backed agents behind Ollama/OpenAI provider layer
- richer anomaly detection
- YAML export
- Improved UI

