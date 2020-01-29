import pickle
from pathlib import Path
from recon.masscan import ParseMasscanOutput, MasscanScan

tfp = "../data/bitdiscovery"
tf = Path(tfp).stem
el = "../data/blacklist"
rd = "../data/recon-results"

ips = []

test_dict = {
    "104.20.60.51": {"tcp": {"443", "2086", "80", "2087", "8443"}},
    "13.57.162.100": {"tcp": {"443"}},
    "13.57.96.172": {"tcp": {"80", "443"}},
    "104.20.61.51": {"tcp": {"8080", "80"}},
}


def test_massscan_output_location(tmp_path):
    asc = MasscanScan(
        target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100
    )

    assert asc.output().path == str(Path(tmp_path) / f"masscan.{tf}.json")


def test_parsemassscan_output_location(tmp_path):
    pmo = ParseMasscanOutput(
        target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100
    )

    assert pmo.output().path == str(Path(tmp_path) / f"masscan.{tf}.parsed.pickle")


def test_parsemassscan_output_dictionary(tmp_path):
    # pmo = ParseMasscanOutput(
    # target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100
    # )

    # masscan_results = (
    #     Path(__file__) / ".." / ".." / "data" / "recon-results" / f"masscan.{tf}.json"
    # )
    # shutil.copy(masscan_results.resolve(), tmp_path)
    ip_dict = pickle.load(
        (
            Path(__file__).parent.parent
            / "data"
            / "recon-results"
            / f"masscan.{tf}.parsed.pickle"
        ).open("rb")
    )

    for ip, proto_dict in test_dict.items():
        for proto, ports in proto_dict.items():
            assert not ip_dict.get(ip).get(proto).difference(ports)
