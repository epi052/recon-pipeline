import tempfile
from pathlib import Path

import luigi

from pipeline.recon import AmassScan, ParseAmassOutput


amass_json = Path(__file__).parent.parent / "data" / "recon-results" / "amass-results" / "amass.json"


class TestAmassScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = AmassScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

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

    def test_scan_results(self):
        assert self.scan.output().exists()

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder.exists()

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location
