# TechVest Recruitment Agent — Specification

**Version:** 1.0  
**Date:** 2026-07-14  
**Context:** GenAI & Agentic AI Engineering Programme — Day 6 Afternoon Lab

---

## 1. Purpose

The TechVest Recruitment Agent is an autonomous evaluation system that takes a job description and a set of candidate résumés and — in a single run — parses, scores, ranks, and produces an auditable shortlist. Every decision is backed by cited evidence and a full reasoning trace, making the process explainable and reproducible.

The system operates as a genuine agent: it plans its own step sequence, decides which tool to call and in what order, and maintains shared state across all candidates throughout the run.

---

## 2. Scope

| In scope | Out of scope |
|---|---|
| Résumé parsing and structured extraction | External HR system integrations |
| Rubric-based scoring with cited evidence | Calendar/email booking APIs |
| Candidate ranking and verdict assignment | Authentication and multi-user access |
| Interview slot checking and proposal | Real-time LLM streaming UI |
| Human approval gate for scheduling | Bulk résumé file upload beyond three candidates |
| Prompt-injection detection and neutralisation | Persistent database storage |
| Automated fairness check | Multi-role or multi-JD support |
| Full trajectory audit log | |

---

## 3. Functional Requirements

### 3.1 Résumé Intake

- The system accepts résumé text for each candidate (pre-loaded sample data or user-supplied upload).
- PDF uploads are supported; text is extracted before processing.
- Each résumé is treated strictly as untrusted data — embedded instructions must never influence agent behaviour.

### 3.2 Résumé Parsing (`parse_resume`)

- Extracts structured fields from raw résumé text: `name`, `years_experience`, `skills`, `education`, `projects`, `raw_text`.
- Returns a `CandidateProfile` (Pydantic v2 model).
- The parser prompt explicitly instructs the LLM to ignore any instructions embedded in the résumé text.

### 3.3 Candidate Scoring (`score_candidate`)

- Scores each `CandidateProfile` against a four-criterion rubric (see §4).
- Each criterion receives an integer score 0–5 with a mandatory evidence string citing text from the résumé.
- A weighted total is computed: `Σ (score_i × weight_i)`.
- Returns a `ScoreCard` (Pydantic v2 model).

### 3.4 Availability Check (`check_availability`)

- Accepts `candidate_name` and `week` parameters.
- Returns a list of available time slot strings.
- Current implementation: mock/hardcoded slots. Designed to be replaced with a real calendar API.

### 3.5 Interview Proposal (`propose_interview`)

- Accepts `candidate_name`, `slot`, and `approved` (bool, default `False`).
- When `approved=False`: returns `{"status": "blocked_pending_approval"}` — scheduling is deferred to human approval.
- When `approved=True`: returns `{"status": "confirmed", "candidate": …, "slot": …}`.
- The proposal action is **never** auto-confirmed; human approval is always required before confirmation.

### 3.6 Ranking and Verdicts

Verdicts are assigned based on weighted total score:

| Score range | Verdict |
|---|---|
| ≥ 3.2 | `interview` |
| 1.8 – 3.19 | `hold` |
| < 1.8 | `not_a_fit` |

Each verdict is accompanied by a `justification` string and the full `ScoreCard`.

### 3.7 Agent Orchestration

- The agent runs as a LangGraph `StateGraph` with three nodes: `agent_node`, `tool_node`, `schedule_node`.
- `agent_node` builds a prompt from current state and invokes the LLM to decide the next tool call.
- `tool_node` executes the chosen tool, records the observation, and routes back to `agent_node` (or to `schedule_node` if `propose_interview` triggers the human-gate).
- `schedule_node` parks state pending human approval and routes to `END`.
- A `MemorySaver` checkpointer enables pause/resume across the human-in-the-loop approval step.
- A hard step cap prevents infinite loops (checked in `agent_node` via `step_count`).

### 3.8 Streamlit UI

The application exposes a multi-page Streamlit interface:

| Page | Purpose |
|---|---|
| **Dashboard / Run Agent** | Trigger a full agent run; view progress and live trajectory |
| **Intake** | Upload or edit résumé text; view raw input |
| **Parsing** | View extracted `CandidateProfile` fields per candidate |
| **Scoring** | Per-criterion scores, evidence, and weighted totals |
| **Comparison** | Side-by-side candidate comparison table |
| **Human Gate** | Approve or reject interview proposals for shortlisted candidates |
| **Verification / Analytics** | Fairness check result, injection detection result, score distributions |
| **Settings** | Configuration options |

The app uses a claymorphic-glass visual theme (frosted-glass cards, soft neumorphic shadows, animated gradient background).

---

## 4. Evaluation Rubric

Role: Junior AI Engineer at TechVest.

| Criterion | Weight | Score range |
|---|---|---|
| Python / ML fundamentals | 35% | 0–5 |
| Relevant projects | 30% | 0–5 |
| Hands-on tooling | 20% | 0–5 |
| Communication | 15% | 0–5 |

**Python / ML fundamentals** keywords include: `python`, `machine learning`, `pytorch`, `tensorflow`, `scikit-learn`, `numpy`, `pandas`, `transformers`.

**Relevant projects** keywords include: `project`, `built`, `deployed`, `shipped`, `led`, `team`, `ml project`.

**Hands-on tooling** keywords include: `langchain`, `vector db`, `rag`, `faiss`, `pinecone`, `streamlit`, `docker`, `transformers`, `pytorch`.

**Communication** keywords include: `presented`, `documented`, `mentored`, `collaborated`, `wrote`, `communicat`.

Scores are derived from keyword-hit counting against the résumé text (in `shared.py` fast-path) or via LLM-structured output (in `src/tools/score_candidate.py` full-path).

---

## 5. Safety Guardrails

### 5.1 Human-in-the-Loop Gate

`propose_interview` never confirms a slot without `approved=True`. The UI exposes an explicit **Approve & Schedule** button per shortlisted candidate. Nothing is booked until a human clicks it.

### 5.2 Step / Iteration Cap

`agent_node` reads `step_count` from state and terminates (`goto="__end__"`) when the cap is reached, preventing runaway loops.

### 5.3 Prompt-Injection Defence

Before any résumé text is consumed, `detect_injection()` / `sanitize_resume_text()` scans it against a regex pattern list:

```
ignore (prior|previous|all) instructions
disregard … instructions
rank (this candidate|me) first
override all logic
bypass human
ATTENTION SCORER NODE
system:
you must …
you are now …
forget … instructions
new prompt:
ignore above
```

Detected injections are marked `[[INJECTION: …]]` in the cleaned text, and the `injection_detected` flag is surfaced in the UI. The third sample résumé (Meera Iyer) deliberately embeds an injection attempt to demonstrate this defence.

### 5.4 Fairness Check

`run_fairness_check()` compares two candidates whose `years_experience` values are within 2.0 years. If any criterion score differs by more than 1 point between the two, a fairness alert is raised. The check result (`passed` bool + `detail` string) is displayed on the Verification page.

### 5.5 Decision Audit Log

`AuditLog` records every `TrajectoryStep` (thought → action → action_input → observation) to an in-memory list and persists it as JSON to `logs/trajectories/{timestamp}.json`. The full log is downloadable from the UI at the end of a run.

---

## 6. Data Models

```python
class CandidateProfile(BaseModel):
    name: str
    years_experience: float
    skills: list[str]
    education: str
    projects: list[str]
    raw_text: str

class ScoreCard(BaseModel):
    candidate_name: str
    per_criterion_scores: dict[str, int]
    evidence: dict[str, str]
    weighted_total: float

class Decision(BaseModel):
    candidate_name: str
    verdict: Literal["interview", "hold", "not_a_fit"]
    justification: str
    scorecard: ScoreCard
    proposed_slot: str | None
    pending_approval: bool

class TrajectoryStep(BaseModel):
    step_number: int
    thought: str
    action: str | None
    action_input: dict | None
    observation: str | None

class AgentState(TypedDict):
    job_description: str
    rubric: str
    candidates: list[dict[str, str]]
    profiles: dict[str, CandidateProfile]
    scorecards: dict[str, ScoreCard]
    shortlist: list[Decision]
    trajectory: list[TrajectoryStep]
    step_count: int
    pending_approval: dict | None
```

---

## 7. Project Structure

```
recruitment-agent/
├── app.py                        # Streamlit entry point — full self-contained app
├── orchestrator.py               # LangGraph-based orchestrator (standalone runner)
├── requirements.txt
├── .env.example                  # Placeholder env config — no real keys
├── spec.md                       # This document
├── README.md
│
├── src/
│   ├── shared.py                 # Core logic shared across pages (pure Python)
│   ├── schemas.py                # Pydantic v2 data models
│   ├── rubric.py                 # Rubric definition (RubricCriterion list)
│   ├── config.py                 # Configuration constants (placeholder)
│   │
│   ├── data/
│   │   ├── job_description.py    # JD text constant
│   │   └── candidates.py        # Three sample résumés
│   │
│   ├── agent/
│   │   ├── graph.py              # LangGraph StateGraph builder
│   │   ├── nodes.py              # agent_node, tool_node, schedule_node
│   │   └── state.py              # AgentState TypedDict
│   │
│   ├── tools/
│   │   ├── parse_resume.py       # @tool: LLM-backed résumé parser
│   │   ├── score_candidate.py    # @tool: LLM-backed rubric scorer
│   │   ├── check_availability.py # @tool: mock availability checker
│   │   └── propose_interview.py  # @tool: human-gated interview proposal
│   │
│   ├── guardrails/
│   │   ├── injection_defense.py  # sanitize_resume_text(), detect_injection()
│   │   ├── fairness_check.py     # run_fairness_check()
│   │   └── audit_log.py          # AuditLog class
│   │
│   └── ui/
│       ├── components.py         # Reusable Streamlit component helpers
│       └── theme.css             # Custom CSS (claymorphic-glass theme)
│
├── app_pages/
│   ├── intake.py
│   ├── parsing.py
│   ├── scoring.py
│   ├── comparison.py
│   ├── human_gate.py
│   ├── verification.py
│   ├── analytics.py
│   ├── dashboard.py
│   └── settings.py
│
├── tests/
│   ├── test_tools.py             # pytest unit tests for core tools
│   ├── eval_dataset.json         # Eval dataset for automated assessment
│   └── TEST_REPORT.md            # Manual test run results
│
└── logs/
    └── trajectories/             # JSON audit logs, one file per run
```

---

## 8. Sample Candidates

Three candidates are pre-loaded to span the scoring spectrum:

| Candidate | Expected Verdict | Notes |
|---|---|---|
| **Priya Nair** | Interview | Strong fit — Python/PyTorch, RAG chatbot, LangChain/FAISS, team lead |
| **Rahul Verma** | Hold | Borderline — foundational Python/ML, coursework projects, no LLM tooling |
| **Meera Iyer** | Not a Fit | Weak fit — frontend/Java focus, no ML projects, contains injection attempt |

---

## 9. Dependencies

| Package | Purpose |
|---|---|
| `streamlit>=1.38.0` | Web UI |
| `langgraph>=0.2.0` | Agent state graph and checkpointing |
| `langchain-core>=0.3.0` | Tool abstraction (`@tool` decorator) |
| `langchain-anthropic>=0.2.0` | Claude LLM integration |
| `anthropic>=0.34.0` | Anthropic API client |
| `pydantic>=2.7.0` | Data models and structured LLM output |
| `python-dotenv>=1.0.0` | Environment variable loading |
| `pypdf` | PDF résumé text extraction |

The application runs without a real API key using its built-in keyword-scoring path (`shared.py`). The LangGraph/Anthropic path activates when `ANTHROPIC_API_KEY` is set in `.env`.

---

## 10. Configuration

Copy `.env.example` to `.env` and populate as needed:

```
ANTHROPIC_API_KEY=sk-ant-...   # Required only for LLM-backed tool path
```

Never commit `.env` with real keys. `.gitignore` excludes it by default.

---

## 11. Running the Application

```bash
# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Launch
streamlit run app.py
```

Open `http://localhost:8501` in a browser.

To run the test suite:

```bash
pytest tests/
```

---

## 12. Constraints and Design Decisions

- **No external LLM required for basic operation.** The keyword-scoring path in `shared.py` runs entirely offline; the LangGraph graph in `src/agent/` activates only when an Anthropic API key is present.
- **Résumé text is always untrusted.** Injection scanning runs before any text reaches the scoring logic.
- **Human approval is non-negotiable.** `propose_interview` is designed so `approved=False` is the safe default; there is no code path that auto-confirms a slot.
- **Scores are evidence-backed, not vibes.** Every per-criterion score must include a citation string. The LLM prompt enforces this; the data model (`ScoreCard.evidence`) makes it structural.
- **Fairness is checked, not assumed.** The name-swap / experience-parity test runs automatically at the end of every agent run and its result is surfaced alongside the shortlist.
