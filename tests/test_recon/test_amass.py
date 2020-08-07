import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import luigi

from pipeline.recon import AmassScan, ParseAmassOutput, TargetList


amass_json = Path(__file__).parent.parent / "data" / "recon-results" / "amass-results" / "amass.json"


class TestAmassScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = AmassScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def test_scan_requires(self):
        with patch("pipeline.recon.TargetList"):
            with patch("pipeline.recon.amass.meets_requirements"):
                retval = self.scan.requires()
                assert isinstance(retval, TargetList)

    def test_scan_run(self):
        with patch("subprocess.run") as mocked_run:
            self.scan.run()
            assert mocked_run.called

    def test_scan_run_with_hostnames(self):
        with patch("subprocess.run") as mocked_run:
            self.scan.db_mgr = MagicMock()
            self.scan.db_mgr.get_all_hostnames.return_value = ["google.com"]
            self.scan.exempt_list = "stuff"
            self.scan.run()
            assert mocked_run.called

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_output_location(self):
        assert self.scan.output().path == str(Path(self.tmp_path) / "amass-results" / "amass.json")


class TestParseAmass:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = ParseAmassOutput(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )
        self.scan.input = lambda: luigi.LocalTarget(amass_json)
        self.scan.run()

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def test_scan_requires(self):
        with patch("pipeline.recon.AmassScan"):
            retval = self.scan.requires()
            assert isinstance(retval, AmassScan)

    def test_scan_results(self):
        assert self.scan.output().exists()

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder.exists()

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location
