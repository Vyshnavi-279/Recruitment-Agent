"""
Human approval gate — Review and approve/reject candidates for interview scheduling.
"""

import streamlit as st
from src.shared import safe_rerun, verdict_from_score, check_availability, propose_interview

st.title(":material/approval: Human approval gate")
st.caption("Review candidates and approve or reject interview scheduling")

if not st.session_state.scorecards:
    st.info("No scored candidates available. Complete the scoring phase first.", icon=":material/info:")
else:
    st.subheader(":material/rate_review: Candidate review queue")

    # Sort: unscored/candidates needing approval first
    pending = [
        name for name in st.session_state.scorecards
        if not st.session_state.approvals.get(name, False)
    ]
    approved_list = [
        name for name in st.session_state.scorecards
        if st.session_state.approvals.get(name, False)
    ]

    if pending:
        st.markdown(f":material/pending: **{len(pending)}** candidate(s) pending review")

        for name in pending:
            result = st.session_state.scorecards[name]
            sc = result["scorecard"]
            verdict = result["verdict"]

            if verdict == "interview":
                verdict_color = "green"
            elif verdict == "hold":
                verdict_color = "orange"
            else:
                verdict_color = "red"

            with st.container(border=True):
                col_info, col_action = st.columns([3, 1])

                with col_info:
                    st.markdown(f"**:{verdict_color}[{name}]** — verdict: :{verdict_color}-badge[**{verdict}**]")
                    st.markdown(f"Weighted score: **{sc['weighted_total']}** / 5")

                    # Show per-criterion scores
                    for criterion, score in sc["per_criterion"].items():
                        st.markdown(f"- {criterion}: {score}/5")
                        st.progress(score / 5)

                    # Propose interview slots for interview candidates
                    if verdict == "interview" and sc["weighted_total"] >= 3.2:
                        slots = check_availability(name)
                        st.markdown(f"**Available slots:** {', '.join(s for s in slots)}")

                with col_action:
                    if st.button(
                        f":material/check_circle: Approve {name}",
                        key=f"approve_{name}",
                        use_container_width=True,
                        type="primary",
                    ):
                        st.session_state.approvals[name] = True

                        # Propose interview
                        slot = check_availability(name)[0]
                        proposal = propose_interview(name, slot, approved=True)
                        st.session_state.trajectory.append({
                            "name": name,
                            "action": "Approved for interview",
                            "evidence": f"Slot proposed: {slot} — {proposal['status']}",
                        })
                        st.toast(f"{name} approved for interview!", icon=":material/check_circle:")
                        safe_rerun()

                    if st.button(
                        f":material/block: Reject {name}",
                        key=f"reject_{name}",
                        use_container_width=True,
                    ):
                        st.session_state.approvals[name] = False
                        st.session_state.trajectory.append({
                            "name": name,
                            "action": "Rejected by human gate",
                            "evidence": "Candidate not approved for interview",
                        })
                        st.toast(f"{name} rejected.", icon=":material/cancel:")
                        safe_rerun()

    else:
        st.success(":material/check_circle: All candidates reviewed!", icon=":material/check_circle:")

    # -------------------------------------------------------------------
    # Approved candidates
    # -------------------------------------------------------------------
    if approved_list:
        st.divider()
        st.subheader(":material/check_circle: Approved candidates")

        for name in approved_list:
            result = st.session_state.scorecards[name]
            sc = result["scorecard"]
            with st.container(border=True):
                st.markdown(f":material/person_check: **{name}** — score: **{sc['weighted_total']}** / 5")
                st.markdown(f":material/calendar_today: Approved for interview scheduling")

                if st.button(
                    f":material/undo: Revoke approval for {name}",
                    key=f"revoke_{name}",
                    use_container_width=True,
                ):
                    st.session_state.approvals[name] = False
                    st.toast(f"Approval revoked for {name}", icon=":material/undo:")
                    safe_rerun()

    # -------------------------------------------------------------------
    # Bulk actions
    # -------------------------------------------------------------------
    st.divider()
    st.subheader(":material/tune: Bulk actions")

    col_bulk_a, col_bulk_b, col_bulk_c = st.columns(3)

    with col_bulk_a:
        if st.button(":material/check_circle: Approve all interview recommendations", use_container_width=True):
            for name, result in st.session_state.scorecards.items():
                if result["verdict"] == "interview" and not st.session_state.approvals.get(name, False):
                    st.session_state.approvals[name] = True
            st.toast("All interview recommendations approved!", icon=":material/check_circle:")
            safe_rerun()

    with col_bulk_b:
        if st.button(":material/refresh: Reset all approvals", use_container_width=True):
            st.session_state.approvals = {}
            st.toast("All approvals reset!", icon=":material/refresh:")
            safe_rerun()

    with col_bulk_c:
        if st.button(":material/download: Export approval report", use_container_width=True):
            import csv, io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Candidate", "Score", "Verdict", "Approved"])
            for name, result in st.session_state.scorecards.items():
                writer.writerow([
                    name,
                    result["scorecard"]["weighted_total"],
                    result["verdict"],
                    "Yes" if st.session_state.approvals.get(name) else "No",
                ])
            st.download_button(
                label=":material/download: Download CSV",
                data=output.getvalue(),
                file_name="approval_report.csv",
                mime="text/csv",
                use_container_width=True,
            )