"""Reusable, configurable client for a local Ollama chat model.

This class is intentionally generic: it knows how to talk to a chat model, but
nothing about projects or tasks. Any feature (summaries, risk notes, a future
web API) can reuse it by building its own prompt and calling send().
"""

import os

try:
    import ollama
except ImportError:  # Lets the rest of the app run even if ollama isn't installed.
    ollama = None


class AIServiceError(RuntimeError):
    """Raised when the AI service can't be reached or returns an unusable reply."""


class OllamaChatClient:
    DEFAULT_MODEL = "llama3.2"

    def __init__(self, model=None, host=None, system_prompt=None, client=None):
        # Settings can come from arguments or environment variables, so the
        # model or server can change without editing code.
        self.model = model or os.getenv("OLLAMA_MODEL", self.DEFAULT_MODEL)
        self.host = host or os.getenv("OLLAMA_HOST")
        self.system_prompt = system_prompt
        # An existing client can be passed in (dependency injection), which is
        # how the tests swap in a fake instead of a real Ollama server.
        self._client = client

    def _get_client(self):
        if self._client is not None:
            return self._client
        if ollama is None:
            raise AIServiceError(
                "The 'ollama' package is not installed. Run: pip install -r requirements.txt"
            )
        self._client = ollama.Client(host=self.host) if self.host else ollama.Client()
        return self._client

    def build_messages(self, prompt):
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def send(self, prompt):
        """Send one prompt and return the model's reply as text."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        try:
            response = self._get_client().chat(
                model=self.model, messages=self.build_messages(prompt.strip())
            )
        except AIServiceError:
            raise
        except Exception as error:
            raise AIServiceError(
                f"Could not reach the AI model '{self.model}'. Is Ollama running? ({error})"
            ) from error

        content = self._extract_content(response)
        if not content:
            raise AIServiceError("The AI model returned an empty response.")
        return content

    @staticmethod
    def _extract_content(response):
        """Handle both dictionary-style and object-style ollama responses."""
        message = response.get("message") if isinstance(response, dict) else getattr(response, "message", None)
        content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
        return content.strip() if isinstance(content, str) else ""