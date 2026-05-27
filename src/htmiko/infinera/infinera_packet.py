# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

import time

from htmiko.cisco_base_connection import CiscoBaseConnection


class InfineraBase(CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging("terminal more off")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()


class InfineraPacketSSH(InfineraBase):
    pass


class InfineraPacketTelnet(InfineraBase):
    pass
