#!/usr/bin/env python3
"""Merge Claude Helper hook configuration into Claude Code settings."""

import json
import os
import sys


def main():
    if len(sys.argv) < 4:
        print("Usage: merge_hooks.py <settings_path> <hooks_dir> <venv_python>")
        sys.exit(1)

    settings_path = sys.argv[1]
    hooks_dir = sys.argv[2]
    venv_python = sys.argv[3]

    def cmd(script_name):
        return '"' + venv_python + '" "' + os.path.join(hooks_dir, script_name) + '"'

    hooks_config = {
        "SessionStart": [
            {
                "matcher": "startup|resume",
                "hooks": [{"type": "command", "command": cmd("session_start.py")}],
            }
        ],
        "SessionEnd": [
            {
                "matcher": "",
                "hooks": [{"type": "command", "command": cmd("session_end.py")}],
            }
        ],
        "UserPromptSubmit": [
            {
                "matcher": "",
                "hooks": [{"type": "command", "command": cmd("prompt_submit.py")}],
            }
        ],
        "PreToolUse": [
            {
                "matcher": "AskUserQuestion",
                "hooks": [{"type": "command", "command": cmd("elicitation_request.py")}],
            }
        ],
        "PostToolUse": [
            {
                "matcher": "AskUserQuestion",
                "hooks": [{"type": "command", "command": cmd("elicitation_cleanup.py")}],
            },
            {
                "matcher": "",
                "hooks": [{"type": "command", "command": cmd("tool_activity.py")}],
            },
        ],
        "PermissionRequest": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": cmd("permission_request.py"),
                        "timeout": 310,
                    }
                ],
            }
        ],
        "Notification": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": cmd("notification.py"),
                        "async": True,
                    }
                ],
            }
        ],
        "Stop": [
            {
                "matcher": "",
                "hooks": [
                    {"type": "command", "command": cmd("stop.py"), "async": True}
                ],
            }
        ],
    }

    # Read existing settings
    with open(settings_path, "r") as f:
        settings = json.load(f)

    # Deep merge hooks
    existing_hooks = settings.get("hooks", {})
    existing_hooks.update(hooks_config)
    settings["hooks"] = existing_hooks

    # Write back
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print("  + Hooks merged into " + settings_path + " (existing settings preserved)")


if __name__ == "__main__":
    main()
