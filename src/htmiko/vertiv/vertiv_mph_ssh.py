# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from htmiko.cisco_base_connection import CiscoSSHConnection
from htmiko.no_config import NoConfig
from htmiko.no_enable import NoEnable


class VertivMPHBase(NoEnable, NoConfig, CiscoSSHConnection):
    """
    Support for Vertiv MPH Power Distribution Units.
    Should work with any Vertiv Device with an RPC2 module.
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        # self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"cli->")
        self.set_base_prompt()

    def save_config(
        self,
        cmd: str = "save",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves configuration."""
        return super().save_config(
            cmd=cmd,
            confirm=confirm,
            confirm_response=confirm_response,
        )

    def cleanup(self, command: str = "logout") -> None:
        return super().cleanup(command=command)


class VertivMPHSSH(VertivMPHBase):
    pass
