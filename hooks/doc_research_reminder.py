#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Documentation research reminder hook (UserPromptSubmit).
Injects a reminder to consult official docs when the user's prompt
mentions Claude Code configuration topics.
"""

from __future__ import annotations

import json
import re
import sys


# Patterns that indicate Claude Code configuration work.
# Each tuple: (compiled regex, description for context).
PATTERNS = [
    (re.compile(r"\bhooks?\b(?!.*webhook)", re.IGNORECASE), "hooks"),
    (re.compile(r"\bskills?\b", re.IGNORECASE), "skills"),
    (re.compile(r"\b(?:sub)?agents?\b", re.IGNORECASE), "agents"),
    (re.compile(r"\bmcp\b", re.IGNORECASE), "MCP"),
    (re.compile(r"\bCLAUDE\.md\b"), "CLAUDE.md"),
    (re.compile(r"\bsettings\.json\b", re.IGNORECASE), "settings"),
    (re.compile(r"\bsandbox(?:ing)?\b", re.IGNORECASE), "sandboxing"),
    (re.compile(r"\bplugins?\b", re.IGNORECASE), "plugins"),
    (re.compile(r"\bcreate-(?:hook|skill|subagent|mcp)\b", re.IGNORECASE), "meta skill"),
]


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    prompt = hook_input.get("prompt", "")
    if not prompt:
        return 0

    matched_topics = []
    for pattern, topic in PATTERNS:
        if pattern.search(prompt):
            matched_topics.append(topic)

    if not matched_topics:
        return 0

    topics_str = ", ".join(sorted(set(matched_topics)))
    reminder = (
        f"[Doc Reminder] This prompt mentions Claude Code config topics ({topics_str}). "
        "Before modifying configs, check the Documentation Protocol table in CLAUDE.md "
        "and WebFetch the relevant official docs from code.claude.com."
    )

    output = {"additionalContext": reminder}
    json.dump(output, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
