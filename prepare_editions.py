#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Iterable


MARKER_NAME = ".seo-autopilot-generated.json"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_release(root: Path) -> tuple[dict[str, Any], str]:
    manifest_path = root / "release-manifest.json"
    version_path = root / "VERSION"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise SystemExit("release-manifest.json must use schema_version 1")
    if manifest.get("version_file") != "VERSION":
        raise SystemExit("release manifest version_file must be VERSION")
    version = version_path.read_text(encoding="utf-8").strip()
    if not version or any(char not in "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-+" for char in version):
        raise SystemExit(f"invalid VERSION: {version!r}")
    return manifest, version


def iter_tree(root: Path, *, include_marker: bool = False) -> Iterable[Path]:
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if not include_marker and relative.as_posix() == MARKER_NAME:
            continue
        yield path


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in iter_tree(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def marker_payload(edition: str, version: str, content_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generator": "prepare_editions.py",
        "edition": edition,
        "version": version,
        "content_sha256": content_sha256,
    }


def write_marker(target: Path, edition: str, version: str) -> None:
    payload = marker_payload(edition, version, tree_digest(target))
    (target / MARKER_NAME).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_generated_tree(target: Path, edition: str | None = None) -> dict[str, Any]:
    marker = target / MARKER_NAME
    if not marker.is_file():
        raise SystemExit(f"refusing to manage unmarked directory: {target}")
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid generated marker in {target}: {exc}") from exc
    if payload.get("schema_version") != 1 or payload.get("generator") != "prepare_editions.py":
        raise SystemExit(f"unrecognized generated marker in {target}")
    if edition is not None and payload.get("edition") != edition:
        raise SystemExit(f"edition mismatch in {target}: {payload.get('edition')} != {edition}")
    actual = tree_digest(target)
    if payload.get("content_sha256") != actual:
        raise SystemExit(
            f"generated directory has local modifications: {target}\n"
            f"expected {payload.get('content_sha256')}, calculated {actual}. Use --force only after review."
        )
    return payload


def validate_source_entry(root: Path, relative: str) -> Path:
    source = (root / relative).resolve()
    try:
        source.relative_to(root.resolve())
    except ValueError as exc:
        raise SystemExit(f"release entry escapes repository: {relative}") from exc
    if not source.exists():
        raise SystemExit(f"release entry is missing: {relative}")
    if source.is_symlink():
        raise SystemExit(f"release symlinks are not allowed: {relative}")
    if source.is_dir():
        for path in source.rglob("*"):
            if path.is_symlink():
                raise SystemExit(f"release symlinks are not allowed: {path.relative_to(root)}")
    return source


def copy_entry(root: Path, relative: str, destination: Path) -> None:
    source = validate_source_entry(root, relative)
    target = destination / relative
    if source.is_dir():
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", MARKER_NAME),
        )
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def replace_generated_tree(target: Path, prepared: Path, edition: str, force: bool) -> None:
    if target.exists():
        if force:
            shutil.rmtree(target)
        else:
            verify_generated_tree(target, edition)
            backup = target.with_name(target.name + ".backup")
            if backup.exists():
                raise SystemExit(f"stale backup prevents atomic replacement: {backup}")
            target.replace(backup)
            try:
                prepared.replace(target)
            except BaseException:
                backup.replace(target)
                raise
            shutil.rmtree(backup)
            return
    prepared.replace(target)


def materialize_edition(root: Path, manifest: dict[str, Any], version: str, edition: str, force: bool) -> Path:
    entries = manifest.get("editions", {}).get(edition)
    if not isinstance(entries, list) or not all(isinstance(item, str) for item in entries):
        raise SystemExit(f"invalid edition list: {edition}")
    target = root / edition
    with tempfile.TemporaryDirectory(prefix=f"seo-autopilot-{edition}-", dir=str(root)) as temp_name:
        temporary_root = Path(temp_name)
        prepared = temporary_root / edition
        prepared.mkdir()
        for relative in entries:
            copy_entry(root, relative, prepared)
        if edition == "user":
            user_readme = prepared / "USER_EDITION.md"
            if user_readme.is_file():
                shutil.copy2(user_readme, prepared / "README.md")
        write_marker(prepared, edition, version)
        staged = root / f".{edition}.prepared-{os.getpid()}"
        if staged.exists():
            shutil.rmtree(staged)
        prepared.replace(staged)
    replace_generated_tree(target, staged, edition, force)
    verify_generated_tree(target, edition)
    return target


def deterministic_zip(source: Path, output: Path, archive_root: str) -> None:
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in iter_tree(source, include_marker=True):
            relative = Path(archive_root) / path.relative_to(source)
            info = zipfile.ZipInfo(relative.as_posix(), FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            mode = stat.S_IMODE(path.stat().st_mode)
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    temporary.replace(output)


def build_archives(root: Path, manifest: dict[str, Any], version: str, edition_paths: dict[str, Path], force: bool) -> list[dict[str, Any]]:
    dist = root / "dist"
    if dist.exists() and not force:
        marker = dist / MARKER_NAME
        if marker.is_file():
            verify_generated_tree(dist, "dist")
        elif any(dist.iterdir()):
            raise SystemExit("refusing to replace unmanaged non-empty dist/. Use --force after review.")
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir()
    artifacts: list[dict[str, Any]] = []
    templates = manifest.get("artifacts", {})
    for edition in ("user", "engineering"):
        template = templates.get(edition)
        if not isinstance(template, str):
            raise SystemExit(f"artifact template missing: {edition}")
        name = template.format(version=version)
        output = dist / name
        archive_root = name.removesuffix(".zip")
        deterministic_zip(edition_paths[edition], output, archive_root)
        artifacts.append(
            {
                "edition": edition,
                "filename": name,
                "sha256": sha256_file(output),
                "bytes": output.stat().st_size,
            }
        )
    sums = "".join(f"{item['sha256']}  {item['filename']}\n" for item in artifacts)
    (dist / "SHA256SUMS").write_text(sums, encoding="utf-8")
    report = {
        "schema_version": 1,
        "product": manifest.get("product"),
        "version": version,
        "artifacts": artifacts,
    }
    (dist / "release-build.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_marker(dist, "dist", version)
    verify_generated_tree(dist, "dist")
    return artifacts


def verify_source(root: Path, manifest: dict[str, Any], version: str) -> None:
    if version != (root / "VERSION").read_text(encoding="utf-8").strip():
        raise SystemExit("VERSION changed during verification")
    for edition in ("user", "engineering"):
        entries = manifest.get("editions", {}).get(edition)
        if not isinstance(entries, list):
            raise SystemExit(f"missing edition manifest: {edition}")
        for relative in entries:
            validate_source_entry(root, relative)
    for name in ("user", "engineering", "dist"):
        target = root / name
        if target.exists():
            verify_generated_tree(target, name)


def clean_generated(root: Path, force: bool) -> None:
    for name in ("user", "engineering", "dist"):
        target = root / name
        if not target.exists():
            continue
        if not force:
            verify_generated_tree(target, name)
        shutil.rmtree(target)
        print(f"removed: {target}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build transparent, deterministic SEO Autopilot User and Engineering editions from the tracked source tree."
    )
    parser.add_argument("--build-zips", action="store_true", help="Build deterministic ZIP files in dist/.")
    parser.add_argument("--verify-only", action="store_true", help="Verify source and existing generated trees without writing files.")
    parser.add_argument("--clean", action="store_true", help="Remove only generated user/, engineering/ and dist/ trees.")
    parser.add_argument("--force", action="store_true", help="Replace generated or unmanaged output after explicit review.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest, version = load_release(root)

    if args.clean:
        clean_generated(root, args.force)
        return 0
    verify_source(root, manifest, version)
    if args.verify_only:
        print(f"source verification: PASS (v{version})")
        return 0

    edition_paths = {
        edition: materialize_edition(root, manifest, version, edition, args.force)
        for edition in ("user", "engineering")
    }
    print(f"User Edition: {edition_paths['user']}")
    print(f"Engineering Edition: {edition_paths['engineering']}")
    if args.build_zips:
        artifacts = build_archives(root, manifest, version, edition_paths, args.force)
        for artifact in artifacts:
            print(f"{artifact['filename']}: {artifact['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
