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
EXAMPLE_R = REPO / "examples" / "drugY_repeated.json"
COMMITTED_LEAN_R = REPO / "lean" / "BioPKPD" / "CertExampleRepeated.lean"


def _spec() -> dict:
    return json.loads(EXAMPLE.read_text())


def _spec_r() -> dict:
    return json.loads(EXAMPLE_R.read_text())


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
    s["compartments"] = 3  # 1 and 2 are certifiable; 3+ is out of subset
    out = certify(s)
    assert out.status == "refused"
    assert out.lean is None
    assert "3-compartment" in out.reason


def test_refuses_nonlinear_elimination():
    s = _spec()
    s["elimination"] = "michaelis_menten"
    out = certify(s)
    assert out.status == "refused"
    assert out.lean is None
    assert "first-order" in out.reason


def test_repeated_bolus_is_now_a_certify_path_not_a_refusal():
    """Regression: repeated_bolus used to be refused outright; it now routes to
    the rational repeated-dose schema. A constant-infusion spec relabelled
    repeated_bolus is simply malformed (missing D/tau/Ceff/Ctox)."""
    s = _spec()
    s["input"] = "repeated_bolus"
    with pytest.raises(SpecError):
        certify(s)


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


# --- repeated-dose schema -------------------------------------------------

def test_repeated_example_certifies():
    out = certify(_spec_r())
    assert out.ok
    assert out.detail["schema"] == "repeated_dose_rational"
    # a = ke_lo*tau = 0.08*8 = 16/25; tox = 20*(1+16/25)/(40*16/25) = 41/32
    assert out.detail["tox_ceiling"] == "41/32"
    # b = ke_hi*tau = 0.1*8 = 4/5; eff = 20*(1-4/5)/(60*4/5) = 1/12
    assert out.detail["eff_floor"] == "1/12"
    assert "repeated_dose_window_rational" in out.lean
    assert "sorry" not in out.lean


def test_repeated_emitter_matches_committed_artifact():
    out = certify(_spec_r())
    assert out.lean == COMMITTED_LEAN_R.read_text()


def test_repeated_fractional_args_are_parenthesized():
    """Regression: fractional term-position args must be parenthesized so the
    application does not misparse (`f a / b` binds application before `/`)."""
    out = certify(_spec_r())
    assert "(1 / 20) (3 / 2)" in out.lean  # Ceff, Ctox in the application


def test_repeated_refuses_when_kehi_tau_ge_one():
    s = _spec_r()
    s["tau"] = 12  # ke_hi*tau = 0.1*12 = 1.2 ≥ 1
    out = certify(s)
    assert out.status == "refused"
    assert out.lean is None
    assert "ke_hi·τ < 1" in out.reason


def test_repeated_toxicity_can_fail():
    s = _spec_r()
    s["Ctox"] = 1  # rational ceiling 41/32 ≈ 1.28 > 1
    out = certify(s)
    assert out.status == "failed"
    assert out.lean is None
    assert "toxicity" in out.reason


def test_repeated_efficacy_can_fail():
    s = _spec_r()
    s["Ceff"] = 1  # 1 > rational floor 1/12
    out = certify(s)
    assert out.status == "failed"
    assert out.lean is None
    assert "efficacy" in out.reason


def test_repeated_requires_both_endpoints():
    s = _spec_r()
    s["parameters"]["ke"] = [0.08]  # point estimate -> lo == hi, allowed
    out = certify(s)
    assert out.ok  # ke_hi == ke_lo == 0.08, still valid


# --- two-compartment schema -----------------------------------------------

EXAMPLE_2C = REPO / "examples" / "drugW_two_compartment.json"
COMMITTED_LEAN_2C = REPO / "lean" / "BioPKPD" / "CertExampleTwoCompartment.lean"


def _spec_2c() -> dict:
    return json.loads(EXAMPLE_2C.read_text())


def test_two_compartment_certifies():
    out = certify(_spec_2c())
    assert out.ok
    assert out.detail["schema"] == "two_compartment_ss"
    # peripheral compartment cancels: same ceiling as 1-cpt, R/(ke_lo*V1_lo)=200/3
    assert out.detail["worst_case_exposure"] == "200/3"
    assert "central_steady_state_bound" in out.lean
    assert "sorry" not in out.lean


def test_two_compartment_emitter_matches_committed_artifact():
    out = certify(_spec_2c())
    assert out.lean == COMMITTED_LEAN_2C.read_text()


def test_two_compartment_accepts_V_alias():
    s = _spec_2c()
    s["parameters"]["V"] = s["parameters"].pop("V1")  # central volume as "V"
    out = certify(s)
    assert out.ok


def test_two_compartment_can_fail():
    s = _spec_2c()
    s["threshold"] = 10  # 200/3 ≈ 66.7 > 10
    out = certify(s)
    assert out.status == "failed"
    assert out.lean is None


def test_two_compartment_non_infusion_refused():
    s = _spec_2c()
    s["input"] = "repeated_bolus"
    out = certify(s)
    assert out.status == "refused"
    assert out.lean is None
    assert "two-compartment" in out.reason
