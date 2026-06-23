"""Tests for `axm report`: the MIDD certificate report for each outcome, the
self-consistency of the proof-identity hash, and that the committed example
report stays in sync with the generator.
"""

from __future__ import annotations

import json
import pathlib

from axm import certify
from axm.report import proof_hash, report

REPO = pathlib.Path(__file__).resolve().parent.parent
EXAMPLE = REPO / "examples" / "drugX_infusion.json"
COMMITTED_REPORT = REPO / "examples" / "drugX_infusion.report.md"
COMMITTED_LEAN = REPO / "lean" / "BioPKPD" / "CertExample.lean"


def _spec() -> dict:
    return json.loads(EXAMPLE.read_text())


def test_certified_report_has_all_sections():
    out = certify(_spec())
    md = report(_spec(), out)
    for heading in ("Theorem", "Assumptions", "Parameter provenance",
                    "Proof identity", "Model-risk note"):
        assert heading in md
    # Provenance from the spec must appear.
    assert "FOCEI (NONMEM)" in md
    assert "run 14" in md


def test_report_hash_matches_emitted_lean():
    """The proof-identity hash must equal sha256 of the emitted artifact, which
    must equal the committed, kernel-checked file."""
    out = certify(_spec())
    h = proof_hash(out.lean)
    assert h in report(_spec(), out)
    import hashlib
    assert h == hashlib.sha256(COMMITTED_LEAN.read_bytes()).hexdigest()


def test_committed_report_in_sync():
    out = certify(_spec())
    assert report(_spec(), out) == COMMITTED_REPORT.read_text()


def test_refused_report_emits_no_theorem():
    s = _spec()
    s["compartments"] = 3
    out = certify(s)
    md = report(s, out)
    assert "REFUSED" in md
    assert "fail closed" in md
    # No proof identity / theorem section for a refusal.
    assert "Proof identity" not in md
    assert "Model-risk note" in md


def test_failed_report_is_a_finding_not_a_proof():
    s = _spec()
    s["threshold"] = 10
    out = certify(s)
    md = report(s, out)
    assert "does **not** hold" in md
    assert "finding, not an error" in md
    assert "Proof identity" not in md
    # Provenance still reported for a failed certificate.
    assert "FOCEI (NONMEM)" in md


def test_missing_provenance_is_flagged():
    s = _spec()
    del s["provenance"]
    out = certify(s)
    md = report(s, out)
    assert "No parameter provenance supplied" in md


# --- repeated-dose report -------------------------------------------------

EXAMPLE_R = REPO / "examples" / "drugY_repeated.json"
COMMITTED_REPORT_R = REPO / "examples" / "drugY_repeated.report.md"
COMMITTED_LEAN_R = REPO / "lean" / "BioPKPD" / "CertExampleRepeated.lean"


def _spec_r() -> dict:
    return json.loads(EXAMPLE_R.read_text())


def test_repeated_report_in_sync():
    out = certify(_spec_r())
    assert report(_spec_r(), out) == COMMITTED_REPORT_R.read_text()


def test_repeated_report_names_its_schema_and_hash():
    out = certify(_spec_r())
    md = report(_spec_r(), out)
    assert "repeated IV bolus" in md
    assert "repeated_dose_window_rational" in md
    assert "ke_hi·τ < 1" in md
    import hashlib
    assert hashlib.sha256(COMMITTED_LEAN_R.read_bytes()).hexdigest() in md
