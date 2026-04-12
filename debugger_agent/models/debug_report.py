"""Data model for a single detected error."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ErrorEntry:
    tool: str         # "ast" | "flake8" | "pylint"
    type: str         # error code or symbolic name
    line: int         # 1-based line number (0 = file-level)
    message: str      # human-readable description


@dataclass
class DebugReport:
    errors: List[ErrorEntry] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "DebugReport":
        entries = [ErrorEntry(**e) for e in data.get("errors", [])]
        return cls(errors=entries)

    def to_dict(self) -> dict:
        return {"errors": [vars(e) for e in self.errors]}

    def __len__(self):
        return len(self.errors)

    def __bool__(self):
        return bool(self.errors)
