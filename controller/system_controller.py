from agents.error_detect_agent import detect_errors
from agents.error_fix_agent import fix_errors
from agents.documentation_agent import generate_documentation

MAX_ITERATIONS = 3


def run_debugger(code: str) -> tuple[str, dict, dict]:
    report = detect_errors(code)
    fix_notes = []
    iteration = 0

    while report["errors"] and iteration < MAX_ITERATIONS:
        iteration += 1
        prev_error_count = len(report["errors"])

        fixed_code, note = fix_errors(code, report)
        fix_notes.append(f"Iteration {iteration}: {note}")

        # If the fix agent couldn't do anything (no API key, not installed, etc.)
        # break immediately — looping is pointless
        if fixed_code == code:
            fix_notes.append("Fix Agent returned unchanged code — stopping loop early.")
            break

        code = fixed_code
        report = detect_errors(code)

        # No improvement? Stop to avoid wasting API quota
        if len(report["errors"]) >= prev_error_count:
            fix_notes.append(
                f"Iteration {iteration}: error count did not decrease "
                f"({prev_error_count} → {len(report['errors'])}) — stopping loop."
            )
            break

    if not report["errors"]:
        fix_notes.append("All errors resolved.")

    documentation = generate_documentation(
        code, report,
        iterations=iteration,
        fix_notes=fix_notes
    )

    return code, report, documentation
