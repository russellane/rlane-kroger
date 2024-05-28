"""Command line interface."""

from pathlib import Path
from typing import List, Optional

from libcli import BaseCLI

from .archive import KrogerArchiveCmd
from .myinfo import KrogerMyInfoCmd
from .mytime import KrogerMyTimeCmd
from .print import KrogerPrintCmd


class KrogerCLI(BaseCLI):
    """Command line interface."""

    config = {
        # name of config file.
        "config-file": Path.home() / ".kroger.toml",
        # toml [section-name].
        "config-name": "kroger",
        # archive directory.
        "archive-path": Path.home() / "kroger-payslips",
        # signon.
        "myinfo-url": "",
        "mytime-url": "",
        "sso-user": "",
        "sso-password": "",
    }

    def init_parser(self) -> None:
        """Docstring."""

        self.parser = self.ArgumentParser(
            prog="kroger",
            description=self.dedent(
                """
            Kroger `payslip-pdf` tools; signon, parse, print, and archive payslips.
                """
            ),
        )

    def add_arguments(self) -> None:
        """Docstring."""

        self.add_subcommand_classes(
            [KrogerMyInfoCmd, KrogerMyTimeCmd, KrogerArchiveCmd, KrogerPrintCmd]
        )

    def main(self) -> None:
        """Command line interface entry point (method)."""

        if not self.options.cmd:
            self.parser.print_help()
            self.parser.exit(2, "error: Missing COMMAND\n")

        self.options.cmd()


def main(args: Optional[List[str]] = None) -> None:
    """Command line interface entry point (function)."""
    return KrogerCLI(args).main()
