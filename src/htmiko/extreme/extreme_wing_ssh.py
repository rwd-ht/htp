# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from htmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeWingSSH(CiscoSSHConnection):
    """Extreme WiNG support."""

    def session_preparation(self) -> None:
        """Disable paging and set Max term width"""
        self._test_channel_read(pattern=r">|#")
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 512", pattern="terminal")
        self.disable_paging(command="no page")
