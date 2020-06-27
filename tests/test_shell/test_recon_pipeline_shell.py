import re
import sys
import time
import pickle
import shutil
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.models.port_model import Port
from pipeline.models.target_model import Target
from pipeline.models.db_manager import DBManager
from pipeline.tools import tools
from pipeline.recon.config import defaults
from pipeline.models.ip_address_model import IPAddress

recon_shell = importlib.import_module("pipeline.recon-pipeline")
existing_db = Path(__file__).parent.parent / "data" / "existing-database-test"


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
        testdb = Path(defaults.get("database-dir")) / "testdb6"
        testdb.touch()
        assert testdb in list(recon_shell.ReconShell.get_databases())
        try:
            testdb.unlink()
        except FileNotFoundError:
            pass

    def test_database_list_bad(self, capsys):
        def empty_gen():
            yield from ()

        self.shell.get_databases = empty_gen

        self.shell.database_list("")
        assert "There are no databases" in capsys.readouterr().out

    def test_database_attach_new(self, capsys, tmp_path):
        testdb = Path(tmp_path) / "testdb1"
        shell = recon_shell.ReconShell()

        shell.select = lambda x: "create new database"
        shell.read_input = lambda x: str(testdb)
        shell.database_attach("")
        time.sleep(1)
        assert "created database @" in capsys.readouterr().out
        try:
            testdb.unlink()
        except FileNotFoundError:
            pass

    def test_database_attach_existing(self, capsys, tmp_path):
        testdb = Path(tmp_path) / "testdb2"
        shutil.copy(self.db_location, testdb)
        assert testdb.exists()
        shell = recon_shell.ReconShell()

        shell.select = lambda x: str(testdb.expanduser().resolve())
        shell.get_databases = MagicMock(return_value=[str(testdb)])
        shell.database_attach("")
        time.sleep(1)
        assert "attached to sqlite database @" in capsys.readouterr().out
        try:
            testdb.unlink()
        except FileNotFoundError:
            pass

    def test_database_detach_connected(self, capsys):
        self.shell.db_mgr = MagicMock()
        self.shell.db_mgr.location = "stuff"
        self.shell.database_detach("")
        assert "detached from sqlite database @" in capsys.readouterr().out

    def test_database_detach_not_connected(self, capsys):
        self.shell.database_detach("")
        assert "you are not connected to a database" in capsys.readouterr().out

    def test_database_delete_without_index(self, capsys, tmp_path):
        testdb = Path(tmp_path) / "testdb3"
        testdb.touch()
        self.shell.select = lambda x: str(testdb.expanduser().resolve())
        self.shell.get_databases = MagicMock(return_value=[str(testdb)])
        self.shell.database_delete("")
        try:
            assert not testdb.exists()
        except AssertionError:
            try:
                testdb.unlink()
            except FileNotFoundError:
                pass
            raise AssertionError
        assert "[+] deleted sqlite database" in capsys.readouterr().out

    def test_database_delete_with_index(self, capsys):
        testdb = Path(defaults.get("database-dir")) / "testdb4"
        testdb.touch()
        shell = recon_shell.ReconShell()
        shell.select = lambda x: str(testdb.expanduser().resolve())
        shell.prompt = f"[db-1] {recon_shell.DEFAULT_PROMPT}> "
        shell.db_mgr = MagicMock()
        shell.db_mgr.location = "stuff"
        shell.get_databases = MagicMock(return_value=[str(testdb)])
        shell.database_delete("")
        try:
            assert not testdb.exists()
        except AssertionError:
            try:
                testdb.unlink()
            except FileNotFoundError:
                pass
            raise AssertionError
        out = capsys.readouterr().out
        assert "[+] deleted sqlite database" in out

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (None, "you are not connected to a database"),
            ("", "View results of completed scans"),
            ("ports", "blog.bitdiscovery.com: 443,80"),
            ("ports --paged", "blog.bitdiscovery.com: 443,80"),
            ("ports --host assetinventory.bugcrowd.com", "assetinventory.bugcrowd.com: 8443,8080,443,80"),
            ("ports --host assetinventory.bugcrowd.com --paged", "assetinventory.bugcrowd.com: 8443,8080,443,80"),
            ("ports --port-number 8443", "assetinventory.bugcrowd.com: 8443,8080,443,80"),
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
            ("targets --vuln-to-subdomain-takeover --paged", ""),
            ("targets --type ipv4 --paged", "13.226.182.120"),
            ("targets --type ipv6", "2606:4700:10::6814:3c33"),
            ("targets --type domain-name --paged", "email.assetinventory.bugcrowd.com"),
            ("web-technologies", "CloudFlare (CDN)"),
            ("web-technologies --host blog.bitdiscovery.com --type CDN", "Amazon Cloudfront (CDN)"),
            ("web-technologies --host blog.bitdiscovery.com --product WordPress", "WordPress (CMS,Blogs)"),
            ("web-technologies --product WordPress", "13.226.191.61"),
            ("web-technologies  --type Miscellaneous", "13.226.191.85"),
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
            testdb = Path(defaults.get("database-dir")) / "testdb5"
            testdb.touch()
            self.shell.do_database(test_input)
            assert str(testdb) in capsys.readouterr().out
            try:
                testdb.unlink()
            except FileNotFoundError:
                pass

    @patch("webbrowser.open", autospec=True)
    def test_do_status(self, mock_browser):
        self.shell.do_status("--host 127.0.0.1 --port 1111")
        assert mock_browser.called

    @pytest.mark.parametrize("test_input, expected", [(None, "Manage tool actions (install/uninstall/reinstall)")])
    def test_do_tools(self, test_input, expected, capsys):
        if test_input is None:
            self.shell.do_tools("")
            assert expected in capsys.readouterr().out

    # after tools moved to DB, update this test
    @pytest.mark.parametrize(
        "test_input, expected, return_code",
        [
            ("all", "[-] go queued", 0),
            ("amass", "check output from the offending command above", 1),
            ("amass", "has an unmet dependency", 0),
            ("waybackurls", "[!] waybackurls has an unmet dependency", 0),
            ("go", "[+] go installed!", 0),
            ("masscan", "[!] masscan is already installed.", 0),
        ],
    )
    def test_tools_install(self, test_input, expected, return_code, capsys, tmp_path):
        process_mock = MagicMock()
        attrs = {"communicate.return_value": (b"output", b"error"), "returncode": return_code}
        process_mock.configure_mock(**attrs)

        tooldir = tmp_path / ".local" / "recon-pipeline" / "tools"
        tooldir.mkdir(parents=True, exist_ok=True)

        tools["go"]["installed"] = False
        tools["waybackurls"]["installed"] = True
        tools["masscan"]["installed"] = True
        tools["amass"]["shell"] = False
        tools["amass"]["installed"] = False

        pickle.dump(tools, (tooldir / ".tool-dict.pkl").open("wb"))

        with patch("subprocess.Popen", autospec=True) as mocked_popen:
            mocked_popen.return_value = process_mock
            self.shell.tools_dir = tooldir
            self.shell.do_tools(f"install {test_input}")
            if test_input != "masscan":
                assert mocked_popen.called

        assert expected in capsys.readouterr().out

        if test_input != "all" and return_code == 0:
            assert self.shell._get_dict().get(test_input).get("installed") is True

    # after tools moved to DB, update this test
    @pytest.mark.parametrize(
        "test_input, expected, return_code",
        [
            ("all", "waybackurls queued", 0),
            ("amass", "check output from the offending command above", 1),
            ("waybackurls", "[+] waybackurls uninstalled!", 0),
            ("go", "[!] go is not installed", 0),
        ],
    )
    def test_tools_uninstall(self, test_input, expected, return_code, capsys, tmp_path):
        process_mock = MagicMock()
        attrs = {"communicate.return_value": (b"output", b"error"), "returncode": return_code}
        process_mock.configure_mock(**attrs)

        tooldir = tmp_path / ".local" / "recon-pipeline" / "tools"
        tooldir.mkdir(parents=True, exist_ok=True)

        tools["go"]["installed"] = False
        tools["waybackurls"]["installed"] = True
        tools["amass"]["shell"] = False
        tools["amass"]["installed"] = True

        pickle.dump(tools, (tooldir / ".tool-dict.pkl").open("wb"))

        with patch("subprocess.Popen", autospec=True) as mocked_popen:
            mocked_popen.return_value = process_mock
            self.shell.tools_dir = tooldir
            self.shell.do_tools(f"uninstall {test_input}")
            if test_input != "go":
                assert mocked_popen.called

        assert expected in capsys.readouterr().out
        if test_input != "all" and return_code == 0:
            assert self.shell._get_dict().get(test_input).get("installed") is False

    def test_tools_reinstall(self, capsys):
        self.shell.do_tools("reinstall amass")
        output = capsys.readouterr().out
        assert "[*] Removing amass..." in output or "[!] amass is not installed." in output
        assert "[*] Installing amass..." in output

    def test_tools_list(self, capsys, tmp_path):
        tooldir = tmp_path / ".local" / "recon-pipeline" / "tools"
        tooldir.mkdir(parents=True, exist_ok=True)

        tools["go"]["installed"] = True
        tools["waybackurls"]["installed"] = True
        tools["masscan"]["installed"] = False

        regexes = [r"Installed.*go/bin/go", r"Installed.*bin/waybackurls", r":Missing:.*tools/masscan"]

        pickle.dump(tools, (tooldir / ".tool-dict.pkl").open("wb"))

        self.shell.tools_dir = tooldir

        self.shell.do_tools("list")

        output = capsys.readouterr().out

        for regex in regexes:
            assert re.search(regex, output)

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
            ("FullScan --target-file required", "If anything goes wrong, rerun your command with --verbose", True),
            ("FullScan --target required", "If anything goes wrong, rerun your command with --verbose", True),
        ],
    )
    def test_do_scan(self, test_input, expected, db_mgr, capsys, tmp_path):
        process_mock = MagicMock()
        attrs = {"communicate.return_value": (b"output", b"error"), "returncode": 0}
        process_mock.configure_mock(**attrs)

        with patch("subprocess.run", autospec=True) as mocked_popen, patch(
            "webbrowser.open", autospec=True
        ) as mocked_web, patch("selectors.DefaultSelector.register", autospec=True) as mocked_selector, patch(
            "cmd2.Cmd.select"
        ) as mocked_select:
            mocked_select.return_value = "Resume"
            mocked_popen.return_value = process_mock

            test_input += f" --results-dir {tmp_path / 'mostuff'}"

            if db_mgr is None:
                self.shell.do_scan(test_input)
                assert expected in capsys.readouterr().out
            else:
                self.shell.db_mgr = MagicMock()
                self.shell.db_mgr.location = tmp_path / "stuff"
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
        with patch("cmd2.Cmd.cmdloop") as mocked_loop, patch("sys.exit"), patch("cmd2.Cmd.select") as mocked_select:
            mocked_select.return_value = "No"
            recon_shell.main(name="__main__")
            assert mocked_loop.called

    @pytest.mark.parametrize("test_input", ["Yes", "No"])
    def test_remove_old_recon_tools(self, test_input, tmp_path):
        tooldict = tmp_path / ".tool-dict.pkl"
        tooldir = tmp_path / ".recon-tools"
        searchsploit_rc = tmp_path / ".searchsploit_rc"

        tooldict.touch()
        assert tooldict.exists()

        searchsploit_rc.touch()
        assert searchsploit_rc.exists()

        tooldir.mkdir()
        assert tooldir.exists()

        subfile = tooldir / "subfile"

        subfile.touch()
        assert subfile.exists()

        with patch("cmd2.Cmd.cmdloop"), patch("sys.exit"), patch("cmd2.Cmd.select") as mocked_select:
            mocked_select.return_value = test_input
            recon_shell.main(
                name="__main__", old_tools_dir=tooldir, old_tools_dict=tooldict, old_searchsploit_rc=searchsploit_rc
            )

        for file in [subfile, tooldir, tooldict, searchsploit_rc]:
            if test_input == "Yes":
                assert not file.exists()
            else:
                assert file.exists()

    @pytest.mark.parametrize(
        "test_input", [("1", "Resume", True, 1), ("2", "Remove", False, 0), ("3", "Save", False, 1)]
    )
    def test_check_scan_directory(self, test_input, tmp_path):
        user_input, answer, exists, numdirs = test_input

        new_tmp = tmp_path / f"check_scan_directory_test-{user_input}-{answer}"
        new_tmp.mkdir()

        with patch("cmd2.Cmd.select") as mocked_select:
            mocked_select.return_value = answer

            self.shell.check_scan_directory(str(new_tmp))

            assert new_tmp.exists() == exists
            assert len(list(tmp_path.iterdir())) == numdirs

            if answer == "Save":
                assert (
                    re.search(r"check_scan_directory_test-3-Save-[0-9]{6,8}-[0-9]+", str(list(tmp_path.iterdir())[0]))
                    is not None
                )
