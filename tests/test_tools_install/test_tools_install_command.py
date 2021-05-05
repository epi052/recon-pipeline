import os
import pickle
import shutil
import tempfile
import importlib
import subprocess
from pathlib import Path

import pytest

from tests import utils
from pipeline.tools.loader import get_go_version

recon_pipeline = importlib.import_module("pipeline.recon-pipeline")
tools = recon_pipeline.tools


class TestUnmockedToolsInstall:
    def setup_method(self):
        self.shell = recon_pipeline.ReconShell()
        self.tmp_path = Path(tempfile.mkdtemp())
        self.shell.tools_dir = self.tmp_path / ".local" / "recon-pipeline" / "tools"
        self.shell.tools_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(self.shell.tools_dir)

    def teardown_method(self):
        def onerror(func, path, exc_info):
            subprocess.run(f"sudo rm -rf {self.shell.tools_dir}".split())

        shutil.rmtree(self.tmp_path, onerror=onerror)

    def perform_add_remove(self, tools_dict, tool_name, install, exists):
        if install:
            pickle.dump(tools_dict, Path(self.shell.tools_dir / ".tool-dict.pkl").open("wb"))

        tool = Path(tools_dict.get(tool_name).get("path"))

        if install and exists is False:
            assert tool.exists() is False
        elif not install and exists is True:
            assert tool.exists() is True

        if install:
            utils.run_cmd(self.shell, f"tools install {tool_name}")
            assert tool.exists() is True
        else:
            utils.run_cmd(self.shell, f"tools uninstall {tool_name}")
            assert tool.exists() is False

    def setup_go_test(self, tool_name, tool_dict):
        # install go in tmp location
        dependency = "go"
        dependency_path = f"{self.shell.tools_dir}/go/bin/go"
        tmp_path = tempfile.mkdtemp()

        tool_dict.get(dependency)["path"] = dependency_path
        tool_dict.get(dependency).get("install_commands")[
            0
        ] = f"wget -q https://dl.google.com/go/{get_go_version(None, None)}.tar.gz -O {tmp_path}/go.tar.gz"
        tool_dict.get(dependency).get("install_commands")[
            1
        ] = f"tar -C {self.shell.tools_dir} -xvf {tmp_path}/go.tar.gz"
        tool_dict.get(dependency).get("uninstall_commands")[0] = f"rm -rvf {self.shell.tools_dir}/go"
        tool_dict[dependency]["uninstall_commands"].append(f"rm -rvf {tmp_path}")

        # handle env for local go install
        if tool_name != "go":

            tmp_go_path = f"{self.shell.tools_dir}/mygo"
            Path(tmp_go_path).mkdir(parents=True, exist_ok=True)
            tool_dict.get(tool_name)["environ"]["GOPATH"] = tmp_go_path

            tool_path = f"{tool_dict.get(tool_name).get('environ').get('GOPATH')}/bin/{tool_name}"
            tool_dict.get(tool_name)["path"] = tool_path

        tool_dict.get(tool_name)["installed"] = False
        tool_dict.get(dependency)["installed"] = False

        print(tool_dict.get(tool_name))
        print(tool_dict.get(dependency))

        return tool_dict

    def test_install_masscan(self):
        tool = "masscan"
        tools_copy = tools.copy()

        tmp_path = tempfile.mkdtemp()
        tool_path = f"{self.shell.tools_dir}/{tool}"

        tools_copy.get(tool)["path"] = tool_path
        tools_copy.get(tool)["installed"] = False

        tools_copy.get(tool).get("install_commands")[
            0
        ] = f"git clone https://github.com/robertdavidgraham/masscan {tmp_path}/masscan"
        tools_copy.get(tool).get("install_commands")[1] = f"make -s -j -C {tmp_path}/masscan"
        tools_copy.get(tool).get("install_commands")[2] = f"mv {tmp_path}/masscan/bin/masscan {tool_path}"
        tools_copy.get(tool).get("install_commands")[3] = f"rm -rf {tmp_path}/masscan"
        tools_copy.get(tool).get("install_commands")[4] = f"sudo setcap CAP_NET_RAW+ep {tool_path}"
        tools_copy.get(tool).get("uninstall_commands")[0] = f"rm {tool_path}"

        self.perform_add_remove(tools_copy, tool, True, False)
        self.perform_add_remove(tools_copy, tool, False, True)

    def test_install_amass(self):
        tool = "amass"
        url = "github.com/OWASP/Amass/v3/..."
        tools_copy = tools.copy()
        tool_path = f"{self.shell.tools_dir}/mygo/bin/amass"

        tools_copy.update(self.setup_go_test(tool, tools_copy))

        tools_copy.get(tool).get("install_commands")[0] = f"{tools_copy.get('go').get('path')} get {url}"
        tools_copy.get(tool).get("uninstall_commands")[0] = f"rm {tool_path}"

        self.perform_add_remove(tools_copy, tool, True, False)
        self.perform_add_remove(tools_copy, tool, False, True)

    def test_install_aquatone(self):
        tool = "aquatone"
        tools_copy = tools.copy()

        tool_path = f"{self.shell.tools_dir}/{tool}"
        tmp_path = tempfile.mkdtemp()

        tools_copy.get(tool)["path"] = tool_path
        tools_copy.get(tool).get("install_commands")[0] = f"mkdir /{tmp_path}/aquatone"
        tools_copy.get(tool).get("install_commands")[
            1
        ] = f"wget -q https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip -O /{tmp_path}/aquatone/aquatone.zip"
        tools_copy.get(tool).get("install_commands")[
            3
        ] = f"unzip /{tmp_path}/aquatone/aquatone.zip -d /{tmp_path}/aquatone"
        tools_copy.get(tool).get("install_commands")[4] = f"mv /{tmp_path}/aquatone/aquatone {tool_path}"
        tools_copy.get(tool).get("install_commands")[5] = f"rm -rf /{tmp_path}/aquatone"
        tools_copy.get(tool).get("uninstall_commands")[0] = f"rm {tool_path}"

        self.perform_add_remove(tools_copy, tool, True, False)
        self.perform_add_remove(tools_copy, tool, False, True)

    def test_install_go(self):
        tool = "go"
        tools_copy = tools.copy()

        tools_copy.update(self.setup_go_test(tool, tools_copy))

        self.perform_add_remove(tools_copy, tool, True, False)
        self.perform_add_remove(tools_copy, tool, False, True)

    def test_install_gobuster(self):
        tool = "gobuster"
        dependency = "go"
        tools_copy = tools.copy()
        tool_path = f"{self.shell.tools_dir}/mygo/bin/gobuster"

        tools_copy.update(self.setup_go_test(tool, tools_copy))

        tools_copy.get(tool)["dependencies"] = [dependency]
        tools_copy.get(tool).get("install_commands")[
            0
        ] = f"{tools_copy.get(dependency).get('path')} get github.com/OJ/gobuster"
        tools_copy.get(tool).get("uninstall_commands")[0] = f"rm {tool_path}"

        self.perform_add_remove(tools_copy, tool, True, False)
        self.perform_add_remove(tools_copy, tool, False, True)

    def pause_luigi(self):
        proc = subprocess.run("systemctl is-enabled luigid.service".split(), stdout=subprocess.PIPE)

        if proc.stdout.decode().strip() == "enabled":
            subprocess.run("sudo systemctl disable luigid.service".split())

        proc = subprocess.run("systemctl is-active luigid.service".split(), stdout=subprocess.PIPE)

        if proc.stdout.decode().strip() == "active":
            subprocess.run("sudo systemctl stop luigid.service".split())

    def test_install_luigi_service(self):
        luigi_service = Path("/lib/systemd/system/luigid.service")

        self.pause_luigi()

        if luigi_service.exists():
            subprocess.run(f"sudo rm {luigi_service}".split())

        tools_copy = tools.copy()
        pickle.dump(tools_copy, Path(self.shell.tools_dir / ".tool-dict.pkl").open("wb"))

        if Path("/usr/local/bin/luigid").exists():
            subprocess.run("sudo rm /usr/local/bin/luigid".split())

        assert (
            subprocess.run("systemctl is-enabled luigid.service".split(), stdout=subprocess.PIPE)
            .stdout.decode()
            .strip()
            != "enabled"
        )

        assert (
            subprocess.run("systemctl is-active luigid.service".split(), stdout=subprocess.PIPE).stdout.decode().strip()
            != "active"
        )

        assert not Path("/usr/local/bin/luigid").exists()

        utils.run_cmd(self.shell, "tools install luigi-service")

        assert Path("/lib/systemd/system/luigid.service").exists()

        proc = subprocess.run("systemctl is-enabled luigid.service".split(), stdout=subprocess.PIPE)
        assert proc.stdout.decode().strip() == "enabled"

        proc = subprocess.run("systemctl is-active luigid.service".split(), stdout=subprocess.PIPE)
        assert proc.stdout.decode().strip() == "active"

        assert Path("/usr/local/bin/luigid").exists()

        utils.run_cmd(self.shell, "tools uninstall luigi-service")

        proc = subprocess.run("systemctl is-enabled luigid.service".split(), stdout=subprocess.PIPE)
        assert proc.stdout.decode().strip() != "enabled"

        proc = subprocess.run("systemctl is-active luigid.service".split(), stdout=subprocess.PIPE)
        assert proc.stdout.decode().strip() != "active"

        assert luigi_service.exists() is False

    @pytest.mark.parametrize("test_input", ["install", "update"])
    def test_install_recursive_gobuster(self, test_input):
        tool = "recursive-gobuster"
        tools_copy = tools.copy()

        parent = f"{self.shell.tools_dir}/{tool}"
        tool_path = f"{parent}/recursive-gobuster.pyz"

        if test_input == "update":
            subprocess.run(f"git clone https://github.com/epi052/recursive-gobuster.git {parent}".split())

        tools_copy.get(tool)["path"] = tool_path
        tools_copy.get(tool)["dependencies"] = None

        tools_copy.get(tool).get("install_commands")[0] = f"bash -c 'if [ -d {parent} ]; "
        tools_copy.get(tool).get("install_commands")[0] += f"then cd {parent} && git fetch --all && git pull; "
        tools_copy.get(tool).get("install_commands")[
            0
        ] += "else git clone https://github.com/epi052/recursive-gobuster.git "
        tools_copy.get(tool).get("install_commands")[0] += f"{parent} ; fi'"
        tools_copy.get(tool).get("uninstall_commands")[0] = f"sudo rm -r {parent}"

        if test_input == "update":
            self.perform_add_remove(tools_copy, tool, True, True)
        else:
            self.perform_add_remove(tools_copy, tool, True, False)
            self.perform_add_remove(tools_copy, tool, False, True)

    @pytest.mark.parametrize("test_input", ["install", "update"])
    def test_install_searchsploit(self, test_input):
        tool = "searchsploit"
        tools_copy = tools.copy()

        home_path = f"{self.shell.tools_dir}/home"
        Path(home_path).mkdir(parents=True, exist_ok=True)

        copied_searchsploit_rc = f"{home_path}/.searchsploit_rc"

        dependency_path = f"{self.shell.tools_dir}/exploitdb"
        searchsploit_rc_path = f"{dependency_path}/.searchsploit_rc"
        tool_path = f"{dependency_path}/{tool}"

        sed_cmd = f"s#/opt#{self.shell.tools_dir}#g"

        if test_input == "update":
            subprocess.run(f"git clone https://github.com/offensive-security/exploitdb.git {dependency_path}".split())

        tools_copy.get(tool)["path"] = tool_path

        first_cmd = "bash -c 'if [ -d /usr/share/exploitdb ]; then ln -fs "
        first_cmd += f"/usr/share/exploitdb {dependency_path} && ln -fs $(which searchsploit) {tool_path}"
        first_cmd += f"; elif [ -d {dependency_path} ]; then cd {dependency_path} && git fetch --all && git pull; else "
        first_cmd += f"git clone https://github.com/offensive-security/exploitdb.git {dependency_path}; fi'"

        tools_copy.get(tool).get("install_commands")[0] = first_cmd

        tools_copy.get(tool).get("install_commands")[1] = f"bash -c 'if [ -f {searchsploit_rc_path} ]; "
        tools_copy.get(tool).get("install_commands")[1] += f"then cp -n {searchsploit_rc_path} {home_path} ; fi'"

        tools_copy.get(tool).get("install_commands")[2] = f"bash -c 'if [ -f {copied_searchsploit_rc} ]; "
        tools_copy.get(tool).get("install_commands")[2] += f"then sed -i {sed_cmd} {copied_searchsploit_rc}; fi'"

        tools_copy.get(tool).get("uninstall_commands")[0] = f"sudo rm -r {dependency_path}"

        pickle.dump(tools_copy, Path(self.shell.tools_dir / ".tool-dict.pkl").open("wb"))

        if test_input == "install":
            assert not Path(tool_path).exists()
            assert not Path(copied_searchsploit_rc).exists()
            assert not Path(dependency_path).exists()

        utils.run_cmd(self.shell, f"tools install {tool}")
        assert subprocess.run(f"grep {self.shell.tools_dir} {copied_searchsploit_rc}".split()).returncode == 0
        assert Path(copied_searchsploit_rc).exists()
        assert Path(dependency_path).exists()

        utils.run_cmd(self.shell, f"tools uninstall {tool}")
        assert Path(dependency_path).exists() is False

    @pytest.mark.parametrize("test_input", ["install", "update"])
    def test_install_seclists(self, test_input):
        tool = "seclists"
        tools_copy = tools.copy()

        tool_path = f"{self.shell.tools_dir}/seclists"

        tools_copy.get(tool)["path"] = tool_path

        if test_input == "update":
            subprocess.run(f"git clone https://github.com/danielmiessler/SecLists.git {tool_path}".split())

        first_cmd = f"bash -c 'if [ -d /usr/share/seclists ]; then ln -s /usr/share/seclists {tool_path}; elif "
        first_cmd += f"[[ -d {tool_path} ]] ; then cd {tool_path} && git fetch --all && git pull; "
        first_cmd += f"else git clone https://github.com/danielmiessler/SecLists.git {tool_path}; fi'"

        tools_copy.get(tool).get("install_commands")[0] = first_cmd
        tools_copy.get(tool).get("uninstall_commands")[0] = f"sudo rm -r {tool_path}"

        if test_input == "update":
            self.perform_add_remove(tools_copy, tool, True, True)
        else:
            self.perform_add_remove(tools_copy, tool, True, False)
            self.perform_add_remove(tools_copy, tool, False, True)

    def test_install_subjack(self):
        tool = "subjack"
        url = "github.com/haccer/subjack"
        tools_copy = tools.copy()
        tool_path = f"{self.shell.tools_dir}/mygo/bin/subjack"

        tools_copy.update(self.setup_go_test(tool, tools_copy))

        tools_copy.get(tool).get("install_commands")[0] = f"{tools_copy.get('go').get('path')} get {url}"
        tools_copy.get(tool).get("uninstall_commands")[0] = f"rm {tool_path}"

        self.perform_add_remove(tools_copy, tool, True, False)
        self.perform_add_remove(tools_copy, tool, False, True)

    def test_install_tkosubs(self):
        tool = "tko-subs"
        url = "github.com/anshumanbh/tko-subs"
        tools_copy = tools.copy()
        tool_path = f"{self.shell.tools_dir}/mygo/bin/tko-subs"

        tools_copy.update(self.setup_go_test(tool, tools_copy))

        tools_copy.get(tool).get("install_commands")[0] = f"{tools_copy.get('go').get('path')} get {url}"
        tools_copy.get(tool).get("uninstall_commands")[0] = f"rm {tool_path}"

        self.perform_add_remove(tools_copy, tool, True, False)
        self.perform_add_remove(tools_copy, tool, False, True)

    def test_install_waybackurls(self):
        tool = "waybackurls"
        url = "github.com/tomnomnom/waybackurls"
        tools_copy = tools.copy()
        tool_path = f"{self.shell.tools_dir}/mygo/bin/waybackurls"

        tools_copy.update(self.setup_go_test(tool, tools_copy))

        tools_copy.get(tool).get("install_commands")[0] = f"{tools_copy.get('go').get('path')} get {url}"
        tools_copy.get(tool).get("uninstall_commands")[0] = f"rm {tool_path}"

        self.perform_add_remove(tools_copy, tool, True, False)
        self.perform_add_remove(tools_copy, tool, False, True)

    def test_install_webanalyze(self):
        tool = "webanalyze"
        url = "github.com/rverton/webanalyze/..."
        tools_copy = tools.copy()
        tool_path = f"{self.shell.tools_dir}/mygo/bin/webanalyze"

        tools_copy.update(self.setup_go_test(tool, tools_copy))

        tools_copy.get(tool).get("install_commands")[0] = f"{tools_copy.get('go').get('path')} get {url}"
        tools_copy.get(tool).get("uninstall_commands")[0] = f"rm {tool_path}"

        self.perform_add_remove(tools_copy, tool, True, False)
        self.perform_add_remove(tools_copy, tool, False, True)
