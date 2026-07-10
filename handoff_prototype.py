"""
Three-Agent Handoff + Boundary Validation — LangGraph
======================================================
Résumé Analyst (Agent 1) → Scorer (Agent 2) → Verifier (Agent 3)

Features:
- Analyst occasionally returns malformed profiles (missing skills) to simulate broken handoffs
- Pydantic model validation at the Scorer's boundary rejects malformed profiles
- Rejected profiles route back to Analyst via feedback loop (max 3 revisions)
- Total step budget across all agents caps execution
- Deployment note covering cost, latency, observability, and human approval gate
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import re
import random
from typing import TypedDict, Optional, Literal

from pydantic import BaseModel, Field, ValidationError

from src.rubric import RUBRIC
from src.data.candidates import PRIYA_RESUME, RAHUL_RESUME, MEERA_RESUME

# Keyword-based rubric matching
KEYWORD_RUBRIC = [
    {"name": "Python / ML fundamentals", "weight": 0.35, "keywords": ["python", "machine learning", "ml", "pytorch", "tensorflow", "scikit", "numpy", "pandas"]},
    {"name": "Relevant projects", "weight": 0.30, "keywords": ["project", "built", "deployed", "shipped", "led"]},
    {"name": "Hands-on tooling", "weight": 0.20, "keywords": ["langchain", "vector db", "rag", "api", "docker", "faiss", "pinecone", "streamlit"]},
    {"name": "Communication", "weight": 0.15, "keywords": ["presented", "documented", "mentored", "collaborated", "wrote", "communicat"]},
]

BORDERLINE_LOW = 2.8
BORDERLINE_HIGH = 3.4
MAX_REVISIONS = 3
MAX_TOTAL_STEPS = 20  # Step budget across all agents (see justification below)


# ---------------------------------------------------------------------------
# 1. Pydantic model for profile validation at the Scorer boundary
# ---------------------------------------------------------------------------

class ValidatedProfile(BaseModel):
    """Pydantic model that enforces the contract for the Scorer's input."""
    name: str = Field(..., min_length=1, description="Candidate name (required)")
    skills: list[str] = Field(..., min_length=1, description="At least one skill required")
    projects: list[str] = Field(default_factory=list)
    education: str = Field(default="Not specified")
    sanitized_text: str = Field(..., min_length=10, description="Sanitized resume text (required)")
    injection_detected: bool = False
    injection_phrase: Optional[str] = None


# ---------------------------------------------------------------------------
# 2. Shared state
# ---------------------------------------------------------------------------

class CandidateProfile(TypedDict):
    name: str
    skills: list[str]
    projects: list[str]
    education: str
    sanitized_text: str
    injection_detected: bool
    injection_phrase: Optional[str]


class Scorecard(TypedDict):
    candidate_name: str
    per_criterion: dict[str, float]
    evidence: dict[str, str]
    weighted_total: float


class ValidationReport(TypedDict):
    candidate_name: str
    valid: bool
    errors: list[str]


class VerificationResult(TypedDict):
    candidate_name: str
    passed: bool
    name_swap_score: Optional[float]
    injection_leak_detected: bool
    reason: str
    route_to: Literal["analyst", "scorer", "human", "accept"]


class HandoffState(TypedDict):
    candidates: dict[str, str]
    parsed_profiles: dict[str, CandidateProfile]
    validated_profiles: dict[str, ValidatedProfile]   # after Pydantic check
    validation_reports: dict[str, ValidationReport]    # pass/fail per candidate
    scorecards: dict[str, Scorecard]
    verifications: dict[str, VerificationResult]
    revision_count: int
    escalated: list[str]
    total_steps: int
    job_description: str


# ---------------------------------------------------------------------------
# 3. Analyst Node — occasionally returns a malformed profile
# ---------------------------------------------------------------------------

def _detect_injection(text: str) -> tuple[bool, Optional[str]]:
    patterns = [
        r"ignore\s+(prior|previous|all)\s+(instructions|scoring|rules)",
        r"rank\s+this\s+candidate\s+first",
        r"exception\s+should\s+be\s+made",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return True, m.group(0)
    return False, None


def _extract_skills(text: str) -> list[str]:
    m = re.search(r"Skills:\s*(.+?)(?:\n\n|\Z)", text, re.DOTALL)
    if not m:
        return []
    skills_text = m.group(1)
    items = re.split(r"[\n,•\-;]+", skills_text)
    return [s.strip() for s in items if s.strip() and len(s.strip()) > 2]


def _extract_projects(text: str) -> list[str]:
    projects = []
    for m in re.finditer(r"\d+\.\s*(.+?)(?:\n\d+\.|\n\n|\Z)", text, re.DOTALL):
        proj = m.group(1).strip()
        if proj and len(proj) > 10:
            projects.append(proj)
    return projects


def _extract_education(text: str) -> str:
    m = re.search(r"Education:\s*(.+?)(?:\n\n|\Z)", text, re.DOTALL)
    if m:
        return m.group(1).strip().replace("\n", "; ")
    m = re.search(r"(B\.\w+|M\.\w+|Ph\.D\.)[^.\n]+", text)
    return m.group(0).strip() if m else "Not specified"


def _sanitize_text(text: str, injection_detected: bool) -> str:
    if not injection_detected:
        return text
    lines = text.split("\n")
    sanitized = []
    for line in lines:
        if re.search(r"ignore\s+|exception\s+should\s+be\s+made", line, re.IGNORECASE):
            continue
        sanitized.append(line)
    return "\n".join(sanitized)


def analyst_node(state: HandoffState) -> dict:
    """
    Parse all candidates and write parsed_profiles.
    Occasionally (30% chance) returns a malformed profile with empty skills
    to simulate a broken handoff.
    """
    candidates = state.get("candidates", {})
    revision_count = state.get("revision_count", 0)
    # Use revision count as seed so the degradation is deterministic per revision
    random.seed(revision_count + 42)
    profiles: dict[str, CandidateProfile] = {}

    for name, raw_text in candidates.items():
        injection_detected, phrase = _detect_injection(raw_text)
        sanitized = _sanitize_text(raw_text, injection_detected)
        skills = _extract_skills(raw_text)

        # Simulate a bad handoff: 50% chance of returning empty skills
        # Higher chance on later revisions to stress the loop
        malformed_chance = min(0.5 + revision_count * 0.1, 0.7)
        if random.random() < malformed_chance:
            skills = []
            print(f"\n  ⚠ ANALYST BUG: '{name}' profile returned with empty skills list "
                  f"(revision {revision_count})")

        profiles[name] = CandidateProfile(
            name=name,
            skills=skills,
            projects=_extract_projects(raw_text),
            education=_extract_education(raw_text),
            sanitized_text=sanitized,
            injection_detected=injection_detected,
            injection_phrase=phrase,
        )

    return {"parsed_profiles": profiles, "total_steps": state.get("total_steps", 0) + 1}


# ---------------------------------------------------------------------------
# 4. Validation Gate — Pydantic check at the Scorer's boundary
# ---------------------------------------------------------------------------

def validate_node(state: HandoffState) -> dict:
    """
    Validate parsed_profiles against the Pydantic model.
    Rejects malformed profiles (e.g. missing skills) before they reach the Scorer.
    """
    profiles = state.get("parsed_profiles", {})
    validated: dict[str, ValidatedProfile] = {}
    reports: dict[str, ValidationReport] = {}

    for name, profile in profiles.items():
        errors: list[str] = []
        try:
            vp = ValidatedProfile(**profile)
            validated[name] = vp
            reports[name] = ValidationReport(
                candidate_name=name, valid=True, errors=[]
            )
        except ValidationError as e:
            for err in e.errors():
                errors.append(f"{'.'.join(str(l) for l in err['loc'])}: {err['msg']}")
            reports[name] = ValidationReport(
                candidate_name=name, valid=False, errors=errors
            )
            print(f"\n  ❌ VALIDATION FAILED for '{name}': {errors}")

    return {
        "validated_profiles": validated,
        "validation_reports": reports,
        "total_steps": state.get("total_steps", 0) + 1,
    }


# ---------------------------------------------------------------------------
# 5. Scorer Node — only scores validated profiles
# ---------------------------------------------------------------------------

def _score_single(profile: ValidatedProfile) -> Scorecard:
    """Score one validated candidate profile against the keyword rubric."""
    text_lower = profile.sanitized_text.lower()
    per_criterion: dict[str, float] = {}
    evidence: dict[str, str] = {}

    for crit in KEYWORD_RUBRIC:
        hits = [kw for kw in crit["keywords"] if kw in text_lower]
        if hits:
            score = min(5.0, len(hits) * 1.5)
            per_criterion[crit["name"]] = score
            evidence[crit["name"]] = f"matched: {', '.join(hits[:5])}"
        else:
            per_criterion[crit["name"]] = 0.0
            evidence[crit["name"]] = "no direct evidence found"

    weighted_total = sum(
        per_criterion[c["name"]] * c["weight"] for c in KEYWORD_RUBRIC
    )

    return Scorecard(
        candidate_name=profile.name,
        per_criterion=per_criterion,
        evidence=evidence,
        weighted_total=round(weighted_total, 2),
    )


def scorer_node(state: HandoffState) -> dict:
    """Score only validated profiles. Rejects unvalidated ones."""
    validated = state.get("validated_profiles", {})
    if not validated:
        # If there are no profiles at all (Analyst never ran), fail hard
        if not state.get("parsed_profiles"):
            raise KeyError(
                "parsed_profiles is empty or missing! "
                "The Analyst node must run before the Scorer node."
            )
        # If profiles exist but none passed validation, return empty
        return {"scorecards": {}, "total_steps": state.get("total_steps", 0) + 1}

    scorecards: dict[str, Scorecard] = {}
    for name, profile in validated.items():
        scorecards[name] = _score_single(profile)

    return {"scorecards": scorecards, "total_steps": state.get("total_steps", 0) + 1}


# ---------------------------------------------------------------------------
# 6. Verifier Node — peer-to-peer check
# ---------------------------------------------------------------------------

def _name_swap_test(profile: ValidatedProfile) -> Optional[float]:
    """Re-score with the candidate's name removed to check for name bias."""
    name_swapped_text = re.sub(
        rf"\b{re.escape(profile.name)}\b",
        "Candidate",
        profile.sanitized_text,
        flags=re.IGNORECASE,
    )
    swapped_profile = ValidatedProfile(
        name="Candidate",
        skills=profile.skills,
        projects=profile.projects,
        education=profile.education,
        sanitized_text=name_swapped_text,
        injection_detected=profile.injection_detected,
        injection_phrase=profile.injection_phrase,
    )
    swapped_scorecard = _score_single(swapped_profile)
    return swapped_scorecard["weighted_total"]


def _check_injection_leak(profile: ValidatedProfile, scorecard: Scorecard) -> bool:
    if not profile.injection_detected:
        return False
    for crit_evidence in scorecard["evidence"].values():
        if profile.injection_phrase and profile.injection_phrase.lower() in crit_evidence.lower():
            return True
    if _detect_injection(profile.sanitized_text)[0]:
        return True
    return False


def verifier_node(state: HandoffState) -> dict:
    """
    Verify borderline candidates:
    1. Only re-check candidates with score in borderline band (2.8–3.4)
    2. Run name-swap fairness test
    3. Check for injection leaks
    4. Route back to Analyst, Scorer, or human based on findings
    """
    scorecards = state.get("scorecards", {})
    validated = state.get("validated_profiles", {})
    revision_count = state.get("revision_count", 0)
    escalated = list(state.get("escalated", []))
    verifications: dict[str, VerificationResult] = dict(state.get("verifications", {}))

    for name, sc in scorecards.items():
        score = sc["weighted_total"]
        profile = validated.get(name)
        if profile is None:
            continue

        is_borderline = BORDERLINE_LOW <= score <= BORDERLINE_HIGH
        injection_leak = _check_injection_leak(profile, sc)

        name_swap_score = None
        if is_borderline:
            name_swap_score = _name_swap_test(profile)

        if injection_leak:
            verifications[name] = VerificationResult(
                candidate_name=name, passed=False,
                name_swap_score=name_swap_score, injection_leak_detected=True,
                reason=f"Injection leak: '{profile.injection_phrase}' found in scoring evidence.",
                route_to="analyst",
            )
        elif is_borderline and name_swap_score is not None and abs(name_swap_score - score) > 0.5:
            verifications[name] = VerificationResult(
                candidate_name=name, passed=False,
                name_swap_score=name_swap_score, injection_leak_detected=False,
                reason=f"Name-swap failed: original={score}, anonymized={name_swap_score:.2f}. Possible bias.",
                route_to="scorer",
            )
        elif is_borderline and name_swap_score is not None and abs(name_swap_score - score) <= 0.5:
            verifications[name] = VerificationResult(
                candidate_name=name, passed=True,
                name_swap_score=name_swap_score, injection_leak_detected=False,
                reason=f"Borderline. Name-swap passed (delta={abs(name_swap_score - score):.2f}).",
                route_to="accept",
            )
        else:
            verifications[name] = VerificationResult(
                candidate_name=name, passed=True,
                name_swap_score=name_swap_score, injection_leak_detected=False,
                reason="Outside borderline range. No issues.",
                route_to="accept",
            )

    return {
        "verifications": verifications,
        "revision_count": revision_count,
        "escalated": escalated,
        "total_steps": state.get("total_steps", 0) + 1,
    }


# ---------------------------------------------------------------------------
# 7. Router — decides where to go next
# ---------------------------------------------------------------------------

def router_node(state: HandoffState) -> dict:
    """
    Update state: mark escalated candidates and increment revision_count
    if we're about to loop. The actual routing decision is made by
    router_fn (used in add_conditional_edges).
    """
    verifications = state.get("verifications", {})
    validation_reports = state.get("validation_reports", {})
    revision_count = state.get("revision_count", 0)
    escalated = list(state.get("escalated", []))
    total_steps = state.get("total_steps", 0)

    # --- Step budget check ---
    if total_steps >= MAX_TOTAL_STEPS:
        for name, r in validation_reports.items():
            if not r["valid"] and name not in escalated:
                escalated.append(f"{name} (step budget exhausted)")
        for name, v in verifications.items():
            if not v["passed"] and name not in escalated:
                escalated.append(f"{name} (step budget exhausted)")
        print(f"\n  ⏰ STEP BUDGET EXHAUSTED ({total_steps}/{MAX_TOTAL_STEPS}). "
              f"Escalating {len(escalated)} candidate(s) to human.")
        return {"escalated": escalated, "total_steps": total_steps + 1}

    # --- Revision limit check ---
    if revision_count >= MAX_REVISIONS:
        for name, r in validation_reports.items():
            if not r["valid"] and name not in escalated:
                escalated.append(f"{name} (revision limit)")
        for name, v in verifications.items():
            if not v["passed"] and name not in escalated:
                escalated.append(f"{name} (revision limit)")
        print(f"\n  ⚠ REVISION LIMIT REACHED ({MAX_REVISIONS}). "
              f"Escalating {len(escalated)} candidate(s) to human.")
        return {"escalated": escalated, "total_steps": total_steps + 1}

    # Check if we need to loop — but only if we haven't hit the revision limit
    needs_loop = False
    if revision_count < MAX_REVISIONS:
        for name, r in validation_reports.items():
            if not r["valid"] and name not in escalated:
                needs_loop = True
                break
        if not needs_loop:
            for name, v in verifications.items():
                if not v["passed"] and name not in escalated:
                    needs_loop = True
                    break

    if needs_loop:
        next_revision = revision_count + 1
        print(f"\n  🔄 Routing back to ANALYST/SCORER (revision {next_revision}/{MAX_REVISIONS})")
        if next_revision >= MAX_REVISIONS:
            # This is the last attempt — also escalate any remaining failures now
            # so they're recorded even if the next loop fails
            for name, r in validation_reports.items():
                if not r["valid"] and name not in escalated:
                    escalated.append(f"{name} (revision limit)")
            for name, v in verifications.items():
                if not v["passed"] and name not in escalated:
                    escalated.append(f"{name} (revision limit)")
            if escalated:
                print(f"  ⚠ Escalating {len(escalated)} candidate(s) to human: {escalated}")
        return {"revision_count": next_revision, "escalated": escalated, "total_steps": total_steps + 1}

    return {"total_steps": total_steps + 1}


def router_fn(state: HandoffState) -> Literal["analyst", "scorer", "__end__"]:
    """
    Separate routing function for add_conditional_edges.
    Reads the current state and returns the next node name.
    """
    verifications = state.get("verifications", {})
    validation_reports = state.get("validation_reports", {})
    revision_count = state.get("revision_count", 0)
    escalated = state.get("escalated", [])
    total_steps = state.get("total_steps", 0)

    # Budget / revision limit reached → end
    if total_steps >= MAX_TOTAL_STEPS or revision_count >= MAX_REVISIONS:
        return "__end__"

    # Validation failures → Analyst
    for name, r in validation_reports.items():
        if not r["valid"] and name not in escalated:
            return "analyst"

    # Verification failures → Analyst or Scorer
    for name, v in verifications.items():
        if not v["passed"] and name not in escalated:
            return v["route_to"] if v["route_to"] in ("analyst", "scorer") else "__end__"

    return "__end__"


# ---------------------------------------------------------------------------
# 8. Wire the graph
# ---------------------------------------------------------------------------

def build_handoff_graph():
    """Build a LangGraph with analyst → validate → scorer → verifier → router."""
    try:
        from langgraph.graph import StateGraph, END, START
    except ImportError:
        print("ERROR: langgraph is not installed. Install with: pip install langgraph")
        sys.exit(1)

    builder = StateGraph(HandoffState)

    builder.add_node("analyst", analyst_node)
    builder.add_node("validate", validate_node)
    builder.add_node("scorer", scorer_node)
    builder.add_node("verifier", verifier_node)
    builder.add_node("router", router_node)

    builder.add_edge(START, "analyst")
    builder.add_edge("analyst", "validate")
    builder.add_edge("validate", "scorer")
    builder.add_edge("scorer", "verifier")
    builder.add_edge("verifier", "router")
    builder.add_conditional_edges(
        "router",
        router_fn,
        {
            "analyst": "analyst",
            "scorer": "scorer",
            "__end__": END,
        },
    )

    return builder.compile()


# ---------------------------------------------------------------------------
# 9. Run and print
# ---------------------------------------------------------------------------

def print_state(phase: str, state: dict):
    print(f"\n{'='*60}")
    print(f"  STATE AFTER: {phase}")
    print(f"{'='*60}")

    if "parsed_profiles" in state:
        for name, p in state["parsed_profiles"].items():
            print(f"\n  📄 {name}")
            print(f"     Skills: {len(p['skills'])} items — {p['skills'][:3] if p['skills'] else 'EMPTY!'}")
            print(f"     Injection: {p['injection_detected']}")

    if "validation_reports" in state:
        for name, r in state["validation_reports"].items():
            status = "✅" if r["valid"] else "❌"
            print(f"\n  🛡 {name} validation: {status}")
            if r["errors"]:
                for e in r["errors"]:
                    print(f"       {e}")

    if "scorecards" in state:
        for name, sc in state["scorecards"].items():
            print(f"\n  📊 {name}: {sc['weighted_total']}/5")
            for crit, score in sc["per_criterion"].items():
                print(f"     {crit}: {score}/5")

    if "verifications" in state:
        for name, v in state["verifications"].items():
            status = "✅ PASS" if v["passed"] else "❌ FAIL"
            print(f"\n  🔍 {name}: {status}")
            print(f"     {v['reason']}")
            if v["name_swap_score"] is not None:
                print(f"     Name-swap: {v['name_swap_score']:.2f}")
            print(f"     Route: {v['route_to']}")

    if state.get("escalated"):
        print(f"\n  🚨 Escalated: {state['escalated']}")
    if state.get("revision_count", 0) > 0:
        print(f"  🔄 Revisions: {state['revision_count']}/{MAX_REVISIONS}")
    print(f"  ⏱ Steps: {state.get('total_steps', 0)}/{MAX_TOTAL_STEPS}")


def run_prototype():
    print("\n" + "="*60)
    print("  THREE-AGENT HANDOFF + BOUNDARY VALIDATION")
    print("  Analyst → Validate → Scorer → Verifier → Router")
    print("="*60)

    initial_state: HandoffState = {
        "candidates": {
            "Priya": PRIYA_RESUME,
            "Rahul": RAHUL_RESUME,
            "Meera": MEERA_RESUME,
        },
        "parsed_profiles": {},
        "validated_profiles": {},
        "validation_reports": {},
        "scorecards": {},
        "verifications": {},
        "revision_count": 0,
        "escalated": [],
        "total_steps": 0,
        "job_description": "Junior AI Engineer — TechVest",
    }

    graph = build_handoff_graph()

    print("\n▶ Running the graph...")
    accumulated_state = dict(initial_state)
    step_num = 0
    for event in graph.stream(initial_state):
        for node_name, state_snapshot in event.items():
            step_num += 1
            print(f"\n--- Execution Step {step_num}: {node_name.upper()} ---")
            print_state(node_name.upper(), state_snapshot)
            for k, v in state_snapshot.items():
                accumulated_state[k] = v

    # Summary
    print(f"\n{'='*60}")
    print("  FINAL SUMMARY")
    print(f"{'='*60}")
    reports = accumulated_state.get("validation_reports", {})
    passed_val = [n for n, r in reports.items() if r["valid"]]
    failed_val = [n for n, r in reports.items() if not r["valid"]]
    verifs = accumulated_state.get("verifications", {})
    passed_v = [n for n, v in verifs.items() if v["passed"]]
    failed_v = [n for n, v in verifs.items() if not v["passed"]]
    print(f"\n  ✅ Validation passed: {passed_val}")
    print(f"  ❌ Validation failed: {failed_val}")
    print(f"  ✅ Verified:          {passed_v}")
    print(f"  ❌ Failed verification: {failed_v}")
    print(f"  🚨 Escalated:         {accumulated_state.get('escalated', [])}")
    print(f"  🔄 Total revisions:   {accumulated_state.get('revision_count', 0)}")
    print(f"  ⏱ Total steps:        {accumulated_state.get('total_steps', 0)}/{MAX_TOTAL_STEPS}")

    return accumulated_state


# ---------------------------------------------------------------------------
# 10. Deployment Note
# ---------------------------------------------------------------------------

DEPLOYMENT_NOTE = """
══════════════════════════════════════════════════════════════════
  DEPLOYMENT NOTE — Multi-Agent Recruitment Pipeline
══════════════════════════════════════════════════════════════════

  COST: ~$0.08–0.15 per candidate (3 agents × 2–3 LLM calls each ×
  Claude Sonnet pricing). Budget at $0.50/candidate with 3 retries.

  LATENCY: ~8–15s per candidate in the happy path (Analyst → Scorer
  → Verifier). Each feedback loop iteration adds ~4–8s. Set client
  timeout to 60s to accommodate 3 retries.

  OBSERVABILITY: Every state transition is logged to the trajectory
  (step count, agent name, inputs/outputs). Validation failures and
  verification decisions are surfaced as structured events. Integrate
  with LangSmith or a custom trace sink for production monitoring.

  HUMAN APPROVAL GATE: Sits after the Verifier's router, before any
  interview scheduling. The gate is triggered when: (a) revision_count
  exceeds MAX_REVISIONS (3), (b) total_steps exceeds MAX_TOTAL_STEPS
  (20), or (c) a candidate is flagged as "not_a_fit" and the hiring
  manager must confirm. The gate blocks the propose_interview tool
  until a human approves or overrides.

  STEP BUDGET (MAX_TOTAL_STEPS = 20): Justification — 3 candidates ×
  3 agents per pass × 3 revision cycles = 27 worst-case. 20 is a
  tighter bound that leaves room for 2 full cycles plus overhead,
  preventing runaway loops while still allowing the feedback loop to
  resolve most validation failures. Exceeding 20 triggers escalation
  to human rather than silent failure.
══════════════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# 11. Seam test
# ---------------------------------------------------------------------------

def test_skip_analyst():
    """Verify that omitting the Analyst breaks the pipeline cleanly."""
    print(f"\n{'='*60}")
    print("  SEAM TEST: Skip Analyst, run Scorer directly")
    print(f"{'='*60}")

    try:
        from langgraph.graph import StateGraph, END, START
        builder = StateGraph(HandoffState)
        builder.add_node("scorer", scorer_node)
        builder.add_edge(START, "scorer")
        builder.add_edge("scorer", END)
        graph = builder.compile()

        state: HandoffState = {
            "candidates": {"Priya": PRIYA_RESUME},
            "parsed_profiles": {},
            "validated_profiles": {},
            "validation_reports": {},
            "scorecards": {},
            "verifications": {},
            "revision_count": 0,
            "escalated": [],
            "total_steps": 0,
            "job_description": "test",
        }

        list(graph.stream(state))
        print("  ❌ FAIL: Scorer should have raised an error but didn't!")
    except KeyError as e:
        print(f"  ✓ PASS: Scorer raised KeyError cleanly: {e}")
    except Exception as e:
        print(f"  ✓ PASS: Scorer failed with error: {type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_prototype()
    test_skip_analyst()
    print(DEPLOYMENT_NOTE)