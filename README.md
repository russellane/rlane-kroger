# kroger
```
usage: kroger [-h] [-H] [-v] [-V] [--config FILE] [--print-config]
              [--print-url] [--completion [SHELL]]
              COMMAND ...

Kroger `payslip-pdf` tools; signon, parse, print, and archive payslips.

Specify one of:
  COMMAND
    myinfo              Open browser, signon to Kroger MyInfo, and navigate to
                        `Payslips` page.
    mytime              Open browser, signon to Kroger MyTime, and extract
                        `Schedule`.
    archive             Copy and rename `payslip-pdf` to reflect its
                        `paydate`.
    print               Parse and print select fields from a `payslip-pdf`
                        file.

General options:
  -h, --help            Show this help message and exit.
  -H, --long-help       Show help for all commands and exit.
  -v, --verbose         `-v` for detailed output and `-vv` for more detailed.
  -V, --version         Print version number and exit.
  --config FILE         Use config `FILE` (default: `~/.kroger.toml`).
  --print-config        Print effective config and exit.
  --print-url           Print project url and exit.
  --completion [SHELL]  Print completion scripts for `SHELL` and exit
                        (default: `bash`).
```

## kroger myinfo
```
usage: kroger myinfo [-h]

The `kroger myinfo` command opens a browser, and logs in to
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

Configuration file `/Users/russe/.kroger.toml` defines these variables:
    myinfo-url = `https://myinfo.kroger.com`
    sso-user = "*******"
    sso-password = "********"

options:
  -h, --help  Show this help message and exit.
```

## kroger mytime
```
usage: kroger mytime [-h]

The `kroger mytime` command opens a browser, and logs in to
Kroger's MyTime application.

Configuration file `/Users/russe/.kroger.toml` defines these variables:
    mytime-url = `https://kroger-sso.prd.mykronos.com/`
    sso-user = "*******"
    sso-password = "********"

options:
  -h, --help  Show this help message and exit.
```

## kroger archive
```
usage: kroger archive [-h] PAYSLIP-PDF [PAYSLIP-PDF ...]

The `kroger archive` command copies `PAYSLIP-PDF` files
to `archive-path`, naming the copy, and touching its
modification-time, to reflect the payslip's `paydate`.

Configuration file `~/.kroger.toml` defines:
    archive-path = /Users/russe/Documents/Finances/Kroger-Pay-Stubs

positional arguments:
  PAYSLIP-PDF  List of one or more Kroger payslip `.pdf` files.

options:
  -h, --help   Show this help message and exit.
```

## kroger print
```
usage: kroger print [-h] [--dump] [--csv] PAYSLIP-PDF [PAYSLIP-PDF ...]

The `kroger print` command parses and prints fields from one
or more `PAYSLIP-PDF` files.

positional arguments:
  PAYSLIP-PDF  List of one or more Kroger payslip `.pdf` files.

options:
  -h, --help   Show this help message and exit.
  --dump       Print internal data structures.
  --csv        Print in `CSV` file format.
```

