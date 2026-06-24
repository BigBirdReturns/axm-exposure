"""CLI fail-closed contract: exit codes for certified / failed / refused."""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
EX = REPO / "examples"


def _certify(spec: str) -> int:
    return subprocess.run(
        [sys.executable, "-m", "axm", "certify", str(EX / spec)],
        cwd=REPO, capture_output=True,
    ).returncode


def test_exit_codes_are_fail_closed():
    assert _certify("drugX_infusion.json") == 0          # certified
    assert _certify("drugY_repeated.json") == 0          # certified
    assert _certify("failed_infusion.json") == 2         # in-subset finding
    assert _certify("refused_two_compartment.json") == 3 # out of subset
