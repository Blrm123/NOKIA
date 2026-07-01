"""
workflow/workflow_state.py
--------------------------
Dataclass representing the in-memory workflow execution state.

Responsibilities:
- Act as the canonical in-memory container for a single workflow run
- Provide a to_dict() method for JSON serialisation
- No I/O or business logic — pure data holder
"""

from dataclasses import dataclass, field
from typing import Optional

from app.core.constants import WorkflowStatus


@dataclass
class WorkflowState:
    """Holds the complete state of a single workflow execution.

    Attributes:
        workflow_id:   UUID string uniquely identifying this run.
        repository:    Full repository name, e.g. 'owner/repo'.
        branch:        Short branch name, e.g. 'main'.
        status:        Current lifecycle status (see WorkflowStatus enum).
        commit_sha:    HEAD commit SHA after the push.
        timestamp:     ISO-8601 UTC timestamp of workflow creation.
        changed_files: All files touched in the push (added + modified + removed).
        error_message: Optional error detail when status is FAILED.
    """

    workflow_id: str
    repository: str
    branch: str
    status: WorkflowStatus
    commit_sha: str
    timestamp: str
    changed_files: list[str] = field(default_factory=list)
    error_message: Optional[str] = None

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Convert this state object to a JSON-serialisable dictionary.

        Returns:
            dict: Plain Python dictionary with all fields.
                  Enum values are converted to their string representations.
        """
        return {
            "workflow_id": self.workflow_id,
            "repository": self.repository,
            "branch": self.branch,
            "status": self.status.value,
            "commit_sha": self.commit_sha,
            "timestamp": self.timestamp,
            "changed_files": self.changed_files,
            "error_message": self.error_message,
        }

    # ------------------------------------------------------------------
    # Convenience mutators
    # ------------------------------------------------------------------

    def mark_in_progress(self) -> None:
        """Transition status to IN_PROGRESS."""
        self.status = WorkflowStatus.IN_PROGRESS

    def mark_completed(self) -> None:
        """Transition status to COMPLETED."""
        self.status = WorkflowStatus.COMPLETED
        self.error_message = None

    def mark_failed(self, reason: str) -> None:
        """Transition status to FAILED and record the failure reason.

        Args:
            reason: Human-readable description of the failure.
        """
        self.status = WorkflowStatus.FAILED
        self.error_message = reason
