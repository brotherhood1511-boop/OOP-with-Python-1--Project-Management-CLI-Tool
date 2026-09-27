"""Project model. A project is owned by one user and holds many tasks."""

from project_tracker.models.base import BaseModel
from project_tracker.models.task import Task
from project_tracker.utils import parse_due_date


class Project(BaseModel):
    def __init__(self, title, owner, description="", due_date=None, tasks=None, **base):
        super().__init__(**base)
        self.title = title
        self._owner = self._require_text(owner, "Project owner")
        self.description = description
        self.due_date = due_date
        self._tasks = list(tasks or [])

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = self._require_text(value, "Project title")

    @property
    def owner(self):
        return self._owner

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = (value or "").strip()

    @property
    def due_date(self):
        return self._due_date

    @due_date.setter
    def due_date(self, value):
        # Stored as an ISO string (YYYY-MM-DD) so it saves cleanly to JSON.
        self._due_date = parse_due_date(value)

    @property
    def tasks(self):
        return list(self._tasks)

    def add_task(self, task):
        if not isinstance(task, Task):
            raise TypeError("Only Task objects can be added to a project.")
        if self.get_task(task.title):
            raise ValueError(f"Project '{self.title}' already has a task named '{task.title}'.")
        self._tasks.append(task)
        return task

    def get_task(self, title):
        for task in self._tasks:
            if task.title.lower() == title.strip().lower():
                return task
        return None

    @property
    def completed_count(self):
        return sum(1 for task in self._tasks if task.is_complete)

    @property
    def progress(self):
        """Percent of tasks complete, as a whole number."""
        if not self._tasks:
            return 0
        return round(self.completed_count / len(self._tasks) * 100)

    @property
    def status(self):
        if not self._tasks:
            return "not started"
        if self.completed_count == len(self._tasks):
            return "complete"
        return "in progress"

    def to_dict(self):
        return {
            **self._base_dict(),
            "title": self.title,
            "owner": self.owner,
            "description": self.description,
            "due_date": self.due_date,
            "tasks": [task.to_dict() for task in self._tasks],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            title=data["title"],
            owner=data["owner"],
            description=data.get("description", ""),
            due_date=data.get("due_date"),
            tasks=[Task.from_dict(task) for task in data.get("tasks", [])],
            id=data.get("id"),
            created_at=data.get("created_at"),
        )