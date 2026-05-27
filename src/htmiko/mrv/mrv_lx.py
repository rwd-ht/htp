# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""MRV Communications Driver (LX)."""

from __future__ import annotations

import re
import time
from typing import Optional

from htmiko.cisco_base_connection import CiscoSSHConnection


class MrvLxSSH(CiscoSSHConnection):
    """MRV Communications Driver (LX)."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>|>>]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="no pause")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, check_string: str = ">>") -> bool:
        """MRV has a >> for enable mode and config mode instead of # like Cisco"""
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "assword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter enable mode."""
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )

    def check_config_mode(
        self,
        check_string: str = r"Conf.*>>",
        pattern: str = "",
        force_regex: bool = True,
    ) -> bool:
        return super().check_config_mode(
            check_string=check_string,
            pattern=pattern,
            force_regex=force_regex,
        )

    def config_mode(
        self,
        config_command: str = "configuration",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command,
            pattern=pattern,
            re_flags=re_flags,
        )

    def save_config(
        self,
        cmd: str = "save config flash",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves configuration."""
        return super().save_config(
            cmd=cmd,
            confirm=confirm,
            confirm_response=confirm_response,
        )
