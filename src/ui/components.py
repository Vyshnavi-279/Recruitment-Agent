"""Reusable Streamlit render functions for the recruitment agent UI."""

import streamlit as st
from src.schemas import Decision

GUARDRAIL_LABELS = {
    "step_cap": ("Step Cap", "active"),
    "human_gate": ("Human Gate", "pending"),
    "injection_defense": ("Injection Defense", "pending"),
    "fairness": ("Fairness Check", "pending"),
}


def render_guardrail_pill(name: str, status: str) -> None:
    """Render a small colored guardrail status pill."""
    label, _ = GUARDRAIL_LABELS.get(name, (name, "pending"))
    st.markdown(
        f'<span class="guardrail-pill {status}">{label}: {status}</span>',
        unsafe_allow_html=True,
    )


def render_candidate_card(decision: Decision, on_approve=None) -> None:
    """Render a candidate card with verdict badge, scores, and optional approve button."""
    verdict_class = decision.verdict.replace("_", "-")
    card_html = f"""
    <div class="candidate-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3>{decision.candidate_name}</h3>
            <span class="verdict-badge {verdict_class}">{decision.verdict}</span>
        </div>
        <p><strong>Weighted Score:</strong> {decision.scorecard.weighted_total:.2f}</p>
        <p><strong>Justification:</strong> {decision.justification}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Per-criterion scores
    criteria_df = {
        "Criterion": list(decision.scorecard.per_criterion_scores.keys()),
        "Score": list(decision.scorecard.per_criterion_scores.values()),
        "Evidence": [
            decision.scorecard.evidence.get(c, "")
            for c in decision.scorecard.per_criterion_scores.keys()
        ],
    }
    st.dataframe(criteria_df, use_container_width=True, hide_index=True)

    # Approve button for interview-verdict candidates
    if decision.verdict == "interview" and on_approve is not None:
        proposed = decision.proposed_slot
        if proposed:
            st.write(f"**Proposed Slot:** {proposed}")
            if st.button(
                f"✓ Approve & Schedule — {decision.candidate_name}",
                key=f"approve_{decision.candidate_name}",
            ):
                on_approve(decision.candidate_name, proposed)


def render_trajectory_step(step, idx: int, highlight: bool = False) -> None:
    """Render a single expandable trajectory step."""
    header_class = "injection-step" if highlight else ""
    with st.expander(f"Step {step.step_number}: {step.action or 'thought'}", expanded=False):
        if step.thought:
            st.markdown(f"**Thought:** {step.thought}")
        if step.action:
            st.markdown(f"**Action:** `{step.action}`")
        if step.action_input:
            st.json(step.action_input)
        if step.observation:
            st.markdown(f"**Observation:**")
            st.code(step.observation, language="json")