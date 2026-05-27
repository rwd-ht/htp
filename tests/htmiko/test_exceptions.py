#!/usr/bin/env python

# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

from __future__ import annotations

from datetime import datetime
from os import path

import pytest
from test_utils import parse_yaml

from htmiko import ConnectHandler
from htmiko import HTMikoTimeoutException

PWD = path.dirname(path.realpath(__file__))
# DEVICE_DICT = parse_yaml(PWD + "/etc/test_devices_exc.yml")
DEVICE_DICT = {}


def test_valid_conn():
    """Verify device without modifications works."""
    device = DEVICE_DICT["cisco3_invalid"]
    conn = ConnectHandler(**device)
    assert conn.find_prompt() == "cisco3#"


def test_invalid_port():
    device = DEVICE_DICT["cisco3_invalid"]
    device["port"] = 8022
    with pytest.raises(HTMikoTimeoutException):
        ConnectHandler(**device)


def test_conn_timeout():
    device = DEVICE_DICT["cisco3_invalid"]
    device["conn_timeout"] = 5
    device["port"] = 8022
    start_time = datetime.now()
    with pytest.raises(HTMikoTimeoutException):
        ConnectHandler(**device)
    end_time = datetime.now()
    time_delta = end_time - start_time
    assert time_delta.total_seconds() > 5.0
    assert time_delta.total_seconds() < 5.1


def test_dns_fail():
    device = DEVICE_DICT["cisco3_invalid"]
    device["host"] = "invalid.lasthop.io"
    with pytest.raises(HTMikoTimeoutException):
        try:
            ConnectHandler(**device)
        except HTMikoTimeoutException as e:
            assert "DNS failure" in str(e)
            raise


def test_dns_fail_timeout():
    """Should fail very fast."""
    device = DEVICE_DICT["cisco3_invalid"]
    device["host"] = "invalid.lasthop.io"
    start_time = datetime.now()
    with pytest.raises(HTMikoTimeoutException):
        try:
            ConnectHandler(**device)
        except HTMikoTimeoutException as e:
            assert "DNS failure" in str(e)
            raise
    end_time = datetime.now()
    time_delta = end_time - start_time
    assert time_delta.total_seconds() < 0.1


def test_auth_timeout():
    assert True


def test_banner_timeout():
    assert True
