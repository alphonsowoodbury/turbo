"""Project Management Agent for issue auditing and organization."""

import re
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.comment import Comment
from turbo.core.models.issue import Issue
from turbo.core.repositories.issue import IssueRepository


class PMAgent:
    """
    Project Management Agent that audits issues and keeps the tracker clean.

    Responsibilities:
    - Audit open issues for completion
    - Validate if work is actually done
    - Organize issues into initiatives/milestones
    - Add comments to document findings
    - @ mention user when human decision needed
    """

    def __init__(self, session: AsyncSession, user_mention: str = "@alphonso"):
        """Initialize PM Agent."""
        self.session = session
        self.user_mention = user_mention
        self.issue_repo = IssueRepository(session)

    async def run_audit(self) -> dict[str, Any]:
        """
        Run full issue audit.

        Returns summary of actions taken.
        """
        result = {
            "issues_audited": 0,
            "issues_closed": 0,
            "issues_updated": 0,
            "comments_added": 0,
            "decisions_needed": 0,
            "started_at": datetime.utcnow().isoformat(),
        }

        # Get all open issues
        stmt = select(Issue).where(Issue.status != "closed")
        issues_result = await self.session.execute(stmt)
        issues = list(issues_result.scalars().all())

        result["issues_audited"] = len(issues)

        for issue in issues:
            action = await self._audit_issue(issue)

            if action["type"] == "close":
                result["issues_closed"] += 1
            elif action["type"] == "update":
                result["issues_updated"] += 1
            elif action["type"] == "ask_user":
                result["decisions_needed"] += 1

            if action.get("comment_added"):
                result["comments_added"] += 1

        result["completed_at"] = datetime.utcnow().isoformat()
        return result

    async def _audit_issue(self, issue: Issue) -> dict[str, Any]:
        """
        Audit a single issue and take appropriate action.

        Returns dict with action type and details.
        """
        # Analyze issue content
        analysis = await self._analyze_issue(issue)

        # Decide action based on analysis
        if analysis["confidence"] == "high" and analysis["appears_complete"]:
            # Close the issue
            await self._close_issue_with_evidence(issue, analysis)
            return {"type": "close", "comment_added": True}

        elif analysis["confidence"] == "medium" and analysis["appears_complete"]:
            # Ask user to confirm
            await self._request_user_confirmation(issue, analysis)
            return {"type": "ask_user", "comment_added": True}

        elif analysis["needs_organization"]:
            # Suggest initiative/milestone
            await self._suggest_organization(issue, analysis)
            return {"type": "update", "comment_added": True}

        else:
            # No action needed
            return {"type": "none"}

    async def _analyze_issue(self, issue: Issue) -> dict[str, Any]:
        """
        Analyze an issue to determine status and next steps.

        Returns analysis with confidence level and recommendations.
        """
        analysis = {
            "appears_complete": False,
            "confidence": "low",  # low, medium, high
            "evidence": [],
            "needs_organization": False,
            "suggested_actions": [],
        }

        # Check for completion signals in title/description
        completion_keywords = [
            r"\b(done|completed|finished|implemented|fixed|resolved)\b",
            r"\bmerged\b",
            r"\bshipped\b",
        ]

        text = f"{issue.title} {issue.description}".lower()
        for pattern in completion_keywords:
            if re.search(pattern, text):
                analysis["evidence"].append("Completion keyword found in issue text")
                analysis["appears_complete"] = True

        # Check comments for completion evidence
        comments = await self._get_issue_comments(issue.id)
        for comment in comments[-5:]:  # Check last 5 comments
            comment_text = comment.content.lower()
            for pattern in completion_keywords:
                if re.search(pattern, comment_text):
                    analysis["evidence"].append(
                        f"Completion mentioned in comment by {comment.author_name}"
                    )
                    analysis["appears_complete"] = True

        # Check if issue mentions specific files/components
        file_patterns = [
            r"([a-zA-Z0-9_-]+\.(py|tsx?|jsx?|md))",
            r"(/[a-zA-Z0-9/_-]+\.[a-zA-Z0-9]+)",
        ]
        mentioned_files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, issue.description or "")
            mentioned_files.extend([m if isinstance(m, str) else m[0] for m in matches])

        if mentioned_files:
            analysis["evidence"].append(
                f"Issue mentions files: {', '.join(set(mentioned_files[:3]))}"
            )

        # Check for phase/feature keywords that suggest grouping
        grouping_keywords = [
            "terminal",
            "layout",
            "agent",
            "calendar",
            "knowledge graph",
        ]
        for keyword in grouping_keywords:
            if keyword in text:
                analysis["needs_organization"] = True
                analysis["suggested_actions"].append(
                    f"Consider adding to '{keyword}' initiative"
                )

        # Determine confidence level
        evidence_count = len(analysis["evidence"])
        if evidence_count >= 3:
            analysis["confidence"] = "high"
        elif evidence_count >= 1:
            analysis["confidence"] = "medium"
        else:
            analysis["confidence"] = "low"

        return analysis

    async def _get_issue_comments(self, issue_id: str) -> list[Comment]:
        """Get all comments for an issue."""
        stmt = (
            select(Comment)
            .where(Comment.issue_id == issue_id)
            .order_by(Comment.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _close_issue_with_evidence(
        self, issue: Issue, analysis: dict[str, Any]
    ) -> None:
        """Close an issue with a comment explaining why."""
        evidence_text = "\n".join(f"- {e}" for e in analysis["evidence"])

        comment_text = f"""🤖 **PM Agent Audit**

I've analyzed this issue and determined it appears to be complete based on:

{evidence_text}

**Action**: Closing this issue as completed.

If this was incorrect, {self.user_mention} can reopen it."""

        # Add comment
        comment = Comment(
            issue_id=issue.id,
            content=comment_text,
            author_name="PM Agent",
            author_type="ai",
        )
        self.session.add(comment)

        # Close issue
        issue.status = "closed"
        issue.updated_at = datetime.utcnow()

        await self.session.commit()

    async def _request_user_confirmation(
        self, issue: Issue, analysis: dict[str, Any]
    ) -> None:
        """Ask user to confirm if issue is complete."""
        evidence_text = "\n".join(f"- {e}" for e in analysis["evidence"])

        comment_text = f"""🤖 **PM Agent Audit**

{self.user_mention} I've analyzed this issue and it *might* be complete:

{evidence_text}

**Question**: Is this issue done? If yes, I can close it. If no, let me know what's remaining.

Reply with:
- ✅ to close
- 📝 to add remaining work
- ⏭️ if you want to skip this for now"""

        comment = Comment(
            issue_id=issue.id,
            content=comment_text,
            author_name="PM Agent",
            author_type="ai",
        )
        self.session.add(comment)
        await self.session.commit()

    async def _suggest_organization(
        self, issue: Issue, analysis: dict[str, Any]
    ) -> None:
        """Suggest organizing issue into initiative/milestone."""
        suggestions = "\n".join(f"- {s}" for s in analysis["suggested_actions"])

        comment_text = f"""🤖 **PM Agent Audit**

{self.user_mention} This issue could benefit from better organization:

{suggestions}

Would you like me to create or link this to an initiative/milestone?"""

        comment = Comment(
            issue_id=issue.id,
            content=comment_text,
            author_name="PM Agent",
            author_type="ai",
        )
        self.session.add(comment)
        await self.session.commit()
