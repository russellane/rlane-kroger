"""Kroger payslip-pdf tools; signon, parse, print, and archive payslips."""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from libcli import BaseCmd

from .pdfparser import KrogerPdfParser


class KrogerArchiveCmd(BaseCmd):
    """Copy and rename `payslip-pdf` to reflect its `paydate`."""

    def init_command(self) -> None:
        """Docstring."""

        parser = self.add_subcommand_parser(
            "archive",
            help=KrogerArchiveCmd.__doc__,
            description=self.cli.dedent(
                f"""
            The `%(prog)s` command copies `PAYSLIP-PDF` files
            to `archive-path`, naming the copy, and touching its
            modification-time, to reflect the payslip's `paydate`.

            Configuration file `~/.kroger.toml` defines:
                archive-path = `{self.cli.config["archive-path"]}`
                """
            ),
        )

        parser.add_argument(
            "PAYSLIP_PDF_FILES",
            nargs="+",
            metavar="PAYSLIP-PDF",
            type=Path,
            help="List of one or more Kroger payslip `.pdf` files",
        )

    def run(self) -> None:
        """Perform the command."""

        if not self.cli.config["archive-path"]:
            self.cli.parser.exit(
                2, f"error: Missing `archive-path` in `{self.options['config-file']}`\n"
            )

        for payslip_pdf in self.options.PAYSLIP_PDF_FILES:
            pdf = KrogerPdfParser(payslip_pdf, archive_flag=True)
            self._archive(payslip_pdf, pdf.payslip["payment_date"])

    def _archive(self, payslip_pdf: Path, payment_date: datetime) -> None:
        """Copy `payslip_pdf` to `archive-path`.

        with unique filename based on `payment_date`,
        and touch atime and mtime to `payment_date`.
        """

        self.cli.config["archive-path"].mkdir(parents=True, exist_ok=True)  # mkdir -p

        filename = datetime.strftime(payment_date, "Kroger-%Y-%m-%d.pdf")
        target = self.cli.config["archive-path"] / filename
        shutil.copy(payslip_pdf, target)

        payment_timestamp = int(payment_date.timestamp())
        os.utime(target, (payment_timestamp, payment_timestamp))
        subprocess.run(["ls", "-l", target], check=True)
