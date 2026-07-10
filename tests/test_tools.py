"""Pytest tests for recruitment agent tools and guardrails."""

from unittest.mock import MagicMock

from src.guardrails.injection_defense import sanitize_resume_text
from src.schemas import CandidateProfile
from src.tools.check_availability import check_availability
from src.tools.propose_interview import propose_interview


def test_parse_resume_with_mocked_llm():
    """Test parse_resume returns a CandidateProfile when llm is mocked."""
    from src.tools.parse_resume import parse_resume

    mock_llm = MagicMock()
    mock_profile = CandidateProfile(
        name="Test Candidate",
        years_experience=3.0,
        skills=["Python", "ML"],
        education="B.Tech CS",
        projects=["Project A"],
        raw_text="Resume text here.",
    )
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = mock_profile
    mock_llm.with_structured_output.return_value = mock_structured

    result = parse_resume.invoke(
        {"resume_text": "Sample resume.", "llm": mock_llm}
    )

    assert isinstance(result, CandidateProfile)
    assert result.name == "Test Candidate"
    assert result.years_experience == 3.0
    assert "Python" in result.skills


def test_score_candidate_with_mocked_llm():
    """Test score_candidate returns a ScoreCard when llm is mocked."""
    from src.tools.score_candidate import score_candidate
    from src.rubric import RUBRIC
    from src.schemas import ScoreCard

    mock_llm = MagicMock()
    mock_scorecard = ScoreCard(
        candidate_name="Test Candidate",
        per_criterion_scores={"Python/ML fundamentals": 4},
        evidence={"Python/ML fundamentals": "Strong Python skills with ML projects."},
        weighted_total=4.0 * 0.35,
    )
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = mock_scorecard
    mock_llm.with_structured_output.return_value = mock_structured

    profile = CandidateProfile(
        name="Test Candidate",
        years_experience=3.0,
        skills=["Python"],
        education="B.Tech",
        projects=["Project"],
        raw_text="Sample project.",
    )

    result = score_candidate.invoke(
        {"profile": profile, "rubric": RUBRIC, "llm": mock_llm}
    )

    assert result.candidate_name == "Test Candidate"
    assert result.per_criterion_scores["Python/ML fundamentals"] == 4
    assert result.weighted_total > 0


def test_check_availability_returns_three_slots():
    """Test check_availability returns the expected hardcoded slots."""
    result = check_availability.invoke(
        {"candidate_name": "Priya Sharma", "week": "next-week"}
    )

    assert isinstance(result, list)
    assert len(result) == 3
    assert all("IST" in slot for slot in result)


def test_propose_interview_blocked_when_not_approved():
    """Test propose_interview never returns 'confirmed' when approved=False."""
    result = propose_interview.invoke(
        {
            "candidate_name": "Priya Sharma",
            "slot": "2026-07-15 10:00-11:00 IST",
            "approved": False,
        }
    )

    assert result["status"] == "blocked_pending_approval"


def test_propose_interview_confirmed_when_approved():
    """Test propose_interview returns 'confirmed' when approved=True."""
    result = propose_interview.invoke(
        {
            "candidate_name": "Priya Sharma",
            "slot": "2026-07-15 10:00-11:00 IST",
            "approved": True,
        }
    )

    assert result["status"] == "confirmed"
    assert result["candidate"] == "Priya Sharma"
    assert "slot" in result


def test_sanitize_resume_detects_injection_in_meera_resume():
    """Test that sanitize_resume_text catches the injection in MEERA_RESUME."""
    from src.data.candidates import MEERA_RESUME

    cleaned, detected = sanitize_resume_text(MEERA_RESUME)

    assert detected is True
    assert "[[INJECTION:" in cleaned


def test_sanitize_resume_no_false_positive_on_clean_resume():
    """Test that sanitize_resume_text passes clean resumes."""
    clean_text = "This is a normal resume with Python and ML experience."

    cleaned, detected = sanitize_resume_text(clean_text)

    assert detected is False
    assert cleaned == clean_text