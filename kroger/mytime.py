"""Kroger payslip-pdf tools; signon, parse, print, and archive payslips."""

import re
from pprint import pprint
from time import localtime, mktime, sleep, strftime

from libcli import BaseCmd
from selenium import webdriver
from selenium.webdriver.common.by import By


class Shift:
    """A work shift."""

    # pylint: disable=too-few-public-methods

    # Parse strings like: "1:15 PM-8:00 PM [6.75]"

    pattern = re.compile(
        "-".join(
            [
                r"(?P<fr_hh>\d{1,2}):(?P<fr_mm>\d{1,2}) (?P<fr_ampm>[AP]M)",
                r"(?P<to_hh>\d{1,2}):(?P<to_mm>\d{1,2}) (?P<to_ampm>[AP]M)",
            ]
        )
    )

    def __init__(self, date: int, dayname: str, daynum: int, timestr: str):
        """Docstring."""

        self.dayname: str = dayname  # scraped from website
        self.daynum: int = daynum  # ..scraped from website
        self.timestr: str = timestr  # scraped from website
        self.date: int = None  # seconds since the epoch.
        self.duration: int = None  # number of minutes.

        m = re.match(self.pattern, timestr)
        if not m:
            raise RuntimeError(f"timestr={timestr!r}")

        fr_hh = int(m["fr_hh"])
        fr_mm = int(m["fr_mm"])
        if m["fr_ampm"] == "PM" and fr_hh < 12:
            fr_hh += 12

        to_hh = int(m["to_hh"])
        to_mm = int(m["to_mm"])
        if m["to_ampm"] == "PM" and to_hh < 12:
            to_hh += 12

        fr_minutes = (fr_hh * 60) + fr_mm
        self.date = date + (fr_minutes * 60)

        to_minutes = (to_hh * 60) + to_mm
        self.duration = to_minutes - fr_minutes

    def __repr__(self) -> str:

        return (
            f"{__class__.__name__}("
            + ", ".join(
                [
                    f"dayname={self.dayname!r}",
                    f"daynum={self.daynum!r}",
                    f"date={strftime('%Y-%m-%d %H:%M', localtime(self.date))}",
                    f"duration={self.duration//60:02}:{self.duration%60:02}",
                    f"timestr={self.timestr!r}",
                ]
            )
            + ")"
        )


class KrogerMyTimeCmd(BaseCmd):
    """Open browser, login to Kroger MyTime, extract `Schedule`, and print `gcalcli` commands."""

    testing: bool = False

    def init_command(self) -> None:
        """Docstring."""

        self.add_subcommand_parser(
            "mytime",
            help=KrogerMyTimeCmd.__doc__,
            description=self.cli.dedent(
                f"""
            The `%(prog)s` command opens a browser, logs in to Kroger's
            MyTime application, extracts the `schedule`, and prints `gcalcli`
            commands to create events in the configured google calendar.

            Configuration file `{self.cli.config["config-file"]}` defines these variables:
                mytime-url = `{self.cli.config["mytime-url"]}`
                google-calendar = "*******"
                sso-user = "*******"
                sso-password = "********"
                """,
            ),
        )

    def run(self) -> None:
        """Perform the command."""

        if self.testing:
            schedule = self.example_schedule
        else:
            schedule = self.get_schedule()
            if self.cli.options.verbose:
                pprint(schedule)

        for shift in self.parse_schedule(schedule):
            print(
                "gcalcli",
                "add",
                "--calendar",
                self.cli.config["google-calendar"],
                "--title",
                repr("Fry's"),
                "--when",
                strftime('"%Y-%m-%d %H:%M"', localtime(shift.date)),
                "--duration",
                shift.duration,
                "--reminder",
                "30m",
                "--noprompt",
            )

    def get_schedule(self) -> ["str"]:
        """Opens a browser, logs in to Kroger's MyTime, and returns the schedule."""

        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(options=options)
        driver.get(self.cli.config["mytime-url"])
        sleep(5)

        user = driver.find_element(by=By.NAME, value="submittedIdentifier")
        user.send_keys(self.cli.config["sso-user"])

        # submit = driver.find_element(by=By.XPATH, value="//input[@type='submit']")
        submit = driver.find_element(by=By.XPATH, value="//button[@id='btnSignIn']/div")
        submit.click()
        sleep(5)

        password = driver.find_element(by=By.NAME, value="password")
        password.send_keys(self.cli.config["sso-password"])

        # submit = driver.find_element(by=By.XPATH, value="//input[@type='submit']")
        submit = driver.find_element(by=By.XPATH, value="//button[@id='btnSignIn']/div")
        submit.click()
        sleep(10)

        schedule = driver.find_element(by=By.XPATH, value="//ng-myschedule-list")
        lines = schedule.text.splitlines()

        driver.quit()

        return lines

    # The first day has 4 or 6 lines; each remaining day has 3 lines.
    example_schedule = [
        "Sat",
        "25",
        "Today",
        "12:00 PM-4:30 PM [4.50]",
        "12:00 PM-4:30 PM [4.50]",
        "0660/03/00054/E-Commerce/E-Commerce Clerk",
        "Sun",
        "26",
        "1:00 PM-7:30 PM [6.50]",
        "Mon",
        "27",
        "9:00 AM-12:00 PM [3.00]",
        "Mon",
        "27",
        "3:45 PM-7:45 PM [4.00]",
        "Tue",
        "28",
        "9:15 AM-3:00 PM [5.75]",
        "Wed",
        "29",
        "You have nothing planned.",
        "Thu",
        "30",
        "You have nothing planned.",
        "Fri",
        "31",
        "12:00 PM-4:30 PM [4.50]",
    ]

    def parse_schedule(self, schedule: ["str"]) -> [Shift]:
        """Returns a list of `Shift`s from the given `schedule`."""

        shifts = []
        _t = localtime()
        year, mon = _t.tm_year, _t.tm_mon

        first = True
        while schedule:
            dayname = schedule.pop(0)
            daynum = int(schedule.pop(0))
            timestr = schedule.pop(0)
            if timestr == "Today":
                timestr = schedule.pop(0)
                if schedule[0] == timestr:
                    schedule.pop(0)  # timestr repeats, then
                    schedule.pop(0)  # "0660/03/00054/E-Commerce/E-Commerce Clerk"

            print(f"# {dayname!r} {daynum!r} {timestr!r}")

            if not first and daynum == 1:  # new month.
                if mon < 12:
                    mon += 1
                else:
                    mon = 1
                    year += 1
            date = mktime((year, mon, daynum, 0, 0, 0, 0, 0, 0))
            first = False

            while timestr != "You have nothing planned.":
                try:
                    shifts.append(Shift(date, dayname, daynum, timestr))
                    break
                except RuntimeError:
                    # Perhaps a holiday message, like: "Independence Day".
                    timestr = schedule.pop(0)
                    print(f"# {dayname!r} {daynum!r} {timestr!r}")

        return shifts
