"""
Candidate intake — Upload resumes, load samples, and manage the candidate queue.
"""

import streamlit as st
from src.shared import (
    SAMPLE_CANDIDATES, detect_injection, extract_text_from_pdf, safe_rerun
)

st.title(":material/person_add: Candidate intake")
st.caption("Load candidate profiles into the pipeline for evaluation")

# ---------------------------------------------------------------------------
# Upload section
# ---------------------------------------------------------------------------
st.subheader(":material/upload_file: Upload resumes")

uploaded = st.file_uploader(
    "Upload resume files (.pdf, .txt)",
    type=["pdf", "txt"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded:
    if st.button(":material/description: Process uploaded files", use_container_width=True):
        for f in uploaded:
            name = f.name.rsplit(".", 1)[0]
            if f.type == "application/pdf":
                text = extract_text_from_pdf(f)
            else:
                text = f.read().decode("utf-8", errors="ignore").strip()
            if text:
                st.session_state.candidates[name] = text
                inj, _ = detect_injection(text)
                st.session_state.injection_flags[name] = inj
        st.toast(f"Processed {len(uploaded)} file(s)!", icon=":material/check_circle:")
        safe_rerun()

st.divider()

# ---------------------------------------------------------------------------
# Sample / manual input
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader(":material/dataset: Sample profiles")
    st.caption("Load pre-built demo candidates for testing")

    if st.button(":material/person: Load 3 sample candidates", use_container_width=True, type="primary"):
        for name, text in SAMPLE_CANDIDATES.items():
            st.session_state.candidates[name] = text
            inj, _ = detect_injection(text)
            st.session_state.injection_flags[name] = inj
        st.toast("Sample candidates loaded!", icon=":material/check_circle:")
        safe_rerun()

with col2:
    st.subheader(":material/edit_note: Manual entry")
    st.caption("Paste resume text directly")

    manual_name = st.text_input("Candidate name", placeholder="e.g. John Doe", key="manual_name")
    manual_text = st.text_area("Resume text", placeholder="Paste the full resume text here...", height=150, key="manual_text")

    if st.button(":material/save: Add candidate", use_container_width=True, disabled=not (manual_name and manual_text)):
        st.session_state.candidates[manual_name] = manual_text
        inj, _ = detect_injection(manual_text)
        st.session_state.injection_flags[manual_name] = inj
        st.toast(f"Added {manual_name}!", icon=":material/check_circle:")
        safe_rerun()

st.divider()

# ---------------------------------------------------------------------------
# Candidate queue management
# ---------------------------------------------------------------------------
st.subheader(":material/queue: Candidate queue")

if not st.session_state.candidates:
    st.info("No candidates loaded yet. Upload files, load samples, or enter text manually.", icon=":material/info:")
else:
    # Sort candidates by injection flag (flagged first)
    sorted_names = sorted(
        st.session_state.candidates.keys(),
        key=lambda n: (0 if st.session_state.injection_flags.get(n) else 1, n),
    )

    for name in sorted_names:
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([4, 1, 1])

            with col_a:
                flag = st.session_state.injection_flags.get(name)
                if flag:
                    st.markdown(f":material/warning: :orange[**{name}**] — potential injection detected")
                else:
                    st.markdown(f":material/person: **{name}**")

                # Show preview
                text = st.session_state.candidates[name]
                preview = text[:200] + "..." if len(text) > 200 else text
                st.caption(preview)

            with col_b:
                if st.button(":material/visibility: View", key=f"view_{name}"):
                    st.session_state[f"view_{name}"] = not st.session_state.get(f"view_{name}", False)

            with col_c:
                if st.button(":material/delete: Remove", key=f"del_{name}"):
                    del st.session_state.candidates[name]
                    if name in st.session_state.profiles:
                        del st.session_state.profiles[name]
                    if name in st.session_state.scorecards:
                        del st.session_state.scorecards[name]
                    if name in st.session_state.verified:
                        del st.session_state.verified[name]
                    if name in st.session_state.approvals:
                        del st.session_state.approvals[name]
                    if name in st.session_state.injection_flags:
                        del st.session_state.injection_flags[name]
                    st.toast(f"Removed {name}", icon=":material/delete:")
                    safe_rerun()

            # Expanded view
            if st.session_state.get(f"view_{name}", False):
                st.markdown("**Full text:**")
                st.code(text, language="text")

    # Pipeline advancement
    st.divider()
    if st.button(":material/arrow_forward: Advance to resume parsing", use_container_width=True, type="primary"):
        st.session_state.pipeline_step = max(st.session_state.pipeline_step, 2)
        st.toast("Moving to parsing phase!", icon=":material/arrow_forward:")
        safe_rerun()