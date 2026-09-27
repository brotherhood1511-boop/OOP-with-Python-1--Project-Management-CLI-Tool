"""Task model. Tasks belong to a project and can have many contributors."""

from datetime import datetime

from project_tracker.models.base import BaseModel


class Task(BaseModel):
    TODO = "todo"
    DONE = "done"
    STATUSES = (TODO, DONE)

    def __init__(self, title, status=TODO, contributors=None, completed_at=None, **base):
        super().__init__(**base)
        self.title = title
        if status not in self.STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(self.STATUSES)}.")
        self._status = status
        self._completed_at = completed_at
        # Contributors are stored by user name. A task can have many users and a
        # user can contribute to many tasks: a many-to-many relationship.
        self._contributors = []
        for name in contributors or []:
            self.add_contributor(name)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = self._require_text(value, "Task title")

    @property
    def status(self):
        return self._status

    @property
    def is_complete(self):
        return self._status == self.DONE

    @property
    def completed_at(self):
        return self._completed_at

    @property
    def contributors(self):
        """Return a copy so callers can't change the list without validation."""
        return list(self._contributors)

    def add_contributor(self, user_name):
        user_name = self._require_text(user_name, "Contributor name")
        if user_name.lower() not in (name.lower() for name in self._contributors):
            self._contributors.append(user_name)

    def has_contributor(self, user_name):
        return user_name.lower() in (name.lower() for name in self._contributors)

    def complete(self):
        if self.is_complete:
            raise ValueError(f"Task '{self.title}' is already complete.")
        self._status = self.DONE
        self._completed_at = datetime.now().isoformat(timespec="seconds")

    def to_dict(self):
        return {
            **self._base_dict(),
            "title": self.title,
            "status": self.status,
            "contributors": self.contributors,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            title=data["title"],
            status=data.get("status", cls.TODO),
            contributors=data.get("contributors", []),
            completed_at=data.get("completed_at"),
            id=data.get("id"),
            created_at=data.get("created_at"),
        )