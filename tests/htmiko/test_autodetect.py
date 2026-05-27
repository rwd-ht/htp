#!/usr/bin/env python

# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

from __future__ import annotations


def test_ssh_connect(ssh_autodetect):
    """Verify the connection was established successfully."""
    net_conn, real_device_type = ssh_autodetect
    device_type = net_conn.autodetect()
    print(device_type)
    assert device_type == real_device_type
