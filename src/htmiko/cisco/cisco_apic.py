# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Subclass specific to Cisco APIC."""

from __future__ import annotations

from htmiko.cisco_base_connection import CiscoSSHConnection
from htmiko.linux.linux_ssh import LinuxSSH


class CiscoApicSSH(LinuxSSH):
    """
    Subclass specific to Cisco APIC.

    This class inherit from LinuxSSH because Cisco APIC is based on Linux
    """

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        In LinuxSSH, the disable_paging method does nothing; however, paging is enabled
        by default on Cisco APIC. To handle this, we utilize the disable_paging method
        from CiscoSSHConnection, the parent class of LinuxSSH. This approach leverages
        the shared implementation for Cisco SSH connections and ensures that any updates to
        disable_paging in the parent class are inherited.
        """
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        CiscoSSHConnection.disable_paging(self, command="terminal length 0")
