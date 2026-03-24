from __future__ import annotations

import enum
import logging
import os
import re

import pydantic
from typing_extensions import Self
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

_EXTRACT_VAR_PATTERN = re.compile(
    r"\{\{\s*([a-z][a-z0-9_-]*)\s*\}\}",
    flags=re.IGNORECASE,
)


class ParseType(enum.Enum):
    indented = "indented"
    lines = "lines"
    flat = "flat"
    regex = "regex"


class Result(pydantic.BaseModel):
    passes: bool
    message: str


class Action(enum.Enum):
    none = "none"
    fix_missing = "fix_missing"
    fix_found = "fix_found"
    alert_missing = "alert_missing"
    alert_found = "alert_found"
    capture_one = "capture_one"
    capture_zero_or_one = "capture_zero_or_one"
    capture_zero_or_more = "capture_zero_or_more"
    capture_one_or_more = "capture_one_or_more"


class Pattern(pydantic.BaseModel):
    """
    Pattern, used to match things
    """

    pattern: str
    name: str = ""
    action: Action = Action.none
    regex: bool = False
    icase: bool = False
    condition: str | None = None
    fix: str | None = None
    patterns: list[Pattern] | None = None


def _test_valid_varname(var):
    if not (var.isupper() or var.islower()):
        raise RuntimeError("mixed case not supported")


def set_environment_variable(string: str) -> str:
    """
    replace {{ VARIABLE }} with value from environment
    matches any variable name that is all caps
    raises RuntimeError if VARIABLE not set
    """
    if not (match := _EXTRACT_VAR_PATTERN.search(string)):
        return string
    var = match.group(1)
    _test_valid_varname(var)
    if not var.isupper():
        logger.debug(f"Ignoring dynamic variable: {string!r}")
        return string
    logger.info(f"Found environment Variable: {string!r}")
    start, stop = match.span()
    envvar = os.getenv(var)
    if envvar is None:
        raise RuntimeError(f"{var} not defined")
    return string[:start] + envvar + string[stop:]


def get_dynamic_instances(string, variables: dict[str, list[str]]) -> list[str]:
    """
    replace {{ variable }} with all instances of variable in variables
    """
    if not (match := _EXTRACT_VAR_PATTERN.search(string)):
        return [string]
    var = match.group(1)
    _test_valid_varname(var)
    if not var.islower():
        logger.debug(f"Ignoring environment variable: {string!r}")
        return string
    logger.info(f"Found dynamic Variable: {string!r}")
    start, stop = match.span()
    instances = variables.get(var)
    if instances is None:
        raise RuntimeError(f"{var} not defined")
    return [string[:start] + i + string[stop:] for i in instances]


def parse_indented(
    text: str,
    comment_character: str = "!",
):
    width = 0
    result = {}
    parent = None
    for line in text.splitlines():
        print(width)
        if not line:
            continue
        if line[0] == " " and not parent:
            raise RuntimeError("not expected to start indented")
        elif line[0] == " " and width:
            if line[:width].strip():
                raise RuntimeError("Unexpected indent level in {line!r}")
            result.setdefault(parent, []).append(line[width:])
        elif line[0] == " " and not width:
            while line[width] == " ":
                width += 1
            result.setdefault(parent, []).append(line[width:])
        else:
            parent = line
            result.setdefault(parent, [])
            width = 0
    from pprint import pp

    pp(result)
    return {k: "\n".join(v) for k, v in result.items()}


def parse_lines(
    string: str,
):
    return {k: {} for k in string.splitlines() if k.strip()}


def parse_flat(
    string: str,
):
    return {string: {}}


def parse_regex(
    string: str,
):
    return {string: {}}


if __name__ == "__main__":
    pass
