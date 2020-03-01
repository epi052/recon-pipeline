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


def test_webtargets_creates_webtargets_txt(tmp_path):
    gwt = GatherWebTargets(target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100, db_location="")

    mass_pickle = tmp_path / "masscan.parsed.pickle"

    pickle.dump(test_dict, mass_pickle.open("wb"))

    input_dict["masscan-output"] = luigi.LocalTarget(mass_pickle)

    gwt.input = lambda: input_dict
    gwt.run()

    assert Path(gwt.output().path) == tmp_path / "target-results" / "webtargets.txt"


def test_webtargets_finds_all_web_targets_with_non_web_ports(tmp_path):
    gwt = GatherWebTargets(target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100, db_location="")

    mass_pickle = tmp_path / "masscan.parsed.pickle"

    pickle.dump(test_dict, mass_pickle.open("wb"))

    input_dict["masscan-output"] = luigi.LocalTarget(mass_pickle)

    gwt.input = lambda: input_dict
    gwt.run()

    contents = (Path(gwt.output().path)).read_text()

    for line in contents.splitlines():
        if ":" in line:
            assert line.split(":")[1] in web_ports
        else:
            assert line.strip() == "10.10.10.161"


def test_webtargets_finds_all_web_targets_with_multiple_targets(tmp_path):
    gwt = GatherWebTargets(target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100, db_location="")

    mass_pickle = Path(__file__).parent.parent / "data" / "recon-results" / "masscan-results" / "masscan.parsed.pickle"
    ipv4_addys = Path(__file__).parent.parent / "data" / "recon-results" / "target-results" / "ipv4_addresses"
    sumdomains_prod = Path(__file__).parent.parent / "data" / "recon-results" / "target-results" / "subdomains"
    ipv6_addys = Path(__file__).parent.parent / "data" / "recon-results" / "target-results" / "ipv6_addresses"

    input_dict["masscan-output"] = luigi.LocalTarget(mass_pickle)
    input_dict["amass-output"] = {
        "target-ips": luigi.LocalTarget(ipv4_addys),
        "target-ip6s": luigi.LocalTarget(sumdomains_prod),
        "target-subdomains": luigi.LocalTarget(ipv6_addys),
    }

    gwt.input = lambda: input_dict
    gwt.run()

    contents = (Path(gwt.output().path)).read_text()

    subdomains = [
        "blog.bitdiscovery.com",
        "bitdiscovery.com",
        "staging.bitdiscovery.com",
        "tenable.bitdiscovery.com",
        "ibm.bitdiscovery.com",
    ]

    ips = [
        "13.225.54.22",
        "13.57.162.100",
        "52.53.92.161",
        "104.20.61.51",
        "54.183.32.157",
        "104.20.60.51",
        "13.225.54.58",
        "13.225.54.41",
        "52.9.23.177",
        "13.225.54.100",
    ]

    ip6s = ["2606:4700:10::6814:3c33", "2606:4700:10::6814:3d33"]

    for line in contents.splitlines():
        if "." in line and ":" in line:  # ipv4 w/ port
            tgt, port = line.split(":")
            assert port in web_ports and tgt in ips
        elif ":" in line:  # ipv6
            assert line.strip() in ip6s
        else:  # domain or bare ip
            try:
                # bare ip
                ipaddress.ip_interface(line.strip())
                assert line.strip() in ips
            except ValueError:
                # domain
                assert line.strip() in subdomains
