def generate_documentation(
    original_code,
    corrected_code,
    initial_report,
    final_report,
    iterations_used=0,
    max_iterations=3
):
    doc = []
    doc.append("## Debugging Report\n")

    doc.append("### Summary\n")

    initial_errors = initial_report.get("errors", [])
    final_errors = final_report.get("errors", [])

    doc.append(f"- Initial Issues Detected: {len(initial_errors)}")
    doc.append(f"- Remaining Issues: {len(final_errors)}")
    doc.append(f"- Iterations Used: {iterations_used}/{max_iterations}\n")

    doc.append("### Code Structure\n")

    lines = corrected_code.strip().split("\n")
    functions_found = []

    for line in lines:
        if line.strip().startswith("def "):
            func_name = line.split("(")[0].replace("def", "").strip()
            functions_found.append(func_name)

    if functions_found:
        for f in functions_found:
            doc.append(f"- Function `{f}` defined")
    else:
        doc.append("- No functions detected")

    doc.append("")

    doc.append("### Initial Errors Detected\n")

    if not initial_errors:
        doc.append("- No errors found in original code\n")
    else:
        for err in initial_errors:
            doc.append(
                f"- Line {err['line']}: `{err['type']}` → {err['message']}"
            )

    doc.append("")
    doc.append("### Remaining Issues After Fixing\n")

    if not final_errors:
        doc.append("- All detected issues were resolved\n")
    else:
        for err in final_errors:
            doc.append(
                f"- Line {err['line']}: `{err['type']}` → {err['message']}"
            )

    doc.append("")
    doc.append("### Original Code\n")
    doc.append("```python")
    doc.append(original_code)
    doc.append("```")


    doc.append("\n### Corrected Code\n")
    doc.append("```python")
    doc.append(corrected_code)
    doc.append("```")

    return "\n".join(doc)
