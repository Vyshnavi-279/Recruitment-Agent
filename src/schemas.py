"""Pydantic v2 models for the recruitment agent."""

from typing import Literal

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    """Profile of a candidate, derived from resume parsing."""

    name: str
    years_experience: float
    skills: list[str]
    education: str
    projects: list[str]
    raw_text: str


class RubricCriterion(BaseModel):
    """A single criterion in the evaluation rubric with a 0–5 scoring scale."""

    name: str
    weight: float = Field(ge=0.0)
    descriptors: dict[int, str]  # maps score 0–5 to a textual descriptor


class ScoreCard(BaseModel):
    """Per-criterion scores and evidence for a single candidate evaluation."""

    candidate_name: str
    per_criterion_scores: dict[str, int]
    evidence: dict[str, str]
    weighted_total: float


class Decision(BaseModel):
    """Final decision for a candidate, including the scorecard and approval status."""

    candidate_name: str
    verdict: Literal["interview", "hold", "not_a_fit"]
    justification: str
    scorecard: ScoreCard
    proposed_slot: str | None = None
    pending_approval: bool


class TrajectoryStep(BaseModel):
    """A single reasoning step recorded along the agent's execution trace."""

    step_number: int
    thought: str
    action: str | None = None
    action_input: dict | None = None
    observation: str | None = None