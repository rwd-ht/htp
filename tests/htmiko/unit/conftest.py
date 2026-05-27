# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

import pytest

TEST_ENCRYPTION_KEY = "boguskey"


@pytest.fixture
def set_encryption_key(monkeypatch):
    """Fixture to set a test encryption key"""

    def _set_key(key=TEST_ENCRYPTION_KEY):
        """Inner function to set a test encryption key"""
        monkeypatch.setenv("HTMIKO_TOOLS_KEY", key)
        return key

    return _set_key
