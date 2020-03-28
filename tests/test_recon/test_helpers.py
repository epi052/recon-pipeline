import pytest

from pipeline.recon.helpers import get_ip_address_version, get_scans, is_ip_address


def test_get_scans():
    scans = get_scans()

    scan_names = [
        "AmassScan",
        "CORScannerScan",
        "GobusterScan",
        "MasscanScan",
        "SubjackScan",
        "TKOSubsScan",
        "AquatoneScan",
        "FullScan",
        "HTBScan",
        "SearchsploitScan",
        "ThreadedNmapScan",
        "WebanalyzeScan",
    ]

    assert len(scan_names) == len(scans.keys())

    for name in scan_names:
        assert name in scans.keys()

    modules = [
        "pipeline.recon.amass",
        "pipeline.recon.masscan",
        "pipeline.recon.nmap",
        "pipeline.recon.nmap",
        "pipeline.recon.web",
        "pipeline.recon.web",
        "pipeline.recon.web",
        "pipeline.recon.web",
        "pipeline.recon.web",
        "pipeline.recon.web",
        "pipeline.recon.wrappers",
        "pipeline.recon.wrappers",
    ]

    for module in scans.values():
        assert module[0] in modules


@pytest.mark.parametrize(
    "test_input, expected",
    [("127.0.0.1", True), ("::1", True), ("abcd", False), ("", False), (-1, False), (1.0, False)],
)
def test_is_ip_address(test_input, expected):
    assert is_ip_address(test_input) == expected


@pytest.mark.parametrize(
    "test_input, expected", [("127.0.0.1", "4"), ("::1", "6"), ("abcd", None), ("", None), (-1, None), (1.0, None)]
)
def test_get_ip_address_version(test_input, expected):
    assert get_ip_address_version(test_input) == expected
