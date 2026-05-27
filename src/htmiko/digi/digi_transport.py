# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Digi TransPort Routers"""

from __future__ import annotations

from typing import Any

from htmiko.cisco_base_connection import CiscoSSHConnection
from htmiko.no_config import NoConfig
from htmiko.no_enable import NoEnable


class DigiTransportBase(NoEnable, NoConfig, CiscoSSHConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)

    def save_config(
        self,
        cmd: str = "config 0 save",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        output = self._send_command_str(
            command_string=cmd,
            expect_string="Please wait...",
        )
        return output


class DigiTransportSSH(DigiTransportBase):
    pass
