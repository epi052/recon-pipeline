import tempfile
from pathlib import Path

from pipeline.recon import TargetList

tfp = Path(__file__).parent.parent / "data" / "bitdiscovery"


class TestReconTargets:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = TargetList(
            target_file=str(tfp), results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results(self):
        assert self.scan.output().exists()
