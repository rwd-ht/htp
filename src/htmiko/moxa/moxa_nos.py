# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""
Tested with

EDS-508A
EDS-516A

Note:
This only works in CLI mode. If the device is in Menu mode, you need to change that first.
"""

from __future__ import annotations

from htmiko.cisco_base_connection import CiscoSSHConnection


class MoxaNosBase(CiscoSSHConnection):
    """MOXA base driver"""

    pass


class MoxaNosSSH(MoxaNosBase):
    """MOXA SSH driver"""

    pass
