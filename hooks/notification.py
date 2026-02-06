#!/usr/bin/env python3
"""Hook: Notification — tracks idle/elicitation notifications.

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

    ntype = input_data.get("notification_type", "")
    title = input_data.get("title", "notification")

    # Determine waiting_for and status based on notification type or title
    match = ntype or title
    match_lower = match.lower()

    if "permission" in match_lower:
        waiting_for = "permission"
        status = "permission"
    elif "idle" in match_lower or "input" in match_lower:
        waiting_for = "input"
        status = "idle"
    elif "elicitation" in match_lower:
        waiting_for = "elicitation"
        status = "idle"
    else:
        waiting_for = title
        status = "idle"

    try:
        with open(info_file, "r") as f:
            info = json.load(f)
        info["waiting_for"] = waiting_for
        info["status"] = status
        info["last_updated"] = int(time.time())
        with open(info_file, "w") as f:
            json.dump(info, f, indent=4)
    except (json.JSONDecodeError, IOError):
        pass


if __name__ == "__main__":
    main()
