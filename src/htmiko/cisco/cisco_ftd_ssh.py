# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Subclass specific to Cisco FTD."""

from __future__ import annotations

from typing import Any

from htmiko.cisco_base_connection import CiscoSSHConnection
from htmiko.no_config import NoConfig
from htmiko.no_enable import NoEnable


class CiscoFtdSSH(NoEnable, NoConfig, CiscoSSHConnection):
    """Subclass specific to Cisco FTD."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

    def send_config_set(self, *args: Any, **kwargs: Any) -> str:
        """Canot change config on FTD via ssh"""
        raise NotImplementedError

    def check_config_mode(
        self,
        check_string: str = "",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """Canot change config on FTD via ssh"""
        return False
