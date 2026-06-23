"""Tests for `axm certify`: the accept path, every fail-closed path, and the
guarantee that the committed Lean artifact is exactly what the emitter produces.

Pure Python, no Lean required (the *Lean* side is kernel-checked separately in
the lean workflow). Run with `pytest`.
"""

from __future__ import annotations

import copy
import json
import pathlib

import pytest

from axm import certify
from axm.certify import SpecError

REPO = pathlib.Path(__file__).resolve().parent.parent
EXAMPLE = REPO / "examples" / "drugX_infusion.json"
COMMITTED_LEAN = REPO / "lean" / "BioPKPD" / "CertExample.lean"


def _spec() -> dict:
    return json.loads(EXAMPLE.read_text())


def test_example_certifies():
    out = certify(_spec())
    assert out.ok
    assert out.status == "certified"
    # worst case = R / (ke_lo * V_lo) = 100 / (0.3 * 5) = 200/3
    assert out.detail["worst_case_exposure"] == "200/3"
    assert out.lean is not None and "infusion_safety_bound" in out.lean


def test_emitter_matches_committed_artifact():
    """The repo's kernel-checked CertExample.lean must be byte-identical to a
    fresh emission, so the thing CI proves is the thing the tool produces."""
    out = certify(_spec())
    assert out.lean == COMMITTED_LEAN.read_text()


def test_refuses_multicompartment():
    s = _spec()
    s["compartments"] = 2
    out = certify(s)
    assert out.status == "refused"
    assert out.lean is None
    assert "2-compartment" in out.reason


def test_refuses_nonlinear_elimination():
    s = _spec()
    s["elimination"] = "michaelis_menten"
    out = certify(s)
    assert out.status == "refused"
    assert out.lean is None
    assert "first-order" in out.reason


def test_refuses_repeated_bolus_with_specific_reason():
    s = _spec()
    s["input"] = "repeated_bolus"
    out = certify(s)
    assert out.status == "refused"
    assert out.lean is None
    # Must name *why*: proved but transcendental, not auto-emittable.
    assert "transcendental" in out.reason
    assert "RepeatedDose" in out.reason


def test_refuses_nonpositive_lower_bound():
    s = _spec()
    s["parameters"]["ke"] = [0.0, 0.5]
    out = certify(s)
    assert out.status == "refused"
    assert out.lean is None
    assert "strictly positive" in out.reason


def test_certificate_can_fail_in_subset():
    """A recognized model whose worst-case exposure exceeds the threshold is a
    real safety finding, distinct from a refusal — and emits no Lean."""
    s = _spec()
    s["threshold"] = 10  # 200/3 ≈ 66.7 > 10
    out = certify(s)
    assert out.status == "failed"
    assert out.lean is None
    assert "does NOT hold" in out.reason


def test_boundary_is_certified():
    """Equality at the worst-case corner still certifies (the bound is `≤`)."""
    s = _spec()
    s["threshold"] = "200/3"
    out = certify(s)
    assert out.ok


def test_exact_rationals_no_float_noise():
    s = _spec()
    s["parameters"]["ke"] = [0.1]
    s["parameters"]["V"] = [0.1]
    out = certify(s)
    # 100 / (1/10 * 1/10) = 10000; threshold 80 -> fails, but exactly.
    assert out.detail["worst_case_exposure"] == "10000"
    assert out.status == "failed"


def test_point_estimate_and_object_interval_shapes():
    s = _spec()
    s["parameters"]["ke"] = 0.3          # bare scalar (point estimate)
    s["parameters"]["V"] = {"lo": 5}     # object form
    out = certify(s)
    assert out.ok


def test_malformed_spec_raises():
    s = _spec()
    del s["R"]
    with pytest.raises(SpecError):
        certify(s)


def test_emitted_lean_has_no_sorry():
    out = certify(_spec())
    assert "sorry" not in out.lean
    assert "admit" not in out.lean
