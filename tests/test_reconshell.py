import importlib
from pathlib import Path
from recon.config import tool_paths
import time

recon_pipeline = importlib.import_module("recon-pipeline")


def test_install_masscan():
    masscan = Path(tool_paths.get("masscan"))

    try:
        masscan.unlink()
    except FileNotFoundError:
        pass

    rs = recon_pipeline.ReconShell()
    rs.onecmd_plus_hooks("install masscan")

    for i in range(40):
        time.sleep(1)

    assert masscan.exists() is True
