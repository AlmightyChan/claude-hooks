#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Validates that all Docs Index globs in CLAUDE.md match 1+ files on disk."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def _default_claude_md_path() -> Path:
    """Get default CLAUDE.md path.

    Uses $CLAUDE_PROJECT_DIR/CLAUDE.md if set, else ~/BASECAMP/CLAUDE.md.
    """
    import os

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return Path(project_dir) / "CLAUDE.md"
    return Path.home() / "BASECAMP" / "CLAUDE.md"


def find_docs_index_block(claude_md: str) -> str | None:
    """Extract the code block following '## Docs Index'."""
    match = re.search(
        r"## Docs Index.*?```\n(.*?)```",
        claude_md,
        re.DOTALL,
    )
    return match.group(1) if match else None


def parse_index_lines(block: str) -> list[tuple[str, list[str]]]:
    """Parse index lines into (dirname, [patterns]) tuples.

    Handles:
      |dirname:{pattern1,pattern2}  -> dirname, [pattern1, pattern2]
      |dirname:{*.md}               -> dirname, [*.md]
      |dirname:{dir/}               -> dirname, [dir/]
      |dirname:{see ...}            -> skipped (non-pattern text)
      |ACTIVE.md                    -> '', [ACTIVE.md]
      root: ./docs                  -> skipped
    """
    entries: list[tuple[str, list[str]]] = []
    for line in block.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("root:"):
            continue

        # Line without braces: |ACTIVE.md
        if line.startswith("|") and "{" not in line:
            filename = line.lstrip("|").strip()
            if filename:
                entries.append(("", [filename]))
            continue

        # Line with braces: |dirname:{patterns}
        match = re.match(r"\|([^:]+):\{(.+)\}", line)
        if not match:
            continue

        dirname = match.group(1).strip()
        content = match.group(2).strip()

        # Skip non-pattern text like "see insights-log.md for inventory"
        if content.startswith("see "):
            continue

        patterns = [p.strip() for p in content.split(",")]
        entries.append((dirname, patterns))

    return entries


def validate_entries(
    docs_root: Path, entries: list[tuple[str, list[str]]]
) -> tuple[int, int, list[str]]:
    """Validate each entry has 1+ matching files. Returns (total, matched, broken)."""
    total = 0
    matched = 0
    broken: list[str] = []

    for dirname, patterns in entries:
        base = docs_root / dirname if dirname else docs_root
        for pattern in patterns:
            total += 1
            # Directory reference like "pitch/"
            if pattern.endswith("/"):
                target = base / pattern.rstrip("/")
                if target.is_dir():
                    matched += 1
                else:
                    broken.append(f"{dirname}/{pattern}" if dirname else pattern)
            else:
                # Glob pattern or exact filename
                matches = list(base.glob(pattern))
                if matches:
                    matched += 1
                else:
                    broken.append(f"{dirname}/{pattern}" if dirname else pattern)

    return total, matched, broken


def main() -> int:
    claude_md_path = Path(sys.argv[1]) if len(sys.argv) > 1 else _default_claude_md_path()

    if not claude_md_path.exists():
        print(f"ERROR: {claude_md_path} not found", file=sys.stderr)
        return 1

    content = claude_md_path.read_text()
    block = find_docs_index_block(content)
    if block is None:
        print("ERROR: No Docs Index code block found in CLAUDE.md", file=sys.stderr)
        return 1

    docs_root = claude_md_path.parent / "docs"
    entries = parse_index_lines(block)
    total, matched, broken = validate_entries(docs_root, entries)

    print(f"Docs Index: {total} patterns, {matched} matched, {len(broken)} zero-match")
    if broken:
        for b in broken:
            print(f"  BROKEN: {b}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
