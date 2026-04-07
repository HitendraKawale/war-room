from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import yaml

from src.data_loader import load_feedback, load_metrics, load_text, load_yaml
from src.orchestrator import WarRoomOrchestrator
from src.state import WarRoomState


st.set_page_config(page_title="PurpleMerit War Room", layout="wide")

st.title("PurpleMerit War Room")
st.caption("Multi-agent launch decision simulator")

with st.sidebar:
    st.header("Inputs")
    metrics_path = st.text_input("Metrics CSV", value="data/metrics.csv")
    feedback_path = st.text_input("Feedback JSONL", value="data/feedback.jsonl")
    release_notes_path = st.text_input("Release Notes", value="data/release_notes.md")
    thresholds_path = st.text_input("Thresholds YAML", value="data/thresholds.yaml")
    output_dir = st.text_input("Output directory", value="outputs")
    run_button = st.button("Run Simulation", type="primary")

if run_button:
    metrics = load_metrics(metrics_path)
    feedback = load_feedback(feedback_path)
    release_notes = load_text(release_notes_path)
    thresholds = load_yaml(thresholds_path)

    state: WarRoomState = {
        "metrics": metrics,
        "feedback": feedback,
        "release_notes": release_notes,
        "thresholds": thresholds,
        "trace": [],
        "errors": [],
    }

    result = WarRoomOrchestrator().run(state)
    final_output = result["final_output"]
    agent_outputs = result["agent_outputs"]
    trace = result["trace"]

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ui_final_decision.json").write_text(
        json.dumps(final_output, indent=2),
        encoding="utf-8",
    )
    (out_dir / "ui_final_decision.yaml").write_text(
        yaml.safe_dump(final_output, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    st.subheader("Decision")
    c1, c2, c3 = st.columns(3)
    c1.metric("Decision", final_output["decision"])
    c2.metric("Confidence", final_output["confidence"])
    c3.metric("Risks", len(final_output["risk_register"]))

    st.subheader("Agent Stances")
    stance_rows = []
    for name, output in agent_outputs.items():
        if "stance" in output:
            stance_rows.append(
                {
                    "agent": name,
                    "stance": output["stance"],
                    "confidence": output["confidence"],
                }
            )
        else:
            stance_rows.append(
                {
                    "agent": name,
                    "stance": output["draft_decision"],
                    "confidence": output["confidence"],
                }
            )
    st.dataframe(stance_rows, use_container_width=True)

    left, right = st.columns(2)

    with left:
        st.subheader("Final JSON")
        st.json(final_output)

    with right:
        st.subheader("Trace")
        st.dataframe(trace, use_container_width=True)

    st.subheader("YAML Preview")
    st.code(
        yaml.safe_dump(final_output, sort_keys=False, allow_unicode=True),
        language="yaml",
    )

    st.success("Simulation completed and outputs saved.")
