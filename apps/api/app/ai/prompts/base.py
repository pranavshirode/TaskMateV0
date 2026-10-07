"""Base prompt template with version tracking."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PromptTemplate:
    """A versioned prompt template.

    All prompts used in production must have a version.
    This enables evaluation comparison across prompt iterations.
    """
    name: str
    version: str
    template: str
    description: str = ""

    @property
    def versioned_name(self) -> str:
        """Return the full versioned name, e.g. 'task_creation_v1'."""
        return f"{self.name}_{self.version}"

    def render(self, **kwargs: Any) -> str:
        """Render the template with the given variables."""
        return self.template.format(**kwargs)
