import pickle
import ipaddress
from pathlib import Path

import luigi

from pipeline.recon import web_ports
from pipeline.recon.web import GatherWebTargets

test_dict = {
    "10.10.10.161": {
        "tcp": {
            "135",
            "139",
            "3268",
            "3269",
            "389",
            "445",
            "464",
            "47001",
            "49664",
            "49665",
            "49666",
            "49667",
            "49671",
            "49676",
            "49677",
            "49684",
            "49703",
            "49903",
            "53",
            "593",
            "5985",
            "636",
            "88",
            "9389",
            "80",
            "443",
            "8080",
        }
    }
}

tfp = "../data/bitdiscovery"
tf = Path(tfp).stem
el = "../data/blacklist"
rd = "../data/recon-results"

input_dict = {"masscan-output": None, "amass-output": {}}


def test_webtargets_creates_webtargets(tmp_path):
    gwt = GatherWebTargets(
        target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100, db_location="testing.sqlite"
    )

    mass_pickle = tmp_path / "masscan.parsed.pickle"

    pickle.dump(test_dict, mass_pickle.open("wb"))

    input_dict["masscan-output"] = luigi.LocalTarget(mass_pickle)

    gwt.input = lambda: input_dict
    gwt.run()

    assert gwt.output().exists()
