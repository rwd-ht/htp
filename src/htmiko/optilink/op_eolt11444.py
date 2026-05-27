# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from htmiko.cisco_base_connection import CiscoBaseConnection


class OptilinkEOLT11444Base(CiscoBaseConnection):
    """
    Optilink EOLT 11444
    Optilink EOLT 11448
    """

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging()
        self.clear_buffer()
        self.exit_enable_mode()

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Enter into configuration mode."""
        return super().config_mode(
            config_command=config_command,
            pattern=pattern,
            re_flags=re_flags,
        )


class OptilinkEOLT11444Telnet(OptilinkEOLT11444Base):
    """
    Optilink EOLT 11444 telnet driver
    Optilink EOLT 11448 telnet driver
    """

    pass
