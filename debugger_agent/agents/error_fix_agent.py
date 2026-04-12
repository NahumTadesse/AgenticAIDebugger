"""
Fix Agent — uses Google ADK (Gemini) to intelligently fix detected errors.

Requirements:
    pip install google-adk google-generativeai

Set your API key before running:
    export GOOGLE_API_KEY="your-key-here"
    (or GEMINI_API_KEY — either is accepted)

If the ADK / API key is unavailable the agent falls back gracefully
and returns the original code unchanged with an explanatory note.
"""

import os
import re

# ---------------------------------------------------------------------------
# Try to import the Google ADK / Generative AI SDK
# ---------------------------------------------------------------------------
try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


def _build_prompt(code: str, report: dict) -> str:
    """Build a clear, constrained prompt for Gemini."""
    error_lines = []
    for e in report.get("errors", []):
        error_lines.append(
            f"  - Line {e['line']} [{e['tool']}] {e['type']}: {e['message']}"
        )
    errors_text = "\n".join(error_lines) if error_lines else "  (none)"

    return f"""You are an expert Python debugger. Fix ALL of the errors listed below in the code.

RULES:
1. Return ONLY the corrected Python code — no explanations, no markdown fences, no commentary.
2. Preserve the original logic and indentation style.
3. Do NOT add new features or refactor beyond what is needed to fix the errors.
4. If an error cannot be fixed automatically, leave a short inline comment: # FIX NEEDED: <reason>

ERRORS TO FIX:
{errors_text}

CODE:
{code}
"""


def _extract_code(raw: str) -> str:
    """Strip any accidental markdown fences Gemini might return."""
    # Remove ```python ... ``` or ``` ... ```
    fenced = re.match(r"```(?:python)?\n(.*?)```", raw, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    return raw.strip()


def fix_errors(code: str, report: dict) -> tuple[str, str]:
    """
    Attempt to fix errors in `code` using Google Gemini via the ADK.

    Returns:
        (fixed_code: str, fix_note: str)
        - fixed_code: the corrected code (or original if fixing failed)
        - fix_note:   human-readable explanation of what happened
    """
    if not report.get("errors"):
        return code, "No errors to fix."

    # --- Check API availability ---
    if not _GENAI_AVAILABLE:
        return code, (
            "Fix Agent skipped: google-generativeai is not installed. "
            "Run:  pip install google-adk google-generativeai"
        )

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return code, (
            "Fix Agent skipped: GOOGLE_API_KEY (or GEMINI_API_KEY) environment "
            "variable is not set. Export it before running."
        )

    # --- Call Gemini ---
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = _build_prompt(code, report)
        response = model.generate_content(prompt)
        fixed_code = _extract_code(response.text)

        if not fixed_code:
            return code, "Fix Agent: Gemini returned an empty response. Original code kept."

        return fixed_code, f"Fix Agent: applied Gemini fixes ({len(report['errors'])} error(s) addressed)."

    except Exception as exc:  # broad catch so we never crash the pipeline
        return code, f"Fix Agent error: {exc}. Original code kept."
