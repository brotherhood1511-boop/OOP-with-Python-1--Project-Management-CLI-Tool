"""Small reusable helpers shared across the app."""

import re
from datetime import date

from tabulate import tabulate

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email):
    """Return a cleaned email address or raise ValueError if it looks invalid."""
    email = (email or "").strip()
    if not EMAIL_PATTERN.match(email):
        raise ValueError(f"'{email}' is not a valid email address.")
    return email.lower()


def parse_due_date(value):
    """Accept None or a YYYY-MM-DD string and return an ISO date string or None."""
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value).strip()).isoformat()
    except ValueError:
        raise ValueError(f"Due date '{value}' must use the format YYYY-MM-DD.") from None


def make_table(rows, headers):
    """Render rows as a readable grid table using the tabulate package."""
    if not rows:
        return "(nothing to show)"
    return tabulate(rows, headers=headers, tablefmt="rounded_outline")

def truncate(text, width=40):
    text = text or ""
    return text if len(text) <= width else text[: width - 3] + "..."
