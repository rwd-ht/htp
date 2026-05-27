# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Generic Terminal Server driver."""

from __future__ import annotations

from typing import Any

from htmiko.base_connection import BaseConnection


class TerminalServer(BaseConnection):
    """Generic Terminal Server driver.

    Allow direct write_channel / read_channel operations without session_preparation causing
    an exception.
    """

    def session_preparation(self) -> None:
        """Do nothing here; base_prompt is not set; paging is not disabled."""
        pass


class TerminalServerSSH(TerminalServer):
    """Generic Terminal Server driver SSH."""

    pass


class TerminalServerTelnet(TerminalServer):
    """Generic Terminal Server driver telnet."""

    def telnet_login(self, *args: Any, **kwargs: Any) -> str:
        # Disable automatic handling of username and password when using terminal server driver
        return ""

    def std_login(self, *args: Any, **kwargs: Any) -> str:
        return super().telnet_login(*args, **kwargs)
