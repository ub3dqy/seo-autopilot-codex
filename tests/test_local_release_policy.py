from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LocalReleasePolicyTests(unittest.TestCase):
    def test_no_active_github_actions_workflows(self) -> None:
        workflow_root = ROOT / ".github" / "workflows"
        active: list[str] = []
        if workflow_root.exists():
            for pattern in ("*.yml", "*.yaml"):
                active.extend(path.relative_to(ROOT).as_posix() for path in workflow_root.rglob(pattern))
        self.assertEqual(sorted(active), [])

    def test_local_verification_is_the_documented_release_gate(self) -> None:
        for relative in ("README.md", "RELEASE_NOTES.md", "docs/local-verification.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("LOCAL VERIFICATION ONLY", text, relative)
            self.assertIn("BLOCKED_EXTERNAL / WAIVED_BY_OWNER", text, relative)
            self.assertIn("python scripts/verify_local.py", text, relative)

    def test_dependency_free_installer_is_in_user_edition(self) -> None:
        manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
        self.assertIn("src", manifest["editions"]["user"])
        self.assertIn("INSTALL_WINDOWS.cmd", manifest["editions"]["user"])
        self.assertIn("install.sh", manifest["editions"]["user"])
        self.assertTrue((ROOT / "src" / "seo_autopilot" / "local_install.py").is_file())


if __name__ == "__main__":
    unittest.main()
