"""Kroger payslip-pdf tools; signon, parse, print, and archive payslips."""

import pdb
from time import sleep

from libcli import BaseCmd
from selenium import webdriver
from selenium.webdriver.common.by import By


class KrogerMyInfoCmd(BaseCmd):
    """Open browser, signon to Kroger MyInfo, and navigate to `Payslips` page."""

    def init_command(self) -> None:
        """Docstring."""

        self.add_subcommand_parser(
            "myinfo",
            help=KrogerMyInfoCmd.__doc__,
            description=self.cli.dedent(
                f"""
            The `%(prog)s` command opens a browser, and logs in to
            Kroger's MyInfo application, and navigates to the `Payslips`
            page.

            User should now download any new payslips into their
            `~/Downloads` folder.  The filenames of the payslips shown
            on the website are unique, but they are not the default names
            assigned when downloading the files; instead, they are named:

                USOnlinePayslip.pdf
                USOnlinePayslip (1).pdf
                USOnlinePayslip (2).pdf
                etc.

            See the `archive` command to extract the `paydate` from a
            downloaded file, and embed the paydate into the name of an
            archived copy of the file.

            Configuration file `{self.cli.config["config-file"]}` defines these variables:
                myinfo-url = `{self.cli.config["myinfo-url"]}`
                sso-user = "*******"
                sso-password = "********"
                """,
            ),
        )

    def run(self) -> None:
        """Perform the command."""

        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(options=options)
        driver.get(self.cli.config["myinfo-url"])
        driver.implicitly_wait(0.8)

        element = driver.find_element(By.ID, "ssoBtn")
        element.click()

        if self.cli.config["sso-user"] and self.cli.config["sso-password"]:

            user = driver.find_element(by=By.NAME, value="USER")
            user.send_keys(self.cli.config["sso-user"])

            password = driver.find_element(by=By.NAME, value="PASSWORD")
            password.send_keys(self.cli.config["sso-password"])

            submit = driver.find_element(by=By.XPATH, value="//input[@type='submit']")
            submit.click()

            sleep(2)
            pay = driver.find_element(by=By.ID, value="itemNode_my_information_pay_0")
            pay.click()

            sleep(2)
            payslips = driver.find_element(By.XPATH, value="//a[contains(., 'My Payslips')]")
            payslips.click()

        pdb.set_trace()  # pylint: disable=forgotten-debug-statement
        driver.quit()
