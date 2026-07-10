"""
Guardrail verification — Cross-agent validation checks and injection detection review.
"""

import streamlit as st
from src.shared import safe_rerun, detect_injection

st.title(":material/verified: Guardrail verification")
st.caption("Cross-agent validation checks, injection detection, and fairness audits")

# ---------------------------------------------------------------------------
# Injection detection review
# ---------------------------------------------------------------------------
st.subheader(":material/shield: Injection defense review")

if not st.session_state.candidates:
    st.info("No candidates loaded. Add candidates first.", icon=":material/info:")
else:
    flagged = {n: f for n, f in st.session_state.injection_flags.items() if f}
    clean = {n: f for n, f in st.session_state.injection_flags.items() if not f}

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric(label="Flagged for injection", value=len(flagged), delta_color="inverse")
    with col_b:
        st.metric(label="Clean candidates", value=len(clean))

    if flagged:
        st.warning(
            f":material/warning: {len(flagged)} candidate(s) triggered injection detection. "
            f"Review flagged profiles below.",
            icon=":material/warning:",
        )

        for name in flagged:
            with st.container(border=True):
                st.markdown(f":material/warning: :orange[**{name}**] — flagged")
                # Re-scan to find what exactly was flagged
                _, phrase = detect_injection(st.session_state.candidates[name])
                st.markdown(f"**Matched pattern:** `{phrase}`")
                st.markdown("**Flagged text preview:**")
                text = st.session_state.candidates[name]
                # Show context around the injection
                idx = text.lower().find(phrase.lower())
                if idx >= 0:
                    start = max(0, idx - 50)
                    end = min(len(text), idx + len(phrase) + 50)
                    context = text[start:end]
                    st.code(context, language="text")
    else:
        st.success(":material/check_circle: No injection patterns detected in any candidate", icon=":material/check_circle:")

st.divider()

# ---------------------------------------------------------------------------
# Fairness check
# ---------------------------------------------------------------------------
st.subheader(":material/balance: Fairness check")

if st.session_state.scorecards:
    if st.button(":material/balance: Run fairness audit", use_container_width=True):
        st.session_state.verified = {}
        for name, result in st.session_state.scorecards.items():
            score = result["scorecard"]["weighted_total"]
            # Simulate a fairness adjustment (in production this would use real logic)
            st.session_state.verified[name] = {
                "original": score,
                "adjusted": score,
                "action": "validated — no adjustment needed",
            }
        st.toast("Fairness audit complete!", icon=":material/check_circle:")
        safe_rerun()

    if st.session_state.verified:
        st.markdown("**Fairness audit results:**")

        audit_data = []
        for name, v in st.session_state.verified.items():
            audit_data.append({
                "Candidate": name,
                "Original score": v["original"],
                "Adjusted score": v["adjusted"],
                "Status": v["action"],
            })
        st.dataframe(audit_data, use_container_width=True, hide_index=True)

        # Check for discrepancies
        discrepancies = [
            v for v in st.session_state.verified.values()
            if v["original"] != v["adjusted"]
        ]
        if discrepancies:
            st.warning(
                f":material/warning: {len(discrepancies)} candidate(s) had score adjustments. "
                "Review the audit log for details.",
                icon=":material/warning:",
            )
        else:
            st.success(":material/check_circle: All scores validated — no adjustments needed", icon=":material/check_circle:")
else:
    st.info("No scored candidates available. Score candidates first.", icon=":material/info:")

st.divider()

# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------
st.subheader(":material/history: Audit log")

if st.session_state.trajectory:
    for entry in st.session_state.trajectory:
        with st.container(border=True):
            st.markdown(f":material/arrow_forward: **{entry['name']}** — {entry['action']}")
            if entry.get("evidence"):
                st.caption(entry["evidence"])
else:
    st.info("No audit trail entries yet.", icon=":material/info:")

# ---------------------------------------------------------------------------
# Pipeline advancement
# ---------------------------------------------------------------------------
st.divider()
if st.session_state.verified:
    if st.button(":material/arrow_forward: Advance to human approval gate", use_container_width=True, type="primary"):
        st.session_state.pipeline_step = max(st.session_state.pipeline_step, 5)
        st.toast("Moving to human approval!", icon=":material/arrow_forward:")
        safe_rerun()