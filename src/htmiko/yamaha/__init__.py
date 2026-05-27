# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations
from __future__ import unicode_literals

from htmiko.yamaha.yamaha import YamahaSSH
from htmiko.yamaha.yamaha import YamahaTelnet

__all__ = ["YamahaSSH", "YamahaTelnet"]
