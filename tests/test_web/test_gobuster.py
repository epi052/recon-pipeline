import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from pipeline.recon.web import GobusterScan, GatherWebTargets

gobuster_results = Path(__file__).parent.parent / "data" / "recon-results" / "gobuster-results"


class TestGobusterScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = GobusterScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )
        self.scan.exception = False

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def test_scan_requires(self):
        with patch("pipeline.recon.web.GatherWebTargets"):
            with patch("pipeline.recon.web.gobuster.meets_requirements"):
                retval = self.scan.requires()
                assert isinstance(retval, GatherWebTargets)

    def test_scan_run(self):
        with patch("concurrent.futures.ThreadPoolExecutor.map") as mocked_run:
            self.scan.parse_results = MagicMock()
            self.scan.db_mgr.get_all_web_targets = MagicMock()
            self.scan.db_mgr.get_all_web_targets.return_value = [
                "13.56.144.135",
                "2606:4700:10::6814:3c33",
                "google.com",
            ]
            self.scan.extensions = "php"
            self.scan.proxy = "127.0.0.1:8080"

            self.scan.run()
            assert mocked_run.called
            assert self.scan.parse_results.called

    def test_scan_recursive_run(self, tmp_path):
        os.chdir(tmp_path)
        with patch("concurrent.futures.ThreadPoolExecutor.map") as mocked_run:
            self.scan.parse_results = MagicMock()
            self.scan.db_mgr.get_all_web_targets = MagicMock()
            self.scan.db_mgr.get_all_web_targets.return_value = [
                "13.56.144.135",
                "2606:4700:10::6814:3c33",
                "google.com",
            ]
            self.scan.extensions = "php"
            self.scan.proxy = "127.0.0.1:8080"
            self.scan.recursive = True

            self.scan.run()
            assert mocked_run.called
            assert self.scan.parse_results.called

    def test_scan_run_with_wrong_threads(self, caplog):
        with patch("concurrent.futures.ThreadPoolExecutor.map"):
            self.scan.threads = "a"
            retval = self.scan.run()
            assert retval is None
            assert "The value supplied to --threads must be a non-negative integer" in caplog.text

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "gobuster-results"

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results(self):
        self.scan.results_subfolder = gobuster_results
        self.scan.parse_results()
        assert self.scan.output().exists()
