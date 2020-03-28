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
            target_file=tf,
            exempt_list=el,
            results_dir=str(self.tmp_path),
            db_location=str(self.tmp_path / "testing.sqlite"),
        )

    def test_parse_amass_creates_database(self):
        assert self.asc.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.asc.db_mgr.location

    def test_amassscan_output_location(self):
        assert self.asc.output().path == str(Path(self.tmp_path) / "amass-results" / "amass.json")


class TestParseAmass:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.pao = ParseAmassOutput(
            target_file=tf,
            exempt_list=el,
            results_dir=str(self.tmp_path),
            db_location=str(self.tmp_path / "testing.sqlite"),
        )

        self.pao.input = lambda: luigi.LocalTarget(amass_json)
        self.pao.run()

    def test_parse_amass_ip_results(self):
        assert self.pao.output().exists()

    def test_parse_amass_hostname_results(self):
        parsed_hosts = self.pao.db_mgr.get_all_hostnames()
        for hostname in subdomains:
            assert hostname in parsed_hosts

    def test_parse_amass_ipv4_results(self):
        parsed_hosts = self.pao.db_mgr.get_all_ipv4_addresses()
        for ip in ips:
            assert ip in parsed_hosts

    def test_parse_amass_ipv6_results(self):
        parsed_hosts = self.pao.db_mgr.get_all_ipv6_addresses()
        for ip in ip6s:
            assert ip in parsed_hosts

    def test_parse_amass_creates_results_dir(self):
        assert self.pao.results_subfolder.exists()

    def test_parse_amass_creates_database(self):
        assert self.pao.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.pao.db_mgr.location
