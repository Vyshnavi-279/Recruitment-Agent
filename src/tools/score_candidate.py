"""Tool to score a candidate against a rubric using an LLM."""

from langchain_core.tools import tool

from src.schemas import CandidateProfile, RubricCriterion, ScoreCard


@tool
def score_candidate(
    profile: CandidateProfile,
    rubric: list[RubricCriterion],
    llm,
) -> ScoreCard:
    """Score a candidate's profile against the given evaluation rubric.

    For each criterion, the LLM assigns a 0-5 score and provides a one-line
    evidence quote from the candidate's raw text. A weighted total is computed
    from the scores and criterion weights.

    Args:
        profile: The candidate's structured profile.
        rubric: The list of rubric criteria with weights and descriptors.
        llm: A ChatAnthropic instance with structured output support.

    Returns:
        A ScoreCard with per-criterion scores, evidence, and weighted total.
    """
    rubric_text = "\n".join(
        f"- {c.name} (weight {c.weight}): "
        + "; ".join(f"{k}={v}" for k, v in c.descriptors.items())
        for c in rubric
    )

    structured_llm = llm.with_structured_output(ScoreCard)
    result = structured_llm.invoke(
        "Score the following candidate against the rubric. "
        "For each criterion, assign a score 0-5 and provide a one-line "
        "evidence quote from the candidate's raw text. "
        "Every score MUST be accompanied by evidence.\n\n"
        f"---CANDIDATE---\n{profile.model_dump_json(indent=2)}\n---END CANDIDATE---\n\n"
        f"---RUBRIC---\n{rubric_text}\n---END RUBRIC---"
    )
    return result