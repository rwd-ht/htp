# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from htmiko.paloalto.paloalto_panos import PaloAltoPanosSSH
from htmiko.paloalto.paloalto_panos import PaloAltoPanosTelnet

__all__ = ["PaloAltoPanosSSH", "PaloAltoPanosTelnet"]
