from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from seo_autopilot import local_install


class LocalInstallTests(unittest.TestCase):
    def test_dependency_free_install_creates_package_skill_and_launcher(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            user_site = root / "site-packages"
            user_base = root / "user-base"
            codex_home = root / "codex-home"
            with (
                patch.object(local_install.site, "getusersitepackages", return_value=str(user_site)),
                patch.object(local_install.site, "USER_BASE", str(user_base)),
            ):
                result = local_install.install(codex_home=codex_home, force=False)

            package = Path(result["package"])
            skill = Path(result["skill"])
            launcher = Path(result["launcher"])
            dist_info = Path(result["dist_info"])
            self.assertTrue((package / "__init__.py").is_file())
            self.assertTrue((package / "entrypoint.py").is_file())
            self.assertTrue((package / "scope.py").is_file())
            self.assertTrue((package / local_install.MARKER).is_file())
            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertTrue((skill / local_install.MARKER).is_file())
            self.assertTrue(launcher.is_file())
            self.assertTrue((dist_info / "METADATA").is_file())

            env = dict(os.environ)
            env["PYTHONPATH"] = str(user_site)
            completed = subprocess.run(
                [sys.executable, "-c", "import seo_autopilot; print(seo_autopilot.__version__)"],
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(completed.stdout.strip(), result["version"])

            website = root / "website"
            website.mkdir()
            (website / "index.html").write_text("<html></html>\n", encoding="utf-8")
            scoped = subprocess.run(
                [sys.executable, "-m", "seo_autopilot", "scope", str(website), "--json"],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(scoped.returncode, 0, scoped.stderr or scoped.stdout)
            payload = json.loads(scoped.stdout)
            self.assertEqual(payload["html_scope"]["selected_paths"], ["index.html"])

    def test_unmanaged_target_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            user_site = root / "site-packages"
            package = user_site / "seo_autopilot"
            package.mkdir(parents=True)
            (package / "owner-file.txt").write_text("preserve\n", encoding="utf-8")
            with (
                patch.object(local_install.site, "getusersitepackages", return_value=str(user_site)),
                patch.object(local_install.site, "USER_BASE", str(root / "user-base")),
            ):
                with self.assertRaises(RuntimeError):
                    local_install.install(codex_home=root / "codex-home", force=False)
            self.assertEqual((package / "owner-file.txt").read_text(encoding="utf-8"), "preserve\n")


if __name__ == "__main__":
    unittest.main()
