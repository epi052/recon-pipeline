import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline.recon.web import GatherWebTargets
from pipeline.recon import ParseMasscanOutput, ParseAmassOutput


class TestGatherWebTargets:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = GatherWebTargets(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def test_scan_requires(self):
        with patch("pipeline.recon.ParseMasscanOutput"), patch("pipeline.recon.ParseAmassOutput"):
            retval = self.scan.requires()
            assert isinstance(retval.get("masscan-output"), ParseMasscanOutput)
            assert isinstance(retval.get("amass-output"), ParseAmassOutput)

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_run(self):
        self.scan.db_mgr.add = MagicMock()
        self.scan.db_mgr.get_all_targets = MagicMock(return_value=["google.com"])
        self.scan.db_mgr.get_ports_by_ip_or_host_and_protocol = MagicMock(return_value=["80", "443"])
        self.scan.db_mgr.get_or_create_target_by_ip_or_hostname = MagicMock()

        self.scan.run()

        assert self.scan.db_mgr.add.called
        assert self.scan.db_mgr.get_all_targets.called
        assert self.scan.db_mgr.get_ports_by_ip_or_host_and_protocol.called
        assert self.scan.db_mgr.get_or_create_target_by_ip_or_hostname.called
