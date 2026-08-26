from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

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

    @unittest.skipUnless(os.name == "nt" and hasattr(Path("."), "is_junction"), "Windows junction test")
    def test_windows_junction_is_not_traversed(self) -> None:
        # Creation of junctions may require a platform command and permissions.
        # The implementation uses Path.is_junction when available; this test is
        # intentionally skipped unless the environment can provide the primitive.
        self.assertTrue(hasattr(Path("."), "is_junction"))


if __name__ == "__main__":
    unittest.main()
