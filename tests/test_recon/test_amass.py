import ipaddress
from pathlib import Path

import luigi

from recon.amass import ParseAmassOutput, AmassScan

tfp = "../data/bitdiscovery"
tf = Path(tfp).stem
el = "../data/blacklist"
rd = "../data/recon-results"
ips = [
    "13.225.54.58",
    "13.225.54.100",
    "13.225.54.22",
    "13.225.54.41",
    "13.57.162.100",
    "52.9.23.177",
    "52.53.92.161",
    "54.183.32.157",
    "54.183.32.157",
    "52.53.92.161",
    "52.53.92.161",
    "54.183.32.157",
    "104.20.60.51",
    "104.20.61.51",
    "104.20.61.51",
    "104.20.60.51",
]
ip6s = [
    "2606:4700:10::6814:3c33",
    "2606:4700:10::6814:3d33",
    "2606:4700:10::6814:3d33",
    "2606:4700:10::6814:3c33",
]
subdomains = [
    "blog.bitdiscovery.com",
    "bitdiscovery.com",
    "staging.bitdiscovery.com",
    "ibm.bitdiscovery.com",
    "tenable.bitdiscovery.com",
]

amass_json = Path(__file__).parent.parent / "data" / "recon-results" / "amass-results" / "amass.json"


def test_amassscan_output_location(tmp_path):
    asc = AmassScan(target_file=tf, exempt_list=el, results_dir=str(tmp_path))

    assert asc.output().path == str(Path(tmp_path) / "amass-results" / "amass.json")


def test_parse_amass_output_locations(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))

    assert pao.output().get("target-ips").path == str((Path(tmp_path) / "target-results" / "ipv4_addresses").resolve())
    assert pao.output().get("target-ip6s").path == str((Path(tmp_path) / "target-results" / "ipv6_addresses").resolve())
    assert pao.output().get("target-subdomains").path == str(
        (Path(tmp_path) / "target-results" / "subdomains").resolve()
    )


def test_parse_amass_ip_results_only_contain_ipv4_addys(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))

    pao.input = lambda: luigi.LocalTarget(amass_json)
    pao.run()

    contents = (Path(pao.output().get("target-ips").path)).read_text()

    for line in contents.split():
        try:
            ipaddress.ip_interface(line.strip())  # is it a valid ip/network?
        except ValueError:
            assert 0


def test_parse_amass_ip6_results_only_contain_ipv6_addys(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))

    pao.input = lambda: luigi.LocalTarget(amass_json)
    pao.run()

    contents = (Path(pao.output().get("target-ip6s").path)).read_text()

    for line in contents.split():
        try:
            ipaddress.ip_interface(line.strip())  # is it a valid ip/network?
        except ValueError:
            assert 0


def test_parse_amass_subdomain_results_only_contain_domains(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))

    pao.input = lambda: luigi.LocalTarget(amass_json)
    pao.run()

    contents = (Path(pao.output().get("target-subdomains").path)).read_text()

    for line in contents.split():
        try:
            ipaddress.ip_interface(line.strip())  # is it a valid ip/network?
        except ValueError:
            continue
        assert 0


def test_parse_amass_ip_results(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))

    pao.input = lambda: luigi.LocalTarget(amass_json)
    pao.run()

    contents = (Path(pao.output().get("target-ips").path)).read_text()

    for line in contents.split():
        assert line.strip() in ips


def test_parse_amass_ip6_results(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))

    pao.input = lambda: luigi.LocalTarget(amass_json)
    pao.run()

    contents = (Path(pao.output().get("target-ip6s").path)).read_text()

    for line in contents.split():
        assert line.strip() in ip6s


def test_parse_amass_subdomain_results(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))

    pao.input = lambda: luigi.LocalTarget(amass_json)
    pao.run()

    contents = (Path(pao.output().get("target-subdomains").path)).read_text()
    print((Path(pao.output().get("target-subdomains").path)))
    print(contents)

    for line in contents.split():
        assert line.strip() in subdomains
