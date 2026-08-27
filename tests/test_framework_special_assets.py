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


def valid_page(title: str) -> str:
    slug = title.casefold().replace(" ", "-")
    return (
        "<!doctype html>\n"
        "<html lang=\"en\"><head>"
        f"<title>{title}</title>"
        f"<meta name=\"description\" content=\"{title} description\">"
        f"<link rel=\"canonical\" href=\"https://example.invalid/{slug}\">"
        "</head><body><h1>Page</h1></body></html>\n"
    )


@unittest.skipUnless(shutil.which("git"), "Git is required")
class FrameworkSpecialAssetTests(unittest.TestCase):
    def init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Special Asset Test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "special-assets@example.invalid"], cwd=root, check=True)

    def next_package(self, root: Path) -> None:
        (root / "package.json").write_text(
            json.dumps({"dependencies": {"next": "15.0.0", "react": "19.0.0"}}),
            encoding="utf-8",
        )

    def write_metadata_routes(self, root: Path) -> None:
        app = root / "src" / "app"
        app.mkdir(parents=True, exist_ok=True)
        (app / "robots.ts").write_text(
            "import type { MetadataRoute } from 'next';\n"
            "export default function robots(): MetadataRoute.Robots { "
            "return { rules: { userAgent: '*', allow: '/' } }; }\n",
            encoding="utf-8",
        )
        (app / "sitemap.ts").write_text(
            "import type { MetadataRoute } from 'next';\n"
            "export default function sitemap(): MetadataRoute.Sitemap { "
            "return [{ url: 'https://example.invalid/', lastModified: '2026-08-19' }]; }\n",
            encoding="utf-8",
        )

    def test_nextjs_metadata_routes_and_ownership_files_do_not_create_page_findings(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.init_repo(root)
            self.next_package(root)
            self.write_metadata_routes(root)

            public = root / "public"
            public.mkdir()
            google = public / "google55fef1f505cfa1c3.html"
            google.write_text(
                "google-site-verification: google55fef1f505cfa1c3.html\n",
                encoding="utf-8",
            )
            yandex = public / "yandex_ee018aae7c9cfe7f.html"
            yandex.write_text(
                "<html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">"
                "</head><body>Verification: ee018aae7c9cfe7f</body></html>\n",
                encoding="utf-8",
            )

            loader = root / "scripts" / "static-first-loader.js"
            loader.parent.mkdir()
            loader.write_text(
                "export function go(){ history.replaceState(null, '', '#lead'); }\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "special asset fixture"], cwd=root, check=True, capture_output=True)

            first = audit_repository(root, POLICY)
            second = audit_repository(root, POLICY)
            rules = [item.rule_id for item in first.findings]
            exclusions = first.scope.excluded_site_verification_files

            self.assertEqual(first.scope.static_html_files_scanned, 0)
            self.assertEqual(first.scope.framework_files_scanned, 3)
            self.assertEqual(
                [item.path for item in exclusions],
                [
                    "public/google55fef1f505cfa1c3.html",
                    "public/yandex_ee018aae7c9cfe7f.html",
                ],
            )
            self.assertTrue(all(item.status == ScopeExclusionStatus.EXCLUDED_BY_SCOPE for item in exclusions))
            self.assertTrue(all(item.files_not_read is False for item in exclusions))
            self.assertEqual({item.detection_markers[0] for item in exclusions}, {"google", "yandex"})
            self.assertNotIn("TECH-ROBOTS-001", rules)
            self.assertNotIn("TECH-SITEMAP-001", rules)
            self.assertFalse(any(rule.startswith(("ONPAGE-", "ACCESSIBILITY-LANG", "CANONICAL-")) for rule in rules))
            self.assertEqual(rules, ["NEXTJS-HASH-NAVIGATION-001"])
            self.assertEqual(first.safe_fixes, [])
            self.assertEqual(first.scope, second.scope)
            self.assertEqual(
                [(item.rule_id, item.path, item.line) for item in first.findings],
                [(item.rule_id, item.path, item.line) for item in second.findings],
            )

    def test_similar_html_names_remain_real_pages_when_content_contract_does_not_match(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.init_repo(root)
            self.next_package(root)
            self.write_metadata_routes(root)
            public = root / "public"
            public.mkdir()
            (public / "google12345678.html").write_text(valid_page("Google product"), encoding="utf-8")
            (public / "yandex_12345678.html").write_text(valid_page("Yandex product"), encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "real page fixture"], cwd=root, check=True, capture_output=True)

            result = audit_repository(root, POLICY)
            self.assertEqual(result.scope.static_html_files_scanned, 2)
            self.assertEqual(result.scope.excluded_site_verification_files, [])
            self.assertNotIn("TECH-ROBOTS-001", {item.rule_id for item in result.findings})
            self.assertNotIn("TECH-SITEMAP-001", {item.rule_id for item in result.findings})

    def test_metadata_filename_without_default_export_does_not_suppress_missing_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.init_repo(root)
            self.next_package(root)
            (root / "index.html").write_text(valid_page("Home"), encoding="utf-8")
            app = root / "src" / "app"
            app.mkdir(parents=True)
            (app / "robots.ts").write_text(
                "export const dynamic = 'force-static';\n",
                encoding="utf-8",
            )
            (app / "sitemap.ts").write_text(
                "export default function sitemap(){ return [{url:'https://example.invalid/'}]; }\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "invalid owner fixture"], cwd=root, check=True, capture_output=True)

            result = audit_repository(root, POLICY)
            rules = {item.rule_id for item in result.findings}
            self.assertIn("TECH-ROBOTS-001", rules)
            self.assertNotIn("TECH-SITEMAP-001", rules)

    def test_new_scope_field_is_optional_for_schema_v1_backward_compatibility(self) -> None:
        schema = json.loads((ROOT / "schemas" / "run.schema.json").read_text(encoding="utf-8"))
        audit_scope = schema["properties"]["audit_scope"]
        self.assertIn("excluded_site_verification_files", audit_scope["properties"])
        self.assertNotIn("excluded_site_verification_files", audit_scope["required"])


if __name__ == "__main__":
    unittest.main()
