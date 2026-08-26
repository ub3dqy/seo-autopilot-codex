from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source_env(*extra_paths: Path) -> dict[str, str]:
    env = dict(os.environ)
    paths = [str(ROOT / "src"), *(str(path) for path in extra_paths)]
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env["PYTHONNOUSERSITE"] = "1"
    return env


class SourceRuntimeVersionTests(unittest.TestCase):
    def test_source_layout_reports_version_without_installed_metadata(self) -> None:
        expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        completed = subprocess.run(
            [sys.executable, "-S", "-m", "seo_autopilot", "--version"],
            cwd=ROOT,
            env=source_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), f"seo-autopilot {expected}")
        self.assertNotIn("0+unknown", completed.stdout)

    def test_source_layout_version_overrides_stale_installed_metadata(self) -> None:
        expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as name:
            fake_site = Path(name)
            dist_info = fake_site / "seo_autopilot_codex-9.9.9.dist-info"
            dist_info.mkdir()
            (dist_info / "METADATA").write_text(
                "Metadata-Version: 2.1\nName: seo-autopilot-codex\nVersion: 9.9.9\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, "-S", "-m", "seo_autopilot", "--version"],
                cwd=ROOT,
                env=source_env(fake_site),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), f"seo-autopilot {expected}")
        self.assertNotIn("9.9.9", completed.stdout)

    def test_user_edition_contains_metadata_needed_for_direct_runtime(self) -> None:
        manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
        user_entries = manifest["editions"]["user"]
        self.assertIn("VERSION", user_entries)
        self.assertIn("release-manifest.json", user_entries)
        self.assertIn("policy-packs", user_entries)
        self.assertIn("schemas", user_entries)
        self.assertIn("src", user_entries)


if __name__ == "__main__":
    unittest.main()
