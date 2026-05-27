# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from typing import Any

from htmiko.cisco_base_connection import CiscoSSHConnection
from htmiko.no_config import NoConfig
from htmiko.no_enable import NoEnable


class BrocadeFOSSSH(NoEnable, NoConfig, CiscoSSHConnection):
    """Brocade Fabric OS support"""

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()
