import ast
import os
import re
import subprocess
import tempfile


def detect_errors(code: str) -> dict:
    """
    Detect errors in the provided Python code using AST, Flake8, and Pylint.
    Returns a deduplicated, structured JSON-compatible error report.
    """
    errors = []
    seen = set()  # used for deduplication

    def add_error(tool, error_type, line, message):
        key = (line, message.strip())
        if key not in seen:
            seen.add(key)
            errors.append({
                "tool": tool,
                "type": error_type,
                "line": line,
                "message": message.strip()
            })

    # --- AST syntax check ---
    try:
        ast.parse(code)
    except SyntaxError as e:
        add_error("ast", "syntax_error", e.lineno or 0, e.msg)
        # Syntax errors block linters, return early
        return {"errors": errors}

    # --- Write to temp file ---
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".py", mode="w", encoding="utf-8"
        ) as f:
            f.write(code)
            temp_file = f.name

        # --- Flake8 ---
        try:
            flake_result = subprocess.run(
                ["flake8", "--max-line-length=120", temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            for line in flake_result.stdout.strip().splitlines():
                match = re.match(r".+:(\d+):\d+:\s([A-Z]\d+)\s(.+)", line)
                if match:
                    add_error(
                        "flake8",
                        match.group(2),
                        int(match.group(1)),
                        match.group(3)
                    )
        except FileNotFoundError:
            errors.append({"tool": "flake8", "type": "setup_error", "line": 0,
                           "message": "flake8 not installed. Run: pip install flake8"})
        except subprocess.TimeoutExpired:
            errors.append({"tool": "flake8", "type": "timeout", "line": 0,
                           "message": "flake8 timed out"})

        # --- Pylint (errors + warnings only, no convention noise) ---
        try:
            pylint_result = subprocess.run(
                [
                    "pylint", temp_file,
                    "--disable=all",
                    "--enable=E,W",          # errors AND warnings
                    "--output-format=text",
                    "--score=no",
                    "--msg-template={line}:{column}: {msg_id}: {msg} ({symbol})"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            for line in pylint_result.stdout.strip().splitlines():
                match = re.match(r"(\d+):\d+:\s([A-Z]\d+):\s(.+?)\s\((.+)\)", line)
                if match:
                    add_error(
                        "pylint",
                        match.group(4),          # symbolic name e.g. undefined-variable
                        int(match.group(1)),
                        match.group(3)
                    )
        except FileNotFoundError:
            errors.append({"tool": "pylint", "type": "setup_error", "line": 0,
                           "message": "pylint not installed. Run: pip install pylint"})
        except subprocess.TimeoutExpired:
            errors.append({"tool": "pylint", "type": "timeout", "line": 0,
                           "message": "pylint timed out"})

    finally:
        # Always clean up temp file
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)

    return {"errors": errors}
