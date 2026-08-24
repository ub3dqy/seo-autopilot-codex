from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from seo_autopilot.models import Evidence, Finding, Phase, RiskLevel, RunReport, RunStatus
from seo_autopilot.reporting import write_reports


ROOT = Path(__file__).resolve().parents[1]


class ReportingTests(unittest.TestCase):
    def test_reports_are_structured_and_html_escaped(self) -> None:
        finding = Finding(
            finding_id="SEO-TEST",
            rule_id="TEST-001",
            severity="high",
            title="Untrusted <script>",
            message="Do not execute <script>alert(1)</script>",
            path="index.html",
            line=4,
            risk=RiskLevel.ADVISORY_ONLY,
            confidence=1.0,
            evidence=[Evidence(source="repository", location="index.html:4", excerpt="<script>")],
        )
        report = RunReport(
            schema_version=1,
            run_id="test-run-123",
            product_version="1.5.0",
            policy_pack_version="2026-08",
            status=RunStatus.REVIEW_REQUIRED,
            phase=Phase.EVIDENCE_COMPLETE,
            repository_root="/tmp/repo",
            repository_commit=None,
            detected_stack="static-html",
            started_at="2026-08-24T00:00:00Z",
            finished_at="2026-08-24T00:01:00Z",
            findings=[finding],
        )
        with tempfile.TemporaryDirectory() as name:
            json_path, markdown_path, html_path = write_reports(report, Path(name))
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["findings"][0]["risk"], "C_ADVISORY_ONLY")
            self.assertIn("SEO-TEST", markdown_path.read_text(encoding="utf-8"))
            html = html_path.read_text(encoding="utf-8")
            self.assertNotIn("<script>alert(1)</script>", html)
            self.assertIn("&lt;script&gt;", html)
            try:
                import jsonschema
            except ImportError:
                jsonschema = None
            if jsonschema is not None:
                schema = json.loads((ROOT / "schemas" / "run.schema.json").read_text(encoding="utf-8"))
                jsonschema.validate(payload, schema)


if __name__ == "__main__":
    unittest.main()
