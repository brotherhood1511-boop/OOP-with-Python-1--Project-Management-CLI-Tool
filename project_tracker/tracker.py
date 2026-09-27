"""ProjectTracker: the application's business logic.

The tracker owns every user, project and task, enforces the relationships
between them, and handles loading and saving through a storage object. The CLI
only talks to the tracker; it never edits models or files directly.
"""

from project_tracker.models import Project, Task, User
from project_tracker.storage import JSONStorage


class TrackerError(ValueError):
    """A user-facing problem such as a missing user or a duplicate project."""


class ProjectTracker:
    def __init__(self, storage):
        self.storage = storage
        self._users = {}

    # ---------- persistence ----------

    @classmethod
    def from_file(cls, path):
        tracker = cls(JSONStorage(path))
        tracker.load()
        return tracker

    def load(self):
        data = self.storage.load()
        self._users = {}
        for user_data in data["users"]:
            user = User.from_dict(user_data)
            self._users[user.name.lower()] = user

    def save(self):
        self.storage.save({"users": [user.to_dict() for user in self.list_users()]})

    # ---------- users ----------

    def add_user(self, name, email=None):
        user = User(name, email)
        if user.name.lower() in self._users:
            raise TrackerError(f"A user named '{user.name}' already exists.")
        if email and any(u.email == user.email for u in self._users.values()):
            raise TrackerError(f"The email '{user.email}' is already in use.")
        self._users[user.name.lower()] = user
        return user

    def get_user(self, name):
        user = self._users.get((name or "").strip().lower())
        if user is None:
            raise TrackerError(f"No user named '{name}'. Run 'list-users' to see users.")
        return user

    def list_users(self):
        return sorted(self._users.values(), key=lambda user: user.name.lower())

    # ---------- projects ----------

    def all_projects(self):
        return [project for user in self.list_users() for project in user.projects]

    def add_project(self, user_name, title, description="", due_date=None):
        user = self.get_user(user_name)
        if self._find_project(title):
            raise TrackerError(f"A project titled '{title.strip()}' already exists.")
        project = Project(title, owner=user.name, description=description, due_date=due_date)
        return user.add_project(project)

    def _find_project(self, title):
        title = (title or "").strip().lower()
        for project in self.all_projects():
            if project.title.lower() == title:
                return project
        return None

    def get_project(self, title):
        project = self._find_project(title)
        if project is None:
            raise TrackerError(f"No project titled '{title}'. Run 'list-projects' to see projects.")
        return project

    def list_projects(self, user_name=None):
        if user_name:
            return self.get_user(user_name).projects
        return self.all_projects()

    # ---------- tasks ----------

    def add_task(self, project_title, title, contributors=None):
        project = self.get_project(project_title)
        names = [self.get_user(name).name for name in contributors or []]
        try:
            return project.add_task(Task(title, contributors=names))
        except ValueError as error:
            raise TrackerError(str(error)) from error

    def get_task(self, project_title, task_title):
        project = self.get_project(project_title)
        task = project.get_task(task_title)
        if task is None:
            raise TrackerError(
                f"Project '{project.title}' has no task named '{task_title}'. "
                f"Run 'list-tasks --project \"{project.title}\"' to see its tasks."
            )
        return task

    def assign_task(self, project_title, task_title, user_name):
        task = self.get_task(project_title, task_title)
        user = self.get_user(user_name)
        if task.has_contributor(user.name):
            raise TrackerError(f"{user.name} is already a contributor on '{task.title}'.")
        task.add_contributor(user.name)
        return task

    def complete_task(self, project_title, task_title):
        task = self.get_task(project_title, task_title)
        try:
            task.complete()
        except ValueError as error:
            raise TrackerError(str(error)) from error
        return task

    def tasks_for_user(self, user_name):
        """Every (project, task) pair where the user is a contributor."""
        user = self.get_user(user_name)
        return [
            (project, task)
            for project in self.all_projects()
            for task in project.tasks
            if task.has_contributor(user.name)
        ]