from pathlib import Path

import luigi

from pipeline.recon import ParseAmassOutput, AmassScan

tfp = "../data/bitdiscovery"
tf = Path(tfp).stem
el = "../data/blacklist"
rd = "../data/recon-results"
ips = [
    "13.225.54.58",
    "13.225.54.100",
    "13.225.54.22",
    "13.225.54.41",
    "13.57.162.100",
    "52.9.23.177",
    "52.53.92.161",
    "54.183.32.157",
    "54.183.32.157",
    "52.53.92.161",
    "52.53.92.161",
    "54.183.32.157",
    "104.20.60.51",
    "104.20.61.51",
    "104.20.61.51",
    "104.20.60.51",
]
ip6s = ["2606:4700:10::6814:3c33", "2606:4700:10::6814:3d33", "2606:4700:10::6814:3d33", "2606:4700:10::6814:3c33"]
subdomains = [
    "blog.bitdiscovery.com",
    "bitdiscovery.com",
    "staging.bitdiscovery.com",
    "ibm.bitdiscovery.com",
    "tenable.bitdiscovery.com",
]

amass_json = Path(__file__).parent.parent / "data" / "recon-results" / "amass-results" / "amass.json"


def test_parse_amass_ip_results(tmp_path):
    pao = ParseAmassOutput(
        target_file=tf, exempt_list=el, results_dir=str(tmp_path), db_location=str(Path(tmp_path) / "testing.sqlite")
    )

    pao.input = lambda: luigi.LocalTarget(amass_json)
    pao.run()

    assert pao.output().exists()
