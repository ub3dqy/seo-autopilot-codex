from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from seo_autopilot.engine import audit_repository
from seo_autopilot.models import ScopeExclusionStatus
from seo_autopilot.policy import load_policy_pack


ROOT = Path(__file__).resolve().parents[1]
POLICY = load_policy_pack(ROOT / "policy-packs" / "google-search" / "2026-08" / "policies.json")


@unittest.skipUnless(shutil.which("git"), "Git is required")
class CookieRoutePrivacyTests(unittest.TestCase):
    def init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Cookie Route Test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "cookie-route@example.invalid"], cwd=root, check=True)

    def write_next_package(self, root: Path) -> None:
        (root / "package.json").write_text(
            json.dumps({"dependencies": {"next": "15.0.0", "react": "19.0.0"}}),
            encoding="utf-8",
        )

    def test_browser_marker_route_directories_remain_current_source(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.init_repo(root)
            self.write_next_package(root)

            route_root = root / "src" / "app" / "(site)" / "(legacy)"
            route_names = ("cookies", "history", "preferences", "bookmarks")
            for route_name in route_names:
                page = route_root / route_name / "page.tsx"
                page.parent.mkdir(parents=True, exist_ok=True)
                page.write_text(
                    "export const metadata = { title: 'Policy page' };\n"
                    "export default function Page(){ return <main><h1>Policy</h1></main>; }\n",
                    encoding="utf-8",
                )

            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "route baseline"], cwd=root, check=True, capture_output=True)

            profile = root / "artifacts" / "runtime-bundler" / "chrome-user-data" / "Default"
            network = profile / "Network"
            network.mkdir(parents=True)
            (network / "Cookies").write_bytes(b"private-cookie-db")
            (profile / "Login Data").write_bytes(b"private-login-db")
            (profile / "secret.html").write_text("must not be audited", encoding="utf-8")

            first = audit_repository(root, POLICY)
            second = audit_repository(root, POLICY)
            sensitive = first.scope.excluded_sensitive_directories
            sensitive_paths = {item.path for item in sensitive}
            finding_paths = {item.path for item in first.findings}

            self.assertTrue(sensitive)
            self.assertTrue(all(item.status == ScopeExclusionStatus.EXCLUDED_SENSITIVE for item in sensitive))
            self.assertTrue(all(item.files_not_read for item in sensitive))
            self.assertTrue(any(path.endswith("chrome-user-data/Default") for path in sensitive_paths))
            self.assertFalse(any(path.startswith("src/") for path in sensitive_paths))
            self.assertEqual(first.scope.framework_files_scanned, len(route_names))
            self.assertFalse(any(path.startswith("artifacts/") for path in finding_paths))
            self.assertEqual(first.scope, second.scope)
            self.assertEqual(
                [(item.rule_id, item.path, item.line) for item in first.findings],
                [(item.rule_id, item.path, item.line) for item in second.findings],
            )

    def test_single_ambiguous_marker_file_does_not_exclude_known_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.init_repo(root)
            self.write_next_package(root)

            source = root / "src" / "app"
            source.mkdir(parents=True)
            (source / "Cookies").write_bytes(b"application-owned source fixture")
            page = source / "page.tsx"
            page.write_text(
                "export const metadata = { title: 'Home' };\n"
                "export default function Page(){ return <main/>; }\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "source marker fixture"], cwd=root, check=True, capture_output=True)

            result = audit_repository(root, POLICY)
            self.assertFalse(any(item.path.startswith("src/") for item in result.scope.excluded_sensitive_directories))
            self.assertEqual(result.scope.framework_files_scanned, 1)


if __name__ == "__main__":
    unittest.main()
