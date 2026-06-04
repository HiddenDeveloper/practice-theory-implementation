#!/usr/bin/env python3
"""Block pyright/mypy invocations in this basedpyright repo."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from typing import Any


DIRECT_TYPE_CHECKER = re.compile(r"(^|[;&|(){}`]|\$\()[ \t]*(mypy|pyright)([^\w]|$)")
RUNNER_COMMAND = re.compile(
    r"(^|[;&|(){}`]|\$\()[ \t]*"
    r"(?P<runner>(uvx|npx|bunx)|(uv|poetry|pipx|pdm|hatch|rye)[ \t]+run|python[0-9.]*[ \t]+-m)"
    r"[ \t]+(?P<rest>[^;&|(){}`]*)"
)

MESSAGE = "use basedpyright, not mypy/pyright (e.g. uv run basedpyright)"
BLOCKED = {"mypy", "pyright"}
OPTIONS_WITH_VALUES = {
    "--directory",
    "--env-file",
    "--extra",
    "--from",
    "--group",
    "--index-url",
    "--keyring-provider",
    "--package",
    "--project",
    "--python",
    "--resolution",
    "--with",
    "--with-editable",
}


def command_from_event(event: dict[str, Any]) -> str:
    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def first_executable_arg(rest: str) -> str | None:
    try:
        tokens = shlex.split(rest)
    except ValueError:
        return None

    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token == "--":
            continue
        if token in OPTIONS_WITH_VALUES:
            skip_next = True
            continue
        if token.startswith("-"):
            continue
        return os.path.basename(token)

    return None


def invokes_blocked_type_checker(command: str) -> bool:
    if DIRECT_TYPE_CHECKER.search(command):
        return True

    return any(first_executable_arg(match.group("rest")) in BLOCKED for match in RUNNER_COMMAND.finditer(command))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if not isinstance(event, dict):
        return 0

    command = command_from_event(event)
    if invokes_blocked_type_checker(command):
        print(MESSAGE, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
