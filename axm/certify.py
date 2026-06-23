"""axm certify — a recognizer + fail-closed certificate emitter for PK/PD
exposure-safety.

This is roadmap step 2 from the project handoff (§5): the piece that turns "I
proved two theorems" into "a system". It mirrors the `bsl certify` pattern
quoted in the handoff (§3):

    recognize a class  ->  compute tight bounds  ->  emit a Lean instance of a
    verified schema  ->  fail closed otherwise.

The *only* verified schema wired up for automatic emission here is the
constant-infusion exposure-safety certificate proved in
`lean/BioPKPD/ConstantInfusion.lean`
(`Bio.PKPD.ConstantInfusion.infusion_safety_bound`). Its certificate condition
is a single rational inequality at the worst-case (smallest-clearance) corner of
the fitted parameter box, so a concrete instance is closed in Lean by `norm_num`
— a fully kernel-checkable artifact with no `sorry`.

Everything outside that subset **fails closed**: a precise, structured reason and
*no* emitted Lean. In particular the repeated-dose schema
(`Bio.PKPD.RepeatedDose.repeated_dose_window`) is *proved* but not auto-emitted,
because its certificate condition is transcendental in `ke` (it contains
`exp(-(ke_lo · τ))`) and is not yet reducible to a `norm_num`-dischargeable
rational; recognizing it returns a refusal that says exactly that.

Discipline (handoff §2), carried verbatim into the output: a certificate is a
statement about *the model under explicitly stated, bounded assumptions*, never a
claim that a drug or dose is safe for a patient.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

# The one model class for which this tool will emit a kernel-checkable proof.
CERTIFIED_SUBSET = (
    "one-compartment, first-order elimination, constant continuous IV infusion"
)


class SpecError(ValueError):
    """The spec is malformed (not a value/shape we can even interpret)."""


@dataclass
class Outcome:
    """Result of `certify`. `status` is one of:

    * ``"certified"`` — in subset and the worst-case certificate condition holds;
      ``lean`` carries a complete, kernel-checkable artifact.
    * ``"failed"``    — in subset but the certificate condition is violated (the
      model *can* exceed the threshold); no Lean emitted.
    * ``"refused"``   — outside the auto-emittable subset; no Lean emitted.

    Only ``"certified"`` ever carries Lean. The other two are the fail-closed
    paths and are deliberately distinct: ``"failed"`` is a real safety finding,
    ``"refused"`` is "I won't pretend to certify something I can't."
    """

    status: str
    reason: str
    lean: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == "certified"


def _frac(x: Any, *, name: str) -> Fraction:
    """Coerce a JSON-ish scalar to an exact rational. Floats go through their
    decimal string so that ``0.3`` becomes ``3/10`` rather than a binary-noise
    approximation."""
    if isinstance(x, bool):  # bool is an int subclass; reject it explicitly
        raise SpecError(f"{name!r} must be a number, got a boolean")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        return Fraction(str(x))
    if isinstance(x, str):
        try:
            return Fraction(x)
        except ValueError as e:
            raise SpecError(f"{name!r} is not a valid number: {x!r}") from e
    raise SpecError(f"{name!r} must be a number, got {type(x).__name__}")


def _interval_lo(spec_params: dict, key: str) -> Fraction:
    """Extract a strictly-positive lower endpoint for parameter ``key``.

    Accepts ``[lo, hi]``, ``[lo]``, a bare scalar (a point estimate, lo == hi),
    or ``{"lo": ...}``. Raises :class:`SpecError` on shape problems and refuses
    (via ValueError to the caller) on non-positive lower bounds is handled in
    ``certify``."""
    if key not in spec_params:
        raise SpecError(f"missing fitted parameter {key!r}")
    v = spec_params[key]
    if isinstance(v, dict):
        if "lo" not in v:
            raise SpecError(f"parameter {key!r} object needs a 'lo' field")
        return _frac(v["lo"], name=f"{key}.lo")
    if isinstance(v, (list, tuple)):
        if not v:
            raise SpecError(f"parameter {key!r} interval is empty")
        return _frac(v[0], name=f"{key}.lo")
    return _frac(v, name=key)


def _lean_num(f: Fraction) -> str:
    """Render an exact rational as a Lean ℝ numeral term."""
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator} / {f.denominator}"


def _lean_lit(f: Fraction) -> str:
    """Render with an explicit ``: ℝ`` ascription (for binders, where the type
    is not otherwise forced)."""
    return f"({_lean_num(f)} : ℝ)"


def _ident(name: str) -> str:
    """Sanitise an arbitrary spec name into a Lean identifier suffix."""
    out = "".join(c if (c.isalnum() or c == "_") else "_" for c in name)
    if not out or not (out[0].isalpha() or out[0] == "_"):
        out = "m_" + out
    return out


def emit_lean(name: str, R: Fraction, ke_lo: Fraction, V_lo: Fraction,
              T: Fraction, worst: Fraction) -> str:
    """Emit a complete, self-contained Lean instance of the constant-infusion
    schema. The certificate hypotheses are discharged by ``norm_num``; the
    interval membership of the actual `ke`, `V`, `t` is left as hypotheses, so
    the conclusion holds for *every* parameter value in the fitted box."""
    thm = f"cert_{_ident(name)}"
    return f"""\
import BioPKPD.ConstantInfusion

open Bio.PKPD.ConstantInfusion

/-- Auto-generated by `axm certify` (do not edit by hand).

Certificate for model spec `{name}`:
{CERTIFIED_SUBSET}.

  infusion rate R = {_lean_num(R)}
  fitted lower bounds: ke_lo = {_lean_num(ke_lo)}, V_lo = {_lean_num(V_lo)}
  toxicity threshold T = {_lean_num(T)}
  worst-case steady-state exposure R / (ke_lo * V_lo) = {_lean_num(worst)} ≤ {_lean_num(T)}  ✓

The plasma concentration the model predicts stays in `[0, T]` for every time
`t ≥ 0` and every parameter value with `ke_lo ≤ ke`, `V_lo ≤ V`. This is a
statement about the model under the stated bounds, not a claim about a patient. -/
theorem {thm} (ke V t : ℝ)
    (hke : {_lean_lit(ke_lo)} ≤ ke) (hV : {_lean_lit(V_lo)} ≤ V) (ht : 0 ≤ t) :
    0 ≤ conc {_lean_num(R)} ke V t ∧ conc {_lean_num(R)} ke V t ≤ {_lean_num(T)} :=
  infusion_safety_bound {_lean_num(R)} ke V t {_lean_num(T)} ({_lean_num(ke_lo)}) ({_lean_num(V_lo)})
    (by norm_num) (by norm_num) hke (by norm_num) hV ht (by norm_num)
"""


def certify(spec: dict) -> Outcome:
    """Recognise, certify, and (on success) emit. Never raises on a well-formed
    dict that is simply out of subset — that is a ``"refused"`` outcome.
    Raises :class:`SpecError` only when the spec is not interpretable at all."""
    if not isinstance(spec, dict):
        raise SpecError("spec must be an object/dict")

    name = str(spec.get("name", "model"))

    # --- Structural recognizer: fail closed on anything outside the subset. ---
    compartments = spec.get("compartments")
    if compartments != 1:
        return Outcome("refused",
                       f"{compartments!r}-compartment model is outside the "
                       f"certified subset ({CERTIFIED_SUBSET})")

    elimination = spec.get("elimination")
    if elimination != "first_order":
        return Outcome("refused",
                       f"elimination {elimination!r} is outside the certified "
                       f"subset (only first-order is supported)")

    input_kind = spec.get("input")
    if input_kind == "repeated_bolus":
        return Outcome("refused",
                       "input 'repeated_bolus' is recognized and proved "
                       "(Bio.PKPD.RepeatedDose.repeated_dose_window) but its "
                       "certificate condition is transcendental in ke "
                       "(contains exp(-(ke_lo*tau))) and is not yet reducible "
                       "to a norm_num-dischargeable rational; out of the "
                       "auto-emittable subset")
    if input_kind != "constant_infusion":
        return Outcome("refused",
                       f"input {input_kind!r} is outside the certified subset "
                       f"(only 'constant_infusion' is auto-emittable)")

    params = spec.get("parameters")
    if not isinstance(params, dict):
        raise SpecError("'parameters' must be an object with ke and V")

    # --- Extract exact rationals; SpecError bubbles up for malformed shapes. ---
    ke_lo = _interval_lo(params, "ke")
    V_lo = _interval_lo(params, "V")
    R = _frac(spec["R"], name="R") if "R" in spec else None
    if R is None:
        raise SpecError("missing infusion rate 'R'")
    if "threshold" not in spec:
        raise SpecError("missing toxicity 'threshold'")
    T = _frac(spec["threshold"], name="threshold")

    # --- Positivity preconditions of the theorem (fail closed, not crash). ---
    if not (ke_lo > 0 and V_lo > 0):
        return Outcome("refused",
                       f"fitted lower bounds must be strictly positive "
                       f"(ke_lo={_lean_num(ke_lo)}, V_lo={_lean_num(V_lo)}); the "
                       f"theorem's clearance hypotheses cannot be met")
    if not R > 0:
        return Outcome("refused",
                       f"infusion rate must be strictly positive (R={_lean_num(R)})")

    # --- The certificate condition, exact at the worst-case corner. ---
    worst = R / (ke_lo * V_lo)
    detail = {
        "name": name,
        "R": str(R),
        "ke_lo": str(ke_lo),
        "V_lo": str(V_lo),
        "threshold": str(T),
        "worst_case_exposure": str(worst),
        "subset": CERTIFIED_SUBSET,
    }

    if worst > T:
        return Outcome(
            "failed",
            f"certificate does NOT hold: worst-case steady-state exposure "
            f"R/(ke_lo*V_lo) = {_lean_num(worst)} exceeds threshold "
            f"{_lean_num(T)}. The model can cross the toxicity bound for "
            f"parameter values in the fitted box.",
            detail=detail,
        )

    lean = emit_lean(name, R, ke_lo, V_lo, T, worst)
    return Outcome(
        "certified",
        f"worst-case steady-state exposure R/(ke_lo*V_lo) = {_lean_num(worst)} "
        f"≤ threshold {_lean_num(T)} for all parameters in the fitted box",
        lean=lean,
        detail=detail,
    )
