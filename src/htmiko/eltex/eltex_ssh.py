# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from typing import Any

from htmiko.cisco_base_connection import CiscoSSHConnection


class EltexSSH(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="terminal datadump")

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented"""
        raise NotImplementedError
