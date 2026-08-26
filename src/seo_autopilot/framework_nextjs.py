from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .models import Evidence, EvidenceClass, Finding, RiskLevel
from .policy import PolicyPack


@dataclass
class FrameworkAuditResult:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    skipped: list[str] = field(default_factory=list)


def _line_for(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset)) + 1


def _finding_id(rule_id: str, relative: str, line: int) -> str:
    import hashlib

    payload = f"{rule_id}\0{relative}\0{line}".encode("utf-8")
    return f"SEO-{hashlib.sha256(payload).hexdigest()[:12].upper()}"


def _finding(
    policy: PolicyPack,
    *,
    rule_id: str,
    relative: str,
    line: int,
    message: str,
    excerpt: str,
    severity: str | None = None,
    risk: RiskLevel | None = None,
) -> Finding:
    rule = policy.rules.get(rule_id)
    selected_risk = risk or (rule.default_risk if rule else RiskLevel.REVIEW_REQUIRED)
    selected_severity = severity or (rule.severity if rule else "medium")
    evidence = [Evidence(source="framework_source", location=f"{relative}:{line}", excerpt=excerpt[:300])]
    if rule:
        evidence.append(Evidence(source=rule.source_url, location=rule.rule_id))
    return Finding(
        finding_id=_finding_id(rule_id, relative, line),
        rule_id=rule_id,
        severity=selected_severity,
        title=rule.title if rule else rule_id,
        message=message,
        path=relative,
        line=line,
        risk=selected_risk,
        confidence=0.86,
        evidence=evidence,
        evidence_class=EvidenceClass.FRAMEWORK_SOURCE,
        auto_fix_available=False,
    )


def _read_source(path: Path) -> tuple[str | None, str | None]:
    try:
        if path.stat().st_size > 2_000_000:
            return None, "file exceeds the 2 MB framework source budget"
        return path.read_text(encoding="utf-8"), None
    except (OSError, UnicodeError) as exc:
        return None, f"cannot read UTF-8 source ({exc})"


def _anchor_navigation_findings(relative: str, text: str, policy: PolicyPack) -> list[Finding]:
    target = re.search(r"#[A-Za-z][A-Za-z0-9_-]{1,80}", text)
    mutation = re.search(
        r"(?:history\.(?:pushState|replaceState)\s*\(|(?:window\.)?location\.hash\s*=|setAttribute\s*\(\s*['\"]href['\"])",
        text,
    )
    if not target or not mutation:
        return []
    resolution = re.search(
        r"(?:scrollIntoView\s*\(|scrollTo\s*\(|getElementById\s*\([^)]*\).*?(?:focus|scroll)|querySelector\s*\([^)]*\).*?(?:focus|scroll))",
        text,
        re.DOTALL,
    )
    if resolution:
        return []
    offset = min(target.start(), mutation.start())
    return [
        _finding(
            policy,
            rule_id="NEXTJS-HASH-NAVIGATION-001",
            relative=relative,
            line=_line_for(text, offset),
            severity="high",
            message=(
                "Hash navigation is changed in source without an explicit post-render target resolution or scroll/focus action. "
                "For deferred or client-rendered targets this can leave the address bar updated while the CTA appears inert; live browser verification and owner-reviewed remediation are required."
            ),
            excerpt=text[max(0, offset - 120) : min(len(text), offset + 260)].replace("\n", " "),
        )
    ]


def _menu_accessibility_findings(relative: str, text: str, policy: PolicyPack) -> list[Finding]:
    lowered_name = Path(relative).name.casefold()
    stateful = re.search(r"(?:menuOpen|isMenuOpen|mobileMenu|setMenuOpen|setMobileMenu|openMenu)", text, re.IGNORECASE)
    button = re.search(r"<button\b", text, re.IGNORECASE)
    likely_navigation = any(token in lowered_name for token in ("header", "menu", "nav")) or bool(stateful)
    if not likely_navigation or not button or not stateful:
        return []
    missing: list[str] = []
    if not re.search(r"aria-expanded\s*=", text, re.IGNORECASE):
        missing.append("aria-expanded")
    if not re.search(r"(?:Escape|Esc|keydown|onKeyDown)", text, re.IGNORECASE):
        missing.append("Escape-key close handling")
    if not missing:
        return []
    offset = stateful.start()
    return [
        _finding(
            policy,
            rule_id="NEXTJS-MENU-A11Y-001",
            relative=relative,
            line=_line_for(text, offset),
            severity="high" if len(missing) > 1 else "medium",
            message=(
                "A stateful navigation/menu control is present but source evidence is missing: "
                + ", ".join(missing)
                + ". Confirm the accessible name, expanded state, focus behavior, and keyboard close behavior in a browser before applying a reviewed fix."
            ),
            excerpt=text[max(0, offset - 100) : min(len(text), offset + 260)].replace("\n", " "),
        )
    ]


def _sitemap_findings(relative: str, text: str, policy: PolicyPack) -> list[Finding]:
    if Path(relative).name.casefold() not in {"sitemap.ts", "sitemap.js", "sitemap.tsx", "sitemap.jsx"}:
        return []
    match = re.search(r"lastModified\s*:\s*(?:new\s+Date\s*\(\s*\)|Date\.now\s*\(\s*\))", text)
    if not match:
        return []
    return [
        _finding(
            policy,
            rule_id="NEXTJS-SITEMAP-LASTMOD-001",
            relative=relative,
            line=_line_for(text, match.start()),
            severity="high",
            message=(
                "Sitemap lastModified is derived from the build/runtime clock rather than page-specific evidence. "
                "Review ownership of meaningful content dates; do not replace all dates with the current date."
            ),
            excerpt=text[max(0, match.start() - 100) : min(len(text), match.end() + 160)].replace("\n", " "),
        )
    ]


def _schema_findings(relative: str, text: str, policy: PolicyPack) -> list[Finding]:
    website_match = re.search(r"['\"]@type['\"]\s*:\s*['\"]WebSite['\"]", text)
    if website_match is None:
        return []
    window = text[max(0, website_match.start() - 700) : min(len(text), website_match.start() + 1800)]
    names = {
        value.strip()
        for value in re.findall(r"(?:['\"]name['\"]|\bname)\s*:\s*['\"]([^'\"]{1,160})['\"]", window)
        if value.strip()
    }
    has_id = bool(re.search(r"['\"]@id['\"]\s*:", window))
    if has_id and len(names) <= 1:
        return []
    details: list[str] = []
    if not has_id:
        details.append("no stable @id is visible in the WebSite object")
    if len(names) > 1:
        details.append("multiple explicit name values are present near the WebSite object")
    return [
        _finding(
            policy,
            rule_id="NEXTJS-SCHEMA-IDENTITY-001",
            relative=relative,
            line=_line_for(text, website_match.start()),
            severity="medium",
            message=(
                "Structured WebSite identity requires owner review because "
                + " and ".join(details)
                + ". Confirm one public name and entity identifier before changing JSON-LD."
            ),
            excerpt=window.replace("\n", " ")[:300],
        )
    ]


def _dynamic_metadata_findings(relative: str, text: str, policy: PolicyPack) -> list[Finding]:
    parts = Path(relative).parts
    if Path(relative).name.casefold() not in {"page.tsx", "page.ts", "page.jsx", "page.js"}:
        return []
    if not any("[" in part and "]" in part for part in parts):
        return []
    if re.search(r"\b(?:generateMetadata|metadata)\b", text):
        return []
    return [
        _finding(
            policy,
            rule_id="NEXTJS-DYNAMIC-METADATA-001",
            relative=relative,
            line=1,
            severity="low",
            risk=RiskLevel.ADVISORY_ONLY,
            message=(
                "This dynamic route has no route-local metadata declaration in the page source. Metadata may be inherited, "
                "so this is a review item rather than proof of a defect; verify the rendered title, description, canonical, and indexability."
            ),
            excerpt=text[:300].replace("\n", " "),
        )
    ]


def audit_nextjs(root: Path, paths: list[Path], policy: PolicyPack) -> FrameworkAuditResult:
    result = FrameworkAuditResult()
    seen_ids: set[str] = set()
    for path in paths:
        try:
            relative = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        text, error = _read_source(path)
        if error:
            result.skipped.append(f"{relative}: {error}")
            continue
        assert text is not None
        result.files_scanned += 1
        candidates = [
            *_anchor_navigation_findings(relative, text, policy),
            *_menu_accessibility_findings(relative, text, policy),
            *_sitemap_findings(relative, text, policy),
            *_schema_findings(relative, text, policy),
            *_dynamic_metadata_findings(relative, text, policy),
        ]
        for finding in candidates:
            if finding.finding_id in seen_ids:
                continue
            seen_ids.add(finding.finding_id)
            result.findings.append(finding)
    result.findings.sort(key=lambda item: (item.path, item.line or 0, item.rule_id, item.finding_id))
    return result
