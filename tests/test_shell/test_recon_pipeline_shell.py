import re
import sys
import time
import pickle
import shutil
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.recon.config import defaults
from pipeline.models.port_model import Port
from pipeline.models.target_model import Target
from pipeline.models.db_manager import DBManager
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

    # ("all", "commands failed and may have not installed properly", 1)
    # after tools moved to DB, update this test
    @pytest.mark.parametrize("test_input, expected, return_code", [("all", "is already installed", 0)])
    def test_do_install(self, test_input, expected, return_code, capsys, tmp_path):
        process_mock = MagicMock()
        attrs = {"communicate.return_value": (b"output", b"error"), "returncode": return_code}
        process_mock.configure_mock(**attrs)

        tool_dict = {
            "tko-subs": {
                "installed": False,
                "dependencies": ["go"],
                "go": "/usr/local/go/bin/go",
                "commands": [
                    "/usr/local/go/bin/go get github.com/anshumanbh/tko-subs",
                    "(cd ~/go/src/github.com/anshumanbh/tko-subs &&  /usr/local/go/bin/go build &&  /usr/local/go/bin/go install)",
                ],
                "shell": True,
            },
            "recursive-gobuster": {
                "installed": False,
                "dependencies": ["go"],
                "recursive-parent": "/home/epi/.local/recon-pipeline/tools/recursive-gobuster",
                "commands": [
                    "bash -c 'if [ -d /home/epi/.local/recon-pipeline/tools/recursive-gobuster ]; then cd /home/epi/.local/recon-pipeline/tools/recursive-gobuster && git fetch --all && git pull; else git clone https://github.com/epi052/recursive-gobuster.git /home/epi/.local/recon-pipeline/tools/recursive-gobuster ; fi'"
                ],
                "shell": False,
            },
            "subjack": {
                "installed": False,
                "dependencies": ["go"],
                "go": "/usr/local/go/bin/go",
                "commands": [
                    "/usr/local/go/bin/go get github.com/haccer/subjack",
                    "(cd ~/go/src/github.com/haccer/subjack && /usr/local/go/bin/go install)",
                ],
                "shell": True,
            },
            "searchsploit": {
                "installed": False,
                "dependencies": None,
                "home": "/home/epi",
                "tools-dir": "/home/epi/.local/recon-pipeline/tools",
                "exploitdb-file": "/home/epi/.local/recon-pipeline/tools/exploitdb",
                "searchsploit-file": "/home/epi/.local/recon-pipeline/tools/exploitdb/searchsploit",
                "searchsploit-rc": "/home/epi/.local/recon-pipeline/tools/exploitdb/.searchsploit_rc",
                "homesploit": "/home/epi/.searchsploit_rc",
                "sed-command": "'s#/opt#/home/epi/.local/recon-pipeline/tools#g'",
                "commands": [
                    "bash -c 'if [ -d /usr/share/exploitdb ]; then ln -fs /usr/share/exploitdb /home/epi/.local/recon-pipeline/tools/exploitdb && sudo ln -fs $(which searchsploit) /home/epi/.local/recon-pipeline/tools/exploitdb/searchsploit ; elif [ -d /home/epi/.local/recon-pipeline/tools/exploitdb ]; then cd /home/epi/.local/recon-pipeline/tools/exploitdb && git fetch --all && git pull; else git clone https://github.com/offensive-security/exploitdb.git /home/epi/.local/recon-pipeline/tools/exploitdb ; fi'",
                    "bash -c 'if [ -f /home/epi/.local/recon-pipeline/tools/exploitdb/.searchsploit_rc ]; then cp -n /home/epi/.local/recon-pipeline/tools/exploitdb/.searchsploit_rc /home/epi ; fi'",
                    "bash -c 'if [ -f /home/epi/.searchsploit_rc ]; then sed -i 's#/opt#/home/epi/.local/recon-pipeline/tools#g' /home/epi/.searchsploit_rc ; fi'",
                ],
                "shell": False,
            },
            "luigi-service": {
                "installed": False,
                "dependencies": None,
                "service-file": "/home/epi/PycharmProjects/recon-pipeline/luigid.service",
                "commands": [
                    "sudo cp /home/epi/PycharmProjects/recon-pipeline/luigid.service /lib/systemd/system/luigid.service",
                    "sudo cp /home/epi/PycharmProjects/recon-pipeline/luigid.service $(which luigid) /usr/local/bin",
                    "sudo systemctl daemon-reload",
                    "sudo systemctl start luigid.service",
                    "sudo systemctl enable luigid.service",
                ],
                "shell": True,
            },
            "aquatone": {
                "installed": False,
                "dependencies": None,
                "aquatone": "/home/epi/.local/recon-pipeline/tools/aquatone",
                "commands": [
                    "mkdir /tmp/aquatone",
                    "wget -q https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip -O /tmp/aquatone/aquatone.zip",
                    "bash -c 'if [[ ! $(which unzip) ]]; then sudo apt install -y zip; fi'",
                    "unzip /tmp/aquatone/aquatone.zip -d /tmp/aquatone",
                    "mv /tmp/aquatone/aquatone /home/epi/.local/recon-pipeline/tools/aquatone",
                    "rm -rf /tmp/aquatone",
                    "bash -c 'found=false; for loc in {/usr/bin/google-chrome,/usr/bin/google-chrome-beta,/usr/bin/google-chrome-unstable,/usr/bin/chromium-browser,/usr/bin/chromium}; do if [[ $(which $loc) ]]; then found=true; break; fi ; done; if [[ $found = false ]]; then sudo apt install -y chromium-browser ; fi'",
                ],
                "shell": False,
            },
            "gobuster": {
                "installed": False,
                "dependencies": ["go", "seclists"],
                "go": "/usr/local/go/bin/go",
                "commands": [
                    "/usr/local/go/bin/go get github.com/OJ/gobuster",
                    "(cd ~/go/src/github.com/OJ/gobuster && /usr/local/go/bin/go build && /usr/local/go/bin/go install)",
                ],
                "shell": True,
            },
            "amass": {
                "installed": False,
                "dependencies": ["go"],
                "go": "/usr/local/go/bin/go",
                "amass": "/home/epi/.local/recon-pipeline/tools/amass",
                "commands": [
                    "/usr/local/go/bin/go get -u github.com/OWASP/Amass/v3/...",
                    "cp ~/go/bin/amass /home/epi/.local/recon-pipeline/tools/amass",
                ],
                "shell": True,
                "environ": {"GO111MODULE": "on"},
            },
            "masscan": {
                "installed": True,
                "dependencies": None,
                "masscan": "/home/epi/.local/recon-pipeline/tools/masscan",
                "commands": [
                    "git clone https://github.com/robertdavidgraham/masscan /tmp/masscan",
                    "make -s -j -C /tmp/masscan",
                    "mv /tmp/masscan/bin/masscan /home/epi/.local/recon-pipeline/tools/masscan",
                    "rm -rf /tmp/masscan",
                    "sudo setcap CAP_NET_RAW+ep /home/epi/.local/recon-pipeline/tools/masscan",
                ],
                "shell": True,
            },
            "go": {
                "installed": False,
                "dependencies": None,
                "go": "/usr/local/go/bin/go",
                "commands": [
                    "wget -q https://dl.google.com/go/go1.13.7.linux-amd64.tar.gz -O /tmp/go.tar.gz",
                    "sudo tar -C /usr/local -xvf /tmp/go.tar.gz",
                    "bash -c 'if [ ! $(echo ${PATH} | grep $(dirname /usr/local/go/bin/go )) ]; then echo PATH=${PATH}:/usr/local/go/bin >> ~/.bashrc; fi'",
                ],
                "shell": True,
            },
            "webanalyze": {
                "installed": False,
                "dependencies": ["go"],
                "go": "/usr/local/go/bin/go",
                "commands": [
                    "/usr/local/go/bin/go get github.com/rverton/webanalyze/...",
                    "(cd ~/go/src/github.com/rverton/webanalyze && /usr/local/go/bin/go build && /usr/local/go/bin/go install)",
                ],
                "shell": True,
            },
            "seclists": {
                "installed": True,
                "depencencies": None,
                "seclists-file": "/home/epi/.local/recon-pipeline/tools/seclists",
                "commands": [
                    "bash -c 'if [[ -d /usr/share/seclists ]]; then ln -s /usr/share/seclists /home/epi/.local/recon-pipeline/tools/seclists ; elif [[ -d /home/epi/.local/recon-pipeline/tools/seclists ]] ; then cd /home/epi/.local/recon-pipeline/tools/seclists && git fetch --all && git pull; else git clone https://github.com/danielmiessler/SecLists.git /home/epi/.local/recon-pipeline/tools/seclists ; fi'"
                ],
                "shell": True,
            },
            "waybackurls": {
                "installed": True,
                "depencencies": ["go"],
                "commands": ["/usr/local/go/bin/go get github.com/tomnomnom/waybackurls"],
                "shell": True,
            },
        }

        tooldir = tmp_path / ".local" / "recon-pipeline" / "tools"
        tooldir.mkdir(parents=True, exist_ok=True)

        pickle.dump(tool_dict, (tooldir / ".tool-dict.pkl").open("wb"))

        with patch("subprocess.Popen", autospec=True) as mocked_popen:
            mocked_popen.return_value = process_mock
            self.shell.tools_dir = tooldir
            self.shell.do_install(test_input)
            assert mocked_popen.called

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
