import shutil
import importlib
import subprocess
from pathlib import Path

from ..utils import setup_install_test, run_cmd, is_kali
from recon.config import tool_paths

recon_pipeline = importlib.import_module("recon-pipeline")


def test_install_masscan():
    masscan = Path(tool_paths.get("masscan"))

    setup_install_test(masscan)

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install masscan")

    assert masscan.exists() is True


def test_install_amass():
    setup_install_test()

    if not is_kali():
        return True

    if shutil.which("amass") is not None:
        subprocess.run("sudo apt remove amass -y".split())

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install amass")

    assert shutil.which("amass") is not None


def test_install_pipenv():
    setup_install_test()

    if not is_kali():
        return True

    if shutil.which("pipenv") is not None:
        subprocess.run("sudo apt remove pipenv -y".split())

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install pipenv")

    assert shutil.which("pipenv") is not None


def test_install_luigi():
    setup_install_test()

    if shutil.which("luigi") is not None:
        subprocess.run("pipenv uninstall luigi".split())

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install luigi")

    assert shutil.which("luigi") is not None


def test_install_aquatone():
    aquatone = Path(tool_paths.get("aquatone"))

    setup_install_test(aquatone)

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install aquatone")

    assert aquatone.exists() is True


def test_install_gobuster():
    gobuster = Path(tool_paths.get("gobuster"))

    setup_install_test(gobuster)

    assert shutil.which("go") is not None

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install gobuster")

    assert gobuster.exists() is True


def test_install_tkosubs():
    tkosubs = Path(tool_paths.get("tko-subs"))

    setup_install_test(tkosubs)

    assert shutil.which("go") is not None

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install tko-subs")

    assert tkosubs.exists() is True


def test_install_subjack():
    subjack = Path(tool_paths.get("subjack"))

    setup_install_test(subjack)

    assert shutil.which("go") is not None

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install subjack")

    assert subjack.exists() is True


def test_install_webanalyze():
    webanalyze = Path(tool_paths.get("webanalyze"))

    setup_install_test(webanalyze)

    assert shutil.which("go") is not None

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install webanalyze")

    assert webanalyze.exists() is True


def test_install_corscanner():
    corscanner = Path(tool_paths.get("CORScanner"))

    setup_install_test(corscanner)

    if corscanner.parent.exists():
        shutil.rmtree(corscanner.parent)

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install corscanner")

    assert corscanner.exists() is True


def test_update_corscanner():
    corscanner = Path(tool_paths.get("CORScanner"))

    setup_install_test()

    if not corscanner.parent.exists():
        subprocess.run(
            f"sudo git clone https://github.com/chenjj/CORScanner.git {corscanner.parent}".split()
        )

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install corscanner")

    assert corscanner.exists() is True


def test_install_recursive_gobuster():
    recursive_gobuster = Path(tool_paths.get("recursive-gobuster"))

    setup_install_test(recursive_gobuster)

    if recursive_gobuster.parent.exists():
        shutil.rmtree(recursive_gobuster.parent)

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install recursive-gobuster")

    assert recursive_gobuster.exists() is True


def test_update_recursive_gobuster():
    recursive_gobuster = Path(tool_paths.get("recursive-gobuster"))

    setup_install_test()

    if not recursive_gobuster.parent.exists():
        subprocess.run(
            f"sudo git clone https://github.com/epi052/recursive-gobuster.git {recursive_gobuster.parent}".split()
        )

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install recursive-gobuster")

    assert recursive_gobuster.exists() is True


def test_install_luigi_service():
    luigi_service = Path("/lib/systemd/system/luigid.service")

    setup_install_test(luigi_service)

    proc = subprocess.run("systemctl is-enabled luigid.service".split(), stdout=subprocess.PIPE)

    if proc.stdout.decode().strip() == "enabled":
        subprocess.run("systemctl disable luigid.service".split())

    proc = subprocess.run("systemctl is-active luigid.service".split(), stdout=subprocess.PIPE)

    if proc.stdout.decode().strip() == "active":
        subprocess.run("systemctl stop luigid.service".split())

    if Path("/usr/local/bin/luigid").exists():
        Path("/usr/local/bin/luigid").unlink()

    rs = recon_pipeline.ReconShell()

    run_cmd(rs, "install luigi-service")

    assert Path("/lib/systemd/system/luigid.service").exists()

    proc = subprocess.run("systemctl is-enabled luigid.service".split(), stdout=subprocess.PIPE)
    assert proc.stdout.decode().strip() == "enabled"

    proc = subprocess.run("systemctl is-active luigid.service".split(), stdout=subprocess.PIPE)
    assert proc.stdout.decode().strip() == "active"

    assert Path("/usr/local/bin/luigid").exists()
