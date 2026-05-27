#!/usr/bin/env python

# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

"""
Implement common functions for tests
"""

import io
import sys


def parse_yaml(yaml_file):
    """
    Parses a yaml file, returning its contents as a dict.
    """

    try:
        import yaml
    except ImportError:
        sys.exit("Unable to import yaml module.")

    try:
        with io.open(yaml_file, encoding="utf-8") as fname:
            return yaml.safe_load(fname)
    except IOError:
        sys.exit("Unable to open YAML file: {0}".format(yaml_file))
