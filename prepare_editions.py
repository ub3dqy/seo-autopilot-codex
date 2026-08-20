#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path, PurePosixPath

BUNDLE_SHA256 = '5f96d6ddc4bc4211599d6399fe287e08f44012d20011b5dd9898e913e8b82a28'
USER_DIRNAME = 'seo-autopilot-codex-user-v1.4.0'
ENGINEERING_DIRNAME = 'seo-autopilot-codex-engineering-v1.4.0'
USER_ZIP = 'seo-autopilot-codex-user-v1.4.0.zip'
ENGINEERING_ZIP = 'seo-autopilot-codex-engineering-v1.4.0.zip'
USER_SHA256 = 'e03e522fb7767ad7597452fac78cb982aac4c83337573054a32b3f19516d399e'
ENGINEERING_SHA256 = '27791aa36257d878c87bc591a03f25ff21ec79fec5251ef34c4a2fe67126db45'

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def safe_extract(archive: Path, destination: Path) -> None:
    with tarfile.open(archive, 'r:xz') as handle:
        for member in handle.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts:
                raise SystemExit(f'unsafe archive path: {member.name}')
            if member.issym() or member.islnk():
                raise SystemExit(f'archive links are not allowed: {member.name}')
        handle.extractall(destination, filter='data')

def replace_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)

def main() -> int:
    parser = argparse.ArgumentParser(description='Materialize SEO Autopilot User and Engineering editions from the verified repository bundle.')
    parser.add_argument('--build-zips', action='store_true', help='Also rebuild exact release ZIP files in dist/.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    parts = sorted((root / 'packages' / 'source-bundle-v1.4.0').glob('part-*'))
    if not parts:
        raise SystemExit('source bundle parts are missing')
    encoded = ''.join(part.read_text(encoding='ascii').strip() for part in parts)
    payload = base64.b64decode(encoded, validate=True)
    actual_bundle = hashlib.sha256(payload).hexdigest()
    if actual_bundle != BUNDLE_SHA256:
        raise SystemExit(f'source bundle SHA-256 mismatch: {actual_bundle}')
    with tempfile.TemporaryDirectory(prefix='seo-autopilot-editions-') as temp_name:
        temp = Path(temp_name)
        archive = temp / 'bundle.tar.xz'
        archive.write_bytes(payload)
        extracted = temp / 'extracted'
        extracted.mkdir()
        safe_extract(archive, extracted)
        user_source = extracted / 'user' / USER_DIRNAME
        engineering_source = extracted / 'engineering' / ENGINEERING_DIRNAME
        if not (user_source / 'README.md').is_file() or not (engineering_source / 'README.md').is_file():
            raise SystemExit('bundle layout validation failed')
        replace_tree(user_source, root / 'user')
        replace_tree(engineering_source, root / 'engineering')
    print(f"User Edition: {root / 'user'}")
    print(f"Engineering Edition: {root / 'engineering'}")
    if args.build_zips:
        dist = root / 'dist'
        dist.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='seo-autopilot-build-') as build_name:
            build_root = Path(build_name) / ENGINEERING_DIRNAME
            shutil.copytree(root / 'engineering', build_root)
            subprocess.run([sys.executable, str(build_root / 'scripts' / 'build_user_release.py'), '--package-root', str(build_root), '--output-dir', str(dist)], check=True)
            subprocess.run([sys.executable, str(build_root / 'scripts' / 'build_release.py'), '--package-root', str(build_root), '--output', str(dist / ENGINEERING_ZIP), '--skip-checks'], check=True)
        for name, expected in {USER_ZIP: USER_SHA256, ENGINEERING_ZIP: ENGINEERING_SHA256}.items():
            actual = sha256(dist / name)
            if actual != expected:
                raise SystemExit(f'{name}: SHA-256 mismatch: {actual}')
            print(f'{name}: {actual}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
