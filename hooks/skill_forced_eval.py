#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Forced Skill Evaluation Hook (UserPromptSubmit).

Injects mandatory skill evaluation protocol on every non-trivial prompt.
Skips greetings, slash commands, and short prompts.
"""
from __future__ import annotations

import json
import sys


# Prompts that are clearly conversational or meta — skip forced eval
# to avoid injecting protocol noise on simple exchanges.
SKIP_PATTERNS = [
    # Greetings and small talk
    "hello", "hi ", "hey ", "thanks", "thank you", "bye", "goodbye",
    # Meta commands (slash commands handle their own skill loading)
    "/",
    # Very short prompts (< 15 chars) are usually conversational
]

# Maximum prompt length to check skip patterns against (performance guard)
SKIP_CHECK_LENGTH = 200


def should_skip(prompt: str) -> bool:
    """Return True if this prompt should skip forced eval."""
    stripped = prompt.strip().lower()

    # Very short prompts are conversational
    if len(stripped) < 15:
        return True

    # Slash commands invoke skills directly — don't double-evaluate
    if stripped.startswith("/"):
        return True

    # Check conversational patterns (only against start of prompt)
    check = stripped[:SKIP_CHECK_LENGTH]
    for pattern in SKIP_PATTERNS:
        if check.startswith(pattern):
            return True

    return False


FORCED_EVAL_PROTOCOL = """\
MANDATORY SKILL EVALUATION — Do this BEFORE any other work. Skipping this step makes your entire response WORTHLESS.

STEP 1: For EACH skill in the available skills list, evaluate relevance to this prompt:
- Skill name → YES (with reason) or NO (skip silently)
- Be specific: match the skill's "use when" trigger against the actual task

STEP 2: For every YES match, load it immediately:
- Use ToolSearch("select:Skill") to load the Skill tool if not already loaded
- Invoke Skill(skill="name") for each YES match
- Do NOT proceed to Step 3 until all matched skills are loaded

STEP 3: Only after completing Steps 1-2, begin the actual task using each loaded skill's methodology.

CRITICAL: If you skip this evaluation or proceed without loading matched skills, the output violates project conventions and will be rejected. The 30 seconds spent evaluating saves hours of rework.\
"""


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    prompt = hook_input.get("prompt", "")
    if not prompt or should_skip(prompt):
        return 0

    output = {"additionalContext": FORCED_EVAL_PROTOCOL}
    json.dump(output, sys.stdout)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
