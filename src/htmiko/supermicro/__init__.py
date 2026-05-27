# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from htmiko.supermicro.smci_smis import SmciSwitchSmisSSH
from htmiko.supermicro.smci_smis import SmciSwitchSmisTelnet

__all__ = ["SmciSwitchSmisSSH", "SmciSwitchSmisTelnet"]
