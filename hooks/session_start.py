#!/usr/bin/env python3
"""Hook: SessionStart — registers a new Claude Code session.

Non-blocking. Reads hook input from stdin.
"""

import json
import os
import sys
import time

STATE_DIR = os.path.expanduser("~/.claude-helper")


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = input_data.get("session_id", "")
    if not session_id:
        sys.exit(0)

    cwd = input_data.get("cwd", "unknown")
    project_name = os.path.basename(cwd)

    session_dir = os.path.join(STATE_DIR, "sessions", session_id)
    os.makedirs(os.path.join(session_dir, "pending"), exist_ok=True)

    parent_pid = os.getppid()

    # Detect whether running inside VS Code or a standalone terminal
    client = "terminal"
    entrypoint = os.environ.get("CLAUDE_CODE_ENTRYPOINT", "")
    if "vscode" in entrypoint or os.environ.get("VSCODE_PID"):
        client = "vscode"

    info = {
        "session_id": session_id,
        "cwd": cwd,
        "project_name": project_name,
        "parent_pid": parent_pid,
        "client": client,
        "status": "working",
        "waiting_for": None,
        "last_updated": int(time.time()),
    }

    with open(os.path.join(session_dir, "info.json"), "w") as f:
        json.dump(info, f, indent=4)


if __name__ == "__main__":
    main()
