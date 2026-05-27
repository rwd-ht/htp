# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Optional

import paramiko
import serial

from htmiko._telnetlib import telnetlib
from htmiko.exceptions import ReadException
from htmiko.exceptions import WriteException
from htmiko.htmiko_globals import MAX_BUFFER
from htmiko.utilities import write_bytes


class Channel(ABC):
    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create the object."""
        pass

    # @abstractmethod
    # def __repr__(self) -> str:
    #     """String representation of the object."""
    #     pass
    #
    # @abstractmethod
    # def open(self, width: int = 511, height: int = 1000) -> None:
    #     """Create the underlying connection."""
    #     pass
    #
    # @abstractmethod
    # def close(self) -> None:
    #     """Close the underlying connection."""
    #     pass
    #
    # @abstractmethod
    # def login(self) -> None:
    #     """Handle the channel login process for any channel that requires it."""
    #     pass

    @abstractmethod
    def read_buffer(self) -> str:
        """Single read of available data."""
        pass

    @abstractmethod
    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        pass

    @abstractmethod
    def write_channel(self, out_data: str) -> None:
        """Write data down the channel."""
        pass

    # @abstractmethod
    # def is_alive(self) -> bool:
    #     """Is the channel alive."""
    #     pass


class SSHChannel(Channel):
    def __init__(self, conn: Optional[paramiko.Channel], encoding: str) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is None:
            raise WriteException(
                "Attempt to write data, but there is no active channel.",
            )
        self.remote_conn.sendall(write_bytes(out_data, encoding=self.encoding))

    def read_buffer(self) -> str:
        """Single read of available data."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        output = ""
        if self.remote_conn.recv_ready():
            outbuf = self.remote_conn.recv(MAX_BUFFER)
            if len(outbuf) == 0:
                raise ReadException("Channel stream closed by remote device.")
            output += outbuf.decode(self.encoding, "ignore")
        return output

    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        output = ""
        while True:
            new_output = self.read_buffer()
            output += new_output
            if new_output == "":
                break
        return output


class TelnetChannel(Channel):
    def __init__(self, conn: Optional[telnetlib.Telnet], encoding: str) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is None:
            raise WriteException(
                "Attempt to write data, but there is no active channel.",
            )
        self.remote_conn.write(write_bytes(out_data, encoding=self.encoding))  # type: ignore

    def read_buffer(self) -> str:
        """Single read of available data."""
        raise NotImplementedError

    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        return self.remote_conn.read_very_eager().decode(self.encoding, "ignore")  # type: ignore


class SerialChannel(Channel):
    def __init__(self, conn: Optional[serial.Serial], encoding: str) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is None:
            raise WriteException(
                "Attempt to write data, but there is no active channel.",
            )
        self.remote_conn.write(write_bytes(out_data, encoding=self.encoding))
        self.remote_conn.flush()

    def read_buffer(self) -> str:
        """Single read of available data."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        if self.remote_conn.in_waiting > 0:
            output = self.remote_conn.read(self.remote_conn.in_waiting).decode(
                self.encoding,
                "ignore",
            )
            assert isinstance(output, str)
            return output
        else:
            return ""

    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        output = ""
        while self.remote_conn.in_waiting > 0:
            output += self.read_buffer()
        return output
