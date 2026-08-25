from __future__ import annotations

import argparse
import json
import os
import shutil
import site
import sys
from pathlib import Path


MARKER = ".seo-autopilot-managed.json"


def _source_root() -> Path:
    candidate = Path(__file__).resolve().parents[2]
    required = [candidate / "VERSION", candidate / "src" / "seo_autopilot", candidate / "skills" / "seo-autopilot" / "SKILL.md"]
    if not all(path.exists() for path in required):
        raise RuntimeError("run the installer from an unpacked SEO Autopilot User or Engineering Edition")
    return candidate


def _user_site() -> Path:
    value = site.getusersitepackages()
    if isinstance(value, (list, tuple)):
        if not value:
            raise RuntimeError("Python did not report a user site-packages directory")
        value = value[0]
    return Path(value).expanduser().resolve()


def _scripts_dir() -> Path:
    base = Path(site.USER_BASE).expanduser().resolve()
    return base / ("Scripts" if os.name == "nt" else "bin")


def _safe_replace_tree(source: Path, target: Path, *, force: bool, metadata: dict[str, object]) -> None:
    marker = target / MARKER
    if target.exists():
        if not force and not marker.is_file():
            raise RuntimeError(f"refusing to replace unmanaged directory: {target}")
        shutil.rmtree(target)
    temporary = target.with_name(target.name + f".tmp-{os.getpid()}")
    if temporary.exists():
        shutil.rmtree(temporary)
    shutil.copytree(source, temporary, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
    (temporary / MARKER).write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)


def _install_dist_info(user_site: Path, version: str) -> Path:
    normalized = version.replace("-", "_")
    target = user_site / f"seo_autopilot_codex-{normalized}.dist-info"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    (target / "METADATA").write_text(
        "Metadata-Version: 2.1\n"
        "Name: seo-autopilot-codex\n"
        f"Version: {version}\n"
        "Summary: Evidence-driven SEO audit and conservative remediation for OpenAI Codex\n",
        encoding="utf-8",
    )
    (target / "top_level.txt").write_text("seo_autopilot\n", encoding="utf-8")
    (target / "INSTALLER").write_text("seo-autopilot-local-installer\n", encoding="utf-8")
    (target / "RECORD").write_text("\n", encoding="utf-8")
    return target


def _install_launcher(version: str) -> Path:
    scripts = _scripts_dir()
    scripts.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        launcher = scripts / "seo-autopilot.cmd"
        launcher.write_text(
            "@echo off\r\n"
            f'"{sys.executable}" -m seo_autopilot %*\r\n',
            encoding="utf-8",
        )
    else:
        launcher = scripts / "seo-autopilot"
        launcher.write_text(
            "#!/bin/sh\n"
            f'exec "{sys.executable}" -m seo_autopilot "$@"\n',
            encoding="utf-8",
        )
        launcher.chmod(0o755)
    return launcher


def install(*, codex_home: Path | None = None, force: bool = False) -> dict[str, str]:
    root = _source_root()
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise RuntimeError("VERSION is empty")

    user_site = _user_site()
    user_site.mkdir(parents=True, exist_ok=True)
    package_target = user_site / "seo_autopilot"
    metadata = {"schema_version": 1, "product": "seo-autopilot-codex", "version": version}
    _safe_replace_tree(root / "src" / "seo_autopilot", package_target, force=force, metadata=metadata)
    dist_info = _install_dist_info(user_site, version)

    home = (codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))).expanduser().resolve()
    skill_target = home / "skills" / "seo-autopilot"
    skill_target.parent.mkdir(parents=True, exist_ok=True)
    _safe_replace_tree(root / "skills" / "seo-autopilot", skill_target, force=force, metadata=metadata)

    launcher = _install_launcher(version)
    return {
        "version": version,
        "package": str(package_target),
        "dist_info": str(dist_info),
        "skill": str(skill_target),
        "launcher": str(launcher),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install SEO Autopilot locally without network access or build dependencies.")
    parser.add_argument("--codex-home")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = install(
            codex_home=Path(args.codex_home) if args.codex_home else None,
            force=args.force,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    scripts = _scripts_dir()
    if str(scripts) not in os.environ.get("PATH", "").split(os.pathsep):
        print(f"NOTE: add {scripts} to PATH to call seo-autopilot directly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
