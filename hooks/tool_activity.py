#!/usr/bin/env python3
"""Hook: PostToolUse (catch-all) — resets stale "question" / "permission" status.

If Claude is using tools, it's working, not waiting for user input.
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

    info_file = os.path.join(STATE_DIR, "sessions", session_id, "info.json")
    if not os.path.isfile(info_file):
        sys.exit(0)

    try:
        with open(info_file, "r") as f:
            info = json.load(f)
    except (json.JSONDecodeError, IOError):
        sys.exit(0)

    # Reset stale interactive status — if a tool is running, Claude is working.
    # In VS Code mode, don't reset "permission" — VS Code handles its own
    # permission dialogs and we rely on a staleness timeout in the tray app
    # to clear the blue dot. Resetting here would just cause the next
    # PermissionRequest to set a fresh timestamp, keeping blue forever.
    current_status = info.get("status")
    if current_status in ("question", "permission"):
        skip = False
        if current_status == "permission" and info.get("client") == "vscode":
            skip = True
        if not skip:
            info["status"] = "working"
            info["waiting_for"] = None
            info["last_updated"] = int(time.time())
            try:
                with open(info_file, "w") as f:
                    json.dump(info, f, indent=4)
            except IOError:
                pass


if __name__ == "__main__":
    main()
