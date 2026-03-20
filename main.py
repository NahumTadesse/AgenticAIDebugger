from controller.system_controller import run_debugger

if __name__ == "__main__":
    print("Paste your code. Type END on a new line when finished:")

    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)

    code = "\n".join(lines)

    fixed_code, report, documentation = run_debugger(code)

    print("\nCorrected Code:")
    print(fixed_code)

    print("\nDetection Report:")
    print(report)

    print("\nDocumentation:")
    print(documentation)