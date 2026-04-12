"""
Agentic AI Debugger — Google ADK agent definition.
 
Pipeline:
  1. detection_agent    — find ALL crash-causing errors in one pass
  2. fix_loop_agent     — fix ALL errors at once, verify, repeat max 3 times
  3. documentation_agent — write a clean session report in plain English
"""
 
import json
import ast
import os
import re
import subprocess
import tempfile
 
from google.adk.agents import Agent, SequentialAgent, LoopAgent
 
 
IGNORE_CODES = {
    "W291", "W292", "W293", "W391", "W503", "W504",
    "E101", "E111", "E114", "E117", "E121", "E122",
    "E123", "E124", "E125", "E126", "E127", "E128",
    "E131", "E133", "E201", "E202", "E203", "E211",
    "E225", "E226", "E227", "E228", "E231", "E241",
    "E242", "E251", "E261", "E262", "E265", "E266",
    "E271", "E272", "E301", "E302", "E303", "E304",
    "E305", "E306", "E401", "E501", "E502",
    "W601", "W602", "W603", "W604",
    "C0103", "C0111", "C0114", "C0115", "C0116",
    "C0301", "C0303", "C0304", "C0305", "C0321",
    "C0325", "C0326", "C0330", "C0411", "C0412",
    "R0201", "R0903", "R0914", "R0915", "R1705",
    "W0107", "W0108", "W0301", "W0311", "W0312",
    "W0401", "W0611",
}
 
FATAL_PYLINT = {
    "undefined-variable", "undefined-loop-variable", "used-before-assignment",
    "not-callable", "no-member", "unsubscriptable-object",
    "unsupported-assignment-operation", "unsupported-delete-operation",
    "invalid-unary-operand-type", "unsupported-binary-operation",
    "missing-kwoa", "too-many-positional-arguments", "unexpected-keyword-arg",
    "redundant-keyword-arg", "missing-positional-args", "no-value-for-argument",
    "too-many-function-args", "import-error", "module-not-found",
    "division-by-zero", "invalid-sequence-index", "invalid-slice-index",
}
 
 
def _run_linters(code: str) -> list:
    errors = []
    seen = set()
 
    def add(tool, etype, line, msg):
        key = (line, msg.strip())
        if key not in seen:
            seen.add(key)
            errors.append({"tool": tool, "type": etype, "line": line, "message": msg.strip()})
 
    try:
        ast.parse(code)
    except SyntaxError as e:
        add("ast", "syntax_error", e.lineno or 0, e.msg)
        return errors
 
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as f:
            f.write(code)
            temp_file = f.name
 
        try:
            r = subprocess.run(
                ["flake8", "--max-line-length=999", "--select=E7,E9,F", temp_file],
                capture_output=True, text=True, timeout=30
            )
            for line in r.stdout.strip().splitlines():
                m = re.match(r".+:(\d+):\d+:\s([A-Z]\d+)\s(.+)", line)
                if m and m.group(2) not in IGNORE_CODES:
                    add("flake8", m.group(2), int(m.group(1)), m.group(3))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
 
        try:
            r = subprocess.run(
                ["pylint", temp_file, "--disable=all", "--enable=E",
                 "--output-format=text", "--score=no",
                 "--msg-template={line}:{column}: {msg_id}: {msg} ({symbol})"],
                capture_output=True, text=True, timeout=30
            )
            for line in r.stdout.strip().splitlines():
                m = re.match(r"(\d+):\d+:\s([A-Z]\d+):\s(.+?)\s\((.+)\)", line)
                if m:
                    symbol = m.group(4)
                    if symbol in FATAL_PYLINT or m.group(2).startswith("E"):
                        add("pylint", symbol, int(m.group(1)), m.group(3))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
 
    return errors
 
 
# ---------------------------------------------------------------------------
# Tool 1: Detect all crash-causing errors
# ---------------------------------------------------------------------------
 
def detect_all_errors(code: str) -> dict:
    """Scan entire code. Return all crash-causing errors in one pass."""
    errors = _run_linters(code)
    clean = len(errors) == 0
    return {
        "original_code": code,
        "error_count": len(errors),
        "errors": errors,
        "errors_json": json.dumps({"errors": errors}),
        "clean": clean,
        "summary": "Code is clean!" if clean else f"{len(errors)} crash-causing error(s) found."
    }
 
 
# ---------------------------------------------------------------------------
# Tool 2: Fix ALL errors at once in one Gemini call
# ---------------------------------------------------------------------------
 
def fix_all_errors(code: str, errors_json: str) -> dict:
    """Fix all errors in one Gemini call. Returns fixed code + plain English change list."""
    try:
        errors = json.loads(errors_json).get("errors", [])
    except Exception:
        errors = []
 
    if not errors:
        return {
            "fixed_code": code,
            "changes": [],
            "clean": True,
            "escalate": True
        }
 
    error_list = "\n".join(
        f"  Line {e['line']} [{e['tool']}] {e['type']}: {e['message']}"
        for e in errors
    )
 
    prompt = f"""You are an expert Python debugger. Fix ALL errors below in one pass.
 
Return a JSON object with exactly two keys:
- "fixed_code": the complete corrected Python code as a string
- "changes": a list of plain English strings describing each change made,
  written exactly like these examples:
  "Added missing colon after def process_data(data) on line 1"
  "Added division-by-zero guard using if len(data) > 0 on line 3"
  "Changed range(10) to range(min(len(data), 10)) on line 8 to prevent IndexError"
  "Defined missing variable result on line 10"
 
Rules:
- Fix EVERY error listed
- Keep original logic intact
- Return ONLY the JSON — no markdown, no extra text
 
ERRORS ({len(errors)} total):
{error_list}
 
CODE:
{code}
 
JSON:"""
 
    def parse_gemini(text):
        text = re.sub(r"^```(?:json|python)?\n?", "", text.strip())
        text = re.sub(r"\n?```$", "", text.strip())
        return json.loads(text.strip())
 
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"fixed_code": code, "changes": [], "clean": False, "escalate": True}
 
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        parsed = parse_gemini(response.text)
        return {
            "fixed_code": parsed.get("fixed_code", code),
            "changes": parsed.get("changes", []),
            "clean": False,
            "escalate": False
        }
    except Exception as exc:
        return {"fixed_code": code, "changes": [], "clean": False, "escalate": True,
                "note": str(exc)}
 
 
# ---------------------------------------------------------------------------
# Tool 3: Verify fixed code
# ---------------------------------------------------------------------------
 
def verify_and_check(fixed_code: str) -> dict:
    """Re-scan the fixed code. escalate=True stops the loop when clean."""
    errors = _run_linters(fixed_code)
    clean = len(errors) == 0
    return {
        "fixed_code": fixed_code,
        "error_count": len(errors),
        "errors_json": json.dumps({"errors": errors}),
        "clean": clean,
        "escalate": clean,
        "summary": "Code is clean!" if clean else f"{len(errors)} error(s) remain."
    }
 
 
# ---------------------------------------------------------------------------
# Tool 4: Generate session report in plain English
# ---------------------------------------------------------------------------
 
def generate_report(original_code: str, final_code: str, changes_json: str, all_errors_resolved: bool) -> dict:
    """
    Write the session report in plain English matching this exact format:
    - Status line
    - Bullet list of changes made
    - Final code block
    """
    from datetime import datetime
 
    try:
        changes = json.loads(changes_json) if changes_json else []
    except Exception:
        changes = []
 
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 
    if all_errors_resolved:
        status = "The code has been fixed and verified. All errors have been resolved."
    elif not changes:
        status = "The code was already clean — no changes were needed."
    else:
        status = "The code has been partially fixed. Some errors could not be resolved automatically."
 
    lines = [
        f"**Generated:** {timestamp}",
        "",
        status,
        "",
    ]
 
    if changes:
        lines.append("Here's a summary of the changes made:")
        for c in changes:
            lines.append(f"* {c}")
    else:
        lines.append("No changes were made.")
 
    lines += [
        "",
        "Here's the final, corrected code:",
        "",
        "```python",
        final_code.strip(),
        "```"
    ]
 
    return {"report": "\n".join(lines)}
 
 
# ---------------------------------------------------------------------------
# ADK Agent definitions
# ---------------------------------------------------------------------------
 
detection_agent = Agent(
    name="detection_agent",
    model="gemini-2.5-flash",
    description="Scans entire Python code and returns ALL crash-causing errors.",
    instruction=(
        "You are a code analysis agent.\n"
        "1. Call detect_all_errors with the exact code the user provided.\n"
        "2. Tell the user what errors were found.\n"
        "3. Do NOT fix anything."
    ),
    tools=[detect_all_errors],
)
 
fix_loop_agent = LoopAgent(
    name="fix_loop_agent",
    description="Fixes ALL errors at once per cycle, verifies, repeats max 3 times.",
    sub_agents=[
        Agent(
            name="fixer_agent",
            model="gemini-2.5-flash",
            description="Fixes all errors in one Gemini call then verifies.",
            instruction=(
                "You are a code fixing agent. Each cycle do EXACTLY 2 steps:\n"
                "STEP 1: Call fix_all_errors with the current code and errors_json.\n"
                "STEP 2: Call verify_and_check with the fixed_code from step 1.\n"
                "STOP. Do not call either tool more than once per cycle.\n"
                "If verify_and_check returns clean=True the loop stops automatically."
            ),
            tools=[fix_all_errors, verify_and_check],
        )
    ],
    max_iterations=3,
)
 
documentation_agent = Agent(
    name="documentation_agent",
    model="gemini-2.5-flash",
    description="Writes the final session report in plain English.",
    instruction=(
        "You are a documentation agent.\n"
        "Call generate_report with:\n"
        "  - original_code: the original code the user submitted\n"
        "  - final_code: the fully fixed code from the fixer agent\n"
        "  - changes_json: a JSON array string of the changes list from fix_all_errors\n"
        "  - all_errors_resolved: true if verify_and_check returned clean=True, else false\n"
        "Then show the report to the user exactly as returned — do not reformat it."
    ),
    tools=[generate_report],
)
 
root_agent = SequentialAgent(
    name="agentic_debugger",
    description=(
        "Multi-agent Python debugger: detects ALL crash-causing errors, "
        "fixes ALL errors per cycle (max 3 cycles), then writes a plain English report."
    ),
    sub_agents=[detection_agent, fix_loop_agent, documentation_agent],
)
 