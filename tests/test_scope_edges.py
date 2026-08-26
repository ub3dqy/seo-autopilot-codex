from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from seo_autopilot.utils import select_files


class AuditScopeEdgeTests(unittest.TestCase):
    def test_nested_artifacts_route_is_not_excluded_by_root_rule(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            route = root / "src" / "app" / "artifacts"
            route.mkdir(parents=True)
            (route / "page.html").write_text("<html></html>\n", encoding="utf-8")

            selection = select_files(root, (".html",))
            selected = [path.relative_to(root).as_posix() for path in selection.files]
            self.assertEqual(selected, ["src/app/artifacts/page.html"])

    def test_symlinked_directory_is_not_traversed(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            outside = root / "outside"
            outside.mkdir()
            (outside / "old.html").write_text("<html></html>\n", encoding="utf-8")
            linked = root / "linked-copy"
            try:
                linked.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlinks are unavailable in this environment")

            selection = select_files(root, (".html",))
            selected = [path.relative_to(root).as_posix() for path in selection.files]
            self.assertEqual(selected, ["outside/old.html"])
            self.assertIn("linked-copy", selection.pruned_directories)

    def test_junction_primitive_is_treated_as_non_traversable(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            junction = root / "junction-copy"
            junction.mkdir()
            (junction / "old.html").write_text("<html></html>\n", encoding="utf-8")

            with patch.object(
                Path,
                "is_junction",
                new=lambda self: self.name == "junction-copy",
                create=True,
            ):
                selection = select_files(root, (".html",))

            self.assertEqual(selection.files, [])
            self.assertIn("junction-copy", selection.pruned_directories)

    def test_ignore_negation_cannot_reinclude_sensitive_paths(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            profile = root / "artifacts" / "runtime" / "chrome-profile"
            profile.mkdir(parents=True)
            (profile / "extension.html").write_text("<html></html>\n", encoding="utf-8")
            (profile / "Cookies").write_text("private\n", encoding="utf-8")
            (root / ".seo-autopilotignore").write_text(
                "!artifacts/**\n!artifacts/runtime/chrome-profile/**\n",
                encoding="utf-8",
            )

            selection = select_files(root, (".html",))
            self.assertEqual(selection.files, [])
            self.assertTrue(any("chrome-profile" in item for item in selection.sensitive_paths))

    def test_ignore_negation_cannot_reinclude_credential_directories(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            private = root / ".ssh"
            private.mkdir()
            (private / "help.html").write_text("<html></html>\n", encoding="utf-8")
            (root / ".seo-autopilotignore").write_text("!.ssh/**\n", encoding="utf-8")

            selection = select_files(root, (".html",))
            self.assertEqual(selection.files, [])
            self.assertIn(".ssh", selection.sensitive_paths)


if __name__ == "__main__":
    unittest.main()
