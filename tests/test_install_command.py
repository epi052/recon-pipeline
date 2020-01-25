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

    print(script_out)
    print(script_err)

    assert masscan.exists() is True


def test_install_amass():
    utils.setup_install_test()

    if not utils.is_kali():
        return True

    subprocess.run("sudo apt remove amass -y".split())

    rs = recon_pipeline.ReconShell()

    script_out, script_err = utils.run_cmd(rs, "install amass")

    assert shutil.which("amass") is not None
