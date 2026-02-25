#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Ruff Linter Validator for Claude Code PostToolUse Hook

Runs `uvx ruff check` on individual Python files after Write/Edit operations.

Outputs JSON decision for Claude Code PostToolUse hook:
- {"decision": "block", "reason": "..."} to block and retry
- {} to allow completion
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import subprocess
import sys
from pathlib import Path

# Logging setup with rotation
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "ruff_validator.log"

handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=1_000_000, backupCount=2
)
handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def main() -> None:
    logger.info("=" * 50)
    logger.info("RUFF VALIDATOR POSTTOOLUSE HOOK TRIGGERED")

    # Read hook input from stdin
    try:
        stdin_data = sys.stdin.read()
        hook_input = json.loads(stdin_data) if stdin_data.strip() else {}
    except json.JSONDecodeError:
        hook_input = {}

    # Extract file_path from PostToolUse input
    file_path = hook_input.get("tool_input", {}).get("file_path", "")
    logger.info(f"file_path: {file_path}")

    # Only run for Python files
    if not file_path.endswith(".py"):
        logger.info("Skipping non-Python file")
        print(json.dumps({}))
        return

    # Path validation: resolve symlinks, reject outside home
    try:
        resolved = Path(file_path).resolve()
        home = Path.home().resolve()
        if not str(resolved).startswith(str(home)):
            logger.warning(f"Path outside home directory: {resolved}")
            print(json.dumps({}))
            return
        if ".." in Path(file_path).parts:
            logger.warning(f"Path contains ..: {file_path}")
            print(json.dumps({}))
            return
    except (OSError, ValueError) as e:
        logger.warning(f"Path validation error: {e}")
        print(json.dumps({}))
        return

    # Run uvx ruff check on the single file
    logger.info(f"Running: uvx ruff check --target-version py310 {file_path}")
    try:
        result = subprocess.run(
            ["uvx", "ruff", "check", "--target-version", "py310", file_path],
            capture_output=True,
            text=True,
            timeout=120,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if stdout:
            for line in stdout.split("\n")[:20]:
                logger.info(f"  {line}")

        if result.returncode == 0:
            logger.info("RESULT: PASS - Lint check successful")
            print(json.dumps({}))
        else:
            logger.info(f"RESULT: BLOCK (exit code {result.returncode})")
            if stderr:
                for line in stderr.split("\n")[:10]:
                    logger.info(f"  stderr: {line}")
            error_output = stdout or stderr or "Lint check failed"
            print(json.dumps({
                "decision": "block",
                "reason": f"Lint check failed:\n{error_output[:500]}",
            }))

    except subprocess.TimeoutExpired:
        logger.info("RESULT: BLOCK (timeout)")
        print(json.dumps({
            "decision": "block",
            "reason": "Lint check timed out after 120 seconds",
        }))
    except FileNotFoundError:
        logger.info("RESULT: PASS (uvx ruff not found, skipping)")
        print(json.dumps({}))
    except Exception:
        logger.exception("Unexpected error")
        print(json.dumps({}))


if __name__ == "__main__":
    main()
