import pytest

from pipeline.recon.helpers import get_ip_address_version, get_scans, is_ip_address, meets_requirements
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
    exception = False

    scans = get_scans()

    for scan in scan_names:
        if hasattr(scan, "requirements") and meets_requirements(scan.requirements, False):
            assert scan.__name__ in scans.keys()
        else:
            assert scan not in scans.keys()


@pytest.mark.parametrize(
    "requirements",
    [
        ["amass"],
        ["masscan"],
        [
            "amass",
            "aquatone",
            "masscan",
            "tko-subs",
            "recursive-gobuster",
            "searchsploit",
            "subjack",
            "gobuster",
            "webanalyze",
            "waybackurls",
        ],
    ],
)
def test_meets_requirements(requirements):
    pass


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
