from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WindowsUtf8GateTests(unittest.TestCase):
    def test_utf8_wrapper_survives_cp1251_strict_console(self) -> None:
        wrapper = ROOT / "scripts" / "verify_local_utf8.py"
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "cp1251:strict"
        env["PYTHONUTF8"] = "0"
        completed = subprocess.run(
            [sys.executable, str(wrapper), "--self-test-console"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        stdout = completed.stdout.decode("utf-8")
        stderr = completed.stderr.decode("utf-8")
        self.assertIn("UTF-8 console probe: \ufffd ✓", stdout)
        self.assertIn("UTF-8 stderr probe: \ufffd ✓", stderr)

    def test_windows_launcher_forwards_release_args_and_forces_utf8(self) -> None:
        text = (ROOT / "VERIFY_LOCAL_WINDOWS.cmd").read_text(encoding="utf-8")
        self.assertIn("chcp 65001", text)
        self.assertIn('set "PYTHONUTF8=1"', text)
        self.assertIn('set "PYTHONIOENCODING=utf-8"', text)
        self.assertIn("-X utf8 scripts\\verify_local_utf8.py %*", text)


if __name__ == "__main__":
    unittest.main()
