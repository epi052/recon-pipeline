import tempfile
from pathlib import Path

from pipeline.recon.web import SubjackScan, TKOSubsScan

subjack_results = Path(__file__).parent.parent / "data" / "recon-results" / "subjack-results"
tkosubs_results = Path(__file__).parent.parent / "data" / "recon-results" / "tkosubs-results"


class TestTKOSubsScanScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = TKOSubsScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "tkosubs-results"

    def test_scan_creates_results_file(self):
        assert self.scan.output_file == self.tmp_path / "tkosubs-results" / "tkosubs.csv"

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results(self):
        self.scan.results_subfolder = tkosubs_results
        self.scan.output_file = self.scan.results_subfolder / "tkosubs.csv"
        self.scan.parse_results()
        assert self.scan.output().exists()


class TestSubjackScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = SubjackScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "subjack-results"

    def test_scan_creates_results_file(self):
        assert self.scan.output_file == self.tmp_path / "subjack-results" / "subjack.txt"

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results(self):
        self.scan.results_subfolder = subjack_results
        self.scan.output_file = self.scan.results_subfolder / "subjack.txt"
        self.scan.parse_results()
        assert self.scan.output().exists()
