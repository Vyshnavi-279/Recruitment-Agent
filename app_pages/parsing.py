"""
Resume parsing — Parse candidate resumes into structured profiles.
"""

import streamlit as st
from src.shared import parse_resume, safe_rerun

st.title(":material/description: Resume parsing")
st.caption("Parse candidate resumes into structured profiles for evaluation")

# ---------------------------------------------------------------------------
# Parse action
# ---------------------------------------------------------------------------
if not st.session_state.candidates:
    st.info("No candidates loaded. Go to the intake page to add candidates first.", icon=":material/info:")
else:
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f":material/person: **{len(st.session_state.candidates)}** candidate(s) loaded and ready for parsing")

    with col2:
        if st.button(":material/description: Parse all profiles", use_container_width=True, type="primary"):
            st.session_state.profiles = {}
            for name, text in st.session_state.candidates.items():
                st.session_state.profiles[name] = parse_resume(name, text)
            st.toast("All profiles parsed!", icon=":material/check_circle:")
            safe_rerun()

    st.divider()

    # -----------------------------------------------------------------------
    # Parsing results
    # -----------------------------------------------------------------------
    if st.session_state.profiles:
        st.subheader(":material/dataset: Parsed profiles")

        for name, p in st.session_state.profiles.items():
            with st.expander(f":material/person: {name}", expanded=True):
                # Education
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Education:** {p['education'] if p['education'] else 'Not specified'}")

                with col_b:
                    st.markdown(f"**Skills detected:** {', '.join(p['skills']) if p['skills'] else 'None detected'}")

                # Evidence lines
                if p["evidence_lines"]:
                    st.markdown("**Key evidence:**")
                    for line in p["evidence_lines"]:
                        st.markdown(f"- {line}")

                # Injection flag
                if p["injection_detected"]:
                    st.error(
                        f":material/warning: Prompt injection detected! "
                        f"Flagged phrase: **{p['injection_phrase']}**",
                        icon=":material/error:",
                    )
                else:
                    st.success(":material/check_circle: No injection patterns detected")

                # Raw text preview
                with st.expander(":material/code: View raw text", icon=":material/code:"):
                    st.code(p["raw_text"], language="text")

    else:
        st.warning("Profiles not yet parsed. Click 'Parse all profiles' above.", icon=":material/warning:")

# ---------------------------------------------------------------------------
# Pipeline advancement
# ---------------------------------------------------------------------------
st.divider()
if st.session_state.profiles:
    if st.button(":material/arrow_forward: Advance to scoring", use_container_width=True, type="primary"):
        st.session_state.pipeline_step = max(st.session_state.pipeline_step, 3)
        st.toast("Moving to scoring phase!", icon=":material/arrow_forward:")
        safe_rerun()