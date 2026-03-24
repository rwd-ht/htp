from __future__ import annotations

import pytest

from htp.pattern import Pattern
from htp.pattern import get_dynamic_instances
from htp.pattern import set_environment_variable


def test_environment_variable_exists(monkeypatch):
    with monkeypatch.context() as m:
        m.setenv("VARIABLE", "value")
        assert set_environment_variable("abc{{ VARIABLE }}def") == "abcvaluedef"


def test_environment_variable_missing():
    with pytest.raises(RuntimeError):
        set_environment_variable("{{ VARIABLE }}")


def test_environment_variable_no_variable():
    assert set_environment_variable("abc") == "abc"


def test_dynamic_variable_no_variable():
    variables = dict()
    string = "abc"
    result = [
        "abc",
    ]
    assert get_dynamic_instances(string, variables) == result


def test_dynamic_variable_one():
    variables = dict(
        variable=[
            "value",
        ],
    )
    string = "abc{{ variable }}def"
    result = [
        "abcvaluedef",
    ]
    assert get_dynamic_instances(string, variables) == result


def test_dynamic_variable_many():
    variables = dict(
        variable=[
            "value1",
            "value2",
        ],
    )
    string = "abc{{ variable }}def"
    result = [
        "abcvalue1def",
        "abcvalue2def",
    ]
    assert get_dynamic_instances(string, variables) == result


def test_dynamic_variable_none():
    variables = dict(
        variable=[],
    )
    string = "abc{{ variable }}def"
    result = []
    assert get_dynamic_instances(string, variables) == result
