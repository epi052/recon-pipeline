from pathlib import Path

from pipeline.recon import tool_paths, defaults, web_ports, top_tcp_ports, top_udp_ports


def test_tool_paths_absolute():
    for path in tool_paths.values():
        assert Path(path).is_absolute()


def test_threads_numeric():
    assert defaults.get("threads").isnumeric()


def test_masscan_rate_numeric():
    assert defaults.get("masscan-rate").isnumeric()


def test_aquatone_scan_timeout_numeric():
    assert defaults.get("aquatone-scan-timeout").isnumeric()


def test_webports_exist_and_numeric():
    assert web_ports is not None
    for port in web_ports:
        assert port.isnumeric()


def test_top_tcp_ports_exist():
    assert top_tcp_ports is not None
    assert len(top_tcp_ports) >= 1


def test_top_udp_ports_exist():
    assert top_udp_ports is not None
    assert len(top_udp_ports) >= 1
