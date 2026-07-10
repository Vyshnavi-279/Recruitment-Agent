"""Tool to propose or confirm an interview slot."""

from langchain_core.tools import tool


@tool
def propose_interview(
    candidate_name: str,
    slot: str,
    approved: bool = False,
) -> dict:
    """Propose an interview slot, optionally confirming if approved.

    If approved is False, the proposal is blocked pending human approval.
    Only when approved is True will the slot be confirmed.

    Args:
        candidate_name: The name of the candidate.
        slot: The proposed time slot string.
        approved: Whether the slot is approved. Defaults to False.

    Returns:
        A dict with status and details.
    """
    if not approved:
        return {"status": "blocked_pending_approval"}

    return {
        "status": "confirmed",
        "candidate": candidate_name,
        "slot": slot,
    }