# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

import os

__version__ = "5.0.0"
MAX_WORKERS = int(os.environ.get("HTMIKO_MAX_THREADS", 10))
ERROR_PATTERN = "%%%failed%%%"

GREP = "/bin/grep"
if not os.path.exists(GREP):
    GREP = "/usr/bin/grep"
