from __future__ import annotations


def set_environment_variable(string: str) -> str:
    """
    replace {{ VARIABLE }} with value from environment
    matches any variable name that is all caps
    raises RuntimeError if VARIABLE not set
    """


def get_dynamic_instances(string: str, variable: dict[str, list]) -> str:
    """
    replace {{ variable }} with all instances of variable in variables
    """


class Pattern:
    """
    Pattern, used to match things
    """
