#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Shared path-matching logic for security hooks."""
from __future__ import annotations

import json
import re
from pathlib import Path


def load_patterns(config_path: Path | None = None) -> dict:
    """Load security_patterns.json. Returns empty dict on any error."""
    if config_path is None:
        config_path = Path(__file__).parent / "security_patterns.json"
    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return {}


def match_bash_pattern(command: str, patterns: list[dict]) -> dict | None:
    """Check if a bash command matches any pattern. Returns the first matching pattern dict or None."""
    for entry in patterns:
        try:
            if re.search(entry["pattern"], command, re.IGNORECASE):
                return entry
        except re.error:
            continue
    return None


def match_path(filepath: str, path_patterns: list[dict]) -> dict | None:
    """Check if a file path matches any path pattern. Returns matching pattern dict or None.

    Matches if:
    - The pattern appears anywhere in the filepath (simple substring/glob match)
    - Pattern starts with ~ : expand to $HOME before matching
    - Pattern has * : use fnmatch-style matching
    """
    filepath_expanded = str(Path(filepath).expanduser().resolve()) if filepath else ""
    filepath_lower = filepath.lower()

    for entry in path_patterns:
        pattern = entry["pattern"]
        # Handle home directory patterns
        if pattern.startswith("~/"):
            expanded = str(Path(pattern).expanduser())
            if filepath_expanded.startswith(expanded) or filepath.startswith(pattern):
                return entry
        # Handle glob patterns with *
        elif "*" in pattern:
            # Convert glob to regex: *.ext -> \.ext$
            regex_pattern = pattern.replace(".", r"\.").replace("*", ".*") + "$"
            if re.search(regex_pattern, filepath, re.IGNORECASE):
                return entry
        # Handle .env specifically to avoid false positives (.environment/, etc.)
        elif pattern == ".env":
            basename = Path(filepath).name
            if basename == ".env" or basename.startswith(".env."):
                return entry
        # Simple substring/contains match
        else:
            if pattern in filepath or pattern in filepath_lower or pattern in filepath_expanded:
                return entry
    return None
