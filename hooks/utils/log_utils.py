"""Shared logging utilities for Claude Code hooks.

Zero external dependencies -- Python stdlib only.
PEP 723 compatible: uv run adds script parent dir to sys.path,
so `from utils.log_utils import ...` works from any hook script.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path


def get_log_dir() -> Path:
    """Get log directory.

    Resolution order:
    1. $CLAUDE_LOG_DIR (explicit log directory override)
    2. $CLAUDE_PROJECT_DIR/logs (project-relative logs)
    3. ~/BASECAMP/logs (legacy fallback)

    Creates the directory if it does not exist.
    """
    log_dir_env = os.environ.get("CLAUDE_LOG_DIR")
    if log_dir_env:
        log_dir = Path(log_dir_env)
    else:
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
        if project_dir:
            log_dir = Path(project_dir) / "logs"
        else:
            log_dir = Path(os.environ.get("CLAUDE_LOG_DIR", str(Path.home() / "BASECAMP" / "logs")))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def append_jsonl(filepath: Path, entry: dict) -> None:
    """Append a single JSON line to a file.

    O(1) -- never reads the file. Opens in append mode, writes one line.
    Uses default=str so datetime, Path, and other non-serializable types
    are converted to strings rather than raising.
    """
    with open(filepath, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def append_event(event_type: str, session_id: str, data: dict | None = None) -> None:
    """Append to logs/event-stream.jsonl. Called from every hook.

    Entry format:
        {"ts": <epoch_ms>, "event": event_type, "session_id": session_id, ...data}
    """
    entry: dict = {
        "ts": int(time.time() * 1000),
        "event": event_type,
        "session_id": session_id,
    }
    if data:
        entry.update(data)
    append_jsonl(get_log_dir() / "event-stream.jsonl", entry)


def load_jsonl(filepath: Path, tail: int = 100) -> list[dict]:
    """Read last N entries from a JSONL file. For display/debug only.

    Reads all lines and returns the last `tail` entries parsed as dicts.
    Lines that fail to parse are silently skipped.
    """
    if not filepath.exists():
        return []
    entries: list[dict] = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue
    return entries[-tail:]
