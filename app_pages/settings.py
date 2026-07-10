"""
Settings — Configure job description, rubric, and pipeline preferences.
"""

import json
import streamlit as st
from src.shared import JOB_DESCRIPTION, RUBRIC, safe_rerun

st.title(":material/settings: Settings")
st.caption("Configure pipeline settings, job description, and evaluation rubric")

# ---------------------------------------------------------------------------
# Job description
# ---------------------------------------------------------------------------
st.subheader(":material/description: Job description")

with st.expander(":material/edit: Edit job description", expanded=False):
    jd = st.text_area(
        "Job description text",
        value=st.session_state.job_description,
        height=200,
        key="jd_editor",
        label_visibility="collapsed",
    )
    if st.button(":material/save: Update job description", use_container_width=True):
        st.session_state.job_description = jd
        st.toast("Job description updated!", icon=":material/check_circle:")
        safe_rerun()

st.markdown("**Current job description:**")
st.markdown(st.session_state.job_description)

st.divider()

# ---------------------------------------------------------------------------
# Rubric configuration
# ---------------------------------------------------------------------------
st.subheader(":material/tune: Evaluation rubric")

with st.expander(":material/edit: Edit rubric criteria", expanded=False):
    st.caption("Each criterion has a name, weight (should sum to 1.0), and keywords for matching.")

    current_rubric = st.session_state.rubric
    updated_rubric = []

    for i, crit in enumerate(current_rubric):
        st.markdown(f"**Criterion {i + 1}**")
        col_n, col_w = st.columns([3, 1])
        with col_n:
            name = st.text_input("Name", value=crit["name"], key=f"crit_name_{i}")
        with col_w:
            weight = st.number_input(
                "Weight",
                min_value=0.0,
                max_value=1.0,
                value=crit["weight"],
                step=0.05,
                key=f"crit_weight_{i}",
                format="%.2f",
            )
        keywords = st.text_input(
            "Keywords (comma-separated)",
            value=", ".join(crit["keywords"]),
            key=f"crit_kw_{i}",
        )
        updated_rubric.append({
            "name": name,
            "weight": weight,
            "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
        })

    if st.button(":material/save: Update rubric", use_container_width=True):
        st.session_state.rubric = updated_rubric
        st.toast("Rubric updated!", icon=":material/check_circle:")
        safe_rerun()

# Display current rubric
if st.session_state.rubric:
    st.markdown("**Current rubric:**")
    total_weight = sum(c["weight"] for c in st.session_state.rubric)
    for crit in st.session_state.rubric:
        st.markdown(f"- **{crit['name']}** (weight: {crit['weight']})")
        st.caption(f"  Keywords: {', '.join(crit['keywords'])}")

    if total_weight != 1.0:
        st.warning(
            f":material/warning: Rubric weights sum to {total_weight:.2f}. "
            f"They should sum to 1.0 for accurate scoring.",
            icon=":material/warning:",
        )
    else:
        st.success(":material/check_circle: Rubric weights correctly sum to 1.0", icon=":material/check_circle:")

st.divider()

# ---------------------------------------------------------------------------
# Pipeline management
# ---------------------------------------------------------------------------
st.subheader(":material/settings: Pipeline management")

col_p1, col_p2 = st.columns(2)

with col_p1:
    current_step = st.number_input(
        "Current pipeline step",
        min_value=1,
        max_value=5,
        value=st.session_state.pipeline_step,
        step=1,
    )
    if st.button(":material/save: Update pipeline step", use_container_width=True):
        st.session_state.pipeline_step = current_step
        st.toast(f"Pipeline set to step {current_step}", icon=":material/check_circle:")
        safe_rerun()

with col_p2:
    if st.button(":material/refresh: Reset all data", use_container_width=True, type="primary"):
        for key in ["candidates", "profiles", "scorecards", "verified", "approvals",
                     "trajectory", "injection_flags"]:
            if key in ["candidates", "profiles", "scorecards", "verified", "approvals"]:
                st.session_state[key] = {}
            elif key == "trajectory":
                st.session_state[key] = []
            elif key == "injection_flags":
                st.session_state[key] = {}
        st.session_state.pipeline_step = 1
        st.toast("All data reset!", icon=":material/refresh:")
        safe_rerun()

st.divider()

# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------
st.subheader(":material/info: About")

st.markdown("""
**TechVest AI Recruitment Suite** v2.0

A comprehensive multi-agent recruitment pipeline powered by:
- :material/shield: Prompt injection detection
- :material/tune: Multi-criteria scoring rubric
- :material/balance: Fairness checks
- :material/verified: Guardrail verification
- :material/approval: Human-in-the-loop approval gate

Built with Streamlit and deployed as a single-page multi-module application.
""")