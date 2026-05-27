# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Subclass specific to Cisco AP."""

from __future__ import annotations

from htmiko.cisco_base_connection import CiscoBaseConnection
from htmiko.no_config import NoConfig


class CiscoApSSH(NoConfig, CiscoBaseConnection):
    """Subclass specific to Cisco AP."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        cmd = "terminal width 132"
        self.set_terminal_width(command=cmd, pattern=cmd)
        self.disable_paging()
        self.set_base_prompt()
