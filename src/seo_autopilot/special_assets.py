from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


MAX_SITE_VERIFICATION_BYTES = 16_384

_GOOGLE_FILENAME_RE = re.compile(r"^google(?P<token>[a-z0-9_-]{8,128})\.html$", re.IGNORECASE)
_YANDEX_FILENAME_RE = re.compile(r"^yandex[_-]?(?P<token>[a-z0-9_-]{8,128})\.html$", re.IGNORECASE)
_GOOGLE_CONTENT_RE = re.compile(
    r"^\ufeff?\s*google-site-verification\s*:\s*(?P<filename>[a-z0-9_.-]+)\s*$",
    re.IGNORECASE,
)
_YANDEX_CONTENT_RE = re.compile(
    r"\bVerification\s*:\s*(?P<token>[a-z0-9_-]{8,128})\b",
    re.IGNORECASE,
)

_NEXTJS_METADATA_ROOTS = {
    ("app",),
    ("src", "app"),
}
_NEXTJS_DYNAMIC_SUFFIXES = {".js", ".ts"}


@dataclass(frozen=True)
class SiteVerificationAsset:
    provider: str
    path: str
    reason: str


def _relative_posix(root: Path, path: Path) -> str | None:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return None


def _allowed_public_location(relative: str) -> bool:
    parts = PurePosixPath(relative.replace("\\", "/")).parts
    if len(parts) == 1:
        return True
    return bool(parts) and parts[0].casefold() in {"public", "static"}


def classify_site_verification_asset(root: Path, path: Path) -> SiteVerificationAsset | None:
    """Recognize exact, small ownership-verification files without treating them as pages."""

    relative = _relative_posix(root, path)
    if relative is None or not _allowed_public_location(relative):
        return None
    try:
        if path.is_symlink() or not path.is_file():
            return None
        size = path.stat().st_size
    except OSError:
        return None
    if size <= 0 or size > MAX_SITE_VERIFICATION_BYTES:
        return None

    name = path.name
    google_match = _GOOGLE_FILENAME_RE.fullmatch(name)
    yandex_match = _YANDEX_FILENAME_RE.fullmatch(name)
    if google_match is None and yandex_match is None:
        return None

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None

    if google_match is not None:
        content_match = _GOOGLE_CONTENT_RE.fullmatch(text)
        if content_match and content_match.group("filename").casefold() == name.casefold():
            return SiteVerificationAsset(
                provider="google",
                path=relative,
                reason="google_site_ownership_verification_file",
            )
        return None

    assert yandex_match is not None
    content_match = _YANDEX_CONTENT_RE.search(text)
    if content_match and content_match.group("token").casefold() == yandex_match.group("token").casefold():
        return SiteVerificationAsset(
            provider="yandex",
            path=relative,
            reason="yandex_site_ownership_verification_file",
        )
    return None


def _dynamic_metadata_endpoint(relative: str, text: str) -> str | None:
    parts = PurePosixPath(relative.replace("\\", "/")).parts
    if len(parts) < 2:
        return None
    parent = tuple(part.casefold() for part in parts[:-1])
    if parent not in _NEXTJS_METADATA_ROOTS:
        return None

    name = Path(parts[-1]).name.casefold()
    suffix = Path(name).suffix
    stem = Path(name).stem
    if suffix not in _NEXTJS_DYNAMIC_SUFFIXES or stem not in {"robots", "sitemap"}:
        return None
    if re.search(r"\bexport\s+default\b", text) is None:
        return None
    return "robots.txt" if stem == "robots" else "sitemap.xml"


def nextjs_metadata_route_owners(root: Path, framework_paths: Iterable[Path]) -> dict[str, str]:
    """Return deterministic source owners for Next.js metadata endpoints."""

    owners: dict[str, str] = {}

    for relative, endpoint in (
        ("app/robots.txt", "robots.txt"),
        ("src/app/robots.txt", "robots.txt"),
        ("app/sitemap.xml", "sitemap.xml"),
        ("src/app/sitemap.xml", "sitemap.xml"),
    ):
        candidate = root / relative
        try:
            if candidate.is_file() and not candidate.is_symlink():
                owners.setdefault(endpoint, relative)
        except OSError:
            continue

    for path in framework_paths:
        relative = _relative_posix(root, path)
        if relative is None:
            continue
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        endpoint = _dynamic_metadata_endpoint(relative, text)
        if endpoint:
            owners.setdefault(endpoint, relative)

    return dict(sorted(owners.items()))
