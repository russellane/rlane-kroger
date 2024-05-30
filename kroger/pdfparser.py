"""Kroger payslip-pdf tools; signon, parse, print, and archive payslips."""

from datetime import datetime
from pathlib import Path
from pprint import pprint

from pdfminer.high_level import extract_text


class KrogerPdfParser:
    """Parse Kroger `payslip-pdf` file."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=consider-using-enumerate

    company = None
    employee = None
    payslip = None
    w4 = None
    summary = None
    earnings = None
    tax_deductions = None
    distributions = None
    lines: [str] = None
    num_lines: int = None
    payslip_pdf: Path = None

    def __init__(self, payslip_pdf: Path, archive_flag=False) -> None:
        """Parse Kroger `payslip-pdf` file."""

        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        text = extract_text(payslip_pdf)
        self.lines = text.splitlines()
        self.num_lines = len(self.lines)
        self.payslip_pdf = payslip_pdf

        # Begin parsing...

        self.company = {
            "name1": self.lines.pop(0),  # Smith's Food and Drug Centers, Inc. (FEIN: 87-
            "name2": self.lines.pop(0),  # 0258768)
            "addr1": self.lines.pop(0),  # 1014 Vine Street
            "addr2": self.lines.pop(0),  # Cincinnati OH 45202
            "division": None,
            "location": None,
        }
        self.assert_eq(self.lines.pop(0), "")

        self.assert_startswith(self.lines[0], "Person Number: ")
        self.employee = {
            "empno": self.lines.pop(0).split()[2],  # Person Number: 1234567
            "name": self.lines.pop(0),  # John Doe
            "addr1": self.lines.pop(0),  # 125 N. Main Street
            "addr2": self.lines.pop(0),  # Anytown US 12345
        }
        self.assert_eq(self.lines.pop(0), "")

        # This section may be here, or it may be below.

        if self.lines[0].startswith("Division: "):
            self.company["division"] = self.lines.pop(0).split()[1]  # 2nd word
            self.assert_startswith(self.lines[0], "HR Location: ")
            self.company["location"] = self.lines.pop(0).split()[2]  # 3rd word
            self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Period")
        self.assert_eq(self.lines.pop(0), "Payment Date")
        self.assert_eq(self.lines.pop(0), "Payroll")
        self.assert_eq(self.lines.pop(0), "")
        self.assert_eq(self.lines.pop(0), "Pay Frequency")
        self.assert_eq(self.lines.pop(0), "")

        self.payslip = {
            "period": self.lines.pop(0),  # 09/10/23 - 09/16/23
            "payment_date": self.lines.pop(0),  # 09/21/23
            "payroll": self.lines.pop(0),  # Retail Weekly Sun-Sat
            "pay_frequency": None,
            "hourly_rate": None,
            "has_sunday_pay": False,
            "has_reg_hours_retro": False,
            "has_night_premium": False,
            "total_hours_worked": None,
            "sick_hours_available": None,
        }
        self.payslip["payment_date"] = datetime.strptime(
            self.payslip["payment_date"], "%m/%d/%y"
        )
        period_begin, _, period_end = self.payslip["period"].split()
        self.payslip["period_begin"] = datetime.strptime(period_begin, "%m/%d/%y")
        self.payslip["period_end"] = datetime.strptime(period_end, "%m/%d/%y")

        # -------------------------------------------------------------------------------

        if archive_flag:
            # We've parsed enough to name the archived file properly.
            return

        # Continue parsing...
        # -------------------------------------------------------------------------------

        self.assert_eq(self.lines.pop(0), "")
        self.payslip["pay_frequency"] = self.lines.pop(0)  # Weekly
        self.assert_eq(self.lines.pop(0), "")

        # This section may be here, or it may have been above.

        if self.lines[0].startswith("Division: "):
            self.company["division"] = self.lines.pop(0).split()[1]  # 2nd word
            self.assert_startswith(self.lines[0], "HR Location: ")
            self.company["location"] = self.lines.pop(0).split()[2]  # 3rd word
            self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Hourly Rate")
        self.assert_eq(self.lines.pop(0), "")
        self.payslip["hourly_rate"] = self.lines.pop(0)  # 14.0000 USD
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Type")
        self.w4 = {
            "line1": self.lines.pop(0),  # "FEDERAL_2020"
            "line2": self.lines.pop(0),  # "AZ"
            "line3": self.lines.pop(0),  # ""
            "marital_status1": None,
            "marital_status2": None,
            "exemptions1": None,
            "exemptions2": None,
            "additional_amount1": None,
            "additional_amount2": None,
        }

        self.assert_eq(self.lines.pop(0), "Current")
        self.assert_eq(self.lines.pop(0), "Year To Date")
        self.assert_eq(self.lines.pop(0), "")
        self.assert_eq(self.lines.pop(0), "Name")

        # -------------------------------------------------------------------------------

        self.earnings = []
        while self.lines[0]:
            self.earnings.append(
                {
                    "name": self.lines.pop(0).strip(),
                    "current": None,
                    "ytd": None,
                }
            )
        self.assert_eq(self.lines.pop(0), "")

        # -------------------------------------------------------------------------------

        self.assert_eq(self.lines.pop(0), "Marital Status")
        self.w4["marital_status1"] = self.lines.pop(0)
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "W4 Information")
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Exemptions")
        self.w4["exemptions1"] = self.lines.pop(0)
        self.w4["exemptions2"] = self.lines.pop(0)
        self.assert_eq(self.lines.pop(0), "")

        # -------------------------------------------------------------------------------

        self.summary = {
            "gross": None,
            "gross_ytd": None,
            "non_payroll": None,
            "non_payroll_ytd": None,
            "pretax_deductions": None,
            "pretax_deductions_ytd": None,
            "tax_deductions": None,
            "tax_deductions_ytd": None,
            "after_tax_deduction": None,
            "after_tax_deduction_ytd": None,
            "net_pay": None,
            "net_pay_ytd": None,
        }

        if self.lines[0] == "Additional Amount":
            self.lines.pop(0)
            self.lines.pop(0)
            self.lines.pop(0)
            self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Gross Earnings")
        self.summary["gross"] = float(self.lines.pop(0))
        self.summary["gross_ytd"] = self.lines.pop(0)
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Non Payroll")
        self.summary["non_payroll"] = self.lines.pop(0)
        self.summary["non_payroll_ytd"] = self.lines.pop(0)
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), " Earnings")
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Summary")
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Pretax Deductions")
        self.summary["pretax_deductions"] = self.lines.pop(0)
        self.summary["pretax_deductions_ytd"] = self.lines.pop(0)
        self.assert_eq(self.lines.pop(0), "")

        # -------------------------------------------------------------------------------
        # This section may be here, or it may be below.

        if self.lines[0] == "Tax Deductions":
            self.lines.pop(0)
            self.summary["tax_deductions"] = self.lines.pop(0)
            self.summary["tax_deductions_ytd"] = self.lines.pop(0)
            self.assert_eq(self.lines.pop(0), "")

        # -------------------------------------------------------------------------------
        # This section may be here, or it may be below.

        if self.lines[0] == "After Tax Deduction":
            self.lines.pop(0)
            self.summary["after_tax_deduction"] = self.lines.pop(0)
            self.summary["after_tax_deduction_ytd"] = self.lines.pop(0)
            self.assert_eq(self.lines.pop(0), "Pretax Deductions")
            self.assert_eq(self.lines.pop(0), "Tax Deductions")
            self.assert_eq(self.lines.pop(0), "")

        # -------------------------------------------------------------------------------

        if (
            self.lines[0]
            == "Start Date End Date Hours  x  Rate  xi Factor  =  Current Hrs YTD Earnings YTD"
        ):
            self.lines.pop(0)
            for i in range(len(self.earnings)):
                if not self.lines[0]:
                    break
                self.earnings[i]["ytd"] = self.lines.pop(0)

            # skip unparsable section
            while self.lines[0] not in ["Tax Deductions", "After Tax Deduction", "Name"]:
                # print(f"SKIPPING {self.lines[0]!r}")
                self.lines.pop(0)

        # -------------------------------------------------------------------------------
        # This section may be here, or it may have been above.

        if self.lines[0] == "Tax Deductions":
            self.lines.pop(0)
            self.summary["tax_deductions"] = self.lines.pop(0)
            self.summary["tax_deductions_ytd"] = self.lines.pop(0)
            self.assert_eq(self.lines.pop(0), "")

        if self.lines[0] == "Name" and self.lines[1] == "Employee Contribution":
            self.lines.pop(0)
            self.lines.pop(0)
            self.assert_eq(self.lines.pop(0), "Total")
            self.assert_eq(self.lines.pop(0), "")

        # -------------------------------------------------------------------------------
        # This section may be here, or it may have been above.

        if self.lines[0] == "After Tax Deduction":
            self.lines.pop(0)
            self.summary["after_tax_deduction"] = self.lines.pop(0)
            self.summary["after_tax_deduction_ytd"] = self.lines.pop(0)
            self.assert_eq(self.lines.pop(0), "Pretax Deductions")
            if self.lines[0] == "":
                self.lines.pop(0)
            self.assert_eq(self.lines.pop(0), "Tax Deductions")
            self.assert_eq(self.lines.pop(0), "")

        # self.assert_eq(self.lines.pop(0), "Name")
        if self.lines[0] != "Name":
            self.lines.pop(0)
            self.lines.pop(0)

        self.tax_deductions = []
        while self.lines[0]:
            self.tax_deductions.append(
                {
                    "name": self.lines.pop(0).strip(),
                    "current": None,
                    "ytd": None,
                }
            )
        self.assert_eq(self.lines.pop(0), "")

        while True:
            if self.lines[0] == "Current":
                self.lines.pop(0)
                for i in range(len(self.tax_deductions)):
                    if not self.lines[0]:
                        break
                    self.tax_deductions[i]["current"] = self.lines.pop(0)
                self.assert_eq(self.lines.pop(0), "")

            if self.lines[0] == "After Tax(AT) Deductions":
                self.lines.pop(0)
                self.assert_eq(self.lines.pop(0), "")

            if self.lines[0] == "Additional Amount":
                self.lines.pop(0)
                self.w4["additional_amount1"] = self.lines.pop(0)
                self.w4["additional_amount2"] = self.lines.pop(0)
                self.assert_eq(self.lines.pop(0), "")

            if self.lines[0] == "Net Pay":
                self.lines.pop(0)
                self.summary["net_pay"] = float(self.lines.pop(0))
                self.summary["net_pay_ytd"] = self.lines.pop(0)
                self.assert_eq(self.lines.pop(0), "")

            if self.lines[0] == "YTD":
                self.lines.pop(0)
                for i in range(len(self.tax_deductions)):
                    if not self.lines[0]:
                        break
                    self.tax_deductions[i]["ytd"] = self.lines.pop(0)
                self.assert_eq(self.lines.pop(0), "")

            if self.lines[0].startswith("Total Hours Worked: "):
                break

            self.lines.pop(0)

        # Total Hours Worked: 2.50
        self.payslip["total_hours_worked"] = float(self.lines.pop(0).split()[3])  # 4th word
        self.assert_eq(self.lines.pop(0), "")

        # -------------------------------------------------------------------------------

        # Sick Hours Available: 0.00
        if self.lines[0].startswith("Sick Hours Available: "):
            self.payslip["sick_hours_available"] = float(
                self.lines.pop(0).split()[3]
            )  # 4th word
            self.assert_eq(self.lines.pop(0), "")

        # -------------------------------------------------------------------------------

        self.assert_eq(self.lines.pop(0), "Net Pay Distribution")
        self.assert_eq(self.lines.pop(0), "Payment Method")

        self.distributions = []
        while self.lines[0]:
            self.distributions.append(
                {
                    "payment_method": self.lines.pop(0),
                    "bank_name": None,
                    "branch": None,
                    "account_type": None,
                    "payment_reference": None,
                    "payment_amount": None,
                }
            )
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Bank Name")
        for i in range(len(self.distributions)):
            if not self.lines[0]:
                break
            self.distributions[i]["bank_name"] = self.lines.pop(0)
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Branch")
        for i in range(len(self.distributions)):
            if not self.lines[0]:
                break
            self.distributions[i]["branch"] = self.lines.pop(0)
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Account Type")
        for i in range(len(self.distributions)):
            if not self.lines[0]:
                break
            self.distributions[i]["account_type"] = self.lines.pop(0)
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Payment Reference")
        for i in range(len(self.distributions)):
            if not self.lines[0]:
                break
            self.distributions[i]["payment_reference"] = self.lines.pop(0)
        self.assert_eq(self.lines.pop(0), "")

        self.assert_eq(self.lines.pop(0), "Payment Amount")
        for i in range(len(self.distributions)):
            if not self.lines[0]:
                break
            self.distributions[i]["payment_amount"] = self.lines.pop(0)
        self.assert_eq(self.lines.pop(0), "")

    def assert_eq(self, text: str, expected: str) -> None:
        """Assert wrapper."""
        if text != expected:
            self._abort(f"text {text!r} != expected {expected!r}")

    def assert_startswith(self, text: str, expected: str) -> None:
        """Assert wrapper."""
        if not text.startswith(expected):
            self._abort(f"text {text!r} doesn't start with {expected!r}")

    def _abort(self, msg: str) -> None:
        self.dump()
        raise AssertionError(
            f"{msg} around line {self.num_lines - len(self.lines)} "
            f"of {str(self.payslip_pdf)!r}"
        )

    def dump(self) -> None:
        """Print internal data structures."""

        def _dump(title: str, obj) -> None:
            print("# " + title.upper() + " #")
            pprint(obj, indent=4, sort_dicts=True)

        _dump("Company", self.company)
        _dump("Employee", self.employee)
        _dump("Payslip", self.payslip)
        _dump("W4", self.w4)
        _dump("Summary", self.summary)
        _dump("Earnings", self.earnings)
        _dump("Tax Deductions", self.tax_deductions)
        _dump("Net Pay Distributions", self.distributions)
