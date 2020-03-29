import tempfile
from pathlib import Path

from pipeline.recon.web import GatherWebTargets


class TestAmassScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = GatherWebTargets(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results(self):
        self.scan.run()
        assert self.scan.output().exists()
