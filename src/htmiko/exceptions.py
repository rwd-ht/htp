# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from paramiko.ssh_exception import AuthenticationException
from paramiko.ssh_exception import SSHException


class HTMikoBaseException(Exception):
    """General base exception except for exceptions that inherit from Paramiko."""

    pass


class ConnectionException(HTMikoBaseException):
    """Generic exception indicating the connection failed."""

    pass


class HTMikoTimeoutException(SSHException):
    """SSH session timed trying to connect to the device."""

    pass


HTMikoTimeoutException = HTMikoTimeoutException


class HTMikoAuthenticationException(AuthenticationException):
    """SSH authentication exception based on Paramiko AuthenticationException."""

    pass


HTMikoAuthenticationException = HTMikoAuthenticationException


class ConfigInvalidException(HTMikoBaseException):
    """Exception raised for invalid configuration error."""

    pass


class WriteException(HTMikoBaseException):
    """General exception indicating an error occurred during a write operation."""

    pass


class ReadException(HTMikoBaseException):
    """General exception indicating an error occurred during a read operation."""

    pass


class ReadTimeout(ReadException):
    output: str | None = None
    timeout: int | None = None
    """General exception indicating an error occurred during a read operation."""

    def __init__(self, message, output: str | None = None, timeout: int | None = None):
        self.output = output
        self.timeout = timeout
        super().__init__(message)

    pass
