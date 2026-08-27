from __future__ import annotations

import html
from pathlib import Path
from typing import Callable

from .models import AuditScope, ScopeExclusion, ScopeExclusionStatus
from .special_assets import classify_site_verification_asset, nextjs_metadata_route_owners


_ACTIVATED = False
_LATEST_SCOPE: dict[str, AuditScope] = {}


def latest_scope(repository_root: str | Path) -> AuditScope | None:
    try:
        key = str(Path(repository_root).resolve())
    except (OSError, ValueError):
        key = str(repository_root)
    return _LATEST_SCOPE.get(key)


def _scope_markdown(report) -> str:
    scope = getattr(report, "audit_scope", None)
    if scope is None:
        return ""
    lines = [
        "## Audit scope and privacy boundary",
        "",
        f"- Mode: `{scope.mode}`",
        f"- Git repository: `{str(scope.git_repository).lower()}`",
        f"- Tracked candidates: `{scope.tracked_candidates}`",
        f"- Untracked source candidates: `{scope.untracked_source_candidates}`",
        f"- Candidate files: `{scope.candidate_files}`",
        f"- Static HTML scanned: `{scope.static_html_files_scanned}`",
        f"- Framework source scanned: `{scope.framework_files_scanned}`",
        f"- Metadata entries examined without content reads: `{scope.metadata_entries_examined}`",
        "",
    ]
    if scope.excluded_generated_directories:
        lines.extend(["### Excluded generated/temporary trees", ""])
        for item in scope.excluded_generated_directories:
            lines.append(f"- `{item.path}` — `{item.status.value}` ({item.reason}; content not read by the audit engine)")
        lines.append("")
    if scope.excluded_non_production_directories:
        lines.extend(["### Excluded fixtures/examples", ""])
        for item in scope.excluded_non_production_directories:
            lines.append(f"- `{item.path}` — `{item.status.value}` ({item.reason})")
        lines.append("")
    if scope.excluded_site_verification_files:
        lines.extend(["### Excluded site-ownership verification files", ""])
        for item in scope.excluded_site_verification_files:
            provider = ", ".join(f"`{value}`" for value in item.detection_markers) or "verified filename/content contract"
            lines.append(
                f"- `{item.path}` — `{item.status.value}` "
                f"({item.reason}; provider: {provider}; classification read only this small verification file)"
            )
        lines.append("")
    if scope.excluded_sensitive_directories:
        lines.extend(["### Hard privacy exclusions", ""])
        for item in scope.excluded_sensitive_directories:
            markers = ", ".join(f"`{value}`" for value in item.detection_markers) or "metadata markers"
            lines.append(f"- `{item.path}` — `{item.status.value}` ({item.reason}; markers: {markers}; files_not_read=`true`)")
        lines.append("")
    lines.extend([
        "> `REVIEW_REQUIRED` is a review state, not a technical failure. Read-only audit may complete while mutation remains blocked.",
        "",
    ])
    return "\n".join(lines)


def _scope_html(report) -> str:
    scope = getattr(report, "audit_scope", None)
    if scope is None:
        return ""
    rows = [
        ("Mode", scope.mode),
        ("Git repository", str(scope.git_repository).lower()),
        ("Tracked candidates", str(scope.tracked_candidates)),
        ("Untracked source candidates", str(scope.untracked_source_candidates)),
        ("Candidate files", str(scope.candidate_files)),
        ("Static HTML scanned", str(scope.static_html_files_scanned)),
        ("Framework source scanned", str(scope.framework_files_scanned)),
    ]
    summary = "".join(f"<tr><th>{html.escape(label)}</th><td><code>{html.escape(value)}</code></td></tr>" for label, value in rows)
    exclusions = []
    for item in [
        *scope.excluded_generated_directories,
        *scope.excluded_non_production_directories,
        *scope.excluded_site_verification_files,
        *scope.excluded_sensitive_directories,
    ]:
        exclusions.append(
            "<tr>"
            f"<td><code>{html.escape(item.path)}</code></td>"
            f"<td>{html.escape(item.status.value)}</td>"
            f"<td>{html.escape(item.reason)}</td>"
            f"<td>{'yes' if item.files_not_read else 'no'}</td>"
            "</tr>"
        )
    exclusion_rows = "".join(exclusions) or '<tr><td colspan="4">No exclusions recorded.</td></tr>'
    return (
        "<h2>Audit scope and privacy boundary</h2>"
        f"<table><tbody>{summary}</tbody></table>"
        "<table><thead><tr><th>Path</th><th>Status</th><th>Reason</th><th>Files not read</th></tr></thead>"
        f"<tbody>{exclusion_rows}</tbody></table>"
        "<p><strong>REVIEW_REQUIRED is a review state, not a technical failure.</strong></p>"
    )


def _site_verification_partition(root: Path, paths: list[Path]) -> tuple[list[Path], list[ScopeExclusion]]:
    audit_paths: list[Path] = []
    exclusions: list[ScopeExclusion] = []
    for path in paths:
        asset = classify_site_verification_asset(root, path)
        if asset is None:
            audit_paths.append(path)
            continue
        exclusions.append(
            ScopeExclusion(
                path=asset.path,
                status=ScopeExclusionStatus.EXCLUDED_BY_SCOPE,
                reason=asset.reason,
                detection_markers=[asset.provider],
                files_not_read=False,
                entries_not_read=1,
            )
        )
    exclusions.sort(key=lambda item: item.path.casefold())
    return audit_paths, exclusions


def _suppress_framework_owned_endpoint_findings(result, owners: dict[str, str]) -> None:
    rules = {
        "TECH-ROBOTS-001": "robots.txt",
        "TECH-SITEMAP-001": "sitemap.xml",
    }
    suppressed: list[tuple[str, str, str]] = []
    kept = []
    for finding in result.findings:
        endpoint = rules.get(finding.rule_id)
        owner = owners.get(endpoint or "")
        if endpoint is None or owner is None:
            kept.append(finding)
            continue
        suppressed.append((finding.rule_id, endpoint, owner))
    result.findings = kept
    for rule_id, endpoint, owner in sorted(suppressed):
        result.skipped.append(
            f"{rule_id} was not emitted because Next.js metadata route {owner} owns /{endpoint}; "
            "live endpoint verification remains a separate check."
        )


def activate() -> None:
    global _ACTIVATED
    if _ACTIVATED:
        return
    from . import engine, reporting
    from .doctor import detect_stack
    from .framework_nextjs import audit_nextjs
    from .scope import build_scope

    legacy_audit: Callable = engine.audit_repository
    original_write: Callable = reporting.write_reports
    original_markdown: Callable = reporting._markdown
    original_html: Callable = reporting._html

    def scoped_audit(root: Path, policy, *, max_pages: int = 500, stack: str | None = None):
        root = Path(root).resolve()
        detected_stack = stack or detect_stack(root)
        plan = build_scope(root, stack=detected_stack)
        static_audit_paths, verification_exclusions = _site_verification_partition(root, plan.static_paths)
        plan.manifest.excluded_site_verification_files = verification_exclusions
        original_iter = engine.iter_files

        def scoped_iter(candidate_root: Path, suffixes: tuple[str, ...]):
            allowed = {value.casefold() for value in suffixes}
            for path in static_audit_paths:
                if path.suffix.casefold() in allowed:
                    yield path

        engine.iter_files = scoped_iter
        try:
            result = legacy_audit(root, policy, max_pages=max_pages)
        finally:
            engine.iter_files = original_iter

        plan.manifest.static_html_files_scanned = result.pages_scanned
        if verification_exclusions:
            result.skipped.append(
                f"{len(verification_exclusions)} site-ownership verification file(s) were excluded from page-level SEO checks."
            )
        if detected_stack == "nextjs":
            framework = audit_nextjs(root, plan.framework_paths, policy)
            result.findings.extend(framework.findings)
            result.skipped.extend(framework.skipped)
            plan.manifest.framework_files_scanned = framework.files_scanned
            owners = nextjs_metadata_route_owners(root, plan.framework_paths)
            _suppress_framework_owned_endpoint_findings(result, owners)
            if framework.files_scanned:
                result.skipped = [
                    item
                    for item in result.skipped
                    if item != "No static HTML files were found; framework source is not rewritten without an explicit adapter."
                ]
                if not static_audit_paths:
                    result.skipped.append(
                        f"No production static HTML pages were scanned; the Next.js source adapter scanned {framework.files_scanned} framework file(s)."
                    )
            for endpoint, owner in owners.items():
                result.skipped.append(f"Next.js metadata route ownership: /{endpoint} <- {owner}.")
        elif plan.framework_paths:
            result.skipped.append(
                f"{len(plan.framework_paths)} framework source files are scope-eligible, but no deterministic {detected_stack} source adapter is active."
            )
        if plan.manifest.metadata_scan_truncated:
            result.skipped.append("Scope metadata scan reached its safety budget; exclusion inventory may be incomplete.")
        if plan.manifest.excluded_sensitive_directories:
            result.skipped.append(
                f"{len(plan.manifest.excluded_sensitive_directories)} sensitive browser-profile tree(s) were excluded before content reads."
            )
        result.findings.sort(key=lambda item: (item.path, item.line or 0, item.rule_id, item.finding_id))
        result.safe_fixes = [fix for fix in result.safe_fixes if plan.is_auto_fix_eligible(fix.path)]
        plan.manifest.candidate_files = len(plan.static_paths) + len(plan.framework_paths)
        result.scope = plan.manifest
        _LATEST_SCOPE[str(root)] = plan.manifest
        return result

    def hardened_write(report, output_dir: Path):
        if getattr(report, "audit_scope", None) is None:
            report.audit_scope = latest_scope(report.repository_root)
        return original_write(report, output_dir)

    def hardened_markdown(report):
        base = original_markdown(report)
        scope = _scope_markdown(report)
        return base.replace("## Findings", scope + "## Findings", 1) if scope else base

    def hardened_html(report):
        base = original_html(report)
        scope = _scope_html(report)
        if not scope:
            return base
        marker = "<h2>Findings"
        index = base.find(marker)
        return base[:index] + scope + base[index:] if index >= 0 else base

    engine.audit_repository = scoped_audit
    reporting.write_reports = hardened_write
    reporting._markdown = hardened_markdown
    reporting._html = hardened_html
    _ACTIVATED = True
