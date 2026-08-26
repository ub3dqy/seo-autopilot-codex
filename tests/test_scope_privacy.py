from __future__ import annotations

import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from seo_autopilot.engine import audit_repository
from seo_autopilot.models import EvidenceClass, ScopeExclusionStatus
from seo_autopilot.policy import load_policy_pack


ROOT = Path(__file__).resolve().parents[1]
POLICY = load_policy_pack(ROOT / "policy-packs" / "google-search" / "2026-08" / "policies.json")


def png_header(width: int, height: int) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height)


def html(title: str, image: str = "image.png") -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"en\"><head>\n"
        f"<title>{title}</title>\n"
        f"<meta name=\"description\" content=\"{title} description\">\n"
        f"<link rel=\"canonical\" href=\"https://example.invalid/{title.lower()}\">\n"
        "</head><body>\n"
        f"<img src=\"{image}\" alt=\"Current image\">\n"
        "</body></html>\n"
    )


@unittest.skipUnless(shutil.which("git"), "Git is required")
class ScopePrivacyTests(unittest.TestCase):
    def init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Scope Test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "scope@example.invalid"], cwd=root, check=True)

    def test_airsys_like_noise_and_browser_profiles_are_excluded_before_reads(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.init_repo(root)
            (root / ".gitignore").write_text("artifacts/\ntmp/\n", encoding="utf-8")
            source = root / "src"
            source.mkdir()
            (source / "image.png").write_bytes(png_header(320, 180))
            (source / "current.html").write_text(html("Current"), encoding="utf-8")
            public = root / "public"
            public.mkdir()
            (public / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
            (public / "sitemap.xml").write_text("<urlset/>\n", encoding="utf-8")
            subprocess.run(["git", "add", ".gitignore", "src", "public"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)

            artifacts = root / "artifacts" / "runtime-bundler-ab" / "snapshot"
            artifacts.mkdir(parents=True)
            for index in range(150):
                (artifacts / f"archive-{index}.html").write_text(html(f"Archive {index}"), encoding="utf-8")
            temporary = root / "tmp"
            temporary.mkdir()
            for index in range(50):
                (temporary / f"verification-{index}.html").write_text(html(f"Temporary {index}"), encoding="utf-8")

            profile = root / "artifacts" / "runtime-bundler-ab" / "chrome-user-data" / "Default"
            network = profile / "Network"
            network.mkdir(parents=True)
            (network / "Cookies").write_bytes(b"\x00\xffprivate-cookie-db")
            (profile / "Login Data").write_bytes(b"\x00\xffprivate-login-db")
            (profile / "secret.html").write_bytes(b"\xff\xfe\x00should-never-be-read")

            first = audit_repository(root, POLICY)
            second = audit_repository(root, POLICY)
            self.assertTrue(hasattr(first, "scope"))
            self.assertEqual(first.scope.mode, "SOURCE_FIRST")
            self.assertTrue(first.scope.git_repository)
            self.assertEqual(first.scope.static_html_files_scanned, 1)
            self.assertEqual([item.path for item in first.safe_fixes], ["src/current.html"])
            self.assertFalse(any(item.path.startswith(("artifacts/", "tmp/")) for item in first.findings))
            self.assertFalse(any(item.path.startswith(("artifacts/", "tmp/")) for item in first.safe_fixes))
            generated = {item.path for item in first.scope.excluded_generated_directories}
            self.assertIn("artifacts", generated)
            self.assertIn("tmp", generated)
            sensitive = first.scope.excluded_sensitive_directories
            self.assertTrue(sensitive)
            self.assertTrue(any(item.status == ScopeExclusionStatus.EXCLUDED_SENSITIVE for item in sensitive))
            self.assertTrue(all(item.files_not_read for item in sensitive))
            self.assertTrue(any("Cookies" in marker or "Login Data" in marker for item in sensitive for marker in item.detection_markers))
            self.assertEqual(first.scope, second.scope)
            self.assertEqual(
                [(item.rule_id, item.path, item.line) for item in first.findings],
                [(item.rule_id, item.path, item.line) for item in second.findings],
            )

    def test_nextjs_adapter_records_framework_source_findings_in_structured_result(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.init_repo(root)
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"next": "15.0.0", "react": "19.0.0"}}),
                encoding="utf-8",
            )
            loader = root / "scripts" / "static-first-loader.js"
            loader.parent.mkdir()
            loader.write_text("export function go(){ history.replaceState(null, '', '#lead'); }\n", encoding="utf-8")
            header = root / "src" / "widgets" / "header" / "header.tsx"
            header.parent.mkdir(parents=True)
            header.write_text(
                "export function Header(){ const [menuOpen,setMenuOpen]=useState(false); "
                "return <button onClick={()=>setMenuOpen(!menuOpen)}>Menu</button>; }\n",
                encoding="utf-8",
            )
            sitemap = root / "src" / "app" / "sitemap.ts"
            sitemap.parent.mkdir(parents=True)
            sitemap.write_text("export default function sitemap(){ return routes.map(url => ({url,lastModified:new Date()})); }\n", encoding="utf-8")
            schema = root / "src" / "shared" / "seo" / "schema.ts"
            schema.parent.mkdir(parents=True)
            schema.write_text("export const graph = {'@type':'WebSite', name:'Brand A', alternateName:'Brand B'};\n", encoding="utf-8")
            dynamic = root / "src" / "app" / "manufacturers" / "[slug]" / "page.tsx"
            dynamic.parent.mkdir(parents=True)
            dynamic.write_text("export default function Page(){ return <main/> }\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "next fixture"], cwd=root, check=True, capture_output=True)

            result = audit_repository(root, POLICY)
            rules = {item.rule_id for item in result.findings}
            self.assertIn("NEXTJS-HASH-NAVIGATION-001", rules)
            self.assertIn("NEXTJS-MENU-A11Y-001", rules)
            self.assertIn("NEXTJS-SITEMAP-LASTMOD-001", rules)
            self.assertIn("NEXTJS-SCHEMA-IDENTITY-001", rules)
            self.assertIn("NEXTJS-DYNAMIC-METADATA-001", rules)
            framework_findings = [item for item in result.findings if item.rule_id.startswith("NEXTJS-")]
            self.assertTrue(framework_findings)
            self.assertTrue(all(item.evidence_class == EvidenceClass.FRAMEWORK_SOURCE for item in framework_findings))
            self.assertEqual(result.scope.framework_files_scanned, 5)
            self.assertEqual(result.safe_fixes, [])


if __name__ == "__main__":
    unittest.main()
