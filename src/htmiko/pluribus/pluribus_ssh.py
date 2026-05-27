# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

import time
from typing import Any
from typing import Optional

from htmiko.base_connection import BaseConnection
from htmiko.no_config import NoConfig


class PluribusSSH(NoConfig, BaseConnection):
    """Common methods for Pluribus."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._config_mode = False

    def session_preparation(self) -> None:
        """Prepare the htmiko session."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(
        self,
        command: str = "pager off",
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Disable paging on Pluribus devices.

        :param command: Command to disable pagination of output
        :param cmd_verify: Verify command echo before proceeding
        :param pattern: Pattern to terminate reading of channel
        """
        return super().disable_paging(
            command=command,
            cmd_verify=cmd_verify,
            pattern=pattern,
        )
