import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline.recon.web import WaybackurlsScan, GatherWebTargets


class TestGatherWebTargets:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = WaybackurlsScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )
        self.scan.exception = False

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def test_scan_requires(self):
        with patch("pipeline.recon.web.GatherWebTargets"):
            retval = self.scan.requires()
            assert isinstance(retval, GatherWebTargets)

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "waybackurls-results"

    def test_scan_run(self):
        with patch("subprocess.run", autospec=True) as mocked_run:
            self.scan.results_subfolder = self.tmp_path / "waybackurls-results"

            self.scan.db_mgr.get_all_hostnames = MagicMock()
            self.scan.db_mgr.get_all_hostnames.return_value = ["google.com"]

            completed_process_mock = MagicMock()
            completed_process_mock.stdout.return_value = b"https://drive.google.com\nhttps://maps.google.com\n\n"
            completed_process_mock.stdout.decode.return_value = "https://drive.google.com\nhttps://maps.google.com\n\n"
            completed_process_mock.stdout.decode.splitlines.return_value = [
                "https://drive.google.com",
                "https://maps.google.com",
            ]

            mocked_run.return_value = completed_process_mock

            self.scan.db_mgr.add = MagicMock()
            self.scan.db_mgr.get_or_create = MagicMock()
            self.scan.db_mgr.get_or_create_target_by_ip_or_hostname = MagicMock()

            self.scan.run()

            assert mocked_run.called
            assert self.scan.db_mgr.add.called
            assert self.scan.db_mgr.get_or_create.called
            assert self.scan.db_mgr.get_or_create_target_by_ip_or_hostname.called
