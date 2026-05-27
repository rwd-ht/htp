# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

import re
from typing import Any
from typing import Iterator
from typing import Sequence
from typing import TextIO
from typing import Union

from htmiko.cisco_base_connection import CiscoSSHConnection
from htmiko.no_config import NoConfig
from htmiko.no_enable import NoEnable


class ZyxelSSH(NoEnable, NoConfig, CiscoSSHConnection):
    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """No paging on Zyxel"""
        return ""

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        enter_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """No config mode on Zyxel"""
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            enter_config_mode=enter_config_mode,
            **kwargs,
        )

    def session_preparation(self) -> None:
        super().session_preparation()
        # Zyxel switches output ansi codes
        self.ansi_escape_codes = True

    def strip_ansi_escape_codes(self, string_buffer: str) -> str:
        """Replace '^J' code by next line"""
        output = re.sub(r"^\^J", self.RETURN, string_buffer)
        return super().strip_ansi_escape_codes(output)
