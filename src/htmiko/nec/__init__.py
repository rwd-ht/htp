# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations
from __future__ import unicode_literals

from htmiko.nec.nec_ix import NecIxSSH
from htmiko.nec.nec_ix import NecIxTelnet

__all__ = ["NecIxSSH", "NecIxTelnet"]
