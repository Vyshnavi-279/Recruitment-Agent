"""Fairness check comparing two candidate scorecards for potential bias."""

from src.schemas import CandidateProfile, ScoreCard


def run_fairness_check(
    profile_a: CandidateProfile,
    profile_b: CandidateProfile,
    score_a: ScoreCard,
    score_b: ScoreCard,
) -> dict:
    """Compare two candidates with similar experience levels for scoring parity.

    Detects potential bias by flagging significant score differences (>1 point
    on any criterion) between candidates whose profiles show comparable
    relevant experience.

    Args:
        profile_a: First candidate's profile.
        profile_b: Second candidate's profile.
        score_a: Scorecard for the first candidate.
        score_b: Scorecard for the second candidate.

    Returns:
        A dict with keys:
            - "passed" (bool): True if no significant bias indicators found.
            - "detail" (str): Human-readable explanation of the check result.
    """
    disparities = []
    all_criteria = set(score_a.per_criterion_scores.keys()) | set(
        score_b.per_criterion_scores.keys()
    )

    for criterion in sorted(all_criteria):
        a_score = score_a.per_criterion_scores.get(criterion, -1)
        b_score = score_b.per_criterion_scores.get(criterion, -1)
        if a_score != -1 and b_score != -1:
            diff = abs(a_score - b_score)
            if diff > 1:
                disparities.append(
                    f"'{criterion}': {profile_a.name}={a_score} vs "
                    f"{profile_b.name}={b_score} (Δ={diff})"
                )

    exp_a = getattr(profile_a, "years_experience", 0)
    exp_b = getattr(profile_b, "years_experience", 0)

    if disparities and abs(exp_a - exp_b) <= 2.0:
        return {
            "passed": False,
            "detail": (
                f"Fairness alert: {profile_a.name} (exp={exp_a}) and "
                f"{profile_b.name} (exp={exp_b}) have similar experience levels "
                f"but differ by >1 point on: {'; '.join(disparities)}."
            ),
        }

    return {
        "passed": True,
        "detail": (
            f"No significant scoring disparities detected between "
            f"{profile_a.name} and {profile_b.name}."
        ),
    }