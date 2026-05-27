# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from htmiko.cisco_base_connection import CiscoSSHConnection


class ArrisCERBase(CiscoSSHConnection):
    """
    Arris CER Support.

    Implements methods for interacting with Arris CER platforms.
    """

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Enters configuration mode."""
        return super().config_mode(
            config_command=config_command,
            pattern=pattern,
            re_flags=re_flags,
        )

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves the running configuration to NVRAM."""
        return super().save_config(
            cmd=cmd,
            confirm=confirm,
            confirm_response=confirm_response,
        )


class ArrisCERSSH(ArrisCERBase):
    """Arris CER SSH Driver."""

    pass
