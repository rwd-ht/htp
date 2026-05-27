# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

import re
from typing import Optional


class NoEnable:
    """
    Class for platforms that have no enable mode.

    This module translates the meaning of "enable" mode to be a proxy for "can
    go into config mode". In other words, that you ultimately have privileges
    to execute configuration changes.

    The expectation on platforms that have no method for elevating privileges
    is that the standard default privileges allow configuration changes.

    Consequently check_enable_mode returns True by default for platforms that
    don't explicitly support enable mode.
    """

    def check_enable_mode(self, check_string: str = "") -> bool:
        return True

    def enable(
        self,
        cmd: str = "",
        pattern: str = "",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        return ""

    def exit_enable_mode(self, exit_command: str = "") -> str:
        return ""
