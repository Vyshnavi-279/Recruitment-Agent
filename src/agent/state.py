"""Agent state definition for the recruitment LangGraph."""

from typing import TypedDict

from src.schemas import CandidateProfile, Decision, ScoreCard, TrajectoryStep


class AgentState(TypedDict):
    """State passed between nodes in the recruitment agent graph."""

    job_description: str
    rubric: str
    candidates: list[dict[str, str]]  # list of {"name": ..., "text": ...}
    profiles: dict[str, CandidateProfile]
    scorecards: dict[str, ScoreCard]
    shortlist: list[Decision]
    trajectory: list[TrajectoryStep]
    step_count: int
    pending_approval: dict | None