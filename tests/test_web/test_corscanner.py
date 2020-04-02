import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.recon.web import CORScannerScan, GatherWebTargets


class TestCORScannerScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = CORScannerScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def test_scan_requires(self):
        with patch("pipeline.recon.web.GatherWebTargets"):
            retval = self.scan.requires()
            assert isinstance(retval, GatherWebTargets)

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "corscanner-results"

    def test_scan_creates_results_file(self):
        assert self.scan.output().path == str(self.tmp_path / "corscanner-results" / "corscanner.json")

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    @pytest.mark.parametrize("test_input", [["google.com"], None])
    def test_scan_run(self, test_input):
        with patch("subprocess.run") as mocked_run:
            self.scan.db_mgr.get_all_web_targets = MagicMock(return_value=test_input)

            self.scan.run()
            if test_input is None:
                assert not mocked_run.called
            else:
                assert mocked_run.called
