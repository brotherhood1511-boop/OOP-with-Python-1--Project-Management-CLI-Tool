"""Shared behavior for every model in the tracker."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime


class BaseModel(ABC):
    """Base class that gives every model an id, a created timestamp and a
    common contract for converting to and from JSON-ready dictionaries."""

    def __init__(self, id=None, created_at=None):
        self._id = id or uuid.uuid4().hex[:8]
        self._created_at = created_at or datetime.now().isoformat(timespec="seconds")

    @property
    def id(self):
        return self._id

    @property
    def created_at(self):
        return self._created_at

    @staticmethod
    def _require_text(value, field_name):
        """Validate that a field is a non-blank string and return it stripped."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} cannot be empty.")
        return value.strip()

    def _base_dict(self):
        return {"id": self.id, "created_at": self.created_at}

    @abstractmethod
    def to_dict(self):
        """Return a JSON-serializable dictionary for this object."""

    @classmethod
    @abstractmethod
    def from_dict(cls, data):
        """Rebuild an object from a dictionary produced by to_dict()."""

    def __repr__(self):
        return f"<{type(self).__name__} {self.id}>"