# Offline evidence manifest (Android Termux compatible)

This standalone Python 3.9+ tool hashes user-owned files **locally** and writes a privacy-minimised JSON manifest. It does not connect to Stayz, access reservations, run reconnaissance scanners, or transmit images. It deliberately does not assert that an image or booking is genuine.

## Termux setup

Install Termux from F-Droid or the official Termux GitHub release, then:

```sh
pkg update && pkg upgrade
pkg install python git
termux-setup-storage
git clone https://github.com/jamietatebenger-lab/recon-pipeline.git
cd recon-pipeline
git fetch origin feature/offline-evidence-20261014
git switch feature/offline-evidence-20261014
python -m unittest discover -s tests -p test_evidence_manifest.py -v
mkdir -p "$HOME/evidence-reports"
python scripts/evidence_manifest.py "$HOME/storage/downloads/example.png" --output "$HOME/evidence-reports/manifest.json"
```

Replace `example.png` with your own file name, using quoted file paths. If the source is sensitive, copy it into the private Termux home directory before processing.

## Security and evidence limitations

Keep original files unchanged; record collection date, source device, acquisition method, timezone, and permissions separately in a protected case log. The manifest does not include original filenames or absolute paths. Analyst notes are filtered for common Australian phone numbers, emails and booking IDs, but redaction is not comprehensive: **do not enter secrets or identifying free text into notes**. The output may still be sensitive, especially if linked to originals. Store reports outside this public Git repository. Hashes confirm byte-level integrity, not identity, truthfulness, occupancy or admissibility.

The main recon-pipeline's dependency profile targets Python 3.13 and includes third-party tooling that may be unsupported on Termux. This evidence module needs only Python and avoids pipenv entirely.
