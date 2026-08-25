from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from seo_autopilot.doctor import detect_stack, run_doctor
from seo_autopilot.models import RiskLevel, RunStatus
from seo_autopilot.policy import classify_change, load_policy_pack
from seo_autopilot.transaction import GitTransaction, rollback_from_state
from seo_autopilot.trusted_commands import UntrustedCommandError, command_digest, load_trusted_commands


ROOT = Path(__file__).resolve().parents[1]


class CoreTests(unittest.TestCase):
    def test_stack_detection(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"next": "15.0.0", "react": "19.0.0"}}),
                encoding="utf-8",
            )
            self.assertEqual(detect_stack(root), "nextjs")

    def test_policy_pack_and_risk_floor(self) -> None:
        policy = load_policy_pack(ROOT / "policy-packs" / "google-search" / "2026-08" / "policies.json")
        self.assertIn("INDEX-NOINDEX-001", policy.rules)
        self.assertEqual(
            classify_change("public/robots.txt", "Add an allow rule", mechanically_proven=True),
            RiskLevel.ADVISORY_ONLY,
        )
        self.assertEqual(
            classify_change("index.html", "Change canonical", mechanically_proven=True),
            RiskLevel.REVIEW_REQUIRED,
        )
        self.assertEqual(
            classify_change("index.html", "Add proven dimensions", mechanically_proven=True),
            RiskLevel.AUTO_FIX,
        )

    def test_trusted_commands_require_exact_digest(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            argv = ["python", "-m", "unittest"]
            config = {
                "schema_version": 1,
                "checks": [
                    {
                        "name": "tests",
                        "argv": argv,
                        "sha256": command_digest(argv),
                        "timeout_seconds": 60,
                    }
                ],
            }
            (root / ".seo-autopilot.json").write_text(json.dumps(config), encoding="utf-8")
            commands = load_trusted_commands(root)
            self.assertEqual(commands[0].argv, tuple(argv))
            config["checks"][0]["argv"][-1] = "compileall"
            (root / ".seo-autopilot.json").write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(UntrustedCommandError):
                load_trusted_commands(root)

    @unittest.skipUnless(shutil.which("git"), "Git is required")
    def test_isolated_transaction_keeps_owner_tree_unchanged_and_bypasses_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "repo"
            root.mkdir()
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test Owner"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "owner@example.invalid"], cwd=root, check=True)
            (root / "index.html").write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "index.html"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)
            hook_marker = Path(name) / "hook-ran"
            hook = root / ".git" / "hooks" / "pre-commit"
            hook.write_text(f"#!/bin/sh\nprintf ran > '{hook_marker.as_posix()}'\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)
            state_path = Path(name) / "state.json"
            transaction = GitTransaction(root, "test-run-123", state_path)
            worktree = transaction.start()
            (worktree / "index.html").write_text("after\n", encoding="utf-8")
            commit = transaction.commit("test transaction")
            self.assertIsNotNone(commit)
            transaction.close_success()
            self.assertEqual((root / "index.html").read_text(encoding="utf-8"), "before\n")
            shown = subprocess.run(
                ["git", "show", f"{transaction.branch}:index.html"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(shown.stdout, "after\n")
            self.assertFalse(hook_marker.exists())
            removed_branch = rollback_from_state(state_path)
            self.assertEqual(removed_branch, transaction.branch)
            branch_check = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{transaction.branch}"],
                cwd=root,
                check=False,
            )
            self.assertNotEqual(branch_check.returncode, 0)

    @unittest.skipUnless(shutil.which("git"), "Git is required")
    def test_doctor_blocks_dirty_fix_state(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test Owner"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "owner@example.invalid"], cwd=root, check=True)
            (root / "index.html").write_text("<html></html>\n", encoding="utf-8")
            subprocess.run(["git", "add", "index.html"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)
            (root / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            doctor = run_doctor(root)
            self.assertEqual(doctor.status, RunStatus.REVIEW_REQUIRED)
            self.assertFalse(doctor.clean_worktree)


if __name__ == "__main__":
    unittest.main()
