from __future__ import annotations

import dataclasses
import sys

from htp.cli import HTPShell


class HTPCommands(HTPShell):
    def do_sass(self, _):
        """
        transpile style.scss to style.css
        """
        import pysass

        _argv = sys.argv[1:]
        try:
            sys.argv[1:] = [
                "--style=compact",
                "src/htp/htmlfiles/style.scss",
                "src/htp/htmlfiles/style.css",
            ]
            if not pysass.main():
                print("ok!")
        except:
            print("sass problem")
            import traceback

            traceback.print_exc()
        finally:
            sys.argv[1:] = _argv

    def do_config(self, _):
        @dataclasses.dataclass
        class MaxValues:
            keylen: int = 0
            depth: int = 0

        SPACES = 2
        max_values = MaxValues(0, 0)

        def _set_max_values(section: dict, depth=0):
            max_values.depth = max(max_values.depth, depth)
            for key, value in section.items():
                max_values.keylen = max(max_values.keylen, len(key))
                if isinstance(value, dict):
                    _set_max_values(value, depth + 1)

        def _print(section: dict, depth=0):
            for key, value in section.items():
                _output = (depth * " " * SPACES) + key + ":"
                _padding = max(_width - len(_output), 0)
                print(f"{_output} {' ' * _padding}", end="")
                if isinstance(value, dict):
                    print("")
                    _print(value, depth + 1)
                else:
                    print(value)

        _config = self.config.model_dump()
        _set_max_values(_config)
        _width = max_values.keylen + SPACES + (max_values.depth * SPACES)
        _print(_config)

    def do_policy(self, line):
        """
        run policy against configs
        """
        if not line:
            print(f"enter glob for: {self.config.policy.policies_dir}")
            return
        from htp.pattern import run_analysis

        run_analysis(self.config, self.config.policy.policies_dir.glob(line))

    def do_html(self, line):
        """
        output html report for policy results
        """
        from htp.pattern import output_html_report

        args = line.split()
        if "--force" in args or "-f" in args:
            import shutil

            shutil.rmtree(self.config.html.output_dir)
        try:
            output_html_report(self.config)
        except:
            import traceback

            traceback.print_exc()


def main():
    sys.exit(HTPCommands().cmdloop())
