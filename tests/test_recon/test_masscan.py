import pickle
from pathlib import Path

from pipeline.recon import ParseMasscanOutput, MasscanScan

tfp = "../data/bitdiscovery"
tf = Path(tfp).stem
el = "../data/blacklist"
rd = "../data/recon-results"

test_dict = {
    "104.20.60.51": {"tcp": {"8443", "443"}},
    "104.20.61.51": {"tcp": {"8080", "80", "443"}},
    "13.225.54.100": {"tcp": {"443"}},
    "13.225.54.22": {"tcp": {"80"}},
    "52.53.92.161": {"tcp": {"443", "80"}},
    "52.9.23.177": {"tcp": {"80"}},
}


def test_massscan_output_location(tmp_path):
    asc = MasscanScan(target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100)

    assert asc.output().path == str(Path(tmp_path) / "masscan-results" / "masscan.json")


def test_parsemassscan_output_location(tmp_path):
    pmo = ParseMasscanOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100)

    assert pmo.output().path == str(Path(tmp_path) / "masscan-results" / "masscan.parsed.pickle")


def test_parsemassscan_output_dictionary(tmp_path):
    ip_dict = pickle.load(
        (Path(__file__).parent.parent / "data" / "recon-results" / "masscan-results" / "masscan.parsed.pickle").open(
            "rb"
        )
    )

    for ip, proto_dict in test_dict.items():
        for proto, ports in proto_dict.items():
            assert not ip_dict.get(ip).get(proto).difference(ports)
