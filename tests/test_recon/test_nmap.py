import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import luigi
import pytest
from luigi.contrib.sqla import SQLAlchemyTarget

from pipeline.recon import ThreadedNmapScan, SearchsploitScan, ParseMasscanOutput
from pipeline.tools import tools

nmap_results = Path(__file__).parent.parent / "data" / "recon-results" / "nmap-results"


class TestThreadedNmapScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = ThreadedNmapScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )
        self.scan.exception = False

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def test_scan_requires(self):
        with patch("pipeline.recon.ParseMasscanOutput"):
            retval = self.scan.requires()
            assert isinstance(retval, ParseMasscanOutput)

    def test_scan_run(self):
        with patch("concurrent.futures.ThreadPoolExecutor.map") as mocked_run:
            self.scan.parse_nmap_output = MagicMock()
            self.scan.db_mgr.get_all_targets = MagicMock()
            self.scan.db_mgr.get_all_targets.return_value = ["13.56.144.135", "2606:4700:10::6814:3c33"]
            self.scan.db_mgr.get_ports_by_ip_or_host_and_protocol = MagicMock()
            self.scan.db_mgr.get_ports_by_ip_or_host_and_protocol.return_value = ["135", "80"]

            self.scan.run()
            assert mocked_run.called
            assert self.scan.parse_nmap_output.called

    def test_scan_run_with_wrong_threads(self, caplog):
        with patch("concurrent.futures.ThreadPoolExecutor.map"):
            self.scan.threads = "a"
            retval = self.scan.run()
            assert retval is None
            assert "The value supplied to --threads must be a non-negative integer" in caplog.text

    def test_parse_nmap_output(self):
        (self.tmp_path / "nmap-results").mkdir(parents=True, exist_ok=True)
        shutil.copy(nmap_results / "nmap.13.56.144.135-tcp.xml", self.scan.results_subfolder)
        shutil.copy(nmap_results / "nmap.2606:4700:10::6814:3c33-tcp.xml", self.scan.results_subfolder)
        assert len([x for x in self.scan.results_subfolder.iterdir()]) == 2
        assert "13.56.144.135" not in self.scan.db_mgr.get_all_targets()
        assert "2606:4700:10::6814:3c33" not in self.scan.db_mgr.get_all_targets()
        self.scan.parse_nmap_output()
        assert "13.56.144.135" in self.scan.db_mgr.get_all_targets()
        assert "2606:4700:10::6814:3c33" in self.scan.db_mgr.get_all_targets()

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "nmap-results"

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_output_location(self):
        assert self.scan.output().get("localtarget").path == str(self.tmp_path / "nmap-results")


class TestSearchsploitScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = SearchsploitScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )
        self.scan.exception = False

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def test_scan_requires(self):
        with patch("pipeline.recon.ThreadedNmapScan"):
            retval = self.scan.requires()
            assert isinstance(retval, ThreadedNmapScan)

    def test_scan_output(self):
        retval = self.scan.output()
        assert isinstance(retval, SQLAlchemyTarget)

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results(self):
        lcl_nmap = self.tmp_path / "nmap-results"
        lcl_nmap.mkdir(parents=True, exist_ok=True)
        shutil.copy(nmap_results / "nmap.13.56.144.135-tcp.xml", lcl_nmap)
        shutil.copy(nmap_results / "nmap.2606:4700:10::6814:3c33-tcp.xml", lcl_nmap)

        self.scan.input = lambda: {"localtarget": luigi.LocalTarget(lcl_nmap)}

        assert len(self.scan.db_mgr.get_all_searchsploit_results()) == 0

        if not Path(tools.get("searchsploit").get("path")).exists():
            pytest.skip("exploit-db's searchsploit tool not installed")

        self.scan.run()

        assert len(self.scan.db_mgr.get_all_searchsploit_results()) > 0
