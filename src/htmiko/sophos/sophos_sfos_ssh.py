# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""SophosXG (SFOS) Firewall support"""

from __future__ import annotations

import os
import time
from typing import Any

from htmiko.cisco_base_connection import CiscoSSHConnection
from htmiko.no_config import NoConfig
from htmiko.no_enable import NoEnable

SOPHOS_MENU_DEFAULT = os.getenv("HTMIKO_SOPHOS_MENU", "4")


class SophosSfosSSH(NoEnable, NoConfig, CiscoSSHConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"Select Menu Number")
        """
        Sophos Firmware Version SFOS 18.0.0 GA-Build339

        Main Menu

            1.  Network  Configuration
            2.  System   Configuration
            3.  Route    Configuration
            4.  Device Console
            5.  Device Management
            6.  VPN Management
            7.  Shutdown/Reboot Device
            0.  Exit

            Select Menu Number [0-7]:
        """
        self.send_command_expect("\r", expect_string=r"Select Menu Number")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented"""
        raise NotImplementedError
