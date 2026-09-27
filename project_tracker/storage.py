"""JSON file persistence with error handling."""

import json
import os
import tempfile


class StorageError(Exception):
    """Raised when the data file can't be read or written."""


class JSONStorage:
    """Loads and saves a dictionary to a JSON file.

    Saving writes to a temporary file first and then swaps it into place, so a
    crash halfway through a save can't leave a half-written, corrupted file.
    """

    def __init__(self, path):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return {"users": []}
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise StorageError(
                f"Data file '{self.path}' is not valid JSON (line {error.lineno}). "
                "Fix or delete it and try again."
            ) from error
        except OSError as error:
            raise StorageError(f"Could not read data file '{self.path}': {error}") from error

        if not isinstance(data, dict) or not isinstance(data.get("users", []), list):
            raise StorageError(f"Data file '{self.path}' does not have the expected structure.")
        data.setdefault("users", [])
        return data

    def save(self, data):
        directory = os.path.dirname(os.path.abspath(self.path))
        try:
            os.makedirs(directory, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
            os.replace(temp_path, self.path)
        except OSError as error:
            raise StorageError(f"Could not save data file '{self.path}': {error}") from error