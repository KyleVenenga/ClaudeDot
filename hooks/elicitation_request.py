#!/usr/bin/env python3
"""
Hook: PreToolUse (AskUserQuestion) — elicitation handler.

Behavior depends on the client type detected at session start:
- VS Code: Non-blocking. Writes notification to tray, allows tool through
  so VS Code shows the question natively.
- Terminal: Blocking. Writes pending request, polls for system tray answer,
  then denies the tool and passes the answer via additionalContext.

Can be overridden via elicitation_mode in ~/.claude-helper/config.json.
"""

import json
import os
import signal
import sys
import time
import uuid

STATE_DIR = os.path.expanduser("~/.claude-helper")
CONFIG_FILE = os.path.join(STATE_DIR, "config.json")
RESPONSES_DIR = os.path.join(STATE_DIR, "responses")
POLL_INTERVAL = 0.5
TIMEOUT = 300


def _detect_client(info_file):
    """Detect whether running in VS Code or a standalone terminal."""
    try:
        with open(info_file, "r") as f:
            client = json.load(f).get("client")
            if client:
                return client
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        pass
    entrypoint = os.environ.get("CLAUDE_CODE_ENTRYPOINT", "")
    if "vscode" in entrypoint or os.environ.get("VSCODE_PID"):
        return "vscode"
    return "terminal"


def _get_mode(info_file):
    """Determine elicitation mode. Config file overrides auto-detection."""
    # Explicit config override
    try:
        with open(CONFIG_FILE, "r") as f:
            mode = json.load(f).get("elicitation_mode")
            if mode:
                return mode
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        pass

    # Auto-detect from session client type
    client = _detect_client(info_file)
    # VS Code: show question in VS Code, tray just notifies
    # Terminal: show question in tray with answer options
    return "terminal" if client == "vscode" else "menubar"


def _build_question_data(questions):
    data = []
    for i, q in enumerate(questions):
        data.append({
            "index": i,
            "question": q.get("question", "Question"),
            "header": q.get("header", ""),
            "options": [opt.get("label", str(opt)) for opt in q.get("options", [])],
        })
    return data


def _update_session_status(info_file, status, waiting_for):
    if not os.path.isfile(info_file):
        return
    try:
        with open(info_file, "r") as f:
            info = json.load(f)
        info["status"] = status
        info["waiting_for"] = waiting_for
        info["last_updated"] = int(time.time())
        with open(info_file, "w") as f:
            json.dump(info, f)
    except (json.JSONDecodeError, IOError):
        pass


def _cleanup(*files):
    for f in files:
        try:
            os.unlink(f)
        except FileNotFoundError:
            pass


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = input_data.get("session_id", "")
    if not session_id:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "AskUserQuestion":
        sys.exit(0)

    questions = input_data.get("tool_input", {}).get("questions", [])
    if not questions:
        sys.exit(0)

    session_dir = os.path.join(STATE_DIR, "sessions", session_id)
    pending_dir = os.path.join(session_dir, "pending")
    if not os.path.isdir(session_dir):
        sys.exit(0)

    os.makedirs(pending_dir, exist_ok=True)

    request_id = str(uuid.uuid4())
    question_data = _build_question_data(questions)
    pending_file = os.path.join(pending_dir, f"{request_id}.json")
    info_file = os.path.join(session_dir, "info.json")

    mode = _get_mode(info_file)

    if mode == "menubar":
        _run_menubar_mode(request_id, session_id, question_data, pending_file, info_file)
    else:
        _run_terminal_mode(request_id, session_id, question_data, pending_file, info_file)


def _run_terminal_mode(request_id, session_id, question_data, pending_file, info_file):
    """Non-blocking: write notification, allow tool through."""
    request = {
        "id": request_id,
        "type": "elicitation",
        "session_id": session_id,
        "questions": question_data,
        "timestamp": time.time(),
    }
    with open(pending_file, "w") as f:
        json.dump(request, f)

    _update_session_status(info_file, "question", "elicitation")
    sys.exit(0)


def _run_menubar_mode(request_id, session_id, question_data, pending_file, info_file):
    """Blocking: write pending, poll for system tray answer, deny with context."""
    os.makedirs(RESPONSES_DIR, exist_ok=True)
    response_file = os.path.join(RESPONSES_DIR, f"{request_id}.json")

    def _handle_signal(signum, frame):
        _cleanup(pending_file, response_file)
        _update_session_status(info_file, "working", None)
        sys.exit(1)

    signal.signal(signal.SIGTERM, _handle_signal)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, _handle_signal)

    request = {
        "id": request_id,
        "type": "elicitation",
        "session_id": session_id,
        "pid": os.getpid(),
        "questions": question_data,
        "timestamp": time.time(),
    }
    with open(pending_file, "w") as f:
        json.dump(request, f)

    _update_session_status(info_file, "question", "elicitation")

    # Print hint to terminal
    print("\n  [Claude Helper] Question pending in system tray:", file=sys.stderr)
    for q in question_data:
        print(f"    {q['question']}", file=sys.stderr)
        for i, opt in enumerate(q["options"], 1):
            print(f"      {i}) {opt}", file=sys.stderr)
    print("  Answer in system tray, or Ctrl+C to answer here.\n", file=sys.stderr)

    start_time = time.time()
    try:
        while time.time() - start_time < TIMEOUT:
            if os.path.isfile(response_file):
                try:
                    with open(response_file, "r") as f:
                        response = json.load(f)
                except (json.JSONDecodeError, IOError):
                    time.sleep(POLL_INTERVAL)
                    continue

                _cleanup(pending_file, response_file)
                _update_session_status(info_file, "working", None)

                answers = response.get("answers", {})
                lines = []
                for idx_str, val in answers.items():
                    idx = int(idx_str)
                    if idx < len(question_data):
                        lines.append(f"- {question_data[idx]['question']} -> {val}")
                    else:
                        lines.append(f"- Question {idx}: {val}")

                context = "The user responded via Claude Helper system tray:\n" + "\n".join(lines)
                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": "User answered via Claude Helper system tray",
                        "additionalContext": context,
                    }
                }
                print(json.dumps(output))
                sys.exit(0)

            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        _cleanup(pending_file, response_file)
        _update_session_status(info_file, "working", None)

    sys.exit(1)


if __name__ == "__main__":
    main()
