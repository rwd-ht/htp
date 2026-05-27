# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""
Ericsson Ipos looks like it was RedBack equipment.
"""

from __future__ import annotations

import re
import warnings
from typing import Any
from typing import Iterator
from typing import Optional
from typing import Sequence
from typing import TextIO
from typing import Union

from htmiko.base_connection import BaseConnection


class EricssonIposSSH(BaseConnection):
    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 512", pattern=r"terminal")
        self.disable_paging()

    def check_enable_mode(self, check_string: str = "#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "enable 15",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )

    def exit_enable_mode(self, exit_command: str = "disable") -> str:
        return super().exit_enable_mode(exit_command=exit_command)

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command,
            pattern=pattern,
            re_flags=re_flags,
        )

    def exit_config_mode(self, exit_config: str = "end", pattern: str = "#") -> str:
        """
        Exit from configuration mode.
        Ercisson output :
            end                   Commit configuration changes and return to exec mode
        """
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """Ericsson IPOS requires you not exit from configuration mode."""
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            **kwargs,
        )

    def save_config(
        self,
        cmd: str = "save config",
        confirm: bool = True,
        confirm_response: str = "yes",
    ) -> str:
        """Saves configuration"""
        output = ""
        if confirm:
            output += self._send_command_timing_str(
                command_string=cmd,
                strip_prompt=False,
                strip_command=False,
            )

            if confirm_response:
                output += self._send_command_timing_str(
                    confirm_response,
                    strip_prompt=False,
                    strip_command=False,
                )
            else:
                output += self._send_command_timing_str(
                    self.RETURN,
                    strip_prompt=False,
                    strip_command=False,
                )
        else:
            output += self._send_command_str(
                command_string=cmd,
                strip_prompt=False,
                strip_command=False,
            )
        return output

    def commit(
        self,
        confirm: bool = False,
        confirm_delay: Optional[int] = None,
        comment: str = "",
        read_timeout: float = 120.0,
    ) -> str:
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        Automatically enters configuration mode

        """
        if confirm_delay and not confirm:
            raise ValueError(
                "Invalid arguments supplied to commit method both confirm and check",
            )

        command_string = "commit"
        commit_marker = "Transaction committed"
        if confirm:
            if confirm_delay:
                command_string = f"commit confirmed {confirm_delay}"
            else:
                command_string = "commit confirmed"
            commit_marker = "Commit confirmed ,it will be rolled back within"

        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            comment = f'"{comment}"'
            command_string += f" comment {comment}"

        output = self.config_mode()

        output += self._send_command_str(
            command_string,
            strip_prompt=False,
            strip_command=False,
            read_timeout=read_timeout,
        )

        if commit_marker not in output:
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")

        self.exit_config_mode()

        return output
