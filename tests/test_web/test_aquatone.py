import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from pipeline.recon.web import AquatoneScan, GatherWebTargets

aquatone_results = Path(__file__).parent.parent / "data" / "recon-results" / "aquatone-results"


class TestAquatoneScan:
    def setup_method(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.scan = AquatoneScan(
            target_file=__file__, results_dir=str(self.tmp_path), db_location=str(self.tmp_path / "testing.sqlite")
        )

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def test_scan_requires(self):
        with patch("pipeline.recon.web.GatherWebTargets"):
            retval = self.scan.requires()
            assert isinstance(retval, GatherWebTargets)

    def test_scan_creates_results_dir(self):
        assert self.scan.results_subfolder == self.tmp_path / "aquatone-results"

    def test_scan_creates_database(self):
        assert self.scan.db_mgr.location.exists()
        assert self.tmp_path / "testing.sqlite" == self.scan.db_mgr.location

    def test_scan_creates_results(self):
        # self.scan.results_subfolder.mkdir()
        myresults = self.scan.results_subfolder / "aquatone_session.json"
        shutil.copytree(aquatone_results, self.scan.results_subfolder)
        with open(myresults) as f:
            # results.keys -> dict_keys(['version', 'stats', 'pages', 'pageSimilarityClusters'])
            results = json.load(f)

        for page, page_dict in results.get("pages").items():
            if "hasScreenshot" not in page_dict:
                continue
            page_dict["hasScreenshot"] = False
            break

        with open(myresults, "w") as f:
            json.dump(results, f)

        self.scan.parse_results()
        assert self.scan.output().exists()

    # pipeline/recon/web/aquatone.py                83     17    80%   69-79, 183-191, 236-260
    def test_scan_parse_results_with_bad_file(self, caplog):
        self.scan.results_subfolder = Path("/tmp")
        assert not (self.scan.results_subfolder / "aquatone_session.json").exists()
        self.scan.parse_results()
        assert "[Errno 2] No such file or directory:" in caplog.text

    def test_scan_run(self):
        with patch("subprocess.run") as mocked_run:
            self.scan.parse_results = MagicMock()
            self.scan.db_mgr.get_all_web_targets = MagicMock()
            self.scan.db_mgr.get_all_web_targets.return_value = ["google.com"]
            self.scan.run()
            assert self.scan.parse_results.called
            assert mocked_run.called
