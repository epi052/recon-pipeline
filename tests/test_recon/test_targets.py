from pipeline.recon import TargetList


def test_creates_ips(tmp_path):
    targetfile = tmp_path / "test_targetlist"
    targetdb = tmp_path / "testing.sqlite"
    targetfile.write_text("127.0.0.1")

    tl = TargetList(target_file=str(targetfile), results_dir=str(tmp_path / "recon-results"), db_location=str(targetdb))

    out = tl.output()
    assert out.exists()
