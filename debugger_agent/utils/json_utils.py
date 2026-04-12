"""Utility helpers for JSON handling across the pipeline."""

import json


def pretty(data: dict | list) -> str:
    """Return a pretty-printed JSON string."""
    return json.dumps(data, indent=2)


def safe_load(text: str) -> dict | None:
    """
    Safely parse a JSON string, stripping any markdown fences first.
    Returns None on failure instead of raising.
    """
    # Strip ```json ... ``` fences
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        stripped = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return None
