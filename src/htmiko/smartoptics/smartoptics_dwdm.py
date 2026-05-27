# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""SmartOptics DWDM is htmiko SSH class for SmartOptics DWDM devices."""

from __future__ import annotations

from typing import Optional

from htmiko.base_connection import BaseConnection


class SmartOpticsDWDMSSH(BaseConnection):
    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        return super().set_base_prompt(
            pri_prompt_terminator,
            alt_prompt_terminator,
            delay_factor,
            pattern,
        )
