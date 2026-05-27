# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from typing import Any

from htmiko.base_connection import BaseConnection
from htmiko.no_enable import NoEnable


class NetAppcDotSSH(NoEnable, BaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        cmd = self.RETURN + "rows 0" + self.RETURN
        self.disable_paging(command=cmd)

    def send_command_with_y(self, *args: Any, **kwargs: Any) -> str:
        output = self._send_command_timing_str(*args, **kwargs)
        if "{y|n}" in output:
            output += self._send_command_timing_str(
                "y",
                strip_prompt=False,
                strip_command=False,
            )
        return output

    def check_config_mode(
        self,
        check_string: str = "*>",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "set -privilege diagnostic -confirmations off",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command,
            pattern=pattern,
            re_flags=re_flags,
        )

    def exit_config_mode(
        self,
        exit_config: str = "set -privilege admin -confirmations off",
        pattern: str = "",
    ) -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)
