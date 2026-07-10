"""
Candidate comparison — Side-by-side comparison of all scored candidates.
"""

import streamlit as st
from src.shared import generate_comparison_data, safe_rerun

st.title(":material/compare_arrows: Candidate comparison")
st.caption("Compare candidates side-by-side across all evaluation criteria")

if not st.session_state.scorecards:
    st.info("No scored candidates available. Score candidates on the scoring page first.", icon=":material/info:")
else:
    # Generate comparison data
    comparison = generate_comparison_data(st.session_state.scorecards)

    # -------------------------------------------------------------------
    # Visual comparison: Bar chart
    # -------------------------------------------------------------------
    st.subheader(":material/bar_chart: Overall score comparison")

    chart_data = {
        "Candidate": [c["name"] for c in comparison],
        "Weighted score": [c["weighted_total"] for c in comparison],
    }
    st.bar_chart(chart_data, x="Candidate", y="Weighted score", use_container_width=True)

    st.divider()

    # -------------------------------------------------------------------
    # Per-criterion radar-style comparison
    # -------------------------------------------------------------------
    st.subheader(":material/tune: Per-criterion breakdown")

    # Collect all criteria names
    criteria_names = []
    if comparison:
        for key in comparison[0]:
            if key.startswith("score_"):
                criteria_names.append(key.replace("score_", ""))

    # Display as columns of metrics
    cols = st.columns(len(criteria_names))
    for i, criterion in enumerate(criteria_names):
        with cols[i]:
            st.markdown(f"**{criterion}**")
            for c in comparison:
                score_key = f"score_{criterion}"
                score = c.get(score_key, 0)
                st.markdown(f"- {c['name']}: **{score}/5**")

    st.divider()

    # -------------------------------------------------------------------
    # Side-by-side comparison table
    # -------------------------------------------------------------------
    st.subheader(":material/table_chart: Full comparison table")

    # Build table data
    table_data = []
    for c in comparison:
        row = {
            "Candidate": c["name"],
            "Verdict": c["verdict"],
            "Weighted score": c["weighted_total"],
        }
        for criterion in criteria_names:
            score_key = f"score_{criterion}"
            row[criterion] = c.get(score_key, 0)
        table_data.append(row)

    st.dataframe(table_data, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------------------------------------------------
    # Verdict distribution
    # -------------------------------------------------------------------
    st.subheader(":material/pie_chart: Verdict distribution")

    verdict_counts = {}
    for c in comparison:
        v = c["verdict"]
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    col_a, col_b, col_c = st.columns(3)
    verdict_meta = {
        "interview": (col_a, ":green[Interview]", "#1E7A54"),
        "hold": (col_b, ":orange[Hold]", "#8A5A10"),
        "not_a_fit": (col_c, ":red[Not a fit]", "#A13048"),
    }

    for verdict, (col, label, color) in verdict_meta.items():
        with col:
            count = verdict_counts.get(verdict, 0)
            st.metric(label=label, value=count)

    st.divider()

    # -------------------------------------------------------------------
    # Strengths and weaknesses summary
    # -------------------------------------------------------------------
    st.subheader(":material/insights: Key insights")

    if comparison:
        best = comparison[0]
        worst = comparison[-1]
        st.markdown(f":material/trending_up: **Strongest candidate:** {best['name']} ({best['weighted_total']}/5)")
        st.markdown(f":material/trending_down: **Weakest candidate:** {worst['name']} ({worst['weighted_total']}/5)")

        # Highlight top-scoring criterion for each
        st.markdown("**Per-candidate strengths:**")
        for c in comparison[:3]:  # Top 3
            scores = [(crit, c.get(f"score_{crit}", 0)) for crit in criteria_names]
            best_crit = max(scores, key=lambda x: x[1])
            st.markdown(f"- {c['name']}: strongest in **{best_crit[0]}** ({best_crit[1]}/5)")