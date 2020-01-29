import shutil
import ipaddress
from pathlib import Path
from recon.amass import ParseAmassOutput, AmassScan

tfp = "../data/bitdiscovery"
tf = Path(tfp).stem
el = "../data/blacklist"
rd = "../data/recon-results"
ips = [
    "99.84.251.19",
    "99.84.251.119",
    "99.84.251.33",
    "99.84.251.117",
    "13.57.96.172",
    "54.193.13.152",
    "52.9.23.177",
    "13.57.162.100",
    "13.57.96.172",
    "54.193.13.152",
    "54.193.13.152",
    "13.57.96.172",
    "104.20.61.51",
    "104.20.60.51",
]
ip6s = [
    "2606:4700:10::6814:3c33",
    "2606:4700:10::6814:3d33",
]
subdomains = [
    "blog.bitdiscovery.com",
    "bitdiscovery.com",
    "staging.bitdiscovery.com",
    "ibm.bitdiscovery.com",
    "tenable.bitdiscovery.com",
    "email.assetinventory.bugcrowd.com",
]


def test_amassscan_output_location(tmp_path):
    asc = AmassScan(target_file=tf, exempt_list=el, results_dir=str(tmp_path))

    assert asc.output().path == str(Path(tmp_path) / f"amass.{tf}.json")


def test_parse_amass_output_locations(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))

    assert pao.output().get("target-ips").path == str(
        (Path(tmp_path) / tf).with_suffix(".ips").resolve()
    )
    assert pao.output().get("target-ip6s").path == str(
        (Path(tmp_path) / tf).with_suffix(".ip6s").resolve()
    )
    assert pao.output().get("target-subdomains").path == str(
        (Path(tmp_path) / tf).with_suffix(".subdomains").resolve()
    )


def test_parse_amass_ip_results_only_contain_ipv4_addys(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))
    amass_json = (
        Path(__file__) / ".." / ".." / "data" / "recon-results" / f"amass.{tf}.json"
    )
    shutil.copy(amass_json.resolve(), tmp_path)
    pao.run()
    contents = (Path(tmp_path) / tf).with_suffix(".ips").read_text()
    for line in contents.split():
        try:
            ipaddress.ip_interface(line.strip())  # is it a valid ip/network?
        except ValueError:
            assert 0


def test_parse_amass_ip6_results_only_contain_ipv6_addys(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))
    amass_json = (
        Path(__file__) / ".." / ".." / "data" / "recon-results" / f"amass.{tf}.json"
    )
    shutil.copy(amass_json.resolve(), tmp_path)
    pao.run()
    contents = (Path(tmp_path) / tf).with_suffix(".ip6s").read_text()
    for line in contents.split():
        try:
            ipaddress.ip_interface(line.strip())  # is it a valid ip/network?
        except ValueError:
            assert 0


def test_parse_amass_subdomain_results_only_contain_domains(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))
    amass_json = (
        Path(__file__) / ".." / ".." / "data" / "recon-results" / f"amass.{tf}.json"
    )
    shutil.copy(amass_json.resolve(), tmp_path)
    pao.run()
    contents = (Path(tmp_path) / tf).with_suffix(".subdomains").read_text()
    for line in contents.split():
        try:
            ipaddress.ip_interface(line.strip())  # is it a valid ip/network?
        except ValueError:
            continue
        assert 0


def test_parse_amass_ip_results(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))
    amass_json = (
        Path(__file__) / ".." / ".." / "data" / "recon-results" / f"amass.{tf}.json"
    )
    shutil.copy(amass_json.resolve(), tmp_path)
    pao.run()
    contents = (Path(tmp_path) / tf).with_suffix(".ips").read_text()

    for line in contents.split():
        assert line.strip() in ips


def test_parse_amass_ip6_results(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))
    amass_json = (
        Path(__file__) / ".." / ".." / "data" / "recon-results" / f"amass.{tf}.json"
    )
    shutil.copy(amass_json.resolve(), tmp_path)
    pao.run()
    contents = (Path(tmp_path) / tf).with_suffix(".ip6s").read_text()
    for line in contents.split():
        assert line.strip() in ip6s


def test_parse_amass_subdomain_results(tmp_path):
    pao = ParseAmassOutput(target_file=tf, exempt_list=el, results_dir=str(tmp_path))
    amass_json = (
        Path(__file__) / ".." / ".." / "data" / "recon-results" / f"amass.{tf}.json"
    )
    shutil.copy(amass_json.resolve(), tmp_path)
    pao.run()
    contents = (Path(tmp_path) / tf).with_suffix(".subdomains").read_text()
    for line in contents.split():
        assert line.strip() in subdomains
