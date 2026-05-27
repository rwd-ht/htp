# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Adva support."""

from __future__ import annotations

import re
from typing import Any
from typing import Optional

from htmiko.cisco_base_connection import CiscoSSHConnection
from htmiko.no_config import NoConfig
from htmiko.no_enable import NoEnable


class AdvaAosFsp150F2SSH(NoEnable, NoConfig, CiscoSSHConnection):
    """
    Adva AOS FSP 15P F2 SSH Base Class

    F2 AOS applies for the following FSP150 device types: FSP150CC-825

    These devices don't have an Enable Mode or a Config Mode.

    Configuration Should be applied via the configuration context:

    home
    configure snmp
    add v3user guytest noauth-nopriv
    home

    configure system
    home

    Use of home to return to CLI root context, home cannot be used from root
    LAB-R2-825-1:--> home
    Unrecognized command
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        \n for default enter causes some issues with the Adva so setting to \r.
        """
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Handles devices with security prompt enabled
        """
        data = self.read_until_pattern(
            pattern=r"Do you wish to continue \[Y\|N\]-->|-->",
        )
        if "continue" in data:
            self.write_channel(f"y{self.RETURN}")
        else:
            self.write_channel(f"help?{self.RETURN}")
        data = self.read_until_pattern(pattern=r"-->")
        self.set_base_prompt()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = r"(^.+?)-->$",
        alt_prompt_terminator: str = "",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:

        prompt = self.find_prompt()
        match = re.search(pri_prompt_terminator, prompt)
        if not match:
            raise ValueError(f"Router prompt not found: {repr(prompt)}")
        self.base_prompt = match[1]
        return self.base_prompt
