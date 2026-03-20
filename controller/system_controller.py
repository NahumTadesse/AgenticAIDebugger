from agents.error_detect_agent import detect_errors
from agents.error_fix_agent import fix_errors
from agents.documentation_agent import generate_documentation

MAX_ITERATIONS = 3

def run_debugger(code):
    report = detect_errors(code)

    iteration = 0

    while report["errors"] and iteration < MAX_ITERATIONS:
        code = fix_errors(code, report)
        report = detect_errors(code)
        iteration += 1

    documentation = generate_documentation(code, report)

    return code, report, documentation