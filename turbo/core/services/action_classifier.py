"""
Action Classification System

Classifies AI-requested actions into risk levels to determine if they need approval.
Supports auto-execution for safe actions and approval workflow for risky ones.
"""

import enum
from typing import Dict, Any, Tuple


class ActionRiskLevel(str, enum.Enum):
    """Risk level of an action."""
    SAFE = "safe"           # Auto-execute (e.g., add comment, add tag)
    LOW = "low"             # Auto-execute with notification (e.g., update description)
    MEDIUM = "medium"       # Requires approval (e.g., change status, assign)
    HIGH = "high"           # Requires approval (e.g., delete, close issue)
    CRITICAL = "critical"   # Requires approval + confirmation (e.g., bulk delete)


class ActionClassifier:
    """
    Classifies actions based on risk level.

    Risk Levels:
    - SAFE: Auto-execute immediately (add comment, add tag)
    - LOW: Auto-execute with notification (update description, add assignee)
    - MEDIUM: Requires approval (change status, update priority)
    - HIGH: Requires approval (close issue, delete entity)
    - CRITICAL: Requires approval + confirmation (bulk operations, permanent deletions)
    """

    # Action risk mappings
    ACTION_RISKS = {
        # SAFE - Auto-execute immediately
        "add_comment": ActionRiskLevel.SAFE,
        "add_tag": ActionRiskLevel.SAFE,
        "add_label": ActionRiskLevel.SAFE,

        # LOW - Auto-execute with notification
        "update_description": ActionRiskLevel.LOW,
        "update_title": ActionRiskLevel.LOW,
        "add_assignee": ActionRiskLevel.LOW,
        "add_to_milestone": ActionRiskLevel.LOW,
        "add_to_initiative": ActionRiskLevel.LOW,
        "add_dependency": ActionRiskLevel.LOW,

        # MEDIUM - Requires approval
        "update_status": ActionRiskLevel.MEDIUM,
        "update_priority": ActionRiskLevel.MEDIUM,
        "update_type": ActionRiskLevel.MEDIUM,
        "remove_assignee": ActionRiskLevel.MEDIUM,
        "remove_tag": ActionRiskLevel.MEDIUM,
        "update_due_date": ActionRiskLevel.MEDIUM,
        "update_project": ActionRiskLevel.MEDIUM,

        # HIGH - Requires approval
        "close_issue": ActionRiskLevel.HIGH,
        "reopen_issue": ActionRiskLevel.HIGH,
        "archive_project": ActionRiskLevel.HIGH,
        "complete_milestone": ActionRiskLevel.HIGH,
        "cancel_initiative": ActionRiskLevel.HIGH,
        "delete_comment": ActionRiskLevel.HIGH,
        "remove_dependency": ActionRiskLevel.HIGH,

        # CRITICAL - Requires approval + confirmation
        "delete_issue": ActionRiskLevel.CRITICAL,
        "delete_project": ActionRiskLevel.CRITICAL,
        "delete_milestone": ActionRiskLevel.CRITICAL,
        "delete_initiative": ActionRiskLevel.CRITICAL,
        "bulk_update": ActionRiskLevel.CRITICAL,
        "bulk_delete": ActionRiskLevel.CRITICAL,
    }

    @classmethod
    def classify_action(cls, action_type: str, action_params: Dict[str, Any]) -> Tuple[ActionRiskLevel, bool]:
        """
        Classify an action and determine if it can auto-execute.

        Args:
            action_type: Type of action (e.g., "update_issue", "close_issue")
            action_params: Parameters for the action

        Returns:
            Tuple of (risk_level, auto_execute)
        """
        # Get base risk level
        risk_level = cls.ACTION_RISKS.get(action_type, ActionRiskLevel.MEDIUM)

        # Determine if can auto-execute
        auto_execute = risk_level in [ActionRiskLevel.SAFE, ActionRiskLevel.LOW]

        # Special cases that override auto-execute
        if cls._has_special_constraints(action_type, action_params):
            auto_execute = False
            # Elevate risk level if needed
            if risk_level == ActionRiskLevel.SAFE:
                risk_level = ActionRiskLevel.LOW
            elif risk_level == ActionRiskLevel.LOW:
                risk_level = ActionRiskLevel.MEDIUM

        return risk_level, auto_execute

    @classmethod
    def _has_special_constraints(cls, action_type: str, action_params: Dict[str, Any]) -> bool:
        """
        Check if action has special constraints that prevent auto-execution.

        Examples:
        - Updating critical priority items
        - Operating on production environments
        - Actions with large scope (bulk operations)
        """
        # Check for critical priority
        if action_params.get("priority") == "critical":
            return True

        # Check for production workspace
        if action_params.get("workspace") == "work":
            return True

        # Check for bulk operations
        if action_params.get("bulk") or isinstance(action_params.get("ids"), list):
            return True

        # Check for status changes to closed/archived
        if action_type == "update_status" and action_params.get("status") in ["closed", "archived"]:
            return True

        return False

    @classmethod
    def get_action_description(cls, action_type: str, action_params: Dict[str, Any], entity_title: str = None) -> str:
        """
        Generate a human-readable description of the action.

        Args:
            action_type: Type of action
            action_params: Parameters for the action
            entity_title: Title of the entity being acted upon

        Returns:
            Human-readable description
        """
        entity = f'"{entity_title}"' if entity_title else "this item"

        descriptions = {
            "add_comment": f"Add a comment to {entity}",
            "add_tag": f"Add tag '{action_params.get('tag')}' to {entity}",
            "update_description": f"Update the description of {entity}",
            "update_title": f"Change title to '{action_params.get('title')}'",
            "add_assignee": f"Assign {entity} to {action_params.get('assignee')}",
            "update_status": f"Change status of {entity} to '{action_params.get('status')}'",
            "update_priority": f"Change priority of {entity} to '{action_params.get('priority')}'",
            "close_issue": f"Close issue {entity}",
            "reopen_issue": f"Reopen issue {entity}",
            "delete_issue": f"Delete issue {entity}",
            "archive_project": f"Archive project {entity}",
            "add_to_milestone": f"Add {entity} to milestone '{action_params.get('milestone_name')}'",
            "add_to_initiative": f"Add {entity} to initiative '{action_params.get('initiative_name')}'",
            "add_dependency": f"Add blocking dependency to {entity}",
            "remove_dependency": f"Remove dependency from {entity}",
        }

        return descriptions.get(action_type, f"Perform {action_type} on {entity}")

    @classmethod
    def should_notify_user(cls, risk_level: ActionRiskLevel, auto_executed: bool) -> bool:
        """
        Determine if user should be notified about this action.

        Args:
            risk_level: Risk level of the action
            auto_executed: Whether the action was auto-executed

        Returns:
            True if user should be notified
        """
        # Always notify for LOW and above
        if risk_level in [ActionRiskLevel.LOW, ActionRiskLevel.MEDIUM, ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL]:
            return True

        # Notify for SAFE actions only if explicitly requested
        return auto_executed and risk_level == ActionRiskLevel.SAFE

    @classmethod
    def get_approval_message(cls, action_type: str, action_description: str, risk_level: ActionRiskLevel, ai_reasoning: str = None) -> str:
        """
        Generate an approval message for the user.

        Args:
            action_type: Type of action
            action_description: Human-readable description
            risk_level: Risk level
            ai_reasoning: AI's reasoning for suggesting this action

        Returns:
            Approval message with context
        """
        risk_indicator = {
            ActionRiskLevel.SAFE: "✓ Safe",
            ActionRiskLevel.LOW: "⚠️ Low Risk",
            ActionRiskLevel.MEDIUM: "⚠️ Medium Risk",
            ActionRiskLevel.HIGH: "❗ High Risk",
            ActionRiskLevel.CRITICAL: "🛑 Critical Risk",
        }

        message = f"{risk_indicator[risk_level]} - {action_description}"

        if ai_reasoning:
            message += f"\n\n**AI Reasoning:** {ai_reasoning}"

        return message
