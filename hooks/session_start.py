#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Session start hook: Context initialization and logging.
Shows git status, loads context files, and logs session metadata.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from utils.log_utils import append_event, append_jsonl, get_log_dir


def run_command(cmd: list[str], cwd: str | None = None) -> str:
    """Run a command and return output, or empty string on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return ""


def get_git_info(cwd: str) -> dict:
    """Get git branch and uncommitted changes count."""
    branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)

    # Count uncommitted changes
    status = run_command(["git", "status", "--porcelain"], cwd)
    changes = len([line for line in status.split("\n") if line.strip()])

    return {
        "branch": branch or "unknown",
        "uncommitted_changes": changes,
    }


def load_context_file(path: Path) -> str | None:
    """Load a context file if it exists."""
    if path.exists():
        try:
            return path.read_text()
        except IOError:
            return None
    return None


def get_github_issues() -> list:
    """Fetch open GitHub issues via gh CLI."""
    output = run_command(["gh", "issue", "list", "--state", "open", "--limit", "5", "--json", "number,title"])
    if output:
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return []
    return []


def main() -> int:
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    session_id = hook_input.get("session_id", "unknown")
    cwd = os.getcwd()

    # Gather context
    git_info = get_git_info(cwd)

    # Check for context files
    claude_dir = Path(cwd) / ".claude"
    context_md = load_context_file(claude_dir / "CONTEXT.md")
    todo_md = load_context_file(claude_dir / "TODO.md")

    # Fetch GitHub issues (optional, may fail)
    github_issues = get_github_issues()

    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "cwd": cwd,
        "git": git_info,
        "context_files": {
            "CONTEXT.md": bool(context_md),
            "TODO.md": bool(todo_md),
        },
        "github_issues_count": len(github_issues),
    }

    # Save log
    append_jsonl(get_log_dir() / "session_start.jsonl", log_entry)

    # Unified event stream
    append_event("SessionStart", session_id, {"branch": git_info.get("branch")})

    # Output context information for Claude
    output_parts = []

    if git_info["branch"]:
        output_parts.append(f"Git branch: {git_info['branch']}")
    if git_info["uncommitted_changes"] > 0:
        output_parts.append(f"Uncommitted changes: {git_info['uncommitted_changes']}")

    if context_md:
        output_parts.append(f"\n--- CONTEXT.md ---\n{context_md[:2000]}")

    if todo_md:
        output_parts.append(f"\n--- TODO.md ---\n{todo_md[:2000]}")

    if github_issues:
        issues_str = "\n".join([f"  #{i['number']}: {i['title']}" for i in github_issues[:5]])
        output_parts.append(f"\n--- Open Issues ---\n{issues_str}")

    if output_parts:
        print("\n".join(output_parts))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
