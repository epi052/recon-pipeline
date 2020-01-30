from recon import get_scans


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
        "recon.amass",
        "recon.nmap",
        "recon.masscan",
        "recon.wrappers",
        "recon.web.aquatone",
        "recon.web.corscanner",
        "recon.web.gobuster",
        "recon.web.subdomain_takeover",
        "recon.web.webanalyze",
    ]

    for module in scans.values():
        assert module[0] in modules
