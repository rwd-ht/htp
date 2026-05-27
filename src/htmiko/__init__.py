# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

import sys

__version__ = "4.6.1"
PY_MAJ_VER = 3
PY_MIN_VER = 9
MIN_PYTHON_VER = "3.9"


# Make sure user is using a valid Python version
def check_python_version():  # type: ignore
    python_snake = "\U0001f40d"

    msg = f"""

HTMiko Version {__version__} requires Python Version {MIN_PYTHON_VER} or higher.

"""
    if sys.version_info.major != PY_MAJ_VER:
        raise ValueError(msg)
    elif sys.version_info.minor < PY_MIN_VER:
        # Why not :-)
        msg = msg.rstrip() + " {snake}\n\n".format(snake=python_snake)
        raise ValueError(msg)


check_python_version()  # type: ignore


import logging  # noqa

# Logging configuration
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


from htmiko.base_connection import BaseConnection  # noqa
from htmiko.cisco.cisco_ios import InLineTransfer  # noqa
from htmiko.exceptions import ConfigInvalidException  # noqa; noqa
from htmiko.exceptions import ConnectionException
from htmiko.exceptions import HTMikoAuthenticationException
from htmiko.exceptions import HTMikoBaseException
from htmiko.exceptions import HTMikoTimeoutException
from htmiko.exceptions import ReadException
from htmiko.exceptions import ReadTimeout
from htmiko.scp_functions import file_transfer  # noqa
from htmiko.scp_functions import progress_bar
from htmiko.scp_handler import SCPConn  # noqa
from htmiko.ssh_autodetect import SSHDetect  # noqa
from htmiko.ssh_dispatcher import ConnectHandler  # noqa
from htmiko.ssh_dispatcher import ConnLogOnly  # noqa
from htmiko.ssh_dispatcher import ConnUnify  # noqa
from htmiko.ssh_dispatcher import FileTransfer  # noqa
from htmiko.ssh_dispatcher import TelnetFallback  # noqa
from htmiko.ssh_dispatcher import platforms  # noqa
from htmiko.ssh_dispatcher import redispatch  # noqa
from htmiko.ssh_dispatcher import ssh_dispatcher  # noqa

# Alternate naming
HTMiko = ConnectHandler

__all__ = (
    "ConnectHandler",
    "AgnosticHandler",
    "ConnLogOnly",
    "ConnUnify",
    "ssh_dispatcher",
    "platforms",
    "SCPConn",
    "FileTransfer",
    "HTMikoBaseException",
    "ConnectionException",
    "HTMikoTimeoutException",
    "HTMikoTimeoutException",
    "ConfigInvalidException",
    "ReadException",
    "ReadTimeout",
    "HTMikoAuthenticationException",
    "HTMikoAuthenticationException",
    "InLineTransfer",
    "redispatch",
    "SSHDetect",
    "BaseConnection",
    "HTMiko",
    "file_transfer",
    "progress_bar",
)

# Cisco cntl-shift-six sequence
CNTL_SHIFT_6 = chr(30)
