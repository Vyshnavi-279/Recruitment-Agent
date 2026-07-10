"""
Scoring & evaluation — Score candidates against the rubric and view results.
"""

import streamlit as st
from src.shared import score_candidate, verdict_from_score, safe_rerun

st.title(":material/bar_chart: Scoring & evaluation")
st.caption("Score candidates against the evaluation rubric with detailed breakdowns")

# ---------------------------------------------------------------------------
# Scoring action
# ---------------------------------------------------------------------------
if not st.session_state.profiles:
    st.info("No parsed profiles available. Go to the parsing page first.", icon=":material/info:")
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        scored_count = len(st.session_state.scorecards)
        total_count = len(st.session_state.profiles)
        st.markdown(f":material/person: **{scored_count}/{total_count}** candidates scored")

    with col2:
        if st.button(":material/bar_chart: Score all candidates", use_container_width=True, type="primary"):
            st.session_state.scorecards = {}
            st.session_state.trajectory = []
            for name, profile in st.session_state.profiles.items():
                sc = score_candidate(profile, st.session_state.rubric)
                verdict = verdict_from_score(sc["weighted_total"])
                st.session_state.scorecards[name] = {"scorecard": sc, "verdict": verdict}
                st.session_state.trajectory.append({
                    "name": name,
                    "action": "Calculated score evaluation",
                    "evidence": f"Total fit metric value: {sc['weighted_total']}",
                })
            st.toast("All candidates scored!", icon=":material/check_circle:")
            safe_rerun()

    st.divider()

    # -----------------------------------------------------------------------
    # Rubric display
    # -----------------------------------------------------------------------
    with st.expander(":material/tune: View evaluation rubric", icon=":material/tune:"):
        st.markdown("**Current rubric criteria and weights:**")
        for crit in st.session_state.rubric:
            st.markdown(f"- **{crit['name']}** (weight: {crit['weight']})")
            st.caption(f"  Keywords: {', '.join(crit['keywords'])}")

    # -----------------------------------------------------------------------
    # Results
    # -----------------------------------------------------------------------
    if st.session_state.scorecards:
        st.subheader(":material/leaderboard: Scoring results")

        # Sort by score descending
        sorted_results = sorted(
            st.session_state.scorecards.items(),
            key=lambda x: x[1]["scorecard"]["weighted_total"],
            reverse=True,
        )

        for name, result in sorted_results:
            sc = result["scorecard"]
            verdict = result["verdict"]

            # Color-code the verdict
            if verdict == "interview":
                verdict_display = f":green-badge[**{verdict}**]"
                border_color = "#1E7A54"
            elif verdict == "hold":
                verdict_display = f":orange-badge[**{verdict}**]"
                border_color = "#8A5A10"
            else:
                verdict_display = f":red-badge[**{verdict}**]"
                border_color = "#A13048"

            with st.container(border=True):
                col_meta, col_score = st.columns([3, 1])
                with col_meta:
                    st.markdown(f"**{name}** — {verdict_display}")
                with col_score:
                    st.markdown(
                        f"<div style='text-align: right; font-size: 1.5rem; "
                        f"font-weight: 700; color: {border_color};'>"
                        f"{sc['weighted_total']} / 5</div>",
                        unsafe_allow_html=True,
                    )

                # Per-criterion breakdown
                st.markdown("**Criterion breakdown:**")
                for criterion, score in sc["per_criterion"].items():
                    evidence_text = sc["evidence"].get(criterion, "")
                    # Show score as a progress bar
                    st.markdown(f"**{criterion}** — {score}/5")
                    st.progress(score / 5, text=evidence_text)

                # Evidence
                with st.expander(":material/description: View evidence details", icon=":material/description:"):
                    for criterion, ev in sc["evidence"].items():
                        st.markdown(f"- **{criterion}:** {ev}")

                # Trajectory
                trajectory_entries = [
                    t for t in st.session_state.trajectory if t["name"] == name
                ]
                if trajectory_entries:
                    with st.expander(":material/history: Evaluation trajectory", icon=":material/history:"):
                        for t in trajectory_entries:
                            st.markdown(f"- {t['action']}: {t.get('evidence', '')}")

        # Summary table
        st.divider()
        st.subheader(":material/table_chart: Summary comparison")

        summary_data = []
        for name, result in sorted_results:
            sc = result["scorecard"]
            summary_data.append({
                "Candidate": name,
                "Verdict": result["verdict"],
                "Weighted score": sc["weighted_total"],
            })

        st.dataframe(summary_data, use_container_width=True, hide_index=True)

    else:
        st.warning("No scores yet. Click 'Score all candidates' above.", icon=":material/warning:")

# ---------------------------------------------------------------------------
# Pipeline advancement
# ---------------------------------------------------------------------------
st.divider()
if st.session_state.scorecards:
    if st.button(":material/arrow_forward: Advance to verification", use_container_width=True, type="primary"):
        st.session_state.pipeline_step = max(st.session_state.pipeline_step, 4)
        st.toast("Moving to verification phase!", icon=":material/arrow_forward:")
        safe_rerun()