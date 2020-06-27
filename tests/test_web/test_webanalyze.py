import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from pipeline.tools import tools
from pipeline.recon.web import WebanalyzeScan, GatherWebTargets

webanalyze_results = Path(__file__).parent.parent / "data" / "recon-results" / "webanalyze-results"


class TestWebanalyzeScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = WebanalyzeScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def test_scan_requires(self):
        with patch("pipeline.recon.web.GatherWebTargets"):
            retval = self.scan.requires()
            assert isinstance(retval, GatherWebTargets)

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "webanalyze-results"

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results(self):
        self.scan.results_subfolder = webanalyze_results
        self.scan.parse_results()
        assert self.scan.output().exists()

    def test_scan_run(self):
        with patch("concurrent.futures.ThreadPoolExecutor.map") as mocked_map, patch(
            "subprocess.run"
        ) as mocked_run, patch("pathlib.Path.cwd", return_value="/"):
            self.scan.parse_results = MagicMock()
            self.scan.db_mgr.get_all_web_targets = MagicMock()
            self.scan.db_mgr.get_all_web_targets.return_value = [
                "13.56.144.135",
                "2606:4700:10::6814:3c33",
                "google.com",
            ]

            self.scan.run()
            assert mocked_map.called
            assert mocked_run.called
            assert self.scan.parse_results.called

    def test_scan_run_with_wrong_threads(self, caplog):
        self.scan.threads = "a"
        retval = self.scan.run()
        assert retval is None
        assert "The value supplied to --threads must be a non-negative integer" in caplog.text

    def test_wrapped_subprocess(self):
        with patch("subprocess.run") as mocked_run:
            self.scan.results_subfolder.mkdir()
            os.chdir(self.scan.results_subfolder)
            assert len([x for x in self.scan.results_subfolder.iterdir()]) == 0
            cmd = [tools.get("webanalyze").get("path"), "-host", "https://google.com", "-output", "csv"]
            self.scan._wrapped_subprocess(cmd)
            assert len([x for x in self.scan.results_subfolder.iterdir()]) == 1
            assert next(self.scan.results_subfolder.iterdir()).name == "webanalyze-https_google.com.csv"
            assert mocked_run.called
