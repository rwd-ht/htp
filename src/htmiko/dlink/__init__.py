# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from htmiko.dlink.dlink_ds import DlinkDSSSH
from htmiko.dlink.dlink_ds import DlinkDSTelnet

__all__ = ["DlinkDSTelnet", "DlinkDSSSH"]
