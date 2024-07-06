"""Kroger MyTime command."""

import contextlib
import re
from time import localtime, mktime, sleep, strftime

from libcli import BaseCmd
from selenium import webdriver
from selenium.webdriver.common.by import By


class Shift:
    """A work shift."""

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
            raise ValueError(f"Can't parse {timestr!r}")

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

    def __eq__(self, other):
        return self.date == other.date and self.duration == other.duration

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

    def init_command(self) -> None:
        """Docstring."""

        parser = self.add_subcommand_parser(
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

        parser.add_argument(
            "--test1",
            action="store_true",
            help="Run test #1",
        )

        parser.add_argument(
            "--test2",
            action="store_true",
            help="Run test #2",
        )

        parser.add_argument(
            "--test3",
            action="store_true",
            help="Run test #3",
        )

    def run(self) -> None:
        """Perform the command."""

        if self.options.test1:
            schedule = self.example_schedule
        elif self.options.test2:
            schedule = self.example_schedule2
        elif self.options.test3:
            schedule = self.example_schedule3
        else:
            schedule = self.get_schedule()
            if self.cli.options.verbose:
                for line in schedule:
                    print("#", line)

        _last_shift = None
        for shift in self.parse_schedule(schedule):
            if _last_shift and shift == _last_shift:
                # Shifts are doubled for Today.
                print("# ignoring repeated shift.")
                continue
            _last_shift = shift

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

    example_schedule2 = [
        "Thu",
        "4",
        "Today",
        "Independence Day",
        "Independence Day for Calc",
        "3:00 PM-7:30 PM [4.50]",
        "3:00 PM-7:30 PM [4.50]",
        "0660/03/00054/E-Commerce/E-Commerce Clerk",
        "Fri",
        "5",
        "12:00 PM-5:00 PM [5.00]",
        "Sat",
        "6",
        "You have nothing planned.",
        "Sun",
        "7",
        "You have nothing planned.",
        "Mon",
        "8",
        "You have nothing planned.",
        "Tue",
        "9",
        "You have nothing planned.",
        "Wed",
        "10",
        "You have nothing planned.",
    ]

    example_schedule3 = [
        "Sat",
        "6",
        "Today",
        "You have nothing planned.",
        "Sun",
        "7",
        "You have nothing planned.",
        "Mon",
        "8",
        "12:00 PM-5:00 PM [5.00]",
        "Tue",
        "9",
        "You have nothing planned.",
        "Wed",
        "10",
        "You have nothing planned.",
        "Thu",
        "11",
        "2:30 PM-7:30 PM [5.00]",
        "Fri",
        "12",
        "12:00 PM-6:00 PM [6.00]",
    ]

    def parse_schedule(self, schedule: ["str"]) -> [Shift]:
        """Yields `Shift`s from the given `schedule`."""

        # The schedule always begins with today.
        _t = localtime()
        year, mon = _t.tm_year, _t.tm_mon

        _first = True
        while schedule:
            dayname = schedule.pop(0)
            daynum = int(schedule.pop(0))

            if not _first and daynum == 1:  # new month.
                if mon < 12:
                    mon += 1
                else:
                    mon = 1
                    year += 1
            _first = False
            date = mktime((year, mon, daynum, 0, 0, 0, 0, 0, 0))

            while schedule and schedule[0] not in [
                "Sun",
                "Mon",
                "Tue",
                "Wed",
                "Thu",
                "Fri",
                "Sat",
            ]:
                timestr = schedule.pop(0)
                if timestr == "Today":
                    continue
                print(f"# {dayname!r} {daynum!r} {timestr!r}")
                with contextlib.suppress(ValueError):
                    yield Shift(date, dayname, daynum, timestr)
