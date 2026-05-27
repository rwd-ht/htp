# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations


class NoConfig:
    """
    Class for platforms that have no config mode.

    check_config_mode returns True as the expectation is that configuration commands
    can be executed directly. So in your current state, you are in "config mode" i.e.
    you can make configuration changes.

    If you truly cannot make any configuration changes to device then you should probably
    overwrite check_config_mode in the platform specific driver and return False.
    """

    def check_config_mode(
        self,
        check_string: str = "",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        return True

    def config_mode(
        self,
        config_command: str = "",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return ""

    def exit_config_mode(self, exit_config: str = "", pattern: str = "") -> str:
        return ""
