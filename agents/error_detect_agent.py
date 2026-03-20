import ast
import subprocess
import tempfile
import re


def detect_errors(code):
    errors = []

    # AST detection
    try:
        ast.parse(code)
    except SyntaxError as e:
        errors.append({
            "tool": "ast",
            "type": "syntax_error",
            "line": e.lineno,
            "message": e.msg
        })

    # write code to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as f:
        f.write(code)
        temp_file = f.name

    # flake8 detection
    flake_result = subprocess.run(
        ["flake8", temp_file],
        capture_output=True,
        text=True
    )

    if flake_result.stdout:
        for line in flake_result.stdout.strip().split("\n"):
            match = re.match(r".+:(\d+):\d+:\s([A-Z]\d+)\s(.+)", line)
            if match:
                line_number = int(match.group(1))
                error_code = match.group(2)
                message = match.group(3)

                errors.append({
                    "tool": "flake8",
                    "type": error_code,
                    "line": line_number,
                    "message": message
                })

    # pylint detection
    pylint_result = subprocess.run(
        ["pylint", temp_file, "--disable=all", "--enable=E"],
        capture_output=True,
        text=True
    )

    if pylint_result.stdout:
        for line in pylint_result.stdout.strip().split("\n"):
            match = re.match(r".+:(\d+):\d+:\s([A-Z]\d+):\s(.+?)\s\((.+)\)", line)
            if match:
                line_number = int(match.group(1))
                error_code = match.group(2)
                message = match.group(3)
                error_type = match.group(4)

                errors.append({
                    "tool": "pylint",
                    "type": error_type,
                    "line": line_number,
                    "message": message
                })

    return {"errors": errors}