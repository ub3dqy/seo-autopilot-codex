from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from . import __version__
from .doctor import detect_stack, git_commit, run_doctor
from .engine import BudgetExceeded, apply_safe_fixes, audit_repository
from .models import CheckResult, Phase, RiskLevel, RunReport, RunStatus
from .policy import load_policy_pack
from .reporting import has_review_findings, write_reports
from .transaction import GitTransaction, rollback_from_state
from .trusted_commands import (
    UntrustedCommandError,
    command_digest,
    execute_trusted_commands,
    load_trusted_commands,
)
from .utils import run_process, utc_now


def _source_root() -> Path | None:
    candidates = [Path.cwd(), Path(__file__).resolve()]
    for candidate in candidates:
        start = candidate if candidate.is_dir() else candidate.parent
        for parent in (start, *start.parents):
            if (parent / "release-manifest.json").is_file() and (parent / "policy-packs").is_dir():
                return parent
    return None


def _shared_asset(*parts: str) -> Path | None:
    candidate = Path(sys.prefix) / "share" / "seo-autopilot" / Path(*parts)
    return candidate if candidate.exists() else None


def _policy_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    source = _source_root()
    if source:
        candidate = source / "policy-packs" / "google-search" / "2026-08" / "policies.json"
        if candidate.is_file():
            return candidate
    shared = _shared_asset("policy-packs", "google-search", "2026-08", "policies.json")
    if shared:
        return shared
    raise FileNotFoundError("cannot locate the bundled SEO policy pack")


def _run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{secrets.token_hex(4)}"


def _output_dir(root: Path, run_id: str, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    return root / ".seo-autopilot" / "runs" / run_id


def _report_status(findings, *, failed: bool = False) -> RunStatus:
    if failed:
        return RunStatus.FAILED
    if any(finding.status == "OPEN" for finding in findings):
        return RunStatus.REVIEW_REQUIRED
    return RunStatus.PASSED


def _print_paths(paths: tuple[Path, Path, Path]) -> None:
    print(f"run.json: {paths[0]}")
    print(f"report.md: {paths[1]}")
    print(f"report.html: {paths[2]}")


def command_doctor(args: argparse.Namespace) -> int:
    result = run_doctor(Path(args.path))
    payload = {
        "status": result.status.value,
        "repository_root": result.repository_root,
        "stack": result.stack,
        "git_available": result.git_available,
        "codex_available": result.codex_available,
        "clean_worktree": result.clean_worktree,
        "limitations": result.limitations,
        "blockers": result.blockers,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Status: {result.status.value}")
        print(f"Repository: {result.repository_root or 'NOT_FOUND'}")
        print(f"Stack: {result.stack}")
        for item in result.limitations:
            print(f"LIMITATION: {item}")
        for item in result.blockers:
            print(f"BLOCKER: {item}")
    return 2 if result.status == RunStatus.BLOCKED else 1 if result.status == RunStatus.REVIEW_REQUIRED else 0


def command_audit(args: argparse.Namespace) -> int:
    requested = Path(args.path).expanduser().resolve()
    if not requested.is_dir():
        raise FileNotFoundError(f"directory not found: {requested}")
    doctor = run_doctor(requested)
    root = Path(doctor.repository_root) if doctor.repository_root else requested
    policy = load_policy_pack(_policy_path(args.policy_pack))
    run_id = _run_id()
    started = utc_now()
    audit = audit_repository(root, policy, max_pages=args.max_pages)
    report = RunReport(
        schema_version=1,
        run_id=run_id,
        product_version=__version__,
        policy_pack_version=policy.version,
        status=RunStatus.REVIEW_REQUIRED if audit.findings else RunStatus.PASSED,
        phase=Phase.EVIDENCE_COMPLETE,
        repository_root=str(root),
        repository_commit=git_commit(root) if doctor.repository_root else None,
        detected_stack=detect_stack(root),
        started_at=started,
        finished_at=utc_now(),
        mode="audit",
        findings=audit.findings,
        planned_fixes=audit.safe_fixes,
        skipped=[*doctor.limitations, *doctor.blockers, *audit.skipped],
        residual_risks=[
            "Audit mode never changes repository files.",
            "Ranking, indexing and rich-result outcomes are not guaranteed by technical conformance.",
        ],
        budgets={"max_pages": args.max_pages},
        external_sources=list(policy.sources),
    )
    paths = write_reports(report, _output_dir(root, run_id, args.output))
    _print_paths(paths)
    print(f"Findings: {len(report.findings)}; safe fix candidates: {len(report.planned_fixes)}")
    return 1 if report.findings else 0


def _builtin_diff_check(root: Path) -> CheckResult:
    completed = run_process(
        ["git", "-c", "core.hooksPath=/dev/null", "diff", "--check"],
        cwd=root,
        timeout=60,
    )
    return CheckResult(
        name="git diff --check",
        status=RunStatus.PASSED if completed.returncode == 0 else RunStatus.FAILED,
        command=["git", "diff", "--check"],
        returncode=completed.returncode,
        stdout_tail=completed.stdout[-4000:],
        stderr_tail=completed.stderr[-4000:],
    )


def command_fix(args: argparse.Namespace) -> int:
    requested = Path(args.path).expanduser().resolve()
    doctor = run_doctor(requested)
    if doctor.repository_root is None:
        print("BLOCKED: fix mode requires a Git repository.", file=sys.stderr)
        return 2
    root = Path(doctor.repository_root)
    if not doctor.clean_worktree:
        print("BLOCKED: fix mode requires a clean working tree.", file=sys.stderr)
        return 2

    policy = load_policy_pack(_policy_path(args.policy_pack))
    run_id = _run_id()
    output = _output_dir(root, run_id, args.output)
    state_path = output / "state.json"
    started = utc_now()
    initial = audit_repository(root, policy, max_pages=args.max_pages)
    report = RunReport(
        schema_version=1,
        run_id=run_id,
        product_version=__version__,
        policy_pack_version=policy.version,
        status=RunStatus.READY,
        phase=Phase.PLAN_COMPLETE,
        repository_root=str(root),
        repository_commit=git_commit(root),
        detected_stack=doctor.stack,
        started_at=started,
        mode="fix",
        findings=initial.findings,
        planned_fixes=initial.safe_fixes,
        skipped=[*doctor.limitations, *initial.skipped],
        budgets={
            "max_pages": args.max_pages,
            "max_changed_files": args.max_changed_files,
            "max_diff_lines": args.max_diff_lines,
        },
        external_sources=list(policy.sources),
    )
    transaction: GitTransaction | None = None

    if not initial.safe_fixes:
        report.status = _report_status(report.findings)
        report.finished_at = utc_now()
        report.residual_risks.append("No mechanically proven A-level fix was available; no branch was created.")
        paths = write_reports(report, output)
        _print_paths(paths)
        return 1 if report.status == RunStatus.REVIEW_REQUIRED else 0

    try:
        transaction = GitTransaction(root, run_id, state_path)
        worktree = transaction.start()
        report.branch = transaction.branch
        report.rollback = [f"seo-autopilot rollback --state {state_path}"]
        transaction.update_phase(Phase.PLAN_COMPLETE)

        worktree_audit = audit_repository(worktree, policy, max_pages=args.max_pages)
        changes = apply_safe_fixes(
            worktree,
            worktree_audit.safe_fixes,
            max_changed_files=args.max_changed_files,
            max_diff_lines=args.max_diff_lines,
        )
        report.changes = changes
        fixed_ids = {finding_id for change in changes for finding_id in change.finding_ids}
        for finding in report.findings:
            if finding.finding_id in fixed_ids:
                finding.status = "FIXED"
        transaction.update_phase(Phase.PATCH_APPLIED)

        checks = [_builtin_diff_check(worktree)]
        if checks[-1].status == RunStatus.PASSED:
            trusted = load_trusted_commands(worktree)
            checks.extend(execute_trusted_commands(worktree, trusted))
        report.checks = checks
        failed = any(check.status == RunStatus.FAILED for check in checks)

        verification = audit_repository(worktree, policy, max_pages=args.max_pages)
        changed_paths = {change.path for change in changes}
        repeated = [fix for fix in verification.safe_fixes if fix.path in changed_paths]
        if repeated:
            failed = True
            report.checks.append(
                CheckResult(
                    name="idempotency check",
                    status=RunStatus.FAILED,
                    stderr_tail="Safe fixes are still proposed after the first application.",
                )
            )
        else:
            report.checks.append(CheckResult(name="idempotency check", status=RunStatus.PASSED))
        transaction.update_phase(Phase.VALIDATION_COMPLETE)

        if failed:
            transaction.rollback()
            report.phase = Phase.ROLLED_BACK
            report.status = RunStatus.FAILED
            report.residual_risks.append("Validation failed; the isolated worktree and transaction branch were removed.")
        else:
            commit = transaction.commit(f"fix(seo): apply proven SEO corrections ({run_id})")
            if commit is None:
                transaction.rollback()
                report.phase = Phase.ROLLED_BACK
                report.status = RunStatus.FAILED
                report.residual_risks.append("No Git diff remained after the planned fix; the transaction was rolled back.")
            else:
                transaction.close_success()
                report.phase = Phase.COMMITTED
                report.status = _report_status(report.findings)
                report.residual_risks.extend(
                    [
                        f"Changes remain isolated on local branch {transaction.branch}; nothing was pushed, merged or deployed.",
                        "B- and C-level findings require owner review.",
                    ]
                )
    except (BudgetExceeded, UntrustedCommandError, OSError, RuntimeError, ValueError) as exc:
        if transaction is not None:
            try:
                transaction.rollback()
                report.phase = Phase.ROLLED_BACK
            except Exception as rollback_error:
                report.residual_risks.append(f"Rollback also reported an error: {rollback_error}")
                report.phase = Phase.FAILED
        else:
            report.phase = Phase.FAILED
        report.status = RunStatus.FAILED
        report.skipped.append(str(exc))
    finally:
        report.finished_at = utc_now()
        paths = write_reports(report, output)
        _print_paths(paths)

    print(f"Status: {report.status.value}")
    print(f"Branch: {report.branch or 'NONE'}")
    return 0 if report.status == RunStatus.PASSED else 1


def command_rollback(args: argparse.Namespace) -> int:
    branch = rollback_from_state(Path(args.state).expanduser().resolve())
    print(f"Rolled back transaction branch: {branch}")
    return 0


def command_verify(args: argparse.Namespace) -> int:
    run_path = Path(args.run_json).expanduser().resolve()
    payload = json.loads(run_path.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "run_id",
        "product_version",
        "policy_pack_version",
        "status",
        "phase",
        "repository_root",
        "detected_stack",
        "findings",
        "changes",
        "checks",
    }
    missing = sorted(required - set(payload))
    if missing:
        print(f"INVALID: missing fields: {', '.join(missing)}", file=sys.stderr)
        return 1
    if payload.get("schema_version") != 1:
        print("INVALID: unsupported schema_version", file=sys.stderr)
        return 1
    if not isinstance(payload.get("findings"), list) or not isinstance(payload.get("changes"), list):
        print("INVALID: findings and changes must be arrays", file=sys.stderr)
        return 1
    print("VALID: run.json satisfies the built-in release schema gate")
    return 0


def _skill_source() -> Path:
    source = _source_root()
    if source and (source / "skills" / "seo-autopilot" / "SKILL.md").is_file():
        return source / "skills" / "seo-autopilot"
    shared = _shared_asset("skills", "seo-autopilot")
    if shared and (shared / "SKILL.md").is_file():
        return shared
    raise FileNotFoundError("cannot locate bundled Codex skill")


def command_install_skill(args: argparse.Namespace) -> int:
    source = _skill_source()
    codex_home = Path(args.codex_home or os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
    target = codex_home / "skills" / "seo-autopilot"
    marker = target / ".seo-autopilot-managed"
    if target.exists():
        if not marker.is_file() and not args.force:
            raise RuntimeError(f"refusing to replace unmanaged skill directory: {target}")
        if args.force or marker.is_file():
            shutil.rmtree(target)
    temporary = target.with_name(target.name + ".tmp")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, temporary)
    (temporary / ".seo-autopilot-managed").write_text(f"version={__version__}\n", encoding="utf-8")
    temporary.replace(target)
    print(f"Installed Codex skill: {target}")
    return 0


def command_hash(args: argparse.Namespace) -> int:
    argv = list(args.argv)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        print("command-hash requires an argv after --", file=sys.stderr)
        return 2
    print(command_digest(argv))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seo-autopilot",
        description="Evidence-driven SEO audit and conservative remediation for OpenAI Codex.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check Git, Codex, stack and transaction readiness.")
    doctor.add_argument("path", nargs="?", default=".")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(handler=command_doctor)

    audit = subparsers.add_parser("audit", help="Audit without modifying repository files.")
    audit.add_argument("path", nargs="?", default=".")
    audit.add_argument("--output")
    audit.add_argument("--policy-pack")
    audit.add_argument("--max-pages", type=int, default=500)
    audit.set_defaults(handler=command_audit)

    fix = subparsers.add_parser("fix", help="Apply only mechanically proven A-level fixes in an isolated Git worktree.")
    fix.add_argument("path", nargs="?", default=".")
    fix.add_argument("--output")
    fix.add_argument("--policy-pack")
    fix.add_argument("--max-pages", type=int, default=500)
    fix.add_argument("--max-changed-files", type=int, default=10)
    fix.add_argument("--max-diff-lines", type=int, default=200)
    fix.set_defaults(handler=command_fix)

    rollback = subparsers.add_parser("rollback", help="Delete an SEO Autopilot worktree and owned local branch.")
    rollback.add_argument("--state", required=True)
    rollback.set_defaults(handler=command_rollback)

    verify = subparsers.add_parser("verify", help="Validate a generated run.json.")
    verify.add_argument("run_json")
    verify.set_defaults(handler=command_verify)

    install = subparsers.add_parser("install-skill", help="Install the bundled skill into CODEX_HOME.")
    install.add_argument("--codex-home")
    install.add_argument("--force", action="store_true")
    install.set_defaults(handler=command_install_skill)

    digest = subparsers.add_parser("command-hash", help="Calculate the trust digest for an exact argv array.")
    digest.add_argument("argv", nargs=argparse.REMAINDER)
    digest.set_defaults(handler=command_hash)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, PermissionError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
