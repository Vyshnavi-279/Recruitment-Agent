# TechVest Recruitment Agent

An autonomous recruitment agent that takes a job description and a set of candidate résumés, and — in one run — parses, scores, ranks, and produces an **auditable shortlist**, complete with a full reasoning trace and safety guardrails.

Built for the GenAI & Agentic AI Engineering programme, Day 6 Afternoon Lab (TechVest scenario).

---

## What it does

Unlike a simple retrieve-then-generate chatbot, this is a genuine **agent**: it plans its own next step, chooses which tool to call and in what order, holds state across all three candidates, and finishes with a decision it can defend with evidence — not just a bare recommendation.

- Parses each candidate's résumé into structured fields
- Scores every candidate against a weighted, JD-derived rubric — every score is backed by cited evidence, not vibes
- Ranks candidates into **Interview / Hold / Not a Fit**
- Checks interview availability and proposes a slot for shortlisted candidates
- Logs a full **thought → action → observation** trajectory for every step, so any decision can be reconstructed and explained later
- Enforces safety guardrails before any consequential action is taken

---

## Guardrails

| Guardrail | What it does |
|---|---|
| **Human-in-the-loop gate** | `propose_interview` never fires without explicit human approval — the agent proposes, a person confirms |
| **Step / iteration cap** | Hard limit on agent loop steps so a misbehaving run can't loop forever |
| **Prompt-injection defense** | Résumé text is treated as untrusted data. One candidate's résumé deliberately contains a hidden instruction attempting to manipulate the ranking — the agent detects and ignores it |
| **Fairness check** | An automated name-swap test confirms two identical résumés score the same regardless of candidate name |
| **Decision audit log** | The full trajectory and final decision are persisted and downloadable as JSON, so any shortlist can be reconstructed later |

---

## Tech stack

- **UI:** Streamlit, with a custom-themed interface (frosted-glass cards, soft floating 3D orb accents, animated gradient background)
- **Logic:** Pure Python — rubric-based scoring with keyword-evidence matching, no external LLM API required to run out of the box
- **Data:** One job description (Junior AI Engineer) and three candidate résumés designed to span a strong fit, a borderline fit, and a weak fit for the role

---

## Getting started

```bash
git clone https://github.com/Vyshnavi-279/Recruitment-Agent.git
cd Recruitment-Agent
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`).

## Using the app

1. Click **Run Agent** — it parses, scores, and ranks all three candidates in one pass.
2. **Shortlist tab** — see each candidate's verdict, weighted score, per-criterion breakdown, and cited justification. For shortlisted candidates, click **Approve & Schedule** to confirm an interview slot (nothing is booked until you do).
3. **Trajectory & Guardrails tab** — inspect the full step-by-step reasoning trace, the injection-detection result, the fairness check, and download the complete decision audit log as JSON.

---

## Project structure

```
Recruitment-Agent/
├── app.py                 # Streamlit app — UI, agent loop, tools, guardrails
├── requirements.txt
├── .env.example            # placeholder for API config (no real keys committed)
└── README.md
```

---

## Notes

- `.env` (if you add real API keys for an LLM-backed version) is gitignored — never commit real credentials. `.env.example` should only ever contain placeholders.
- This build satisfies the lab's "Done by 3:00" checklist: autonomous tool ordering (no hard-coded pipeline), cited evidence per candidate, full logged trajectory, a human-approval gate on the scheduling action, and a passing fairness check.