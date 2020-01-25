import shutil
import importlib
import subprocess
from pathlib import Path

import utils
from recon.config import tool_paths

recon_pipeline = importlib.import_module("recon-pipeline")


def test_install_masscan():
    masscan = Path(tool_paths.get("masscan"))

    utils.setup_install_test(masscan)

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install masscan")

    assert masscan.exists() is True


def test_install_amass():
    utils.setup_install_test()

    if not utils.is_kali():
        return True

    if shutil.which("amass") is not None:
        subprocess.run("sudo apt remove amass -y".split())

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install amass")

    assert shutil.which("amass") is not None


def test_install_pipenv():
    utils.setup_install_test()

    if not utils.is_kali():
        return True

    if shutil.which("pipenv") is not None:
        subprocess.run("sudo apt remove pipenv -y".split())

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install pipenv")

    assert shutil.which("pipenv") is not None


def test_install_luigi():
    utils.setup_install_test()

    if shutil.which("luigi") is not None:
        subprocess.run("pipenv uninstall luigi".split())

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install luigi")

    assert shutil.which("luigi") is not None


def test_install_aquatone():
    aquatone = Path(tool_paths.get("aquatone"))

    utils.setup_install_test(aquatone)

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install aquatone")

    assert aquatone.exists() is True


def test_install_gobuster():
    gobuster = Path(tool_paths.get("gobuster"))

    utils.setup_install_test(gobuster)

    assert shutil.which("go") is not None

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install gobuster")

    assert gobuster.exists() is True


def test_install_tkosubs():
    tkosubs = Path(tool_paths.get("tko-subs"))

    utils.setup_install_test(tkosubs)

    assert shutil.which("go") is not None

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install tko-subs")

    assert tkosubs.exists() is True


def test_install_subjack():
    subjack = Path(tool_paths.get("subjack"))

    utils.setup_install_test(subjack)

    assert shutil.which("go") is not None

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install subjack")

    assert subjack.exists() is True


def test_install_webanalyze():
    webanalyze = Path(tool_paths.get("webanalyze"))

    utils.setup_install_test(webanalyze)

    assert shutil.which("go") is not None

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install webanalyze")

    assert webanalyze.exists() is True


def test_install_corscanner():
    corscanner = Path(tool_paths.get("CORScanner"))

    utils.setup_install_test(corscanner)

    if corscanner.parent.exists():
        shutil.rmtree(corscanner.parent)

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install corscanner")

    assert corscanner.exists() is True
