"""Comment parsing utilities for detecting AI triggers and mentions."""

import re
from typing import Pattern

# AI trigger patterns (case-insensitive)
AI_TRIGGER_PATTERNS: list[Pattern] = [
    re.compile(r"@claude\b", re.IGNORECASE),
    re.compile(r"@ai\b", re.IGNORECASE),
    re.compile(r"@assistant\b", re.IGNORECASE),
]

# Pattern to detect any @ mention (for staff)
MENTION_PATTERN: Pattern = re.compile(r"@(\w+)", re.IGNORECASE)


def should_trigger_ai_response(content: str) -> bool:
    """Check if comment content contains an AI mention trigger (generic or staff).

    Detects:
    - Generic AI triggers: @claude, @ai, @assistant
    - Staff mentions: @<any_word> (e.g., @Derek, @ChiefOfStaff)

    All patterns are case-insensitive and can appear anywhere in the text.

    Args:
        content: The comment content to check

    Returns:
        True if an AI trigger or staff mention is detected, False otherwise

    Examples:
        >>> should_trigger_ai_response("@claude what do you think?")
        True
        >>> should_trigger_ai_response("Hey @Derek can you help?")
        True
        >>> should_trigger_ai_response("This looks good!")
        False
        >>> should_trigger_ai_response("derek is great")  # No @ symbol
        False
    """
    if not content or not isinstance(content, str):
        return False

    # Check for generic AI triggers OR any @ mention
    return any(pattern.search(content) for pattern in AI_TRIGGER_PATTERNS) or bool(MENTION_PATTERN.search(content))


def extract_mentioned_ai_name(content: str) -> str | None:
    """Extract the specific AI name that was mentioned.

    Args:
        content: The comment content to check

    Returns:
        The AI name that was mentioned (without @), or None if no mention found

    Examples:
        >>> extract_mentioned_ai_name("@claude help me")
        'claude'
        >>> extract_mentioned_ai_name("@AI what's the plan?")
        'ai'
        >>> extract_mentioned_ai_name("no mention here")
        None
    """
    if not content or not isinstance(content, str):
        return None

    for pattern in AI_TRIGGER_PATTERNS:
        match = pattern.search(content)
        if match:
            # Extract the name without the @ symbol
            return match.group(0)[1:].lower()

    return None


def extract_staff_mentions(content: str) -> list[str]:
    """Extract all staff @ mentions from comment content.

    Finds all @mentions in the text and returns them as a list.

    Args:
        content: The comment content to check

    Returns:
        List of mentioned names (without @), or empty list if none found

    Examples:
        >>> extract_staff_mentions("@Derek what do you think?")
        ['Derek']
        >>> extract_staff_mentions("@Derek and @Kevin please review")
        ['Derek', 'Kevin']
        >>> extract_staff_mentions("no mentions here")
        []
    """
    if not content or not isinstance(content, str):
        return []

    matches = MENTION_PATTERN.findall(content)
    return list(matches) if matches else []
