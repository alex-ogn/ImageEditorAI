"""Platform helpers so the UI behaves natively on Windows, macOS and Linux."""

import sys

IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"

# Primary shortcut modifier: Command on macOS, Control everywhere else.
_MOD_EVENT = "Command" if IS_MACOS else "Control"
_MOD_LABEL = "⌘" if IS_MACOS else "Ctrl+"


def shortcut_event(key: str) -> str:
    """Tk event sequence for the primary modifier + key, e.g. '<Control-o>'."""
    return f"<{_MOD_EVENT}-{key.lower()}>"


def shortcut_label(key: str) -> str:
    """Human readable accelerator label, e.g. 'Ctrl+O' or '⌘O'."""
    return f"{_MOD_LABEL}{key.upper()}"
