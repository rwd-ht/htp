# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Centec OS Support"""

from __future__ import annotations

from htmiko.cisco_base_connection import CiscoBaseConnection


class CentecOSBase(CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging()

    def save_config(
        self,
        cmd: str = "write",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save config: write"""
        return super().save_config(
            cmd=cmd,
            confirm=confirm,
            confirm_response=confirm_response,
        )


class CentecOSSSH(CentecOSBase):
    pass


class CentecOSTelnet(CentecOSBase):
    pass
