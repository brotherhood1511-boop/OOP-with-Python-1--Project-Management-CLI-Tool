"""Project-specific AI feature: summaries and next-step suggestions.

The summarizer turns project data into a prompt and hands it to any client
with a send(prompt) method. It also has an offline summary built from the data
alone, used when the AI service is unavailable.
"""

from datetime import date


class ProjectSummarizer:
    SYSTEM_PROMPT = (
        "You are a concise assistant for a software team's project tracker. "
        "Only use the project data you are given. Do not invent tasks, people or dates."
    )

    def __init__(self, client):
        self.client = client

    def build_prompt(self, project):
        lines = [
            f"Project: {project.title}",
            f"Owner: {project.owner}",
            f"Description: {project.description or 'None given'}",
            f"Due date: {project.due_date or 'None set'}",
            f"Today: {date.today().isoformat()}",
            f"Progress: {project.completed_count} of {len(project.tasks)} tasks complete ({project.progress}%)",
            "Tasks:",
        ]
        for task in project.tasks:
            people = ", ".join(task.contributors) or "unassigned"
            lines.append(f"- [{task.status}] {task.title} (contributors: {people})")
        if not project.tasks:
            lines.append("- No tasks yet")

        lines += [
            "",
            "Write a short project update with exactly these three sections:",
            "Summary:",
            "Risks:",
            "Next Steps:",
            "Keep each section to 1-3 sentences or bullets.",
        ]
        return "\n".join(lines)

    def summarize(self, project):
        """Return an AI-written summary. Raises AIServiceError if the service fails."""
        return self.client.send(self.build_prompt(project))

    def offline_summary(self, project):
        """A rule-based summary built only from the data, with no AI call."""
        open_tasks = [task for task in project.tasks if not task.is_complete]
        unassigned = [task for task in open_tasks if not task.contributors]

        summary = (
            f"'{project.title}' (owner: {project.owner}) is {project.status}: "
            f"{project.completed_count} of {len(project.tasks)} tasks done ({project.progress}%)."
        )

        risks = []
        if project.due_date and open_tasks:
            days_left = (date.fromisoformat(project.due_date) - date.today()).days
            if days_left < 0:
                risks.append(f"Overdue by {-days_left} day(s) with {len(open_tasks)} task(s) open.")
            elif days_left <= 3:
                risks.append(f"Due in {days_left} day(s) with {len(open_tasks)} task(s) open.")
        if unassigned:
            risks.append(f"{len(unassigned)} open task(s) have no contributor.")
        if not project.tasks:
            risks.append("No tasks have been planned yet.")

        if not project.tasks:
            next_steps =["Break the project into tasks with add-task."]
        elif not open_tasks:
            next_steps = ["All tasks are done. Review and close out the project."]
        else:
            next_steps = [f"Finish '{task.title}'." for task in open_tasks[:3]]
            if unassigned:
                next_steps.append(f"Assign someone to '{unassigned[0].title}'.")

        return "\n".join(
            [
                "Summary:",
                summary,
                "",
                "Risks:",
                *(f"- {risk}" for risk in risks or ["No obvious risks from the current data."]),
                "",
                "Next Steps:",
                *(f"- {step}" for step in next_steps),
            ]
        )