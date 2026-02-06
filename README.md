# Claude Helper

A Windows system tray utility for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Shows session status at a glance and lets you respond to permission prompts without switching to the terminal.

## Features

- **System tray status indicator** — see what Claude is doing without context-switching
- **Permission requests** — Allow, Always Allow, or Deny tool usage directly from the system tray (terminal mode)
- **Elicitation questions** — view (and optionally answer) Claude's questions from the system tray
- **Multi-session support** — track multiple concurrent Claude Code sessions
- **Auto-start** — optionally launch on login via Windows Registry
- **Smart client detection** — auto-detects VS Code vs terminal and routes dialogs accordingly

## System Tray Icons

| Icon | Meaning |
|------|---------|
| Green filled circle | Claude is actively working |
| Blue filled circle | A session needs your attention (permission request or question) |
| Yellow filled circle | A session has finished or is idle, waiting for input |
| Hollow circle (gray) | No active sessions |

## VS Code vs Terminal

Claude Helper auto-detects the client environment:

| | VS Code | Terminal |
|---|---|---|
| **Permissions** | Blue tray icon; VS Code shows its native dialog | Blue tray icon; tray shows Allow/Deny |
| **Questions** | Blue tray icon; VS Code shows the question | Blue tray icon; tray shows answer options |

## Setup

Requires **Python 3**.

```powershell
.\setup.ps1
```

This will:

1. Create a Python virtual environment at `~/.claude-helper/venv`
2. Install dependencies (`pystray`, `Pillow`, `psutil`)
3. Merge hook configuration into `~/.claude/settings.json`

## Running

Start the system tray app:

```powershell
& "$env:USERPROFILE\.claude-helper\venv\Scripts\python.exe" claude_helper.py
```

To auto-start on login, click **Auto-start: Off** in the system tray dropdown.

## How It Works

Claude Helper uses Claude Code's [hooks system](https://docs.anthropic.com/en/docs/claude-code/hooks) to track session lifecycle events:

- **SessionStart/SessionEnd** — registers and cleans up sessions in `~/.claude-helper/sessions/`
- **UserPromptSubmit** — marks a session as "working" when you send a message
- **PermissionRequest** — in terminal mode, a blocking hook that shows the request in the system tray and polls for your response; in VS Code mode, sets tray status and falls through to VS Code's native dialog
- **PreToolUse (AskUserQuestion)** — captures elicitation questions for display
- **PostToolUse** — resets session status after tool completion
- **Notification/Stop** — tracks idle and completion states

All state is stored as JSON files under `~/.claude-helper/`. The system tray app polls this directory every 2 seconds. Dead sessions (where the Claude Code process has exited) are automatically cleaned up.

## Hooks

| Hook | Script | Purpose |
|------|--------|---------|
| SessionStart | `session_start.py` | Register session, detect VS Code vs terminal |
| SessionEnd | `session_end.py` | Clean up session directory |
| UserPromptSubmit | `prompt_submit.py` | Set status to "working" |
| PermissionRequest | `permission_request.py` | Handle permission dialogs |
| PreToolUse (AskUserQuestion) | `elicitation_request.py` | Handle question dialogs |
| PostToolUse (AskUserQuestion) | `elicitation_cleanup.py` | Clean up after questions |
| PostToolUse (*) | `tool_activity.py` | Reset stale permission/question status |
| Notification | `notification.py` | Track idle/completion |
| Stop | `stop.py` | Mark session as idle |

## Requirements

- Windows
- Python 3
- [pystray](https://github.com/moses-palmer/pystray), [Pillow](https://python-pillow.org/), [psutil](https://github.com/giampaolo/psutil) (installed automatically by setup)
