"""Check informational CLI commands without initializing agents."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    """Keep the CLI lightweight and the public class import available."""

    def test_help_and_version_do_not_load_trading_agents(self):
        """Help and version must work without trading-module imports."""
        code = """
import importlib.abc
import runpy
import sys

class RejectTradingImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname in ("autohedge.main", "swarms"):
            raise AssertionError("Trading import: " + fullname)

sys.meta_path.insert(0, RejectTradingImports())
sys.argv = ["autohedge", sys.argv[1]]
runpy.run_module("autohedge", run_name="__main__")
"""
        env = {
            key: os.environ[key]
            for key in (
                "PATH",
                "SYSTEMROOT",
                "TMP",
                "TEMP",
                "USERPROFILE",
                "HOME",
            )
            if key in os.environ
        }
        env["PYTHONPATH"] = str(ROOT)
        env["PYTHONIOENCODING"] = "utf-8"
        with tempfile.TemporaryDirectory() as directory:
            for argument in ("--help", "help", "--version"):
                with self.subTest(argument=argument):
                    result = subprocess.run(
                        [sys.executable, "-c", code, argument],
                        cwd=directory,
                        env=env,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        timeout=10,
                        check=False,
                    )
                    self.assertEqual(
                        result.returncode, 0, result.stderr
                    )
                    self.assertIn("autohedge", result.stdout.lower())

    def test_public_class_import_is_preserved(self):
        """The package must still expose the lazily imported class."""
        code = """
import sys
import types
import autohedge

assert "autohedge.main" not in sys.modules
main = types.ModuleType("autohedge.main")
main.AutoHedge = type("AutoHedge", (), {})
sys.modules["autohedge.main"] = main
from autohedge import AutoHedge
assert AutoHedge is main.AutoHedge
try:
    autohedge.missing_attribute
except AttributeError:
    pass
else:
    raise AssertionError("Missing attributes must raise AttributeError")
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
