from pathlib import Path

from pipeline.recon import TargetList


def test_creates_ips(tmp_path):
    targetfile = tmp_path / "test_targetlist"
    targetfile.write_text("127.0.0.1")

    tl = TargetList(target_file=str(targetfile), results_dir=str(tmp_path / "recon-results"))

    out = tl.output()

    assert out.path == str((tmp_path / "recon-results" / "target-results" / "ip_addresses").resolve())


def test_creates_domains(tmp_path):
    targetfile = tmp_path / "test_targetlist"
    targetfile.write_text("stuff.com")

    tl = TargetList(target_file=str(targetfile), results_dir=str(tmp_path / "recon-results"))
    out = tl.output()

    assert out.path == str((tmp_path / "recon-results" / "target-results" / "domains").resolve())


def test_filenotfound(tmp_path):

    tl = TargetList(target_file="doesnt_exist", results_dir="")
    out = tl.output()

    assert out is None


def test_results_dir_relative(tmp_path):
    targetfile = tmp_path / "test_targetlist"
    targetfile.write_text("stuff.com")

    tl = TargetList(target_file=str(targetfile), results_dir=str((tmp_path / ".." / tmp_path / "recon-results")))
    out = tl.output()

    assert out.path == str((tmp_path / "recon-results" / "target-results" / "domains").resolve())


def test_results_dir_absolute(tmp_path):
    targetfile = tmp_path / "test_targetlist"
    targetfile.write_text("stuff.com")

    tl = TargetList(target_file=str(targetfile), results_dir=str((tmp_path / "recon-results").resolve()))
    out = tl.output()

    assert out.path == str((tmp_path / "recon-results" / "target-results" / "domains").resolve())


def test_results_dir_empty(tmp_path):
    targetfile = tmp_path / "test_targetlist"
    targetfile.write_text("stuff.com")

    tl = TargetList(target_file=str(targetfile), results_dir="")
    out = tl.output()

    # different asserts used here because an empty string to results_dir causes Path() to use "." i.e. cwd
    # when running tests, this conflicts with tmp_path, but is only a problem during testing
    assert str(Path(out.path).parent.stem) == "target-results"
    assert Path(out.path).stem == "domains"
