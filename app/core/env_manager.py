import os
from typing import Dict, List, Optional, Tuple


def read_env_lines(env_file: str) -> List[Tuple[Optional[str], str]]:
    """Read .env file preserving order and comments.

    Returns a list of (key, line) tuples.
    *key* is ``None`` for blank lines and comments.
    For key=value lines the key is extracted so callers can update values
    while keeping the line position.
    """
    lines: List[Tuple[Optional[str], str]] = []
    if not os.path.exists(env_file):
        return lines
    with open(env_file, "r", encoding="utf-8-sig") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                lines.append((None, line))
            elif "=" in stripped:
                key, _ = stripped.split("=", 1)
                lines.append((key.strip(), line))
            else:
                lines.append((None, line))
    return lines


def env_settings(env_file: str) -> Dict[str, str]:
    """Return current key=value mapping from *env_file*."""
    settings: Dict[str, str] = {}
    for key, line in read_env_lines(env_file):
        if key is None:
            continue
        # line already contains key=value; parse the value part
        _, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        settings[key] = value
    return settings


def save_env_settings(env_file: str, updates: Dict[str, str]) -> None:
    """Write *updates* to *env_file* while preserving comments and line order.

    Keys that already exist are updated in-place. New keys are appended at the
    end of the file. Blank lines and comment lines are kept untouched.
    """
    lines = read_env_lines(env_file)
    updated_keys: set[str] = set()
    new_lines: List[str] = []

    for key, line in lines:
        if key is None:
            new_lines.append(line)
        elif key in updates:
            new_lines.append(f"{key}={updates[key]}")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}")

    with open(env_file, "w", encoding="utf-8") as fh:
        for i, line in enumerate(new_lines):
            if i:
                fh.write("\n")
            fh.write(line)
