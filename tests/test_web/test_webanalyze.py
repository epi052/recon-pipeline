import tempfile
from pathlib import Path

from pipeline.recon.web import WebanalyzeScan

webanalyze_results = Path(__file__).parent.parent / "data" / "recon-results" / "webanalyze-results"


class TestWebanalyzeScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = WebanalyzeScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "webanalyze-results"

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results(self):
        self.scan.results_subfolder = webanalyze_results
        self.scan.parse_results()
        assert self.scan.output().exists()
