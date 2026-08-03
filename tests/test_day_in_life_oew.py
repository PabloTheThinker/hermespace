"""CI-facing day-in-the-life OEW proof (runs the experiment script)."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestDayInLifeOEW(unittest.TestCase):
    def test_day_in_life_script_passes(self) -> None:
        env = os.environ.copy()
        env["HERMESPACE_OEW"] = "1"
        env["PYTHONPATH"] = str(ROOT / "src") + (
            os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )
        proc = subprocess.run(
            [sys.executable, str(ROOT / "experiments" / "day_in_life_oew.py")],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            self.fail(proc.stdout + "\n" + proc.stderr)
        self.assertIn('"fail": 0', proc.stdout)


if __name__ == "__main__":
    unittest.main()
