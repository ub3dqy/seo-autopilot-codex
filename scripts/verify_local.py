#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "local-verification"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
try:
    from prepare_editions import verify_generated_tree, write_marker
    from seo_autopilot.redaction import redact_text
except Exception:  # pragma: no cover - safe fallback before package import is available
    verify_generated_tree = None
    write_marker = None

    def redact_text(text: str, exact_values: Sequence[str] = ()) -> str:
        result = text
        for value in exact_values:
            if value and len(value) >= 8:
                result = result.replace(value, "[REDACTED_EXACT_SECRET]")
        return result


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def source_environment() -> dict[str, str]:
    env = dict(os.environ)
    # Test the package from this checkout, not an unrelated installed copy.
    env["PYTHONPATH"] = str(ROOT / "src")
    return env


class Verification:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.started_at = utc_now()
        self.steps: list[dict[str, Any]] = []
        self.failed = False
        self.report_dir = Path(args.report_dir).resolve()
        self.report_dir.mkdir(parents=True, exist_ok=True)
        stamp = safe_timestamp()
        self.log_path = self.report_dir / f"verification-{stamp}.log"
        self.json_path = self.report_dir / f"verification-{stamp}.json"
        self.latest_log = self.report_dir / "latest.log"
        self.latest_json = self.report_dir / "latest.json"
        self._log_handle = self.log_path.open("w", encoding="utf-8", newline="\n")

    def close(self) -> None:
        self._log_handle.close()

    def log(self, text: str = "") -> None:
        print(text)
        self._log_handle.write(text + "\n")
        self._log_handle.flush()

    def run(
        self,
        name: str,
        argv: Sequence[str],
        *,
        accepted: Sequence[int] = (0,),
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str] | None:
        command = [str(item) for item in argv]
        self.log(f"\n=== {name} ===")
        self.log("$ " + subprocess.list2cmdline(command))
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                shell=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.args.step_timeout,
                env=env,
                check=False,
            )
            returncode = completed.returncode
            stdout = redact_text(completed.stdout)
            stderr = redact_text(completed.stderr)
        except subprocess.TimeoutExpired as exc:
            returncode = 124
            stdout = redact_text(exc.stdout or "")
            stderr = redact_text((exc.stderr or "") + f"\nTimed out after {self.args.step_timeout}s")
            completed = None
        except OSError as exc:
            returncode = 127
            stdout = ""
            stderr = redact_text(str(exc))
            completed = None
        duration = round(time.monotonic() - started, 3)
        if stdout:
            self.log(stdout.rstrip())
        if stderr:
            self.log(stderr.rstrip())
        passed = returncode in accepted
        self.log(f"[{ 'PASS' if passed else 'FAIL' }] returncode={returncode} duration={duration}s")
        self.steps.append(
            {
                "name": name,
                "argv": command,
                "returncode": returncode,
                "accepted_returncodes": list(accepted),
                "duration_seconds": duration,
                "status": "PASS" if passed else "FAIL",
                "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
                "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
            }
        )
        if not passed:
            self.failed = True
        return completed

    def assertion(self, name: str, passed: bool, detail: str) -> None:
        self.log(f"\n=== {name} ===")
        self.log(detail)
        self.log(f"[{ 'PASS' if passed else 'FAIL' }]")
        self.steps.append(
            {
                "name": name,
                "argv": [],
                "returncode": 0 if passed else 1,
                "accepted_returncodes": [0],
                "duration_seconds": 0.0,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )
        if not passed:
            self.failed = True

    def finish(self) -> int:
        git_head = git_value("rev-parse", "HEAD")
        git_branch = git_value("branch", "--show-current")
        git_status = git_value("status", "--porcelain=v1")
        payload: dict[str, Any] = {
            "schema_version": 1,
            "product": "seo-autopilot-codex",
            "mode": "release" if self.args.release else ("build" if self.args.build else "deterministic"),
            "status": "FAIL" if self.failed else "PASS",
            "started_at": self.started_at,
            "finished_at": utc_now(),
            "environment": {
                "platform": platform.platform(),
                "python": sys.version,
                "python_executable": sys.executable,
                "git_head": git_head,
                "git_branch": git_branch,
                "git_dirty": bool(git_status),
            },
            "steps": self.steps,
            "log_file": self.log_path.name,
        }
        if self.args.build and (ROOT / "dist" / "release-build.json").is_file():
            build = json.loads((ROOT / "dist" / "release-build.json").read_text(encoding="utf-8"))
            payload["release"] = build
            sbom = ROOT / "dist" / self.sbom_filename()
            if sbom.is_file():
                payload["release"]["sbom"] = {
                    "filename": sbom.name,
                    "sha256": sha256_file(sbom),
                    "bytes": sbom.stat().st_size,
                }
        self.json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        shutil.copy2(self.json_path, self.latest_json)
        self.log(f"\nVerification status: {payload['status']}")
        self.log(f"JSON evidence: {self.json_path}")
        self.log(f"Log: {self.log_path}")
        self._log_handle.flush()
        shutil.copy2(self.log_path, self.latest_log)
        return 1 if self.failed else 0

    def sbom_filename(self) -> str:
        manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        return manifest["artifacts"]["sbom"].format(version=version)


def read_artifact_hashes() -> dict[str, str]:
    report = json.loads((ROOT / "dist" / "release-build.json").read_text(encoding="utf-8"))
    return {item["filename"]: item["sha256"] for item in report["artifacts"]}


def append_checksum(path: Path, filename: str) -> None:
    sums_path = path / "SHA256SUMS"
    existing = []
    if sums_path.is_file():
        existing = [line for line in sums_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing = [line for line in existing if not line.split(None, 1)[-1].strip().lstrip("*") == filename]
    existing.append(f"{sha256_file(path / filename)}  {filename}")
    sums_path.write_text("\n".join(existing) + "\n", encoding="utf-8")


def seal_dist_marker() -> None:
    """Re-seal the managed dist tree after trusted SBOM/checksum generation."""
    if write_marker is None or verify_generated_tree is None:
        raise RuntimeError("prepare_editions marker helpers are unavailable")
    dist = ROOT / "dist"
    marker = dist / ".seo-autopilot-generated.json"
    if not marker.is_file():
        raise RuntimeError("refusing to seal an unmanaged dist directory")
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid dist marker: {exc}") from exc
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if (
        payload.get("schema_version") != 1
        or payload.get("generator") != "prepare_editions.py"
        or payload.get("edition") != "dist"
        or payload.get("version") != version
    ):
        raise RuntimeError("refusing to seal an unrecognized or version-mismatched dist tree")
    write_marker(dist, "dist", version)
    verify_generated_tree(dist, "dist")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the complete SEO Autopilot verification gate locally, without GitHub Actions."
    )
    parser.add_argument("--build", action="store_true", help="Also build and verify deterministic edition ZIPs and SPDX SBOM.")
    parser.add_argument("--release", action="store_true", help="Run --build and require a clean Git tree for official release evidence.")
    parser.add_argument("--live", action="store_true", help="Also run the optional real Codex canary locally.")
    parser.add_argument("--require-live", action="store_true", help="Treat live canary NOT_RUN as a failure; implies --live.")
    parser.add_argument("--allow-dirty-release", action="store_true", help="Allow release evidence from a dirty Git tree (not recommended).")
    parser.add_argument("--report-dir", default=str(REPORT_DIR), help="Directory for local JSON and log evidence.")
    parser.add_argument("--step-timeout", type=int, default=1800, help="Timeout per subprocess in seconds.")
    args = parser.parse_args()
    if args.require_live:
        args.live = True
    if args.release:
        args.build = True

    verification = Verification(args)
    source_env = source_environment()
    try:
        verification.log("SEO Autopilot local verification (GitHub Actions not required)")
        verification.log(f"Root: {ROOT}")
        verification.log(f"Started: {verification.started_at}")

        verification.run("Python version", [sys.executable, "--version"])
        verification.run("Git availability", ["git", "--version"])

        if args.release:
            status = git_value("status", "--porcelain=v1")
            clean = status == ""
            if status is None:
                allowed = False
                detail = "Official release evidence requires a Git checkout; Git status was unavailable."
            elif clean:
                allowed = True
                detail = "Git tree is clean."
            elif args.allow_dirty_release:
                allowed = True
                detail = "Git tree has uncommitted changes. Proceeding only because --allow-dirty-release was supplied."
            else:
                allowed = False
                detail = "Git tree has uncommitted changes."
            verification.assertion("Release clean-tree gate", allowed, detail)
            if not allowed:
                return verification.finish()

        verification.run(
            "Compile Python sources",
            [sys.executable, "-m", "compileall", "-q", "src", "scripts", "tests", "prepare_editions.py"],
        )
        verification.run(
            "Source-layout import smoke test",
            [sys.executable, "-c", "import seo_autopilot; print(seo_autopilot.__file__)"],
            env=source_env,
        )
        verification.run(
            "Deterministic unit and lifecycle tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            env=source_env,
        )
        verification.run(
            "Tracked-source and generated-tree verification",
            [sys.executable, "prepare_editions.py", "--verify-only"],
        )
        verification.run("Tracked-source secret scan", [sys.executable, "scripts/secret_scan.py"])

        if args.build and not verification.failed:
            verification.run(
                "Build deterministic editions (pass 1)",
                [sys.executable, "prepare_editions.py", "--build-zips"],
            )
            first = read_artifact_hashes() if not verification.failed else {}
            if not verification.failed:
                verification.run(
                    "Build deterministic editions (pass 2)",
                    [sys.executable, "prepare_editions.py", "--build-zips"],
                )
            second = read_artifact_hashes() if not verification.failed else {}
            verification.assertion(
                "Release reproducibility",
                bool(first) and first == second,
                f"pass_1={first}\npass_2={second}",
            )
            if not verification.failed:
                sbom_name = verification.sbom_filename()
                verification.run(
                    "Generate deterministic SPDX SBOM",
                    [sys.executable, "scripts/generate_sbom.py", "--root", ".", "--output", f"dist/{sbom_name}"],
                )
                if not verification.failed:
                    append_checksum(ROOT / "dist", sbom_name)
                    try:
                        seal_dist_marker()
                    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
                        verification.assertion("Seal generated release tree", False, str(exc))
                    else:
                        verification.assertion(
                            "Seal generated release tree",
                            True,
                            "Managed dist marker updated after SBOM and SHA256SUMS generation.",
                        )
                    if not verification.failed:
                        verification.run(
                            "Verify local release assets",
                            [sys.executable, "scripts/verify_release.py", "dist"],
                        )
                        verification.run(
                            "Post-build generated-tree verification",
                            [sys.executable, "prepare_editions.py", "--verify-only"],
                        )

        if args.live and not verification.failed:
            accepted = (0,) if args.require_live else (0, 2)
            verification.run(
                "Optional live Codex canary",
                [
                    sys.executable,
                    "scripts/live_codex_eval.py",
                    "--output",
                    str(verification.report_dir / "live-codex-eval.json"),
                ],
                accepted=accepted,
            )

        return verification.finish()
    except Exception as exc:
        verification.log(f"\nInternal verification error: {redact_text(repr(exc))}")
        verification.steps.append(
            {
                "name": "Verification harness",
                "argv": [],
                "returncode": 1,
                "accepted_returncodes": [0],
                "duration_seconds": 0.0,
                "status": "FAIL",
                "detail": redact_text(repr(exc)),
            }
        )
        verification.failed = True
        return verification.finish()
    finally:
        verification.close()


if __name__ == "__main__":
    raise SystemExit(main())
