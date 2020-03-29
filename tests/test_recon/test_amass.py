import tempfile
from pathlib import Path

import luigi

from pipeline.recon import AmassScan, ParseAmassOutput

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


class TestAmassScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.asc = AmassScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def test_amassscan_creates_database(self):
        assert self.asc.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.asc.db_mgr.location

    def test_amassscan_output_location(self):
        assert self.asc.output().path == str(Path(self.tmp_path) / "amass-results" / "amass.json")


class TestParseAmass:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = ParseAmassOutput(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

        self.scan.input = lambda: luigi.LocalTarget(amass_json)
        self.scan.run()

    def test_scan_results(self):
        assert self.scan.output().exists()

    def test_scan_hostname_results(self):
        parsed_hosts = self.scan.db_mgr.get_all_hostnames()
        for hostname in subdomains:
            assert hostname in parsed_hosts

    def test_scan_ipv4_results(self):
        parsed_hosts = self.scan.db_mgr.get_all_ipv4_addresses()
        for ip in ips:
            assert ip in parsed_hosts

    def test_scan_ipv6_results(self):
        parsed_hosts = self.scan.db_mgr.get_all_ipv6_addresses()
        for ip in ip6s:
            assert ip in parsed_hosts

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder.exists()

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location
