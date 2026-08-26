from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
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
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
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
                    if "-user-" in filename:
                        self.assertTrue(any(name.endswith("/release-manifest.json") for name in names))
                    with tempfile.TemporaryDirectory() as temp_name:
                        handle.extractall(temp_name)
                        extracted = Path(temp_name) / filename.removesuffix(".zip")
                        env = dict(os.environ)
                        env["PYTHONPATH"] = str(extracted / "src")
                        env["PYTHONNOUSERSITE"] = "1"

                        completed = subprocess.run(
                            [sys.executable, "-S", "-m", "seo_autopilot", "--version"],
                            cwd=extracted,
                            env=env,
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                            check=False,
                        )
                        self.assertEqual(completed.returncode, 0, completed.stderr)
                        self.assertEqual(completed.stdout.strip(), f"seo-autopilot {version}")
                        self.assertNotIn("0+unknown", completed.stdout)

                        site = Path(temp_name) / "scope-site"
                        public = site / "public"
                        public.mkdir(parents=True)
                        (site / "package.json").write_text(
                            '{"dependencies":{"next":"15.0.0","react":"19.0.0"}}\n',
                            encoding="utf-8",
                        )
                        (public / "index.html").write_text(
                            "<!doctype html><html lang=\"ru\"><head>"
                            "<title>Current</title>"
                            "<meta name=\"description\" content=\"Current description\">"
                            "<link rel=\"canonical\" href=\"https://example.invalid/\">"
                            "</head><body><h1>Current</h1></body></html>\n",
                            encoding="utf-8",
                        )
                        (public / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
                        (public / "sitemap.xml").write_text("<urlset/>\n", encoding="utf-8")
                        archived = site / "artifacts" / "old"
                        archived.mkdir(parents=True)
                        (archived / "old.html").write_text("<html><body>Old</body></html>\n", encoding="utf-8")
                        (site / "tmp").mkdir()
                        (site / "tmp" / "old.html").write_text("<html><body>Old</body></html>\n", encoding="utf-8")
                        profile = site / "artifacts" / "runtime" / "chrome-profile" / "Default"
                        profile.mkdir(parents=True)
                        for profile_file in ("Cookies", "History", "Login Data"):
                            (profile / profile_file).write_text("private-fixture", encoding="utf-8")

                        scope = subprocess.run(
                            [sys.executable, "-S", "-m", "seo_autopilot", "scope", str(site), "--json"],
                            cwd=extracted,
                            env=env,
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                            check=False,
                        )
                        self.assertEqual(scope.returncode, 1, scope.stderr or scope.stdout)
                        scope_payload = json.loads(scope.stdout)
                        self.assertEqual(scope_payload["status"], "REVIEW_REQUIRED")
                        self.assertEqual(scope_payload["html_scope"]["selected_paths"], ["public/index.html"])
                        self.assertFalse(scope_payload["privacy"]["contents_read"])
                        self.assertTrue(scope_payload["privacy"]["sensitive_paths"])

                        output = Path(temp_name) / "audit-output"
                        audit = subprocess.run(
                            [
                                sys.executable,
                                "-S",
                                "-m",
                                "seo_autopilot",
                                "audit",
                                str(site),
                                "--output",
                                str(output),
                            ],
                            cwd=extracted,
                            env=env,
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                            check=False,
                        )
                        self.assertEqual(audit.returncode, 0, audit.stderr or audit.stdout)
                        run_payload = json.loads((output / "run.json").read_text(encoding="utf-8"))
                        self.assertEqual(run_payload["findings"], [])
                        self.assertEqual(run_payload["planned_fixes"], [])
                        self.assertFalse(
                            any(
                                item.get("path", "").startswith(("artifacts/", "tmp/"))
                                for item in run_payload["findings"]
                            )
                        )
                        verify = subprocess.run(
                            [sys.executable, "-S", "-m", "seo_autopilot", "verify", str(output / "run.json")],
                            cwd=extracted,
                            env=env,
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                            check=False,
                        )
                        self.assertEqual(verify.returncode, 0, verify.stderr or verify.stdout)
        finally:
            subprocess.run([*command, "--clean", "--force"], cwd=ROOT, check=False, capture_output=True, text=True)

    def test_release_gate_reseals_dist_after_sbom_mutation(self) -> None:
        command = [sys.executable, "prepare_editions.py"]
        try:
            subprocess.run([*command, "--build-zips", "--force"], cwd=ROOT, check=True, capture_output=True, text=True)
            dist = ROOT / "dist"
            synthetic = dist / "synthetic.spdx.json"
            synthetic.write_text('{"spdxVersion":"SPDX-2.3"}\n', encoding="utf-8")
            sums = dist / "SHA256SUMS"
            sums.write_text(
                sums.read_text(encoding="utf-8")
                + f"{digest(synthetic)}  {synthetic.name}\n",
                encoding="utf-8",
            )
            stale = subprocess.run([*command, "--verify-only"], cwd=ROOT, check=False, capture_output=True, text=True)
            self.assertNotEqual(stale.returncode, 0)

            sys.path.insert(0, str(ROOT))
            try:
                from scripts.verify_local import seal_dist_marker
                seal_dist_marker()
            finally:
                sys.path.pop(0)

            verified = subprocess.run([*command, "--verify-only"], cwd=ROOT, check=False, capture_output=True, text=True)
            self.assertEqual(verified.returncode, 0, verified.stderr or verified.stdout)
        finally:
            subprocess.run([*command, "--clean", "--force"], cwd=ROOT, check=False, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
