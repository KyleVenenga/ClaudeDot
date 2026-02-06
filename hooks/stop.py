#!/usr/bin/env python3
"""Hook: Stop — marks session as 'done'.

Non-blocking (async). Reads hook input from stdin.
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
        info["status"] = "done"
        info["waiting_for"] = "input"
        info["last_updated"] = int(time.time())
        with open(info_file, "w") as f:
            json.dump(info, f, indent=4)
    except (json.JSONDecodeError, IOError):
        pass


if __name__ == "__main__":
    main()
