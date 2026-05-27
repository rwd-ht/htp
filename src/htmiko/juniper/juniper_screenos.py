# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from htmiko.base_connection import BaseConnection
from htmiko.no_config import NoConfig
from htmiko.no_enable import NoEnable


class JuniperScreenOsSSH(NoEnable, NoConfig, BaseConnection):
    """
    Implement methods for interacting with Juniper ScreenOS devices.
    """

    def _try_session_preparation(self, force_data: bool = False) -> None:
        return super()._try_session_preparation(force_data=force_data)

    def session_preparation(self) -> None:
        """
        ScreenOS can be configured to require: Accept this agreement y/[n]
        """
        terminator = r"\->"
        pattern = rf"(?:Accept this.*|{terminator})"
        data = self.read_until_pattern(pattern=pattern)
        if "Accept this" in data:
            self.write_channel("y")
            data += self.read_until_pattern(pattern=terminator)
        self.set_base_prompt()
        self.disable_paging(command="set console page 0")

    def save_config(
        self,
        cmd: str = "save config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save Config."""
        return self._send_command_str(command_string=cmd)
