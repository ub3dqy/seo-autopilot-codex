from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .models import Phase
from .utils import run_process, utc_now


RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,79}$")


@dataclass
class TransactionState:
    run_id: str
    repository_root: str
    base_commit: str
    branch: str
    worktree: str
    phase: Phase
    created_at: str
    commit: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "schema_version": "1",
            "run_id": self.run_id,
            "repository_root": self.repository_root,
            "base_commit": self.base_commit,
            "branch": self.branch,
            "worktree": self.worktree,
            "phase": self.phase.value,
            "created_at": self.created_at,
            "commit": self.commit,
        }


class GitTransaction:
    def __init__(self, repository_root: Path, run_id: str, state_path: Path) -> None:
        self.root = repository_root.resolve()
        if not RUN_ID_RE.fullmatch(run_id):
            raise ValueError("invalid run id")
        self.run_id = run_id
        self.branch = f"seo-autopilot/{run_id}"
        self.state_path = state_path.resolve()
        self.worktree_root = Path(tempfile.gettempdir()) / "seo-autopilot-worktrees" / self.root.name
        self.worktree = self.worktree_root / run_id
        self.state: TransactionState | None = None

    def _git(self, argv: list[str], *, cwd: Path | None = None, timeout: int = 120):
        return run_process(
            ["git", "-c", "core.hooksPath=/dev/null", *argv],
            cwd=cwd or self.root,
            timeout=timeout,
        )

    def _write_state(self) -> None:
        if self.state is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.state.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)

    def update_phase(self, phase: Phase) -> None:
        if self.state is None:
            raise RuntimeError("transaction has not started")
        self.state.phase = phase
        self._write_state()

    def start(self) -> Path:
        clean = self._git(["status", "--porcelain=v1", "--untracked-files=normal"])
        if clean.returncode != 0:
            raise RuntimeError(clean.stderr.strip() or "cannot inspect Git worktree")
        if clean.stdout.strip():
            raise RuntimeError("fix mode requires a clean working tree")
        base = self._git(["rev-parse", "HEAD"])
        if base.returncode != 0:
            raise RuntimeError(base.stderr.strip() or "cannot resolve HEAD")
        branch_exists = self._git(["show-ref", "--verify", "--quiet", f"refs/heads/{self.branch}"])
        if branch_exists.returncode == 0:
            raise RuntimeError(f"transaction branch already exists: {self.branch}")
        if self.worktree.exists():
            raise RuntimeError(f"transaction worktree already exists: {self.worktree}")
        self.worktree_root.mkdir(parents=True, exist_ok=True)
        added = self._git(["worktree", "add", "--detach", str(self.worktree), base.stdout.strip()], timeout=180)
        if added.returncode != 0:
            raise RuntimeError(added.stderr.strip() or "cannot create isolated worktree")
        created = self._git(["switch", "-c", self.branch], cwd=self.worktree)
        if created.returncode != 0:
            self._git(["worktree", "remove", "--force", str(self.worktree)], timeout=180)
            raise RuntimeError(created.stderr.strip() or "cannot create transaction branch")
        self.state = TransactionState(
            run_id=self.run_id,
            repository_root=str(self.root),
            base_commit=base.stdout.strip(),
            branch=self.branch,
            worktree=str(self.worktree),
            phase=Phase.INITIALIZED,
            created_at=utc_now(),
        )
        self._write_state()
        return self.worktree

    def commit(self, message: str) -> str | None:
        if self.state is None:
            raise RuntimeError("transaction has not started")
        add = self._git(["add", "--all"], cwd=self.worktree)
        if add.returncode != 0:
            raise RuntimeError(add.stderr.strip() or "git add failed")
        staged = self._git(["diff", "--cached", "--quiet"], cwd=self.worktree)
        if staged.returncode == 0:
            return None
        if staged.returncode != 1:
            raise RuntimeError(staged.stderr.strip() or "cannot inspect staged changes")
        committed = self._git(
            [
                "-c",
                "user.name=SEO Autopilot",
                "-c",
                "user.email=seo-autopilot@localhost.invalid",
                "commit",
                "--no-verify",
                "-m",
                message,
            ],
            cwd=self.worktree,
            timeout=180,
        )
        if committed.returncode != 0:
            raise RuntimeError(committed.stderr.strip() or "git commit failed")
        resolved = self._git(["rev-parse", "HEAD"], cwd=self.worktree)
        if resolved.returncode != 0:
            raise RuntimeError(resolved.stderr.strip() or "cannot resolve transaction commit")
        self.state.commit = resolved.stdout.strip()
        self.state.phase = Phase.COMMITTED
        self._write_state()
        return self.state.commit

    def close_success(self) -> None:
        if self.worktree.exists():
            removed = self._git(["worktree", "remove", "--force", str(self.worktree)], timeout=180)
            if removed.returncode != 0:
                raise RuntimeError(removed.stderr.strip() or "cannot remove transaction worktree")
        self._git(["worktree", "prune"])

    def rollback(self) -> None:
        if self.worktree.exists():
            self._git(["worktree", "remove", "--force", str(self.worktree)], timeout=180)
        branch_exists = self._git(["show-ref", "--verify", "--quiet", f"refs/heads/{self.branch}"])
        if branch_exists.returncode == 0:
            deleted = self._git(["branch", "-D", self.branch])
            if deleted.returncode != 0:
                raise RuntimeError(deleted.stderr.strip() or "cannot delete transaction branch")
        self._git(["worktree", "prune"])
        if self.state is not None:
            self.state.phase = Phase.ROLLED_BACK
            self._write_state()


def rollback_from_state(state_path: Path) -> str:
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    root = Path(payload["repository_root"]).resolve()
    branch = str(payload["branch"])
    worktree = Path(payload["worktree"]).resolve()
    if not branch.startswith("seo-autopilot/"):
        raise ValueError("refusing to delete a branch not owned by SEO Autopilot")
    if worktree.exists():
        result = run_process(
            ["git", "-c", "core.hooksPath=/dev/null", "worktree", "remove", "--force", str(worktree)],
            cwd=root,
            timeout=180,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "cannot remove worktree")
    result = run_process(
        ["git", "-c", "core.hooksPath=/dev/null", "branch", "-D", branch],
        cwd=root,
        timeout=60,
    )
    if result.returncode != 0 and "not found" not in result.stderr.lower():
        raise RuntimeError(result.stderr.strip() or "cannot remove branch")
    payload["phase"] = Phase.ROLLED_BACK.value
    state_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if worktree.parent.exists() and not any(worktree.parent.iterdir()):
        shutil.rmtree(worktree.parent, ignore_errors=True)
    return branch
