# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Enterasys support."""

from __future__ import annotations

from typing import Any

from htmiko.cisco_base_connection import CiscoSSHConnection


class EnterasysSSH(CiscoSSHConnection):
    """Enterasys support."""

    def session_preparation(self) -> None:
        """Enterasys requires enable mode to disable paging."""
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()
        self.disable_paging(command="set length 0")

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented"""
        raise NotImplementedError
