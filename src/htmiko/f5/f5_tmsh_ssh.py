# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

from htmiko.base_connection import BaseConnection
from htmiko.no_config import NoConfig


class F5TmshSSH(NoConfig, BaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"#")
        self.tmsh_mode()
        self._config_mode = False
        cmd = 'run /util bash -c "stty cols 255"'
        self.set_terminal_width(command=cmd, pattern="run")
        self.disable_paging(
            command="modify cli preference pager disabled display-threshold 0",
        )

    def tmsh_mode(self, delay_factor: float = 1.0) -> str:
        """tmsh command is equivalent to config command on F5."""
        command = f"{self.RETURN}tmsh{self.RETURN}"
        output = self._send_command_str(command, expect_string=r"tmos.*#")
        self.set_base_prompt()
        return output

    def exit_tmsh(self) -> str:
        output = self._send_command_str("quit", expect_string=r"#")
        self.set_base_prompt()
        return output

    def cleanup(self, command: str = "exit") -> None:
        """Gracefully exit the SSH session."""
        try:
            self.exit_tmsh()
        except Exception:
            pass

        # Always try to send final 'exit' (command)
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)
