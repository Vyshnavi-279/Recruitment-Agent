# state.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class CandidateState:
    name: str
    raw_resume: str
    parsed_data: Optional[Dict[str, Any]] = None
    evaluation_score: Optional[float] = None
    evaluation_notes: Optional[str] = None
    final_decision: Optional[str] = None  # "Interview", "Hold", "Not a Fit"
    decision_justification: Optional[str] = None
    interview_proposal: Optional[str] = None
    p2p_checks: int = 0

@dataclass
class RecruitmentState:
    job_description: str
    candidates: Dict[str, CandidateState] = field(default_factory=dict)
    trajectory: List[str] = field(default_factory=list)  # Thought -> Action -> Observation
    guardrail_status: Dict[str, Any] = field(default_factory=dict)