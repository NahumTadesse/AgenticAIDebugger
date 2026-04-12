# Agentic AI Debugger — Google ADK Version

## Folder structure (ADK requires this exact layout)

```
adk_debugger/                  ← run ALL commands from here
├── requirements.txt
└── debugger_agent/            ← ADK discovers this folder
    ├── __init__.py
    ├── agent.py               ← root_agent lives here
    ├── .env                   ← your API key goes here
    └── tests/
        └── sample_bug.py      ← broken code for testing
```

## Setup (do this once)

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key to debugger_agent/.env
#    Open the file and replace:  your-key-here  with your real key
#    Get a free key at: https://aistudio.google.com/app/apikey
```

## Running with ADK

You MUST be inside the `adk_debugger/` folder for all commands below.

### Option A — Web UI (recommended for testing)
Opens a browser interface where you can chat with the agent:
```bash
adk web
```
Then open http://localhost:8000 in your browser.
Type something like:
> Please debug this code: `def greet(name)\n    print(name`

### Option B — Terminal chat
```bash
adk run debugger_agent
```

### Option C — Single message (scripted)
```bash
adk run debugger_agent --message "Debug this Python code: x = 1/0"
```

## How to give it code to debug

In the web UI or terminal, paste your code like this:

```
Please debug this Python code:

def greet(name)
    print("Hello " + name

x = 1/0
greet("world")
```

The agent will:
1. Run AST + Flake8 + Pylint on your code
2. Send errors to Gemini to fix (up to 3 attempts)
3. Show you the fixed code and a full report
