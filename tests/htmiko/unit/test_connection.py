#!/usr/bin/env python

# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

from __future__ import annotations

import logging
import sys

import pytest

from htmiko import ConnectHandler
from htmiko import ConnectionException
from htmiko import ConnLogOnly
from htmiko import ConnUnify
from htmiko import HTMikoAuthenticationException
from htmiko import HTMikoTimeoutException

is_linux = sys.platform == "linux" or sys.platform == "linux2"
skip_if_not_linux = pytest.mark.skipif(not is_linux, reason="Test Requires Linux")

# Fictional devices that will fail
DEVICE1 = {
    "host": "localhost",
    "device_type": "linux",
    "username": "bogus",
    "password": "bogus",
}

DEVICE2 = {
    "host": "localhost",
    "device_type": "linux",
    "username": "bogus",
    "password": "bogus",
    "port": 8022,
}


@skip_if_not_linux
def test_connecthandler_auth_failure():
    with pytest.raises(HTMikoAuthenticationException):
        net_connect = ConnectHandler(**DEVICE1)  # noqa


def test_connecthandler_timeout():
    with pytest.raises(HTMikoTimeoutException):
        net_connect = ConnectHandler(**DEVICE2)  # noqa


def test_connlogonly(caplog):
    log_level = logging.INFO
    log_file = "my_output.log"

    net_connect = ConnLogOnly(log_file=log_file, log_level=log_level, **DEVICE2)
    assert net_connect is None

    assert "ERROR" in caplog.text
    assert caplog.text.count("ERROR") == 1
    assert "was unable to reach the provided host and port" in caplog.text


def test_connunify():
    with pytest.raises(ConnectionException):
        net_connect = ConnUnify(**DEVICE1)
    with pytest.raises(ConnectionException):
        net_connect = ConnUnify(**DEVICE2)  # noqa
