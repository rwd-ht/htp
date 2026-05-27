# Originally from Coverage.py https://github.com/coveragepy/coveragepy/
# See licenses/LICENSE-COVERAGE
# Copyright 2001 Gareth Rees.  All rights reserved.
# Copyright 2004-2026 Ned Batchelder
# Copyright 2026 HyeTech

from __future__ import annotations

import datetime
import errno
import functools
import hashlib
import importlib
import importlib.util
import inspect
import os
import os.path
import re
import sys
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Sequence
from types import ModuleType
from typing import Any
from typing import TypeVar


def nice_pair(pair: tuple[int, int]) -> str:
    """Make a nice string representation of a pair of numbers.

    If the numbers are equal, just return the number, otherwise return the pair
    with a dash between them, indicating the range.

    """
    start, end = pair
    if start == end:
        return f"{start}"
    else:
        return f"{start}-{end}"


def bool_or_none(b: Any) -> bool | None:
    """Return bool(b), but preserve None."""
    if b is None:
        return None
    else:
        return bool(b)


def join_regex(regexes: Iterable[str]) -> str:
    """Combine a series of regex strings into one that matches any of them."""
    regexes = list(regexes)
    if len(regexes) == 1:
        return regexes[0]
    else:
        return "|".join(f"(?:{r})" for r in regexes)


def file_be_gone(path: str) -> None:
    """Remove a file, and don't get annoyed if it doesn't exist."""
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def ensure_dir(directory: str) -> None:
    """Make sure the directory exists.

    If `directory` is None or empty, do nothing.
    """
    if directory:
        os.makedirs(directory, exist_ok=True)


def ensure_dir_for_file(path: str) -> None:
    """Make sure the directory for the path exists."""
    ensure_dir(os.path.dirname(path))


class Hasher:
    """Hashes Python data for fingerprinting."""

    def __init__(self) -> None:
        self.hash = hashlib.new("sha3_256", usedforsecurity=False)

    def update(self, v: Any) -> None:
        """Add `v` to the hash, recursively if needed."""
        self.hash.update(str(type(v)).encode("utf-8"))
        match v:
            case None:
                pass
            case str():
                self.hash.update(f"{len(v)}:".encode())
                self.hash.update(v.encode("utf-8"))
            case bytes():
                self.hash.update(f"{len(v)}:".encode())
                self.hash.update(v)
            case int() | float():
                self.hash.update(str(v).encode("utf-8"))
            case tuple() | list():
                for e in v:
                    self.update(e)
            case dict():
                for k, kv in sorted(v.items()):
                    self.update(k)
                    self.update(kv)
            case set():
                for e in sorted(v):
                    self.update(e)
            case _:
                for k in dir(v):
                    if k.startswith("__"):
                        continue
                    a = getattr(v, k)
                    if inspect.isroutine(a):
                        continue
                    self.update(k)
                    self.update(a)
        self.hash.update(b".")

    def digest(self) -> bytes:
        """Get the full binary digest of the hash."""
        return self.hash.digest()

    def hexdigest(self) -> str:
        """Retrieve a 32-char hex digest of the hash."""
        return self.hash.hexdigest()[:32]


class DefaultValue:
    """A sentinel object to use for unusual default-value needs.

    Construct with a string that will be used as the repr, for display in help
    and Sphinx output.

    """

    def __init__(self, display_as: str) -> None:
        self.display_as = display_as

    def __repr__(self) -> str:
        return self.display_as


def substitute_variables(text: str, variables: Mapping[str, str]) -> str:
    """Substitute ``${VAR}`` variables in `text` with their values.

    Variables in the text can take a number of shell-inspired forms::

        $VAR
        ${VAR}
        ${VAR?}             strict: an error if VAR isn't defined.
        ${VAR-missing}      defaulted: "missing" if VAR isn't defined.
        $$                  just a dollar sign.

    `variables` is a dictionary of variable values.

    Returns the resulting text with values substituted.

    """
    dollar_pattern = r"""(?x)   # Use extended regex syntax
        \$                      # A dollar sign,
        (?:                     # then
            (?P<dollar> \$ ) |      # a dollar sign, or
            (?P<word1> \w+ ) |      # a plain word, or
            \{                      # a {-wrapped
                (?P<word2> \w+ )        # word,
                (?:                         # either
                    (?P<strict> \? ) |      # with a strict marker
                    -(?P<defval> [^}]* )    # or a default value
                )?                      # maybe.
            }
        )
        """

    dollar_groups = ("dollar", "word1", "word2")

    def dollar_replace(match: re.Match[str]) -> str:
        """Called for each $replacement."""
        # Only one of the dollar_groups will have matched, just get its text.
        word = next(
            g for g in match.group(*dollar_groups) if g
        )  # pragma: always breaks
        if word == "$":
            return "$"
        elif word in variables:
            return variables[word]
        elif match["strict"]:
            msg = f"Variable {word} is undefined: {text!r}"
            raise RuntimeError(msg)
        else:
            return match["defval"]

    text = re.sub(dollar_pattern, dollar_replace, text)
    return text


def format_local_datetime(dt: datetime.datetime) -> str:
    """Return a string with local timezone representing the date."""
    return dt.astimezone().strftime("%Y-%m-%d %H:%M %z")


def import_local_file(modname: str, modfile: str | None = None) -> ModuleType:
    """Import a local file as a module.

    Opens a file in the current directory named `modname`.py, imports it
    as `modname`, and returns the module object.  `modfile` is the file to
    import if it isn't in the current directory.

    """
    if modfile is None:
        modfile = modname + ".py"
    spec = importlib.util.spec_from_file_location(modname, modfile)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    return mod


@functools.cache
def _human_key(s: str) -> tuple[list[str | int], str]:
    """Turn a string into a list of string and number chunks.

    "z23a" -> (["z", 23, "a"], "z23a")

    The original string is appended as a last value to ensure the
    key is unique enough so that "x1y" and "x001y" can be distinguished.
    """

    def tryint(s: str) -> str | int:
        """If `s` is a number, return an int, else `s` unchanged."""
        try:
            return int(s)
        except ValueError:
            return s

    return ([tryint(c) for c in re.split(r"(\d+)", s)], s)


def human_sorted(strings: Iterable[str]) -> list[str]:
    """Sort the given iterable of strings the way that humans expect.

    Numeric components in the strings are sorted as numbers.

    Returns the sorted list.

    """
    return sorted(strings, key=_human_key)


SortableItem = TypeVar("SortableItem", bound=Sequence[Any])


def human_sorted_items(
    items: Iterable[SortableItem],
    reverse: bool = False,
) -> list[SortableItem]:
    """Sort (string, ...) items the way humans expect.

    The elements of `items` can be any tuple/list. They'll be sorted by the
    first element (a string), with ties broken by the remaining elements.

    Returns the sorted list of items.
    """
    return sorted(
        items,
        key=lambda item: (_human_key(item[0]), *item[1:]),
        reverse=reverse,
    )


def plural(n: int, thing: str = "", things: str = "") -> str:
    """Pluralize a word.

    If n is 1, return thing.  Otherwise return things, or thing+s.
    """
    if n == 1:
        noun = thing
    else:
        noun = things or (thing + "s")
    return f"{n} {noun}"


def stdout_link(text: str, url: str) -> str:
    """Format text+url as a clickable link for stdout.

    If attached to a terminal, use escape sequences. Otherwise, just return
    the text.
    """
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return f"\033]8;;{url}\a{text}\033]8;;\a"
    else:
        return text
