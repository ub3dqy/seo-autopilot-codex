from __future__ import annotations

import html
import json
from pathlib import Path

from .models import RiskLevel, RunReport


def write_reports(report: RunReport, output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    json_path = output_dir / "run.json"
    markdown_path = output_dir / "report.md"
    html_path = output_dir / "report.html"
    _atomic_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    _atomic_text(markdown_path, _markdown(report))
    _atomic_text(html_path, _html(report))
    return json_path, markdown_path, html_path


def _atomic_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _markdown(report: RunReport) -> str:
    lines = [
        "# SEO Autopilot report",
        "",
        f"- Run: `{report.run_id}`",
        f"- Status: **{report.status.value}**",
        f"- Phase: `{report.phase.value}`",
        f"- Mode: `{report.mode}`",
        f"- Stack: `{report.detected_stack}`",
        f"- Repository commit: `{report.repository_commit or 'UNKNOWN'}`",
        f"- Transaction branch: `{report.branch or 'NONE'}`",
        "",
        "## Findings",
        "",
    ]
    if not report.findings:
        lines.append("No findings.")
    for finding in report.findings:
        location = f"{finding.path}:{finding.line or 1}"
        lines.extend(
            [
                f"### {finding.finding_id} — {finding.title}",
                "",
                f"- Rule: `{finding.rule_id}`",
                f"- Severity: `{finding.severity}`",
                f"- Risk: `{finding.risk.value}`",
                f"- Location: `{location}`",
                f"- Confidence: `{finding.confidence:.2f}`",
                f"- Status: `{finding.status}`",
                "",
                finding.message,
                "",
            ]
        )
        for evidence in finding.evidence:
            excerpt = evidence.excerpt.replace("\n", " ")[:300]
            lines.append(f"- Evidence: `{evidence.source}` → `{evidence.location}` — {excerpt}")
        lines.append("")

    lines.extend(["## Applied changes", ""])
    if not report.changes:
        lines.append("No repository changes were applied.")
    for change in report.changes:
        lines.extend(
            [
                f"- `{change.path}` — {change.description}",
                f"  - Risk: `{change.risk.value}`",
                f"  - Changed lines: `{change.lines_changed}`",
                f"  - SHA-256: `{change.before_sha256}` → `{change.after_sha256}`",
            ]
        )

    lines.extend(["", "## Validation", ""])
    if not report.checks:
        lines.append("No external project commands were executed.")
    for check in report.checks:
        command = " ".join(check.command) if check.command else "built-in"
        lines.append(f"- **{check.name}**: `{check.status.value}` — `{command}`")

    lines.extend(["", "## Skipped and residual risks", ""])
    for item in [*report.skipped, *report.residual_risks]:
        lines.append(f"- {item}")
    if not report.skipped and not report.residual_risks:
        lines.append("None recorded.")

    lines.extend(["", "## Rollback", ""])
    if report.rollback:
        lines.append("```text")
        lines.extend(report.rollback)
        lines.append("```")
    else:
        lines.append("No rollback action is required because no transaction branch was created.")
    lines.append("")
    return "\n".join(lines)


def _html(report: RunReport) -> str:
    finding_rows = []
    for finding in report.findings:
        finding_rows.append(
            "<tr>"
            f"<td><code>{html.escape(finding.finding_id)}</code></td>"
            f"<td>{html.escape(finding.severity)}</td>"
            f"<td>{html.escape(finding.risk.value)}</td>"
            f"<td><code>{html.escape(finding.path)}:{finding.line or 1}</code></td>"
            f"<td><strong>{html.escape(finding.title)}</strong><br>{html.escape(finding.message)}</td>"
            "</tr>"
        )
    change_rows = []
    for change in report.changes:
        change_rows.append(
            "<tr>"
            f"<td><code>{html.escape(change.path)}</code></td>"
            f"<td>{html.escape(change.description)}</td>"
            f"<td>{html.escape(change.risk.value)}</td>"
            f"<td>{change.lines_changed}</td>"
            "</tr>"
        )
    residual = "".join(f"<li>{html.escape(item)}</li>" for item in [*report.skipped, *report.residual_risks]) or "<li>None recorded.</li>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SEO Autopilot report {html.escape(report.run_id)}</title>
<style>
:root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
body {{ max-width: 1200px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap: .75rem; }}
.card {{ border: 1px solid #8886; border-radius: .75rem; padding: 1rem; }}
table {{ width: 100%; border-collapse: collapse; margin: 1rem 0 2rem; }}
th, td {{ border: 1px solid #8886; padding: .65rem; text-align: left; vertical-align: top; }}
code {{ overflow-wrap: anywhere; }}
.badge {{ display: inline-block; border: 1px solid currentColor; border-radius: 999px; padding: .2rem .6rem; }}
</style>
</head>
<body>
<h1>SEO Autopilot report</h1>
<div class="summary">
<div class="card"><small>Status</small><br><strong class="badge">{html.escape(report.status.value)}</strong></div>
<div class="card"><small>Run</small><br><code>{html.escape(report.run_id)}</code></div>
<div class="card"><small>Stack</small><br><code>{html.escape(report.detected_stack)}</code></div>
<div class="card"><small>Branch</small><br><code>{html.escape(report.branch or 'NONE')}</code></div>
</div>
<h2>Findings ({len(report.findings)})</h2>
<table><thead><tr><th>ID</th><th>Severity</th><th>Risk</th><th>Location</th><th>Evidence-backed conclusion</th></tr></thead>
<tbody>{''.join(finding_rows) or '<tr><td colspan="5">No findings.</td></tr>'}</tbody></table>
<h2>Applied changes ({len(report.changes)})</h2>
<table><thead><tr><th>Path</th><th>Change</th><th>Risk</th><th>Lines</th></tr></thead>
<tbody>{''.join(change_rows) or '<tr><td colspan="4">No changes.</td></tr>'}</tbody></table>
<h2>Skipped and residual risks</h2><ul>{residual}</ul>
<p>Generated from structured <code>run.json</code>. This report does not claim ranking, indexing, or rich-result guarantees.</p>
</body></html>
"""


def has_review_findings(report: RunReport) -> bool:
    return any(finding.risk != RiskLevel.AUTO_FIX and finding.status == "OPEN" for finding in report.findings)
