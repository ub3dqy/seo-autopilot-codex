from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseTests(unittest.TestCase):
    def test_version_is_single_sourced(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version_file"], "VERSION")
        self.assertNotIn("version", manifest)
        self.assertIn("{version}", manifest["artifacts"]["user"])
        self.assertRegex(version, r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")

    def test_opaque_source_bundle_is_not_part_of_the_source_tree(self) -> None:
        self.assertFalse((ROOT / "packages" / "source-bundle-v1.4.0").exists())

    def test_source_verification_and_deterministic_archives(self) -> None:
        command = [sys.executable, "prepare_editions.py"]
        try:
            subprocess.run([*command, "--verify-only"], cwd=ROOT, check=True, capture_output=True, text=True)
            subprocess.run([*command, "--build-zips", "--force"], cwd=ROOT, check=True, capture_output=True, text=True)
            first_report = json.loads((ROOT / "dist" / "release-build.json").read_text(encoding="utf-8"))
            first = {item["filename"]: item["sha256"] for item in first_report["artifacts"]}
            subprocess.run([*command, "--build-zips"], cwd=ROOT, check=True, capture_output=True, text=True)
            second_report = json.loads((ROOT / "dist" / "release-build.json").read_text(encoding="utf-8"))
            second = {item["filename"]: item["sha256"] for item in second_report["artifacts"]}
            self.assertEqual(first, second)
            for filename, expected in second.items():
                archive = ROOT / "dist" / filename
                self.assertEqual(digest(archive), expected)
                with zipfile.ZipFile(archive) as handle:
                    names = handle.namelist()
                    self.assertTrue(any(name.endswith("/README.md") for name in names))
                    self.assertFalse(any("source-bundle" in name for name in names))
        finally:
            subprocess.run([*command, "--clean", "--force"], cwd=ROOT, check=False, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
