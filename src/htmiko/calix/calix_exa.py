# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Calix Exa SSH Driver"""

from __future__ import annotations

from typing import Any
from typing import Optional

from htmiko.base_connection import BaseConnection
from htmiko.no_config import NoConfig
from htmiko.no_enable import NoEnable


class CalixExaBase(BaseConnection, NoEnable, NoConfig):
    def session_preparation(self) -> Any:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()
        self.disable_paging(command="disable session pager")

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )


class CalixExaSSH(CalixExaBase):
    pass


class CalixExaTelnet(CalixExaBase):
    pass
