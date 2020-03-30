import sys
import time
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.recon.config import defaults
from pipeline.models import Target, Port, IPAddress, DBManager

recon_shell = importlib.import_module("pipeline.recon-pipeline")


class TestReconShell:
    luigi_logs = [
        (
            "INFO: Informed scheduler that task SearchsploitScan__home_epi__local_bl_eno1_7c290 has status DONE\n",
            "SearchsploitScan complete!",
        ),
        (
            "INFO: Informed scheduler that task SearchsploitScan__home_epi__local_bl_eno1_7c290 has status PENDING\n",
            "SearchsploitScan queued",
        ),
        ("", ""),
        (
            "INFO: [pid 31387] Worker Worker(pid=31387) running FullScan(target_file=bitdiscovery\n",
            "FullScan running...",
        ),
        ("===== Luigi Execution Summary =====", "Luigi Execution Summary"),
    ]

    def setup_method(self):
        self.shell = recon_shell.ReconShell()
        self.shell.async_alert = print
        self.shell.poutput = print
        self.db_location = Path(__file__).parent.parent / "data" / "recon-results" / "updated-tests"
        self.realdb = DBManager(self.db_location)

    def create_temp_target(self):
        tgt = Target(
            hostname="localhost",
            ip_addresses=[IPAddress(ipv4_address="127.0.0.1"), IPAddress(ipv6_address="::1")],
            open_ports=[Port(port_number=443, protocol="tcp"), Port(port_number=80, protocol="tcp")],
        )
        return tgt

    @pytest.mark.parametrize("test_input", ["tools-dir", "database-dir"])
    def test_scan_creates_results_dir(self, test_input):
        assert Path(defaults.get(test_input)).exists()

    def test_selector_thread_starts(self):
        self.shell._preloop_hook()
        assert self.shell.selectorloop.is_alive()

    def test_selector_thread_stops(self):
        with patch("selectors.DefaultSelector.select"), patch("selectors.DefaultSelector.get_map"):
            self.shell._preloop_hook()
            assert self.shell.selectorloop.is_alive()
            time.sleep(0.5)
            self.shell._postloop_hook()
            time.sleep(1)
            assert self.shell.selectorloop.stopped()

    @pytest.mark.parametrize("test_input", ["tools-dir\n", ""])
    def test_install_error_reporter(self, test_input, capsys):
        stderr = MagicMock()
        stderr.readline.return_value = test_input.encode()

        self.shell._install_error_reporter(stderr)

        if not test_input:
            assert not capsys.readouterr().out
        else:
            assert test_input.strip() in capsys.readouterr().out

    @pytest.mark.parametrize("test_input, expected", luigi_logs)
    def test_luigi_pretty_printer(self, test_input, expected, capsys):
        stderr = MagicMock()
        stderr.readline.return_value = test_input.encode()
        self.shell._luigi_pretty_printer(stderr)
        if not test_input:
            assert not capsys.readouterr().out
        else:
            assert expected in capsys.readouterr().out

    def test_do_scan_without_db(self, capsys):
        self.shell.do_scan(f"FullScan --target-file {__file__}")
        assert "You are not connected to a database" in capsys.readouterr().out

    def test_get_databases(self):
        testdb = Path(defaults.get("database-dir")) / "testdb"
        testdb.touch()
        assert testdb in list(recon_shell.ReconShell.get_databases())
        testdb.unlink()

    def test_database_list_bad(self, capsys):
        def empty_gen():
            yield from ()

        self.shell.get_databases = empty_gen

        self.shell.database_list("")
        assert "There are no databases" in capsys.readouterr().out

    def test_database_attach_new(self, capsys):
        self.shell.select = lambda x: "create new database"
        self.shell.read_input = lambda x: "testdb"
        self.shell.database_attach("")
        (Path(defaults.get("database-dir")) / "testdb").unlink()
        assert "created database @" in capsys.readouterr().out

    def test_database_attach_existing(self, capsys):
        testdb = Path(defaults.get("database-dir")) / "testdb"
        testdb.touch()
        self.shell.select = lambda x: str(testdb.resolve())
        self.shell.database_attach("")
        assert "attached to sqlite database @" in capsys.readouterr().out
        testdb.unlink()

    def test_database_detach_connected(self, capsys):
        self.shell.db_mgr = MagicMock()
        self.shell.db_mgr.location = "stuff"
        self.shell.database_detach("")
        assert "detached from sqlite database @" in capsys.readouterr().out

    def test_database_detach_not_connected(self, capsys):
        self.shell.database_detach("")
        assert "you are not connected to a database" in capsys.readouterr().out

    def test_database_delete_without_index(self, capsys):
        testdb = Path(defaults.get("database-dir")) / "testdb"
        testdb.touch()
        self.shell.select = lambda x: str(testdb.resolve())
        self.shell.database_delete("")
        try:
            assert not testdb.exists()
        except AssertionError:
            testdb.unlink()
            raise AssertionError
        assert "[+] deleted sqlite database" in capsys.readouterr().out

    def test_database_delete_with_index(self, capsys):
        testdb = Path(defaults.get("database-dir")) / "testdb"
        testdb.touch()
        self.shell.select = lambda x: str(testdb.resolve())
        self.shell.prompt = f"[db-1] {recon_shell.DEFAULT_PROMPT}> "
        self.shell.db_mgr = MagicMock()
        self.shell.db_mgr.location = "stuff"
        self.shell.database_delete("")
        try:
            assert not testdb.exists()
        except AssertionError:
            testdb.unlink()
            raise AssertionError
        out = capsys.readouterr().out
        assert "[+] deleted sqlite database" in out
        assert "detached from sqlite database" in out
        assert self.shell.db_mgr is None

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (None, "you are not connected to a database"),
            ("", "View results of completed scans"),
            ("ports", "blog.bitdiscovery.com: 443,80"),
            ("ports --paged", "blog.bitdiscovery.com: 443,80"),
            ("ports --host assetinventory.bugcrowd.com", "assetinventory.bugcrowd.com: 8443,8080,443,80"),
            ("ports --host assetinventory.bugcrowd.com --paged", "assetinventory.bugcrowd.com: 8443,8080,443,80"),
            ("endpoints", " https://ibm.bitdiscovery.com/user\n[\x1b[91m403\x1b[39m] https://52.8.186.88/ADMIN"),
            ("endpoints --host 52.8.186.88", "[\x1b[32m200\x1b[39m] https://52.8.186.88/favicon.ico"),
            ("endpoints --host 52.8.186.88 --status-code 200", "[\x1b[32m200\x1b[39m] https://52.8.186.88/favicon.ico"),
            (
                "endpoints --host 52.8.186.88 --status-code 200 --paged",
                "[\x1b[32m200\x1b[39m] https://52.8.186.88/favicon.ico",
            ),
            ("endpoints --host 52.8.186.88 --status-code 200 --paged --plain", "https://52.8.186.88/favicon.ico"),
            (
                "endpoints --host 52.8.186.88 --status-code 200 --paged --plain --headers",
                "http://52.8.186.88/\n  Access-Control-Allow-Headers: X-Requested-With",
            ),
            (
                "endpoints --host 52.8.186.88 --status-code 200 --paged --headers",
                "[\x1b[32m200\x1b[39m] https://52.8.186.88/\n\x1b[36m  Content-Security-Policy:\x1b[39m default-src 'self' https: 'unsafe-inline' 'unsafe-eval' data: client-api.arkoselabs.com",
            ),
            (
                "nmap-scans",
                "52.8.163.50 - http\n==================\n\ntcp port: 443 - open - syn-ack\nproduct: nginx :: 1.16.1\nnse script(s) output:\n  http-server-header",
            ),
            (
                "nmap-scans --commandline",
                "nmap --open -sT -n -sC -T 4 -sV -Pn -p 8443,8080,443,80 -oA /home/epi/PycharmProjects/recon-pipeline/tests/data/updated-tests/nmap-results/nmap.104.20.60.51-tcp 104.20.60.51",
            ),
            (
                "nmap-scans --host synopsys.bitdiscovery.com",
                "52.53.89.219 - http\n===================\n\ntcp port: 443 - open - syn-ack",
            ),
            (
                "nmap-scans --port 443 --product nginx",
                "52.8.163.50 - http\n==================\n\ntcp port: 443 - open - syn-ack\nproduct: nginx :: 1.16.1",
            ),
            ("nmap-scans --port 443 --nse-script http-title", "http-title\n    bugcrowd - Asset Inventory"),
            (
                "nmap-scans --host synopsys.bitdiscovery.com",
                "52.53.89.219 - http\n===================\n\ntcp port: 443 - open - syn-ack",
            ),
            (
                "searchsploit-results",
                "==================================================================================",
            ),
            ("searchsploit-results --type webapps", "webapps  | 37450.txt|  Amazon S3"),
            ("searchsploit-results --host synopsys.bitdiscovery.com --fullpath", "exploits/linux/local/40768.sh"),
            ("targets", "email.assetinventory.bugcrowd.com"),
            ("targets --vuln-to-subdomain-takeover", "[\x1b[91mnot vulnerable\x1b[39m] ibm.bitdiscovery.com"),
            ("web-technologies", "CloudFlare (CDN)"),
            ("web-technologies --host blog.bitdiscovery.com --paged", "MySQL (Databases)"),
        ],
    )
    def test_do_view_with_real_database(self, test_input, expected, capsys):
        if test_input is None:
            self.shell.do_view("")
            assert expected in capsys.readouterr().out
        else:
            self.shell.db_mgr = self.realdb
            self.shell.add_dynamic_parser_arguments()

            self.shell.do_view(test_input)
            assert expected in capsys.readouterr().out

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (None, "Manage database connections (list/attach/detach/delete)"),
            ("list", "View results of completed scans"),
        ],
    )
    def test_do_database(self, test_input, expected, capsys):
        if test_input is None:
            self.shell.do_database("")
            assert expected in capsys.readouterr().out
        else:
            testdb = Path(defaults.get("database-dir")) / "testdb"
            testdb.touch()
            self.shell.do_database(test_input)
            assert str(testdb) in capsys.readouterr().out
            testdb.unlink()

    @patch("webbrowser.open", autospec=True)
    def test_do_status(self, mock_browser):
        self.shell.do_status("--host 127.0.0.1 --port 1111")
        assert mock_browser.called

    @pytest.mark.parametrize("test_input, expected", [("all", "is already installed")])
    def test_do_install(self, test_input, expected, capsys, tmp_path):
        process_mock = MagicMock()
        attrs = {"communicate.return_value": (b"output", b"error"), "returncode": 0}
        process_mock.configure_mock(**attrs)

        with patch("subprocess.Popen", autospec=True) as mocked_popen, patch.object(
            Path, "home", return_value=tmp_path
        ):
            mocked_popen.return_value = process_mock
            self.shell.do_install(test_input)
            out = capsys.readouterr().out
            assert mocked_popen.called or expected in out

    @pytest.mark.parametrize(
        "test_input, expected, db_mgr",
        [
            (
                "FullScan --target-file required",
                "You are not connected to a database; run database attach before scanning",
                None,
            ),
            (
                "FullScan --target-file required --sausage --verbose",
                "If anything goes wrong, rerun your command with --verbose",
                True,
            ),
            ("FullScan --target-file required ", "If anything goes wrong, rerun your command with --verbose", True),
        ],
    )
    def test_do_scan(self, test_input, expected, db_mgr, capsys):
        process_mock = MagicMock()
        attrs = {"communicate.return_value": (b"output", b"error"), "returncode": 0}
        process_mock.configure_mock(**attrs)

        with patch("subprocess.run", autospec=True) as mocked_popen, patch(
            "webbrowser.open", autospec=True
        ) as mocked_web, patch("selectors.DefaultSelector.register", autospec=True) as mocked_selector:
            mocked_popen.return_value = process_mock
            if db_mgr is None:
                self.shell.do_scan(test_input)
                assert expected in capsys.readouterr().out
            else:
                self.shell.db_mgr = MagicMock()
                self.shell.db_mgr.location = "stuff"
                self.shell.do_scan(test_input)
                if "--sausage" in test_input:
                    assert mocked_web.called
                if "--verbose" not in test_input:
                    assert mocked_selector.called

    def test_cluge_package_imports(self):
        pathlen = len(sys.path)
        recon_shell.cluge_package_imports(name="__main__", package=None)
        assert len(sys.path) > pathlen

    def test_main(self):
        with patch("cmd2.Cmd.cmdloop") as mocked_loop, patch("sys.exit"):
            recon_shell.main(name="__main__")
            assert mocked_loop.called
