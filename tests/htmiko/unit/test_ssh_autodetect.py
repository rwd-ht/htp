#!/usr/bin/env python

# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

from __future__ import annotations

from htmiko.ssh_autodetect import SSH_MAPPER_BASE


def test_ssh_base_mapper_order():
    "SSH_MAPPER_BASE should be sorted based on the most common command used."
    assert SSH_MAPPER_BASE[0][1]["cmd"] == "show version"
