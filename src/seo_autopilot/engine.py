from __future__ import annotations

import difflib
import json
import os
import re
import struct
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .models import Change, Evidence, Finding, RiskLevel, SafeFix
from .policy import PolicyPack
from .utils import iter_files, sha256_bytes


PROMPT_INJECTION_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous",
    "system message",
    "developer message",
    "run this command",
    "execute this command",
    "codex must",
    "assistant must",
)


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class ImageObservation:
    line: int
    offset: int
    raw_tag: str
    src: str
    alt_present: bool
    width: str | None
    height: str | None


@dataclass
class PageObservation:
    path: Path
    title: str = ""
    title_line: int | None = None
    html_lang: str | None = None
    html_line: int | None = None
    descriptions: list[tuple[int, str]] = field(default_factory=list)
    canonicals: list[tuple[int, str]] = field(default_factory=list)
    noindex_lines: list[int] = field(default_factory=list)
    images: list[ImageObservation] = field(default_factory=list)
    invalid_jsonld: list[tuple[int, str]] = field(default_factory=list)
    untrusted_instructions: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class AuditResult:
    findings: list[Finding]
    safe_fixes: list[SafeFix]
    pages_scanned: int
    skipped: list[str] = field(default_factory=list)


class SEOHTMLParser(HTMLParser):
    def __init__(self, source: str, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.source = source
        self.observation = PageObservation(path=path)
        self._line_offsets = [0]
        for match in re.finditer("\n", source):
            self._line_offsets.append(match.end())
        self._in_title = False
        self._title_parts: list[str] = []
        self._title_line: int | None = None
        self._jsonld_depth = 0
        self._jsonld_line: int | None = None
        self._jsonld_parts: list[str] = []

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str | None]:
        return {name.lower(): value for name, value in attrs}

    def _absolute_offset(self) -> int:
        line, column = self.getpos()
        if line < 1 or line > len(self._line_offsets):
            return 0
        return self._line_offsets[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_tag(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_tag(tag, attrs)

    def _handle_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = self._attrs(attrs)
        line, _ = self.getpos()
        if tag == "html":
            self.observation.html_lang = values.get("lang")
            self.observation.html_line = line
        elif tag == "title":
            self._in_title = True
            self._title_parts = []
            self._title_line = line
        elif tag == "meta":
            name = (values.get("name") or "").strip().lower()
            content = (values.get("content") or "").strip()
            if name == "description":
                self.observation.descriptions.append((line, content))
            if name == "robots" and "noindex" in {token.strip() for token in content.lower().split(",")}:
                self.observation.noindex_lines.append(line)
        elif tag == "link":
            rel = {token.lower() for token in (values.get("rel") or "").split()}
            if "canonical" in rel:
                self.observation.canonicals.append((line, (values.get("href") or "").strip()))
        elif tag == "img":
            raw = self.get_starttag_text() or ""
            self.observation.images.append(
                ImageObservation(
                    line=line,
                    offset=self._absolute_offset(),
                    raw_tag=raw,
                    src=(values.get("src") or "").strip(),
                    alt_present="alt" in values,
                    width=values.get("width"),
                    height=values.get("height"),
                )
            )
        elif tag == "script" and (values.get("type") or "").strip().lower() == "application/ld+json":
            self._jsonld_depth += 1
            self._jsonld_line = line
            self._jsonld_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title" and self._in_title:
            self._in_title = False
            self.observation.title = " ".join("".join(self._title_parts).split())
            self.observation.title_line = self._title_line
        elif tag == "script" and self._jsonld_depth:
            payload = "".join(self._jsonld_parts).strip()
            if payload:
                try:
                    json.loads(payload)
                except json.JSONDecodeError as exc:
                    self.observation.invalid_jsonld.append(
                        (self._jsonld_line or self.getpos()[0], f"{exc.msg} at line {exc.lineno}, column {exc.colno}")
                    )
            self._jsonld_depth = 0
            self._jsonld_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        if self._jsonld_depth:
            self._jsonld_parts.append(data)

    def handle_comment(self, data: str) -> None:
        lowered = data.lower()
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern in lowered:
                line, _ = self.getpos()
                self.observation.untrusted_instructions.append((line, data.strip()[:240]))
                break


def _finding_id(rule_id: str, relative: str, line: int | None, extra: str = "") -> str:
    payload = f"{rule_id}\0{relative}\0{line or 0}\0{extra}".encode("utf-8")
    return f"SEO-{sha256(payload).hexdigest()[:12].upper()}"


def _make_finding(
    policy: PolicyPack,
    *,
    rule_id: str,
    relative: str,
    line: int | None,
    message: str,
    excerpt: str = "",
    risk: RiskLevel | None = None,
    severity: str | None = None,
    auto_fix: bool = False,
    extra: str = "",
) -> Finding:
    rule = policy.rules.get(rule_id)
    selected_risk = risk or (rule.default_risk if rule else RiskLevel.REVIEW_REQUIRED)
    selected_severity = severity or (rule.severity if rule else "medium")
    title = rule.title if rule else rule_id
    evidence = [Evidence(source="repository", location=f"{relative}:{line or 1}", excerpt=excerpt)]
    if rule:
        evidence.append(Evidence(source=rule.source_url, location=rule.rule_id))
    return Finding(
        finding_id=_finding_id(rule_id, relative, line, extra),
        rule_id=rule_id,
        severity=selected_severity,
        title=title,
        message=message,
        path=relative,
        line=line,
        risk=selected_risk,
        confidence=1.0 if auto_fix else 0.9,
        evidence=evidence,
        auto_fix_available=auto_fix,
    )


def _safe_relative_image(html_path: Path, src: str, root: Path) -> Path | None:
    if not src or src.startswith(("data:", "//", "#")):
        return None
    parsed = urlsplit(src)
    if parsed.scheme or parsed.netloc:
        return None
    raw_path = unquote(parsed.path)
    if not raw_path or "\x00" in raw_path:
        return None
    if raw_path.startswith("/"):
        candidate = root / raw_path.lstrip("/")
        if not candidate.is_file():
            for public_name in ("public", "static"):
                alternative = root / public_name / raw_path.lstrip("/")
                if alternative.is_file():
                    candidate = alternative
                    break
    else:
        candidate = html_path.parent / raw_path
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


def image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = struct.unpack(">II", data[16:24])
        return (width, height) if width and height else None
    if len(data) >= 10 and data[:6] in (b"GIF87a", b"GIF89a"):
        width, height = struct.unpack("<HH", data[6:10])
        return (width, height) if width and height else None
    if len(data) >= 30 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        kind = data[12:16]
        if kind == b"VP8X" and len(data) >= 30:
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
            return width, height
        if kind == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if kind == b"VP8 " and len(data) >= 30 and data[23:26] == b"\x9d\x01\x2a":
            width = int.from_bytes(data[26:28], "little") & 0x3FFF
            height = int.from_bytes(data[28:30], "little") & 0x3FFF
            return (width, height) if width and height else None
    if len(data) >= 4 and data[:2] == b"\xff\xd8":
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            index += 2
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                continue
            if index + 2 > len(data):
                break
            length = int.from_bytes(data[index:index + 2], "big")
            if length < 2 or index + length > len(data):
                break
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                height = int.from_bytes(data[index + 3:index + 5], "big")
                width = int.from_bytes(data[index + 5:index + 7], "big")
                return (width, height) if width and height else None
            index += length
    return None


def _dimension_replacement(raw: str, width: int, height: int, current_width: str | None, current_height: str | None) -> str:
    attributes = ""
    if current_width is None:
        attributes += f' width="{width}"'
    if current_height is None:
        attributes += f' height="{height}"'
    if raw.rstrip().endswith("/>"):
        close_at = raw.rfind("/>")
        return raw[:close_at].rstrip() + attributes + " />" + raw[close_at + 2:]
    close_at = raw.rfind(">")
    return raw[:close_at] + attributes + raw[close_at:] if close_at >= 0 else raw


def audit_repository(root: Path, policy: PolicyPack, *, max_pages: int = 500) -> AuditResult:
    root = root.resolve()
    findings: list[Finding] = []
    safe_fixes: list[SafeFix] = []
    skipped: list[str] = []
    observations: list[PageObservation] = []
    html_paths = sorted(iter_files(root, (".html", ".htm")))
    if len(html_paths) > max_pages:
        skipped.append(f"HTML page budget reached: {max_pages} of {len(html_paths)} files were scanned.")
        html_paths = html_paths[:max_pages]

    for html_path in html_paths:
        relative = html_path.relative_to(root).as_posix()
        try:
            if html_path.stat().st_size > 5_000_000:
                skipped.append(f"{relative}: skipped because file exceeds 5 MB")
                continue
            source = html_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            skipped.append(f"{relative}: cannot read UTF-8 HTML ({exc})")
            continue
        parser = SEOHTMLParser(source, html_path)
        try:
            parser.feed(source)
            parser.close()
        except Exception as exc:  # HTMLParser should not abort the complete audit
            skipped.append(f"{relative}: parser error ({exc})")
            continue
        page = parser.observation
        observations.append(page)

        if not page.title:
            findings.append(_make_finding(policy, rule_id="ONPAGE-TITLE-001", relative=relative, line=page.title_line or 1, message="The page has no non-empty <title>."))
        if not page.descriptions:
            findings.append(_make_finding(policy, rule_id="ONPAGE-DESCRIPTION-001", relative=relative, line=1, message="The page has no meta description."))
        elif len(page.descriptions) > 1:
            findings.append(_make_finding(policy, rule_id="ONPAGE-DESCRIPTION-002", relative=relative, line=page.descriptions[1][0], message="The page has multiple meta descriptions.", excerpt=str(page.descriptions)))
        if page.html_lang is None or not page.html_lang.strip():
            findings.append(_make_finding(policy, rule_id="ACCESSIBILITY-LANG-001", relative=relative, line=page.html_line or 1, message="The root <html> element has no explicit language."))
        if not page.canonicals:
            findings.append(_make_finding(policy, rule_id="CANONICAL-001", relative=relative, line=1, message="No canonical URL is declared. Codex must not invent one; owner review is required."))
        elif len(page.canonicals) > 1:
            findings.append(_make_finding(policy, rule_id="CANONICAL-002", relative=relative, line=page.canonicals[1][0], message="Multiple canonical links are present.", risk=RiskLevel.ADVISORY_ONLY, severity="high", excerpt=str(page.canonicals)))
        for line in page.noindex_lines:
            findings.append(_make_finding(policy, rule_id="INDEX-NOINDEX-001", relative=relative, line=line, message="A noindex directive is present. It is reported but never removed automatically.", risk=RiskLevel.ADVISORY_ONLY, severity="high", excerpt="noindex"))
        for line, error in page.invalid_jsonld:
            findings.append(_make_finding(policy, rule_id="SCHEMA-JSONLD-001", relative=relative, line=line, message=f"JSON-LD is not valid JSON: {error}", risk=RiskLevel.REVIEW_REQUIRED, severity="high", excerpt=error))
        for line, text in page.untrusted_instructions:
            findings.append(_make_finding(policy, rule_id="SECURITY-PROMPT-INJECTION-001", relative=relative, line=line, message="Instruction-like text was found in an HTML comment. It is evidence only and is never executed.", risk=RiskLevel.ADVISORY_ONLY, severity="high", excerpt=text))

        for image in page.images:
            if not image.alt_present:
                findings.append(_make_finding(policy, rule_id="IMAGE-ALT-001", relative=relative, line=image.line, message="Image has no alt attribute. Alt text requires semantic owner review.", excerpt=image.raw_tag[:240]))
            if image.width is not None and image.height is not None:
                continue
            image_path = _safe_relative_image(html_path, image.src, root)
            dimensions = image_dimensions(image_path) if image_path else None
            if dimensions is None:
                findings.append(_make_finding(policy, rule_id="IMAGE-DIMENSIONS-001", relative=relative, line=image.line, message="Image dimensions are missing and could not be proven from a local image file.", excerpt=image.raw_tag[:240], risk=RiskLevel.REVIEW_REQUIRED))
                continue
            width, height = dimensions
            replacement = _dimension_replacement(image.raw_tag, width, height, image.width, image.height)
            finding = _make_finding(
                policy,
                rule_id="IMAGE-DIMENSIONS-001",
                relative=relative,
                line=image.line,
                message=f"Missing image dimensions are mechanically proven as {width}×{height} from {image_path.relative_to(root).as_posix()}.",
                excerpt=image.raw_tag[:240],
                risk=RiskLevel.AUTO_FIX,
                auto_fix=True,
                extra=f"{image.offset}:{width}x{height}",
            )
            findings.append(finding)
            safe_fixes.append(
                SafeFix(
                    finding_id=finding.finding_id,
                    path=relative,
                    line=image.line,
                    offset=image.offset,
                    original=image.raw_tag,
                    replacement=replacement,
                    description=f"Add proven width={width} and height={height} to local image",
                )
            )

    titles: dict[str, list[PageObservation]] = defaultdict(list)
    for page in observations:
        if page.title:
            titles[page.title.casefold()].append(page)
    for duplicate_pages in titles.values():
        if len(duplicate_pages) < 2:
            continue
        paths = [page.path.relative_to(root).as_posix() for page in duplicate_pages]
        for page in duplicate_pages:
            relative = page.path.relative_to(root).as_posix()
            findings.append(_make_finding(policy, rule_id="ONPAGE-TITLE-002", relative=relative, line=page.title_line or 1, message=f"Title is duplicated across: {', '.join(paths)}", excerpt=page.title, extra="|".join(paths)))

    if observations:
        likely_public = root / "public" if (root / "public").is_dir() else root
        if not (likely_public / "robots.txt").is_file():
            findings.append(_make_finding(policy, rule_id="TECH-ROBOTS-001", relative=likely_public.relative_to(root).as_posix() or ".", line=1, message="robots.txt was not found in the detected public root. Creation requires review."))
        if not any((likely_public / name).is_file() for name in ("sitemap.xml", "sitemap_index.xml")):
            findings.append(_make_finding(policy, rule_id="TECH-SITEMAP-001", relative=likely_public.relative_to(root).as_posix() or ".", line=1, message="No XML sitemap was found in the detected public root. Generation requires route ownership review."))
    else:
        skipped.append("No static HTML files were found; framework source is not rewritten without an explicit adapter.")

    findings.sort(key=lambda item: (item.path, item.line or 0, item.rule_id, item.finding_id))
    safe_fixes.sort(key=lambda item: (item.path, item.offset))
    return AuditResult(findings=findings, safe_fixes=safe_fixes, pages_scanned=len(observations), skipped=skipped)


def apply_safe_fixes(
    root: Path,
    fixes: list[SafeFix],
    *,
    max_changed_files: int = 10,
    max_diff_lines: int = 200,
) -> list[Change]:
    root = root.resolve()
    grouped: dict[str, list[SafeFix]] = defaultdict(list)
    for fix in fixes:
        if fix.risk != RiskLevel.AUTO_FIX:
            raise ValueError(f"non-auto fix supplied: {fix.finding_id}")
        grouped[fix.path].append(fix)
    if len(grouped) > max_changed_files:
        raise BudgetExceeded(f"change budget exceeded: {len(grouped)} files > {max_changed_files}")

    proposals: dict[Path, tuple[str, str, list[SafeFix], int]] = {}
    total_diff_lines = 0
    for relative, file_fixes in grouped.items():
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"fix escapes repository: {relative}") from exc
        before = candidate.read_text(encoding="utf-8")
        after = before
        for fix in sorted(file_fixes, key=lambda item: item.offset, reverse=True):
            end = fix.offset + len(fix.original)
            if fix.offset < 0 or after[fix.offset:end] != fix.original:
                raise RuntimeError(f"stale evidence for {fix.finding_id}; source changed since audit")
            after = after[:fix.offset] + fix.replacement + after[end:]
        diff_lines = sum(
            1
            for line in difflib.ndiff(before.splitlines(), after.splitlines())
            if line.startswith(("+ ", "- "))
        )
        total_diff_lines += diff_lines
        proposals[candidate] = (before, after, file_fixes, diff_lines)
    if total_diff_lines > max_diff_lines:
        raise BudgetExceeded(f"diff budget exceeded: {total_diff_lines} lines > {max_diff_lines}")

    changes: list[Change] = []
    for path, (before, after, file_fixes, diff_lines) in proposals.items():
        if before == after:
            continue
        payload = after.encode("utf-8")
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
        changes.append(
            Change(
                path=path.relative_to(root).as_posix(),
                description="; ".join(dict.fromkeys(fix.description for fix in file_fixes)),
                risk=RiskLevel.AUTO_FIX,
                before_sha256=sha256_bytes(before.encode("utf-8")),
                after_sha256=sha256_bytes(payload),
                lines_changed=diff_lines,
                finding_ids=[fix.finding_id for fix in file_fixes],
            )
        )
    return changes
