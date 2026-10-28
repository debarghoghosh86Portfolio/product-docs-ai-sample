"""TaskFlow Python SDK - tasks module (sample code to be documented by the AI)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

PRIORITIES = ("low", "medium", "high", "urgent")


class TaskFlowError(Exception):
    """Base error for the SDK."""


class TaskBlockedError(TaskFlowError):
    """Raised when completing a task that still has open blockers."""


@dataclass
class Task:
    """A single unit of work inside a project."""

    id: str
    title: str
    priority: str = "medium"
    due: date | None = None
    assignee: str | None = None
    done: bool = False
    blocked_by: list[str] = field(default_factory=list)

    def is_overdue(self, today: date | None = None) -> bool:
        """True if the task has a due date in the past and is not done."""
        today = today or date.today()
        return self.due is not None and not self.done and self.due < today


class TaskClient:
    """Create, update and complete tasks in a TaskFlow project."""

    def __init__(self, api_token: str, project_id: str):
        if not api_token:
            raise ValueError("api_token is required")
        self.project_id = project_id
        self._tasks: dict[str, Task] = {}
        self._next_id = 1

    def create_task(self, title: str, priority: str = "medium", due: date | None = None,
                    assignee: str | None = None) -> Task:
        """Create a new task and return it."""
        if not title.strip():
            raise ValueError("title must not be empty")
        if priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {PRIORITIES}")
        task = Task(id=f"TF-{self._next_id}", title=title.strip(), priority=priority,
                    due=due, assignee=assignee)
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def get_task(self, task_id: str) -> Task:
        """Fetch a task by ID."""
        try:
            return self._tasks[task_id]
        except KeyError:
            raise TaskFlowError(f"task {task_id} not found") from None

    def add_dependency(self, task_id: str, blocked_by: str) -> None:
        """Mark `task_id` as blocked until `blocked_by` is done."""
        if task_id == blocked_by:
            raise ValueError("a task cannot block itself")
        task = self.get_task(task_id)
        self.get_task(blocked_by)
        if blocked_by not in task.blocked_by:
            task.blocked_by.append(blocked_by)

    def complete_task(self, task_id: str) -> Task:
        """Mark a task as done. Fails if any blocking task is still open."""
        task = self.get_task(task_id)
        open_blockers = [b for b in task.blocked_by if not self.get_task(b).done]
        if open_blockers:
            raise TaskBlockedError(f"{task_id} is blocked by {', '.join(open_blockers)}")
        task.done = True
        return task

    def list_overdue(self, today: date | None = None) -> list[Task]:
        """Return all open tasks whose due date has passed, most urgent first."""
        overdue = [t for t in self._tasks.values() if t.is_overdue(today)]
        return sorted(overdue, key=lambda t: PRIORITIES.index(t.priority), reverse=True)
