from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from seo_autopilot.entrypoint import main as entrypoint_main
from seo_autopilot.scope import inspect_scope
from seo_autopilot.utils import select_files


class AuditScopeTests(unittest.TestCase):
    def test_generated_noise_is_excluded_and_browser_profiles_are_not_read(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "SEO Scope Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "scope-test@localhost.invalid"], cwd=root, check=True)

            (root / "package.json").write_text(
                '{"dependencies":{"next":"15.0.0","react":"19.0.0"}}\n',
                encoding="utf-8",
            )
            (root / "public").mkdir()
            (root / "public" / "index.html").write_text("<html></html>\n", encoding="utf-8")

            (root / "artifacts" / "snapshot").mkdir(parents=True)
            (root / "artifacts" / "snapshot" / "index.html").write_text("<html></html>\n", encoding="utf-8")
            (root / "tmp").mkdir()
            (root / "tmp" / "old.html").write_text("<html></html>\n", encoding="utf-8")

            (root / "legacy").mkdir()
            (root / "legacy" / "copy.html").write_text("<html></html>\n", encoding="utf-8")
            (root / ".seo-autopilotignore").write_text("legacy/**\n", encoding="utf-8")

            (root / "ignored-export").mkdir()
            (root / "ignored-export" / "ignored.html").write_text("<html></html>\n", encoding="utf-8")
            (root / ".gitignore").write_text("ignored-export/\n", encoding="utf-8")

            profile = root / "artifacts" / "runtime-bundler" / "chrome-profile" / "Default"
            profile.mkdir(parents=True)
            for filename in ("Cookies", "Login Data", "History"):
                path = profile / filename
                path.write_text("must-not-be-read", encoding="utf-8")
                try:
                    os.chmod(path, 0)
                except OSError:
                    pass

            subprocess.run(
                [
                    "git",
                    "add",
                    "public/index.html",
                    "package.json",
                    ".gitignore",
                    ".seo-autopilotignore",
                ],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "commit", "-m", "scope fixture"], cwd=root, check=True, capture_output=True)

            selection = select_files(root, (".html", ".htm"))
            selected = [path.relative_to(root).as_posix() for path in selection.files]
            self.assertEqual(selected, ["public/index.html"])
            self.assertIn("artifacts", selection.pruned_directories)
            self.assertIn("tmp", selection.pruned_directories)
            self.assertTrue(selection.gitignore_applied)
            self.assertEqual(selection.ignore_file, ".seo-autopilotignore")
            self.assertTrue(any("chrome-profile" in path for path in selection.sensitive_paths))

            payload = inspect_scope(root)
            self.assertEqual(payload["status"], "REVIEW_REQUIRED")
            self.assertEqual(payload["stack"], "nextjs")
            self.assertFalse(payload["privacy"]["contents_read"])
            self.assertEqual(payload["html_scope"]["selected_paths"], ["public/index.html"])

    def test_ignore_negation_reincludes_a_selected_file(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "legacy").mkdir()
            (root / "legacy" / "keep.html").write_text("keep\n", encoding="utf-8")
            (root / "legacy" / "drop.html").write_text("drop\n", encoding="utf-8")
            (root / ".seo-autopilotignore").write_text(
                "legacy/**\n!legacy/keep.html\n",
                encoding="utf-8",
            )

            selection = select_files(root, (".html",))
            selected = [path.relative_to(root).as_posix() for path in selection.files]
            self.assertEqual(selected, ["legacy/keep.html"])

    def test_ignore_negation_can_reinclude_a_default_artifacts_subtree(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "artifacts" / "current").mkdir(parents=True)
            (root / "artifacts" / "old").mkdir(parents=True)
            (root / "artifacts" / "current" / "index.html").write_text("current\n", encoding="utf-8")
            (root / "artifacts" / "old" / "index.html").write_text("old\n", encoding="utf-8")
            (root / ".seo-autopilotignore").write_text(
                "!artifacts/current/**\n",
                encoding="utf-8",
            )

            selection = select_files(root, (".html",))
            selected = [path.relative_to(root).as_posix() for path in selection.files]
            self.assertEqual(selected, ["artifacts/current/index.html"])

    def test_framework_without_in_scope_html_is_ready_with_limitations(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "package.json").write_text(
                '{"dependencies":{"next":"15.0.0","react":"19.0.0"}}\n',
                encoding="utf-8",
            )
            (root / "artifacts").mkdir()
            (root / "artifacts" / "snapshot.html").write_text("<html></html>\n", encoding="utf-8")

            payload = inspect_scope(root)
            self.assertEqual(payload["status"], "READY_WITH_LIMITATIONS")
            self.assertEqual(payload["html_scope"]["selected_files"], 0)
            self.assertTrue(payload["limitations"])

    def test_unified_cli_exposes_scope_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "index.html").write_text("<html></html>\n", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                code = entrypoint_main(["scope", str(root), "--json"])
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "READY")
            self.assertEqual(payload["html_scope"]["selected_paths"], ["index.html"])


if __name__ == "__main__":
    unittest.main()
