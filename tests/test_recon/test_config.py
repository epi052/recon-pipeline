from pathlib import Path

import pytest

from pipeline.recon import tool_paths, defaults, web_ports, top_tcp_ports, top_udp_ports


def test_tool_paths_absolute():
    for path in tool_paths.values():
        assert Path(path).is_absolute()


@pytest.mark.parametrize("test_input", ["database-dir", "tools-dir", "gobuster-wordlist"])
def test_defaults_dirs_absolute(test_input):
    assert Path(defaults.get(test_input)).is_absolute()


@pytest.mark.parametrize("test_input", ["threads", "masscan-rate", "aquatone-scan-timeout"])
def test_defaults_are_numeric(test_input):
    assert defaults.get(test_input).isnumeric()


def test_webports_exist():
    assert web_ports is not None


def test_webports_numeric():
    for port in web_ports:
        assert port.isnumeric()


def test_top_tcp_ports_exist():
    assert top_tcp_ports is not None
    assert len(top_tcp_ports) >= 1


def test_top_udp_ports_exist():
    assert top_udp_ports is not None
    assert len(top_udp_ports) >= 1
