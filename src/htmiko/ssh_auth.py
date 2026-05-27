# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from typing import Any

from paramiko import SSHClient


class SSHClient_noauth(SSHClient):
    """Set noauth when manually handling SSH authentication."""

    def _auth(self, username: str, *args: Any) -> None:
        transport = self.get_transport()
        assert transport is not None
        transport.auth_none(username)
        return
