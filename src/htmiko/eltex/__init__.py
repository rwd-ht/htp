# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from htmiko.eltex.eltex_esr_ssh import EltexEsrSSH
from htmiko.eltex.eltex_ssh import EltexSSH

__all__ = ["EltexSSH", "EltexEsrSSH"]
