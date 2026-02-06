#!/usr/bin/env python3
"""Hook: SessionEnd — cleans up a finished session.

Non-blocking. Reads hook input from stdin.
"""

import json
import os
import shutil
import sys

STATE_DIR = os.path.expanduser("~/.claude-helper")


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = input_data.get("session_id", "")
    if not session_id:
        sys.exit(0)

    session_dir = os.path.join(STATE_DIR, "sessions", session_id)
    if os.path.isdir(session_dir):
        shutil.rmtree(session_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
