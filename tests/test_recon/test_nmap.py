import tempfile
from pathlib import Path

import luigi

from ..utils import is_kali
from pipeline.recon import ThreadedNmapScan, SearchsploitScan

nmap_results = Path(__file__).parent.parent / "data" / "recon-results" / "nmap-results"


class TestThreadedNmapScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = ThreadedNmapScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

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

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_searchsploit_produces_results(self):
        self.scan.input = lambda: {"localtarget": luigi.LocalTarget(nmap_results)}

        if not is_kali():
            return True

        self.scan.run()

        assert len([x for x in (nmap_results / ".." / "searchsploit-results").glob("searchsploit*.txt")]) > 0
