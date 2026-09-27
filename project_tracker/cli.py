"""Command-line interface.

The CLI's only jobs are parsing commands, calling the tracker or services, and
printing results. Business rules live in ProjectTracker, and AI logic lives in
the services package.
"""

import argparse
import os
import sys

from project_tracker.services import AIServiceError, OllamaChatClient, ProjectSummarizer
from project_tracker.storage import StorageError
from project_tracker.tracker import ProjectTracker, TrackerError
from project_tracker.utils import make_table, truncate

DEFAULT_DATA_FILE = os.getenv(
    "PM_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tracker.json"),
)


# ---------- command handlers ----------
# Each handler receives the parsed args and the tracker, prints its result and
# returns True if it changed data that needs saving.


def cmd_add_user(args, tracker):
    user = tracker.add_user(args.name, args.email)
    print(f"Added user '{user.name}'" + (f" <{user.email}>." if user.email else "."))
    return True


def cmd_list_users(args, tracker):
    rows = [
        [user.name, user.email or "-", len(user.projects), len(tracker.tasks_for_user(user.name))]
        for user in tracker.list_users()
    ]
    print(make_table(rows, ["Name", "Email", "Projects", "Tasks assigned"]))
    return False


def cmd_add_project(args, tracker):
    project = tracker.add_project(args.user, args.title, args.description, args.due)
    print(f"Added project '{project.title}' for {project.owner}.")
    return True


def cmd_list_projects(args, tracker):
    projects = tracker.list_projects(args.user)
    rows = [
        [
            project.title,
            project.owner,
            truncate(project.description, 35) or "-",
            project.due_date or "-",
            f"{project.completed_count}/{len(project.tasks)} ({project.progress}%)",
            project.status,
        ]
        for project in projects
    ]
    if args.user:
        print(f"Projects for {tracker.get_user(args.user).name}:")
    print(make_table(rows, ["Title", "Owner", "Description", "Due", "Tasks done", "Status"]))
    return False


def cmd_add_task(args, tracker):
    task = tracker.add_task(args.project, args.title, args.assign)
    message = f"Added task '{task.title}' to '{tracker.get_project(args.project).title}'"
    if task.contributors:
        message += f" (contributors: {', '.join(task.contributors)})"
    print(message + ".")
    return True


def cmd_list_tasks(args, tracker):
    if args.user:
        pairs = tracker.tasks_for_user(args.user)
        print(f"Tasks for {tracker.get_user(args.user).name}:")
    else:
        project = tracker.get_project(args.project)
        pairs = [(project, task) for task in project.tasks]
        print(f"Tasks for '{project.title}':")

    rows = [
        [
            project.title,
            task.title,
            "done" if task.is_complete else "todo",
            ", ".join(task.contributors) or "-",
        ]
        for project, task in pairs
    ]
    print(make_table(rows, ["Project", "Task", "Status", "Contributors"]))
    return False


def cmd_assign_task(args, tracker):
    task = tracker.assign_task(args.project, args.task, args.user)
    print(f"Added {tracker.get_user(args.user).name} as a contributor on '{task.title}'.")
    return True


def cmd_complete_task(args, tracker):
    task = tracker.complete_task(args.project, args.task)
    print(f"Marked '{task.title}' as complete.")
    return True


def cmd_summarize_project(args, tracker):
    project = tracker.get_project(args.project)
    summarizer = ProjectSummarizer(
        OllamaChatClient(model=args.model, system_prompt=ProjectSummarizer.SYSTEM_PROMPT)
    )

    if args.offline:
        print(f"Offline summary for '{project.title}':\n")
        print(summarizer.offline_summary(project))
        return False

    try:
        text = summarizer.summarize(project)
        print(f"AI summary for '{project.title}' ({summarizer.client.model}):\n")
        print(text)
    except AIServiceError as error:
        # Graceful failure: explain what went wrong, then still give a useful answer.
        print(f"Warning: {error}", file=sys.stderr)
        print(f"Showing an offline summary for '{project.title}' instead:\n")
        print(summarizer.offline_summary(project))
    return False


    # ---------- parser ----------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="project-tracker",
        description="Manage users, projects and tasks, with AI-assisted project summaries.",
        epilog='Example: python main.py add-user --name "Alex" --email "alex@example.com"',
    )
    parser.add_argument(
        "--data",
        default=DEFAULT_DATA_FILE,
        help="Path to the JSON data file (default: data/tracker.json or $PM_DATA_FILE).",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p = sub.add_parser("add-user", help="Create a new user.")
    p.add_argument("--name", required=True, help="The user's name.")
    p.add_argument("--email", help="The user's email address (optional).")
    p.set_defaults(func=cmd_add_user)

    p = sub.add_parser("list-users", help="Show all users.")
    p.set_defaults(func=cmd_list_users)

    p = sub.add_parser("add-project", help="Create a project owned by a user.")
    p.add_argument("--user", required=True, help="Name of the user who owns the project.")
    p.add_argument("--title", required=True, help="Project title (must be unique).")
    p.add_argument("--description", default="", help="Short project description.")
    p.add_argument("--due", help="Due date in YYYY-MM-DD format.")
    p.set_defaults(func=cmd_add_project)

    p = sub.add_parser("list-projects", help="Show projects, optionally for one user.")
    p.add_argument("--user", help="Only show projects owned by this user.")
    p.set_defaults(func=cmd_list_projects)

    p = sub.add_parser("add-task", help="Add a task to a project.")
    p.add_argument("--project", required=True, help="Title of the project.")
    p.add_argument("--title", required=True, help="Task title.")
    p.add_argument(
        "--assign", nargs="+", metavar="USER", help="One or more users to add as contributors."
    )
    p.set_defaults(func=cmd_add_task)

    p = sub.add_parser("list-tasks", help="Show tasks for a project or for a user.")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--project", help="Show every task in this project.")
    group.add_argument("--user", help="Show every task this user contributes to.")
    p.set_defaults(func=cmd_list_tasks)

    p = sub.add_parser("assign-task", help="Add a user as a contributor on a task.")
    p.add_argument("--project", required=True, help="Title of the project.")
    p.add_argument("--task", required=True, help="Title of the task.")
    p.add_argument("--user", required=True, help="Name of the user to add.")
    p.set_defaults(func=cmd_assign_task)

    p = sub.add_parser("complete-task", help="Mark a task as complete.")
    p.add_argument("--project", required=True, help="Title of the project.")
    p.add_argument("--task", required=True, help="Title of the task.")
    p.set_defaults(func=cmd_complete_task)

    p = sub.add_parser(
        "summarize-project", help="Get an AI summary, risks and next steps for a project."
    )
    p.add_argument("--project", required=True, help="Title of the project.")
    p.add_argument("--model", help="Ollama model to use (default: llama3.2 or $OLLAMA_MODEL).")
    p.add_argument(
        "--offline", action="store_true", help="Skip the AI and use a rule-based summary."
    )
    p.set_defaults(func=cmd_summarize_project)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "func", None):
        parser.print_help()
        return 1

    try:
        tracker = ProjectTracker.from_file(args.data)
        changed = args.func(args, tracker)
        if changed:
            tracker.save()
    except (TrackerError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except StorageError as error:
        print(f"Storage error: {error}", file=sys.stderr)
        return 2
    return 0