"""
Analytics & reports — Pipeline metrics, export capabilities, and insights.
"""

import streamlit as st
from datetime import datetime
from src.shared import safe_rerun, generate_export_csv, generate_comparison_data

st.title(":material/analytics: Analytics & reports")
st.caption("Pipeline metrics, data export, and performance insights")

# ---------------------------------------------------------------------------
# Pipeline metrics
# ---------------------------------------------------------------------------
st.subheader(":material/query_stats: Pipeline metrics")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    candidates_total = len(st.session_state.candidates)
    st.metric(label="Total candidates", value=candidates_total)

with col_b:
    profiles_parsed = len(st.session_state.profiles)
    parse_rate = round(profiles_parsed / candidates_total * 100) if candidates_total > 0 else 0
    st.metric(label="Profiles parsed", value=profiles_parsed, delta=f"{parse_rate}%")

with col_c:
    scored = len(st.session_state.scorecards)
    score_rate = round(scored / profiles_parsed * 100) if profiles_parsed > 0 else 0
    st.metric(label="Candidates scored", value=scored, delta=f"{score_rate}%")

with col_d:
    approved = sum(1 for v in st.session_state.approvals.values() if v)
    st.metric(label="Approved", value=approved)

st.divider()

# ---------------------------------------------------------------------------
# Verdict distribution chart
# ---------------------------------------------------------------------------
st.subheader(":material/pie_chart: Verdict distribution")

if st.session_state.scorecards:
    verdicts = {"interview": 0, "hold": 0, "not_a_fit": 0}
    for result in st.session_state.scorecards.values():
        v = result["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1

    chart_data = {
        "Verdict": list(verdicts.keys()),
        "Count": list(verdicts.values()),
    }
    st.bar_chart(chart_data, x="Verdict", y="Count", use_container_width=True)

    # Show as metrics too
    col_i, col_h, col_n = st.columns(3)
    with col_i:
        st.metric(
            label=":green[Interview]",
            value=verdicts.get("interview", 0),
            delta=f"{round(verdicts.get('interview', 0)/scored*100)}%" if scored > 0 else None,
        )
    with col_h:
        st.metric(
            label=":orange[Hold]",
            value=verdicts.get("hold", 0),
            delta=f"{round(verdicts.get('hold', 0)/scored*100)}%" if scored > 0 else None,
        )
    with col_n:
        st.metric(
            label=":red[Not a fit]",
            value=verdicts.get("not_a_fit", 0),
            delta=f"{round(verdicts.get('not_a_fit', 0)/scored*100)}%" if scored > 0 else None,
        )
else:
    st.info("No scoring data available yet.", icon=":material/info:")

st.divider()

# ---------------------------------------------------------------------------
# Injection detection stats
# ---------------------------------------------------------------------------
st.subheader(":material/shield: Guardrail statistics")

if st.session_state.injection_flags:
    total_checked = len(st.session_state.injection_flags)
    flagged = sum(1 for f in st.session_state.injection_flags.values() if f)
    clean = total_checked - flagged

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.metric(label="Injection checks performed", value=total_checked)
    with col_f2:
        st.metric(label="Injection attempts detected", value=flagged, delta_color="inverse")

    if flagged > 0:
        st.warning(
            f":material/warning: {flagged} out of {total_checked} candidates flagged "
            f"for prompt injection. Guardrails active.",
            icon=":material/warning:",
        )
    else:
        st.success(":material/check_circle: No injection attempts detected. Guardrails operating normally.", icon=":material/check_circle:")
else:
    st.info("No injection checks performed yet.", icon=":material/info:")

st.divider()

# ---------------------------------------------------------------------------
# Performance timing
# ---------------------------------------------------------------------------
st.subheader(":material/schedule: Session activity")

if st.session_state.trajectory:
    st.markdown(f"**Total pipeline actions:** {len(st.session_state.trajectory)}")
    st.markdown("**Action breakdown:**")

    action_counts = {}
    for t in st.session_state.trajectory:
        action = t.get("action", "Unknown")
        action_counts[action] = action_counts.get(action, 0) + 1

    action_data = {
        "Action": list(action_counts.keys()),
        "Count": list(action_counts.values()),
    }
    st.bar_chart(action_data, x="Action", y="Count", use_container_width=True)

    st.divider()
    with st.expander(":material/history: Full activity log", icon=":material/history:"):
        for i, entry in enumerate(st.session_state.trajectory):
            st.markdown(f"**{i+1}.** {entry['name']} — {entry['action']}")
            if entry.get("evidence"):
                st.caption(f"   {entry['evidence']}")
else:
    st.info("No activity recorded yet.", icon=":material/info:")

st.divider()

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
st.subheader(":material/download: Export data")

if st.session_state.scorecards:
    col_e1, col_e2 = st.columns(2)

    with col_e1:
        csv_data = generate_export_csv(st.session_state.scorecards)
        st.download_button(
            label=":material/table_chart: Download scoring report (CSV)",
            data=csv_data,
            file_name=f"scoring_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_e2:
        # JSON export
        export_json = {
            "generated_at": datetime.now().isoformat(),
            "candidates": list(st.session_state.candidates.keys()),
            "scorecards": {
                name: {
                    "score": result["scorecard"]["weighted_total"],
                    "verdict": result["verdict"],
                    "per_criterion": result["scorecard"]["per_criterion"],
                }
                for name, result in st.session_state.scorecards.items()
            },
            "approvals": st.session_state.approvals,
        }
        import json
        json_str = json.dumps(export_json, indent=2)
        st.download_button(
            label=":material/code: Download JSON export",
            data=json_str,
            file_name=f"recruitment_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )
else:
    st.info("No data to export yet. Score candidates first.", icon=":material/info:")