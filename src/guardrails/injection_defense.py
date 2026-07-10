"""Prompt-injection detection for resume text."""

import re

_INJECTION_PATTERNS = [
    r"ignore\s+(prior|previous|all)\s+instructions",
    r"ignore\s+(prior|previous|all)\s+prompts",
    r"ignore\s+everything",
    r"rank\s+(me|this|this\s+candidate)\s+first",
    r"disregard\s+(prior|previous|all)\s+(instructions|prompts|rules)",
    r"override\s+(instructions|rules|prompts)",
    r"system:",
    r"you\s+must\s+.",
    r"you\s+are\s+now\s+",
    r"forget\s+(prior|previous|all)\s+",
    r"new\s+prompt\s*:",
    r"ignore\s+above",
]


def sanitize_resume_text(text: str) -> tuple[str, bool]:
    """Detect common prompt-injection patterns in resume text.

    Args:
        text: The raw resume text to scan.

    Returns:
        A tuple of (cleaned_text_with_flagged_span_marked, was_injection_detected).
        The cleaned text wraps detected spans in [[INJECTION: ...]] markers.
        The boolean indicates whether any injection pattern was found.
    """
    was_injection_detected = False

    for pattern in _INJECTION_PATTERNS:
        compiled = re.compile(pattern, re.IGNORECASE)
        matches = list(compiled.finditer(text))
        if matches:
            was_injection_detected = True
            # Replace matches in reverse order so positions stay valid
            for match in reversed(matches):
                start, end = match.start(), match.end()
                flagged_text = text[start:end]
                text = text[:start] + f"[[INJECTION:{flagged_text}]]" + text[end:]

    return text, was_injection_detected