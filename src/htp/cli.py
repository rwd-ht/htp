from __future__ import annotations

import cmd
import logging
import pathlib
import re
import readline

from htp.config import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

HISTORY = pathlib.Path.home() / ".htp-history"
HISTORY_MAX = 1000


class HTPShell(cmd.Cmd):
    intro = "Don't Panic.  Type help or ? to list commands."
    file = None

    def __init__(self, *args, **kwargs):
        self.credentails = None
        self.config = load_config()
        super().__init__(*args, **kwargs)
        self.prompt = "htp> "

    def do_shell(self, _):
        """
        run shell command
        """
        print(f"not yet implemented")

    def postcmd(self, stop, line):
        length = readline.get_current_history_length()
        line = re.sub(
            r"(password|secret|enable) \S+",
            r"\g<1> redacted",
            line,
            flags=re.IGNORECASE,
        )
        readline.replace_history_item(length - 1, line)
        return super().postcmd(stop, line)

    def do_history(self, command):
        """
        show history
        """
        lines = readline.get_current_history_length()
        start = lines - (lines - 1)
        if command and command.isdigit():
            start = lines - int(command)
        for idx in range(start, readline.get_current_history_length()):
            print(readline.get_history_item(idx))

    def cmdloop(self, *args, **kwargs):
        try:
            readline.read_history_file(HISTORY)
        except FileNotFoundError:
            pass
        except Exception:
            logger.error(f"can't read {HISTORY}")

        try:
            super().cmdloop(*args, **kwargs)
        except Exception as exc:
            logger.error(f"shell exited: {type(exc).__name__}: {exc}")
        finally:
            readline.set_history_length(HISTORY_MAX)
            readline.write_history_file(HISTORY)

    def emptyline(self):
        return False

    def default(self, line):
        if line.lstrip().startswith("#"):
            return
        print(f"Unknown command: {line}")

    def do_exit(self, _):
        """
        exit the program
        """
        return True

    def do_EOF(self, _):
        """
        exit the program
        """
        print("")
        return True
