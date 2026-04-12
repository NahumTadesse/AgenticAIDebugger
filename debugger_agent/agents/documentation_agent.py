"""
Documentation Agent — generates a Markdown debugging summary.

Uses Google Gemini if available; falls back to a structured plain-text
summary so the pipeline always produces *something* useful.
"""

import os
from datetime import datetime

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Fallback: deterministic documentation (no AI required)
# ---------------------------------------------------------------------------

def _build_fallback_doc(code: str, report: dict, iterations: int, fix_notes: list[str]) -> str:
    errors = report.get("errors", [])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Agentic Debugger — Session Report",
        f"**Generated:** {timestamp}  ",
        f"**Refinement iterations:** {iterations}  ",
        f"**Remaining issues:** {len(errors)}",
        "",
        "## Fix Notes",
    ]
    for note in fix_notes:
        lines.append(f"- {note}")

    lines += ["", "## Remaining Errors"]
    if errors:
        for e in errors:
            lines.append(
                f"- **Line {e['line']}** `[{e['tool']}]` `{e['type']}`: {e['message']}"
            )
    else:
        lines.append("✅ No errors detected.")

    lines += [
        "",
        "## Final Code",
        "```python",
        code.strip(),
        "```",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# AI-powered documentation
# ---------------------------------------------------------------------------

def _build_ai_prompt(code: str, report: dict, iterations: int, fix_notes: list[str]) -> str:
    errors = report.get("errors", [])
    error_text = "\n".join(
        f"  - Line {e['line']} [{e['tool']}] {e['type']}: {e['message']}"
        for e in errors
    ) or "  None"

    notes_text = "\n".join(f"  - {n}" for n in fix_notes) or "  None"

    return f"""You are a technical writer. Write a concise Markdown debugging report for a developer.

Include:
1. A one-paragraph executive summary of what was fixed.
2. A table of any remaining errors (columns: Line | Tool | Type | Message).
3. Inline docstrings or comments added to the final code where helpful.
4. A "Next Steps" section if errors remain.

Do NOT wrap the output in markdown fences — return raw Markdown.

--- INPUT ---
Iterations run: {iterations}
Fix notes:
{notes_text}

Remaining errors:
{error_text}

Final code:
{code}
"""


def generate_documentation(
    code: str,
    report: dict,
    iterations: int = 0,
    fix_notes: list[str] | None = None
) -> dict:
    """
    Generate a documentation summary of the debugging session.

    Returns:
        {"summary": "<markdown string>"}
    """
    if fix_notes is None:
        fix_notes = []

    # Try AI-powered docs
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if _GENAI_AVAILABLE and api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = _build_ai_prompt(code, report, iterations, fix_notes)
            response = model.generate_content(prompt)
            summary = response.text.strip()
            if summary:
                return {"summary": summary, "source": "gemini"}
        except Exception:
            pass  # Fall through to deterministic fallback

    # Fallback
    return {
        "summary": _build_fallback_doc(code, report, iterations, fix_notes),
        "source": "fallback"
    }
