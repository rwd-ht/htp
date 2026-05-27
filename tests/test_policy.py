from __future__ import annotations

import pathlib

import pytest

from htp.config import load_config
from htp.pattern import run_analysis

TESTS_DIR = pathlib.Path().cwd() / "tests"


def test_policy():
    try:
        config = load_config(TESTS_DIR / "htp-test.toml")
        run_analysis(config, (TESTS_DIR / "policies").glob("*.y*ml"))
    except:
        assert False
