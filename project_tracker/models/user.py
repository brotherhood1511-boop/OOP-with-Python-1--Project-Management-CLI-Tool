"""User model. One user owns many projects (one-to-many)."""

from project_tracker.models.base import BaseModel
from project_tracker.models.project import Project
from project_tracker.utils import validate_email


class User(BaseModel):
    def __init__(self, name, email=None, projects=None, **base):
        super().__init__(**base)
        self.name = name
        self.email = email
        self._projects = list(projects or [])

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = self._require_text(value, "User name")

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = validate_email(value) if value else None

    @property
    def projects(self):
        return list(self._projects)

    def add_project(self, project):
        if not isinstance(project, Project):
            raise TypeError("Only Project objects can be added to a user.")
        self._projects.append(project)
        return project

    def get_project(self, title):
        for project in self._projects:
            if project.title.lower() == title.strip().lower():
                return project
        return None

    def to_dict(self):
        return {
            **self._base_dict(),
            "name": self.name,
            "email": self.email,
            "projects": [project.to_dict() for project in self._projects],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            email=data.get("email"),
            projects=[Project.from_dict(project) for project in data.get("projects", [])],
            id=data.get("id"),
            created_at=data.get("created_at"),
        )