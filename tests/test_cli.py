import pytest

from kroger.cli import main


def test_version():
    with pytest.raises(SystemExit) as err:
        main(["--version"])
    assert err.value.code == 0


def test_help():
    with pytest.raises(SystemExit) as err:
        main(["--help"])
    assert err.value.code == 0


def test_md_help():
    with pytest.raises(SystemExit) as err:
        main(["--md-help"])
    assert err.value.code == 0


def test_long_help():
    with pytest.raises(SystemExit) as err:
        main(["--long-help"])
    assert err.value.code == 0


def test_bogus_option():
    with pytest.raises(SystemExit) as err:
        main(["--bogus-option"])
    assert err.value.code == 2


def test_bogus_argument():
    with pytest.raises(SystemExit) as err:
        main(["bogus-argument"])
    assert err.value.code == 2


def test_print_config():
    with pytest.raises(SystemExit) as err:
        main(["--print-config"])
    assert err.value.code == 0


def test_print_url():
    with pytest.raises(SystemExit) as err:
        main(["--print-url"])
    assert err.value.code == 0


def test_debug():
    with pytest.raises(SystemExit) as err:
        main(["-X"])
    assert err.value.code == 0


def test_archive_help():
    with pytest.raises(SystemExit) as err:
        main(["archive", "--help"])
    assert err.value.code == 0


def test_myinfo_help():
    with pytest.raises(SystemExit) as err:
        main(["myinfo", "--help"])
    assert err.value.code == 0


def test_mytime_help():
    with pytest.raises(SystemExit) as err:
        main(["mytime", "--help"])
    assert err.value.code == 0


def test_print_help():
    with pytest.raises(SystemExit) as err:
        main(["print", "--help"])
    assert err.value.code == 0
