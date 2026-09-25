"""End-to-end checks for the detached runner."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "long_task.py"


class RunnerIntegrationTest(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def wait_for_completion(self, run_dir):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            result = self.run_cli("status", "--run-dir", str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            state = json.loads(result.stdout)
            if state["status"] in {"succeeded", "failed"}:
                return state
            time.sleep(0.1)
        self.fail("Detached command did not finish within 15 seconds")

    def test_success_and_failure_recorded(self):
        with tempfile.TemporaryDirectory() as temporary:
            if os.name == "nt":
                cases = (("success", "Write-Output hello", 0), ("failure", "Write-Output error; exit 7", 7))
            else:
                cases = (("success", "printf 'hello\\n'", 0), ("failure", "printf 'error\\n' >&2; exit 7", 7))
            for name, command, expected_code in cases:
                with self.subTest(name=name):
                    result = self.run_cli(
                        "start", "--name", name, "--cwd", temporary,
                        "--estimate", "unknown", "--cmd", command,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    run = json.loads(result.stdout)
                    run_dir = Path(run["run_dir"])
                    status = self.wait_for_completion(run_dir)
                    self.assertEqual(status["exit_code"], expected_code)
                    self.assertEqual((run_dir / "exit_code").read_text().strip(), str(expected_code))
                    self.assertFalse((run_dir / "command.tmp").exists())
                    log = self.run_cli("log", "--run-dir", str(run_dir), "--tail", "1")
                    self.assertEqual(log.returncode, 0, log.stderr)
                    self.assertIn("hello" if expected_code == 0 else "error", log.stdout)


if __name__ == "__main__":
    unittest.main()
