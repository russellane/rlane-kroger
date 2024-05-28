"""Kroger payslip-pdf tools; signon, parse, print, and archive payslips."""

from datetime import datetime
from pathlib import Path

from libcli import BaseCmd

from .pdfparser import KrogerPdfParser


class KrogerPrintCmd(BaseCmd):
    """Parse and print select fields from a `payslip-pdf` file."""

    last_month = None
    month_hours = 0
    month_gross = 0
    month_net = 0

    def init_command(self) -> None:
        """Docstring."""

        parser = self.add_subcommand_parser(
            "print",
            help=KrogerPrintCmd.__doc__,
            description=self.cli.dedent(
                """
            The `%(prog)s` command parses and prints fields from one
            or more `PAYSLIP-PDF` files.
                """,
            ),
        )

        arg = parser.add_argument(
            "--dump",
            action="store_true",
            help="Print internal data structures",
        )
        self.cli.add_default_to_help(arg)

        arg = parser.add_argument(
            "--csv",
            action="store_true",
            help="Print in `CSV` file format",
        )
        self.cli.add_default_to_help(arg)

        arg = parser.add_argument(
            "PAYSLIP_PDF_FILES",
            nargs="+",
            metavar="PAYSLIP-PDF",
            type=Path,
            help="List of one or more Kroger payslip `.pdf` files",
        )

    def run(self) -> None:
        """Perform the command."""

        if self.options.csv:
            print("Paydate,Hours,Gross,Net")
        else:
            self._print_header()

        for payslip_pdf in self.options.PAYSLIP_PDF_FILES:
            self._print(payslip_pdf)

        if not self.options.csv:
            self._print_month_subtotal()

    def _print(self, payslip_pdf: Path) -> None:

        pdf = KrogerPdfParser(payslip_pdf)

        if self.options.dump:
            pdf.dump()

        if self.options.csv:
            self._print_csv(pdf)
        else:
            self._print_txt(pdf)

    def _print_csv(self, pdf: KrogerPdfParser) -> None:

        print(
            ",".join(
                [
                    datetime.strftime(pdf.payslip["period_begin"], "%Y-%m-%d"),
                    datetime.strftime(pdf.payslip["period_end"], "%Y-%m-%d"),
                    datetime.strftime(pdf.payslip["payment_date"], "%Y-%m-%d"),
                    str(pdf.payslip["total_hours_worked"]),
                    str(pdf.summary["gross"]),
                    str(pdf.summary["net_pay"]),
                ]
            )
        )

    def _print_txt(self, pdf: KrogerPdfParser) -> None:

        month = pdf.payslip["period_begin"].month
        if self.last_month is not None and self.last_month != month:
            self._print_month_subtotal()
            print()
            self._print_header()
            self.month_hours = 0
            self.month_gross = 0
            self.month_net = 0

        self.last_month = month
        self.month_hours += pdf.payslip["total_hours_worked"]
        self.month_gross += pdf.summary["gross"]
        self.month_net += pdf.summary["net_pay"]

        print(
            " ".join(
                [
                    datetime.strftime(pdf.payslip["period_begin"], "%Y-%m-%d"),
                    datetime.strftime(pdf.payslip["period_end"], "%Y-%m-%d"),
                    datetime.strftime(pdf.payslip["payment_date"], "%Y-%m-%d"),
                    f"{pdf.payslip['total_hours_worked']:6.2f}",
                    f"{pdf.summary['gross']:9.2f}",
                    f"{pdf.summary['net_pay']:9.2f}",
                ]
            )
        )

    @staticmethod
    def _print_header() -> None:
        print("Begin      End        Paydate     Hours     Gross       Net")
        #     "yyyy-mm-dd yyyy-mm-dd yyyy-mm-dd 123.56 123456.89 123456.89"

    def _print_month_subtotal(self) -> None:
        print(" " * 32, "------ --------- ---------")
        print(" " * 32, f"{self.month_hours:6.2f} {self.month_gross:9.2f} {self.month_net:9.2f}")
