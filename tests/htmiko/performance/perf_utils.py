# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from os import path

from test_utils import parse_yaml


def commands(platform):
    """Parse the commands.yml file to get a commands dictionary."""
    PWD = path.dirname(path.realpath(__file__))
    test_platform = platform
    commands_yml = parse_yaml(PWD + "/../etc/commands.yml")
    return commands_yml[test_platform]
