# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Fiberstore NetworkOS Driver."""

from __future__ import annotations

import time

from htmiko.cisco_base_connection import CiscoBaseConnection


class FiberstoreNetworkOSSSH(CiscoBaseConnection):
    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(
        self,
        cmd: str = "",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Not Implemented"""
        raise NotImplementedError

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "") -> str:
        return super().exit_config_mode(exit_config=exit_config)

    def check_config_mode(
        self,
        check_string: str = "(config)#",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        return super().check_config_mode(
            check_string=check_string,
            pattern=pattern,
            force_regex=force_regex,
        )
