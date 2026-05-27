# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

import time
from typing import Any
from typing import Optional

from htmiko.cisco.cisco_ios import CiscoIosBase
from htmiko.no_config import NoConfig
from htmiko.no_enable import NoEnable


class KeymileSSH(NoEnable, NoConfig, CiscoIosBase):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("default_enter", "\r\n")
        super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """Keymile does not use paging."""
        return ""

    def strip_prompt(self, a_string: str) -> str:
        """Remove appending empty line and prompt from output"""
        a_string = a_string[:-1]
        return super().strip_prompt(a_string=a_string)

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """set prompt termination to >"""
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
