import pytest

from pipeline.recon.helpers import get_ip_address_version, get_scans, is_ip_address
from pipeline.recon import AmassScan, MasscanScan, FullScan, HTBScan, SearchsploitScan, ThreadedNmapScan
from pipeline.recon.web import GobusterScan, SubjackScan, TKOSubsScan, AquatoneScan, WaybackurlsScan, WebanalyzeScan


def test_get_scans():

    scan_names = [
        AmassScan,
        GobusterScan,
        MasscanScan,
        SubjackScan,
        TKOSubsScan,
        AquatoneScan,
        FullScan,
        HTBScan,
        SearchsploitScan,
        ThreadedNmapScan,
        WebanalyzeScan,
        WaybackurlsScan,
    ]

    scans = get_scans()

    for scan in scan_names:
        if hasattr(scan, "meets_requirements") and scan.meets_requirements():
            assert scan.__name__ in scans.keys()
        else:
            assert scan not in scans.keys()


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
