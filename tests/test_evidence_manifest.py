"""Offline evidence module unit tests: no network and no external dependencies."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evidence_manifest.py"
spec = importlib.util.spec_from_file_location("evidence_manifest", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class EvidenceManifestTests(unittest.TestCase):
    def test_digest_and_manifest_do_not_expose_paths(self):
        with tempfile.TemporaryDirectory() as d:
            sample = Path(d) / "private.jpeg"
            sample.write_bytes(b"forensic fixture")
            result = mod.build_manifest([str(sample)], "Call 0413 336 332; test@example.com")
            item = result["items"][0]
            self.assertEqual(item["sha256"], mod.digest(sample))
            self.assertNotIn(d, json.dumps(result))
            self.assertNotIn("0413 336 332", json.dumps(result))
            self.assertNotIn("test@example.com", json.dumps(result))
    def test_cannot_replace_original(self):
        with tempfile.TemporaryDirectory() as d:
            sample = Path(d) / "source.txt"
            sample.write_text("original", encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), str(sample), "--output", str(sample)],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(sample.read_text(), "original")
    def test_new_output_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            sample, output = Path(d) / "source.png", Path(d) / "report.json"
            sample.write_bytes(b"img")
            output.write_text("protected")
            run = subprocess.run([sys.executable, str(SCRIPT), str(sample), "--output", str(output)],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(output.read_text(), "protected")
    def test_booking_redaction(self):
        self.assertNotIn("73531962185864", mod.redact("Reservation ID: 73531962185864"))

if __name__ == "__main__":
    unittest.main()
