"""
Dashboard — Overview of the recruitment pipeline with KPIs and quick actions.
"""

import streamlit as st
from datetime import datetime
from src.shared import (
    SAMPLE_CANDIDATES, detect_injection, looks_like_resume, has_missing_fields,
    parse_resume, score_with_rubric, verdict_from_score, check_availability,
    propose_interview, safe_rerun
)

st.title(":material/dashboard: Dashboard")
st.caption("Overview of your recruitment pipeline at a glance")

# ---------------------------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    total = len(st.session_state.candidates)
    st.metric(
        label="Candidates loaded",
        value=total,
        delta=None,
        help="Total candidates in the pipeline",
    )

with col2:
    scored = len(st.session_state.scorecards)
    delta_val = f"{round(scored/total*100)}%" if total > 0 else None
    st.metric(
        label="Candidates scored",
        value=scored,
        delta=delta_val,
        help="Candidates that have been evaluated",
    )

with col3:
    interview = sum(
        1 for r in st.session_state.scorecards.values()
        if r.get("verdict") == "interview"
    )
    st.metric(
        label="Interview recommendations",
        value=interview,
        help="Candidates recommended for interview",
    )

with col4:
    approved = sum(1 for v in st.session_state.approvals.values() if v)
    st.metric(
        label="Approved for interview",
        value=approved,
        help="Candidates approved by human gate",
    )

# ---------------------------------------------------------------------------
# Pipeline status
# ---------------------------------------------------------------------------
st.subheader(":material/account_tree: Pipeline progress")

steps = [
    ("Candidate intake", len(st.session_state.candidates) > 0),
    ("Resume parsing", len(st.session_state.profiles) > 0),
    ("Scoring & evaluation", len(st.session_state.scorecards) > 0),
    ("Guardrail verification", len(st.session_state.verified) > 0),
    ("Human approval", sum(1 for v in st.session_state.approvals.values() if v) > 0),
]

for step_name, completed in steps:
    if completed:
        st.markdown(f":material/check_circle: :green[**{step_name}**] — complete")
    else:
        st.markdown(f":material/radio_button_unchecked: **{step_name}** — pending")

# ---------------------------------------------------------------------------
# Quick actions
# ---------------------------------------------------------------------------
st.subheader(":material/bolt: Quick actions")

col_a, col_b, col_c = st.columns(3)

with col_a:
    if st.button(":material/person_add: Load sample candidates", use_container_width=True):
        for name, text in SAMPLE_CANDIDATES.items():
            st.session_state.candidates[name] = text
            inj, _ = detect_injection(text)
            st.session_state.injection_flags[name] = inj
        st.toast("Sample candidates loaded!", icon=":material/check_circle:")
        safe_rerun()

with col_b:
    if st.button(
        ":material/bar_chart: Score all candidates",
        use_container_width=True,
        disabled=len(st.session_state.profiles) == 0,
    ):
        st.session_state.scorecards = {}
        st.session_state.trajectory = []
        for name, profile in st.session_state.profiles.items():
            sc = score_with_rubric(profile["raw_text"], st.session_state.rubric)
            verdict = verdict_from_score(sc["weighted_total"])
            st.session_state.scorecards[name] = {"scorecard": sc, "verdict": verdict}
        st.toast("All candidates scored!", icon=":material/check_circle:")
        safe_rerun()

with col_c:
    if st.button(":material/refresh: Reset pipeline", use_container_width=True, type="primary"):
        for key in ["candidates", "profiles", "scorecards", "verified", "approvals",
                     "trajectory", "injection_flags", "pipeline_errors"]:
            if key in ["candidates", "profiles", "scorecards", "verified", "approvals"]:
                st.session_state[key] = {}
            elif key in ["trajectory", "pipeline_errors"]:
                st.session_state[key] = []
            elif key == "injection_flags":
                st.session_state[key] = {}
        st.session_state.pipeline_step = 1
        st.toast("Pipeline reset!", icon=":material/refresh:")
        safe_rerun()

# ---------------------------------------------------------------------------
# Run full pipeline (proper agent workflow: validate → parse → score → verify → gate)
# ---------------------------------------------------------------------------
st.divider()
st.subheader(":material/play_circle: Automated pipeline")

col_run, col_status = st.columns([1, 2])

with col_run:
    if st.button(
        ":material/rocket_launch: Run full pipeline",
        use_container_width=True,
        type="primary",
        help="Load samples → validate → parse → score → verify → propose (human gate always blocks)",
    ):
        # Reset pipeline state
        st.session_state.profiles = {}
        st.session_state.scorecards = {}
        st.session_state.verified = {}
        st.session_state.approvals = {}
        st.session_state.trajectory = []
        st.session_state.pipeline_errors = []
        step = 0

        # ---- Step 1: Load sample candidates if none exist ----
        if not st.session_state.candidates:
            for name, text in SAMPLE_CANDIDATES.items():
                st.session_state.candidates[name] = text
                inj, _ = detect_injection(text)
                st.session_state.injection_flags[name] = inj

        for name, text in list(st.session_state.candidates.items()):
            candidate_trajectory = []
            _step_counter = [step]  # mutable container for closure

            def log(thought, action, args, observation):
                _step_counter[0] += 1
                s = _step_counter[0]
                candidate_trajectory.append({
                    "step": s,
                    "candidate": name,
                    "thought": thought,
                    "action": action,
                    "observation": observation,
                })
                st.session_state.trajectory.append({
                    "name": name,
                    "action": action or thought,
                    "evidence": str(observation),
                })

            # ---- Gate 0: Validate input (is this resume-shaped?) ----
            if not looks_like_resume(text):
                log(
                    "Check whether input looks like a resume.",
                    "validate_input",
                    {"candidate": name},
                    "Not resume-shaped — rejecting before parsing.",
                )
                st.session_state.pipeline_errors.append({
                    "candidate": name,
                    "stage": "validate_input",
                    "error": "Input does not contain resume-like content.",
                })
                continue

            log(
                "Validate input looks like a resume.",
                "validate_input",
                {"candidate": name},
                "Looks like a resume, proceeding.",
            )

            # ---- Step 2: Parse resume ----
            profile = parse_resume(name, text)
            log(
                "Parse resume into structured fields.",
                "parse_resume",
                {"candidate": name},
                f"Parsed. injection_detected={profile['injection_detected']}, "
                f"skills={len(profile.get('skills', []))} found",
            )
            st.session_state.profiles[name] = profile

            # ---- Gate 3: Check required fields ----
            if has_missing_fields(text):
                log(
                    "Check required fields are present.",
                    None,
                    None,
                    "Skills/projects marked not provided — rejecting for retry.",
                )
                st.session_state.pipeline_errors.append({
                    "candidate": name,
                    "stage": "field_validation",
                    "error": "Missing required fields (skills/projects) — cannot score.",
                })
                continue

            # ---- Step 4: Score against rubric ----
            scorecard = score_with_rubric(text, st.session_state.rubric)
            tentative_verdict = verdict_from_score(scorecard["weighted_total"])
            log(
                "Score candidate against rubric.",
                "score_candidate",
                {"candidate": name},
                f"Weighted total: {scorecard['weighted_total']}, verdict: {tentative_verdict}",
            )

            # ---- Step 5: Verify (double-check scoring) ----
            verdict = tentative_verdict
            escalated = False

            if tentative_verdict in ("interview", "hold"):
                # Re-score to verify consistency
                v2 = score_with_rubric(text, st.session_state.rubric)
                v2_total = v2["weighted_total"]
                log(
                    "Double-check score before recommending an action.",
                    "verify_candidate",
                    {"candidate": name},
                    f"Verifier total: {v2_total} vs primary: {scorecard['weighted_total']}",
                )
                if abs(v2_total - scorecard["weighted_total"]) > 1.0:
                    escalated = True
                    verdict = "human_escalation"
                    st.session_state.pipeline_errors.append({
                        "candidate": name,
                        "stage": "verification",
                        "error": f"Score discrepancy: primary={scorecard['weighted_total']}, "
                                 f"verifier={v2_total}",
                    })

            # Record scorecard
            st.session_state.scorecards[name] = {
                "scorecard": scorecard,
                "verdict": verdict,
                "injection_detected": profile["injection_detected"],
                "escalated": escalated,
            }

            # ---- Step 6: Verify injection ----
            st.session_state.verified[name] = {
                "original": scorecard["weighted_total"],
                "adjusted": scorecard["weighted_total"],
                "action": "validated — no adjustment needed",
                "injection_detected": profile["injection_detected"],
                "injection_phrase": profile.get("injection_phrase"),
            }

            # ---- Step 7: For interview candidates — check availability but BLOCK (human gate) ----
            if verdict == "interview":
                slots = check_availability(name)
                log(
                    "Check interview availability.",
                    "check_availability",
                    {"candidate": name},
                    f"Slots: {slots}",
                )
                # Gate: propose but NEVER auto-approve — governance requirement
                proposal = propose_interview(name, slots[0], approved=False)
                log(
                    "Propose interview slot — hold for human approval (gate).",
                    "propose_interview",
                    {"candidate": name, "approved": False},
                    str(proposal),
                )

        # Update pipeline step
        st.session_state.pipeline_step = 5
        errors = st.session_state.pipeline_errors
        if errors:
            st.toast(
                f"Pipeline completed with {len(errors)} error(s). Check 'Recent activity'.",
                icon=":material/warning:",
            )
        else:
            st.toast("Full pipeline complete!", icon=":material/check_circle:")
        safe_rerun()

with col_status:
    st.info(
        "Runs the full agent workflow: validate_input → parse_resume → score_candidate "
        "→ verify_candidate → check_availability → propose_interview. "
        "The human approval gate ALWAYS blocks interview proposals — no auto-approvals.",
        icon=":material/info:",
    )

# ---------------------------------------------------------------------------
# Pipeline errors
# ---------------------------------------------------------------------------
if st.session_state.get("pipeline_errors"):
    st.divider()
    st.subheader(":material/warning: Pipeline errors")
    for err in st.session_state.pipeline_errors:
        with st.container(border=True):
            st.markdown(f":material/error: :orange[**{err['candidate']}**] — {err['stage']}")
            st.caption(err["error"])

# ---------------------------------------------------------------------------
# Recent activity
# ---------------------------------------------------------------------------
st.subheader(":material/history: Recent activity")

if st.session_state.trajectory:
    for entry in st.session_state.trajectory[-8:]:
        st.markdown(
            f"- :material/arrow_forward: **{entry['name']}** — "
            f"{entry['action']} ({entry.get('evidence', '')})"
        )
else:
    st.info("No activity yet. Start by loading candidates.", icon=":material/info:")