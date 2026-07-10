"""Mock tool to check interview slot availability."""

from langchain_core.tools import tool


@tool
def check_availability(candidate_name: str, week: str) -> list[str]:
    """Check available interview time slots for a candidate in a given week.

    This is a mock function returning hardcoded slots.

    Args:
        candidate_name: The name of the candidate.
        week: The week identifier (e.g., "2026-07-13" or "next-week").

    Returns:
        A list of available time slot strings.
    """
    return [
        "2026-07-15 10:00-11:00 IST",
        "2026-07-16 14:00-15:00 IST",
        "2026-07-17 09:00-10:00 IST",
    ]