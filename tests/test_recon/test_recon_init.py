from pipeline.recon import get_scans


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
