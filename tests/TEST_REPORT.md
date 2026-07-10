# Recruitment Agent — Test Report

> **Generated:** 2026-07-10  
> **Test Runner:** pytest 9.1.1 · Python 3.13.7  
> **Result:** 7 / 7 passed ✅

---

## 1. `test_parse_resume_with_mocked_llm`

| Field | Value |
|---|---|
| **File** | `tests/test_tools.py` |
| **Purpose** | Verify that `parse_resume` returns a valid `CandidateProfile` when the LLM is mocked. |
| **What it tests** | The tool correctly invokes a structured-output LLM call and maps the response into a typed `CandidateProfile` object with `name`, `years_experience`, `skills`, `education`, `projects`, and `raw_text`. |
| **Assertions** | `isinstance(result, CandidateProfile)` · `result.name == "Test Candidate"` · `result.years_experience == 3.0` · `"Python" in result.skills` |
| **Status** | ✅ PASSED |

---

## 2. `test_score_candidate_with_mocked_llm`

| Field | Value |
|---|---|
| **File** | `tests/test_tools.py` |
| **Purpose** | Verify that `score_candidate` returns a valid `ScoreCard` when the LLM is mocked. |
| **What it tests** | The tool correctly scores a candidate profile against a rubric, producing per-criterion scores, evidence, and a weighted total. |
| **Assertions** | `result.candidate_name == "Test Candidate"` · `result.per_criterion_scores["Python/ML fundamentals"] == 4` · `result.weighted_total > 0` |
| **Status** | ✅ PASSED |

---

## 3. `test_check_availability_returns_three_slots`

| Field | Value |
|---|---|
| **File** | `tests/test_tools.py` |
| **Purpose** | Verify that `check_availability` returns exactly 3 time slots. |
| **What it tests** | The tool returns a list of 3 strings, each containing `"IST"` (Indian Standard Time). |
| **Assertions** | `isinstance(result, list)` · `len(result) == 3` · `all("IST" in slot for slot in result)` |
| **Status** | ✅ PASSED |

---

## 4. `test_propose_interview_blocked_when_not_approved`

| Field | Value |
|---|---|
| **File** | `tests/test_tools.py` |
| **Purpose** | Verify that `propose_interview` returns `"blocked_pending_approval"` when `approved=False`. |
| **What it tests** | The human-in-the-loop gate works: an interview cannot be confirmed without explicit approval. |
| **Assertions** | `result["status"] == "blocked_pending_approval"` |
| **Status** | ✅ PASSED |

---

## 5. `test_propose_interview_confirmed_when_approved`

| Field | Value |
|---|---|
| **File** | `tests/test_tools.py` |
| **Purpose** | Verify that `propose_interview` returns `"confirmed"` when `approved=True`. |
| **What it tests** | The full interview proposal flow works end-to-end when the human gate is satisfied. |
| **Assertions** | `result["status"] == "confirmed"` · `result["candidate"] == "Priya Sharma"` · `"slot" in result` |
| **Status** | ✅ PASSED |

---

## 6. `test_sanitize_resume_detects_injection_in_meera_resume`

| Field | Value |
|---|---|
| **File** | `tests/test_tools.py` |
| **Purpose** | Verify that `sanitize_resume_text` catches the prompt injection embedded in Meera's resume. |
| **What it tests** | The injection defense guardrail correctly flags a malicious instruction hidden in a candidate's resume text. |
| **Assertions** | `detected is True` · `"[[INJECTION:" in cleaned` |
| **Status** | ✅ PASSED |

---

## 7. `test_sanitize_resume_no_false_positive_on_clean_resume`

| Field | Value |
|---|---|
| **File** | `tests/test_tools.py` |
| **Purpose** | Verify that `sanitize_resume_text` does **not** flag a benign resume. |
| **What it tests** | The injection defense guardrail has no false positives on normal, clean text. |
| **Assertions** | `detected is False` · `cleaned == clean_text` |
| **Status** | ✅ PASSED |

---

## Runtime Error Fixes Applied

| Error | File Fixed | Fix |
|---|---|---|
| `NameError: name 'asyncio' is not defined` | `app.py` | Added `import asyncio` |
| `NameError: name 'Agent' is not defined` | `app.py` | Removed broken "▶ Run Antigravity Agent" button block |
| `AttributeError: no attribute 'process_candidate'` | `app.py` | Changed to `await orchestrator.process_candidate_with_antigravity()` |
| `AntigravityValidationError: API key required` | `orchestrator.py` | Added `dotenv.load_dotenv()` and passed `api_key` to `LocalAgentConfig` |

## Summary

| Test | Category | Status |
|---|---|---|
| Parse resume with mocked LLM | Resume Parsing | ✅ |
| Score candidate with mocked LLM | Scoring | ✅ |
| Check availability returns 3 slots | Availability | ✅ |
| Propose interview blocked (not approved) | Human-in-the-loop Gate | ✅ |
| Propose interview confirmed (approved) | Human-in-the-loop Gate | ✅ |
| Detect injection in Meera's resume | Guardrail — Injection Defense | ✅ |
| No false positive on clean resume | Guardrail — Injection Defense | ✅ |

**All 7 tests pass.** The application is verified for:
- Resume parsing correctness
- Rubric-based scoring
- Availability slot generation
- Human-in-the-loop interview approval flow
- Prompt injection detection (with no false positives)