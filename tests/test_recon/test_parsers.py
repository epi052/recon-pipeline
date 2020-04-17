# noqa: E405
import pytest

from pipeline.recon.parsers import *  # noqa: F403
from pipeline.recon.tool_definitions import tools


@pytest.mark.parametrize("test_input", list(tools.keys()) + ["all"])
def test_install_parser_good(test_input):
    parsed = install_parser.parse_args([test_input])
    assert parsed.tool == test_input


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (1, TypeError),
        (1.0, TypeError),
        ("invalid choice", SystemExit),
        (["all", "-i"], SystemExit),
        (["all", "--invalid"], SystemExit),
    ],
)
def test_install_parser_raises(test_input, expected):
    with pytest.raises(expected):
        install_parser.parse_args([test_input])


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ((None, None), ("127.0.0.1", "8082")),
        (("::1", "8000"), ("::1", "8000")),
        ((None, "8000"), ("127.0.0.1", "8000")),
        (("10.0.0.1", None), ("10.0.0.1", "8082")),
    ],
)
def test_status_parser_good(test_input, expected):

    args = list()
    for arg, ti in zip(("--host", "--port"), test_input):
        if not ti:
            continue
        args += [arg, ti]

    parsed = status_parser.parse_args(args)

    exp_host, exp_port = expected

    assert parsed.host == exp_host
    assert parsed.port == exp_port


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ((1, None), TypeError),
        ((1.0, None), TypeError),
        ((None, None, "invalid_positional"), SystemExit),
        ((None, None, "-i"), SystemExit),
        ((None, None, "--invalid"), SystemExit),
    ],
)
def test_status_parser_raises(test_input, expected):
    with pytest.raises(expected):
        args = list()
        for arg, ti in zip(("--host", "--port"), test_input):
            if not ti:
                continue
            args += [arg, ti]

        if len(test_input) > 2:
            args += test_input[2:]

        status_parser.parse_args(args)


@pytest.mark.parametrize("test_input", get_scans())
def test_scan_parser_positional_choices(test_input):
    parsed = scan_parser.parse_args([test_input, "--target-file", "required"])
    assert parsed.scantype == test_input


@pytest.mark.parametrize("test_input", [x[1] for x in socket.if_nameindex()])
def test_scan_parser_interface_choices(test_input):
    parsed = scan_parser.parse_args(["FullScan", "--interface", test_input, "--target-file", "required"])
    assert parsed.interface == test_input


@pytest.mark.parametrize("option_one, option_two", [("--ports", "--top-ports"), ("--target-file", "--target")])
def test_scan_parser_mutual_exclusion(option_one, option_two):
    with pytest.raises(SystemExit):
        port_arg = "1111"
        scan_parser.parse_args(["FullScan", option_one, port_arg, option_two, "target-arg"])


@pytest.mark.parametrize(
    "test_input, expected", [("verbose", False), ("local_scheduler", False), ("recursive", False), ("sausage", False)]
)
def test_scan_parser_defaults(test_input, expected):
    parsed = scan_parser.parse_known_args(["FullScan", "--target-file", "required"])[0]
    assert getattr(parsed, test_input) == expected


def test_technology_results_parser_defaults():
    parsed = technology_results_parser.parse_known_args(["FullScan", "--target-file", "required"])[0]
    assert not parsed.paged


def test_port_results_parser_defaults():
    parsed = port_results_parser.parse_known_args(["FullScan", "--target-file", "required"])[0]
    assert not parsed.paged


@pytest.mark.parametrize("test_input, expected", [("headers", False), ("paged", False), ("plain", False)])
def test_endpoint_results_parser_defaults(test_input, expected):
    parsed = endpoint_results_parser.parse_known_args(["FullScan", "--target-file", "required"])[0]
    assert getattr(parsed, test_input) == expected


@pytest.mark.parametrize("test_input, expected", [("commandline", False), ("paged", False)])
def test_nmap_results_parser_defaults(test_input, expected):
    parsed = nmap_results_parser.parse_known_args(["FullScan", "--target-file", "required"])[0]
    assert getattr(parsed, test_input) == expected


@pytest.mark.parametrize("test_input, expected", [("fullpath", False), ("paged", False)])
def test_searchsploit_results_parser_defaults(test_input, expected):
    parsed = searchsploit_results_parser.parse_known_args(["FullScan", "--target-file", "required"])[0]
    assert getattr(parsed, test_input) == expected
