#!/usr/bin/env python

# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations


def test_save_base(net_connect, commands, expected_responses):
    """
    Test save config with no options.
    """
    save_verify = expected_responses["save_config"]

    cmd_response = net_connect.save_config()
    assert save_verify in cmd_response


def test_disconnect(net_connect, commands, expected_responses):
    """
    Terminate the SSH session
    """
    net_connect.disconnect()
