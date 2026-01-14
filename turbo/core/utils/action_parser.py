"""
Action Parser

Parses AI responses to detect action requests and extract structured action data.
"""

import re
from typing import Dict, List, Optional, Tuple, Any


class ActionIntent:
    """Represents an action that AI wants to perform."""

    def __init__(
        self,
        action_type: str,
        description: str,
        params: Dict[str, Any],
        reasoning: Optional[str] = None
    ):
        self.action_type = action_type
        self.description = description
        self.params = params
        self.reasoning = reasoning


# Action patterns that AI might use in responses
ACTION_PATTERNS = {
    "close_issue": [
        r"(?:i will|i'll|let me|i'm going to|i should)\s+(?:mark this as complete|close this issue|mark this issue as (?:closed|complete|done))",
        r"(?:closing|will close|should close)\s+(?:this|the)\s+issue",
        r"(?:this issue (?:can|should) be closed|mark (?:this|the) issue as closed)"
    ],
    "update_status": [
        r"(?:i will|i'll|let me|i'm going to|i should)\s+(?:update|change|set)\s+(?:the\s+)?status\s+to\s+(\w+)",
        r"(?:status should be|changing status to|updating status to)\s+(\w+)"
    ],
    "update_priority": [
        r"(?:i will|i'll|let me|i'm going to|i should)\s+(?:update|change|set|raise|lower)\s+(?:the\s+)?priority\s+to\s+(low|medium|high|critical)",
        r"(?:priority should be|changing priority to|updating priority to)\s+(low|medium|high|critical)",
        r"(?:raising|lowering)\s+(?:the\s+)?priority\s+to\s+(low|medium|high|critical)"
    ],
    "add_comment": [
        r"(?:i will|i'll|let me|i'm going to|i should)\s+(?:add a comment|comment|note)",
        r"(?:adding a comment|posting a comment)"
    ],
    "add_tag": [
        r"(?:i will|i'll|let me|i'm going to|i should)\s+(?:add|apply)\s+(?:the\s+)?(?:tag|label)\s+['\"]?(\w+)['\"]?",
        r"(?:tagging this as|adding tag|applying tag)\s+['\"]?(\w+)['\"]?"
    ],
    "add_assignee": [
        r"(?:i will|i'll|let me|i'm going to|i should)\s+assign this to\s+(\S+)",
        r"(?:assigning to|assigning this to)\s+(\S+)"
    ],
    "add_dependency": [
        r"(?:i will|i'll|let me|i'm going to|i should)\s+(?:add|create)\s+(?:a\s+)?(?:dependency|blocker)",
        r"(?:this (?:depends on|is blocked by|requires)|adding dependency)"
    ]
}


def detect_action_intent(ai_response: str) -> List[ActionIntent]:
    """
    Parse AI response text to detect action intents.

    Args:
        ai_response: The AI's response text

    Returns:
        List of detected ActionIntent objects
    """
    intents = []
    ai_response_lower = ai_response.lower()

    # Check for close issue intent
    for pattern in ACTION_PATTERNS["close_issue"]:
        if re.search(pattern, ai_response_lower, re.IGNORECASE):
            reasoning = _extract_reasoning(ai_response, "close")
            intents.append(ActionIntent(
                action_type="close_issue",
                description="Close this issue",
                params={},
                reasoning=reasoning
            ))
            break

    # Check for status update intent
    for pattern in ACTION_PATTERNS["update_status"]:
        match = re.search(pattern, ai_response_lower, re.IGNORECASE)
        if match:
            status = match.group(1) if match.groups() else "closed"
            reasoning = _extract_reasoning(ai_response, "status")
            intents.append(ActionIntent(
                action_type="update_status",
                description=f"Update status to {status}",
                params={"status": status},
                reasoning=reasoning
            ))
            break

    # Check for priority update intent
    for pattern in ACTION_PATTERNS["update_priority"]:
        match = re.search(pattern, ai_response_lower, re.IGNORECASE)
        if match:
            priority = match.group(1)
            reasoning = _extract_reasoning(ai_response, "priority")
            intents.append(ActionIntent(
                action_type="update_priority",
                description=f"Update priority to {priority}",
                params={"priority": priority},
                reasoning=reasoning
            ))
            break

    # Check for tag intent
    for pattern in ACTION_PATTERNS["add_tag"]:
        match = re.search(pattern, ai_response_lower, re.IGNORECASE)
        if match and match.groups():
            tag_name = match.group(1)
            reasoning = _extract_reasoning(ai_response, "tag")
            intents.append(ActionIntent(
                action_type="add_tag",
                description=f"Add tag '{tag_name}'",
                params={"tag_name": tag_name},
                reasoning=reasoning
            ))
            break

    # Check for assignee intent
    for pattern in ACTION_PATTERNS["add_assignee"]:
        match = re.search(pattern, ai_response_lower, re.IGNORECASE)
        if match and match.groups():
            assignee = match.group(1)
            reasoning = _extract_reasoning(ai_response, "assign")
            intents.append(ActionIntent(
                action_type="add_assignee",
                description=f"Assign to {assignee}",
                params={"assignee": assignee},
                reasoning=reasoning
            ))
            break

    return intents


def _extract_reasoning(ai_response: str, action_keyword: str) -> str:
    """
    Extract the reasoning/context around an action from AI response.

    Args:
        ai_response: Full AI response text
        action_keyword: Keyword related to the action

    Returns:
        Extracted reasoning or empty string
    """
    # Find sentences containing the action keyword
    sentences = re.split(r'[.!?]\s+', ai_response)
    relevant_sentences = [s for s in sentences if action_keyword.lower() in s.lower()]

    if relevant_sentences:
        # Return the context (sentence before and after)
        idx = sentences.index(relevant_sentences[0])
        context_sentences = sentences[max(0, idx-1):min(len(sentences), idx+2)]
        return " ".join(context_sentences)

    return ""


def should_detect_actions(entity_type: str) -> bool:
    """
    Determine if action detection should be enabled for this entity type.

    Args:
        entity_type: Type of entity (issue, project, etc.)

    Returns:
        True if action detection should be enabled
    """
    # Enable action detection for issues and projects (where AI can take useful actions)
    # Disable for mentors (conversational only), literature, blueprints
    return entity_type in ["issue", "project"]
