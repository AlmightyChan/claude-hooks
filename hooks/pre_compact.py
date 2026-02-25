#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Pre-compact hook: Transcript backup before context compaction.
Creates timestamped backups of conversation history.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from utils.log_utils import append_event, append_jsonl, get_log_dir


def get_backup_dir() -> Path:
    """Get the transcript backup directory."""
    backup_dir = get_log_dir() / "transcript_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def backup_transcript(session_id: str, transcript_path: str | None) -> str | None:
    """Create a timestamped backup of the transcript."""
    if not transcript_path:
        return None

    source = Path(transcript_path)
    if not source.exists():
        return None

    backup_dir = get_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{session_id}_{timestamp}.jsonl"
    backup_path = backup_dir / backup_name

    try:
        shutil.copy2(source, backup_path)
        return str(backup_path)
    except IOError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-compact hook")
    parser.add_argument("--backup", action="store_true", help="Create transcript backup")
    args = parser.parse_args()

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path")
    summary = hook_input.get("summary", "")

    backup_path = None
    if args.backup and transcript_path:
        backup_path = backup_transcript(session_id, transcript_path)

    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "transcript_path": transcript_path,
        "backup_created": backup_path,
        "summary_length": len(summary) if summary else 0,
    }

    # Save log
    append_jsonl(get_log_dir() / "pre_compact.jsonl", log_entry)

    # Unified event stream
    append_event("PreCompact", session_id, {"backup_created": bool(backup_path)})

    if backup_path:
        print(f"Transcript backed up to: {backup_path}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
