import Mathlib

/-!
# PK/PD flagship: a constant-infusion exposure-safety certificate

This is the lead vertical of the "real version" sketched in the project handoff:
**parameter-bounded exposure-safety certificates for Model-Informed Drug
Development (MIDD).** It is the smallest *non-trivial* case — a single IV bolus
decays monotonically so its safety bound collapses to `C0 ≤ T` and proves
nothing; constant infusion to steady state does not.

## The model

One-compartment model under a constant continuous IV infusion at rate `R`, with
first-order elimination rate constant `ke` and distribution volume `V` (so
clearance `CL = ke * V`). The analytic solution of `V * C' = R - CL * C`,
`C(0) = 0`, is

  `C(t) = (R / (ke * V)) * (1 - exp (-(ke * t)))`.

The parameters `ke` and `V` are not known exactly; they are *fitted with
uncertainty* and known only to lie in intervals with strictly positive lower
endpoints. The question a pharmacometrician actually asks is: **for every
parameter value in the fitted confidence interval, does the model's plasma
concentration stay under the toxicity threshold `T`?**

## What is and isn't claimed

This is a machine-checked proof of **model consistency under explicitly stated,
bounded assumptions** — exactly the standard the rest of this project holds
itself to. It says: *given the model equation and the stated parameter box, the
concentration the model predicts never exceeds `T`.* It is **not** a claim that
a drug or dose is safe for a patient. The proof is about the model, not the
patient (handoff §2.3). The certificate condition is checked at the worst-case
(smallest-clearance) corner of the box, `R / (ke_lo * V_lo)`.

Kernel-checked by Lean + Mathlib in CI; see `.github/workflows/lean.yml`.
-/

namespace Bio.PKPD.ConstantInfusion

/-- Plasma concentration at time `t` for a one-compartment model under a constant
continuous IV infusion of rate `R`, first-order elimination rate constant `ke`,
and distribution volume `V` (clearance `CL = ke * V`):

  `C(t) = (R / (ke * V)) * (1 - exp (-(ke * t)))`. -/
noncomputable def conc (R ke V t : ℝ) : ℝ :=
  (R / (ke * V)) * (1 - Real.exp (-(ke * t)))

/-- **Constant-infusion exposure-safety certificate.**

For a one-compartment constant-infusion model with infusion rate `R > 0`,
where the elimination rate `ke` and volume `V` are known only to lie in fitted
intervals with strictly positive lower endpoints (`0 < ke_lo ≤ ke`,
`0 < V_lo ≤ V`), the plasma concentration stays within `[0, T]` at every time
`t ≥ 0`, provided the **certificate condition** `R / (ke_lo * V_lo) ≤ T` holds.

`R / (ke_lo * V_lo)` is the worst-case steady-state exposure — the smallest
clearance the fitted box allows. Because steady-state exposure is decreasing in
both `ke` and `V`, controlling that one corner controls the whole box: the bound
holds for **every** parameter value in the stated interval.

The conclusion is two-sided on purpose: a real exposure certificate asserts both
that the model concentration is non-negative (a physical sanity invariant that
uses `t ≥ 0`) and that it never crosses the toxicity threshold. -/
theorem infusion_safety_bound
    (R ke V t T ke_lo V_lo : ℝ)
    (hR : 0 < R)
    (hke_lo : 0 < ke_lo) (hke : ke_lo ≤ ke)
    (hV_lo : 0 < V_lo) (hV : V_lo ≤ V)
    (ht : 0 ≤ t)
    (hcert : R / (ke_lo * V_lo) ≤ T) :
    0 ≤ conc R ke V t ∧ conc R ke V t ≤ T := by
  have hke0 : 0 < ke := lt_of_lt_of_le hke_lo hke
  have hV0 : 0 < V := lt_of_lt_of_le hV_lo hV
  have hD : 0 < ke * V := mul_pos hke0 hV0
  have hD0 : 0 < ke_lo * V_lo := mul_pos hke_lo hV_lo
  have hRD : 0 ≤ R / (ke * V) := (div_pos hR hD).le
  -- The exponential factor lies in `[0, 1]` for `t ≥ 0`.
  have hexp_nonneg : 0 ≤ Real.exp (-(ke * t)) := (Real.exp_pos _).le
  have hexp_le_one : Real.exp (-(ke * t)) ≤ 1 := by
    have hmono : Real.exp (-(ke * t)) ≤ Real.exp 0 := by
      apply Real.exp_le_exp.mpr
      have : 0 ≤ ke * t := mul_nonneg hke0.le ht
      linarith
    simpa using hmono
  -- Worst-case denominator: `ke_lo * V_lo ≤ ke * V`.
  have hden : ke_lo * V_lo ≤ ke * V := mul_le_mul hke hV hV_lo.le hke0.le
  -- Lower bound: the time factor is `≥ 0`, so `C(t) ≥ 0`.
  have hlow : 0 ≤ conc R ke V t := by
    have h0 : 0 ≤ 1 - Real.exp (-(ke * t)) := by linarith
    have := mul_nonneg hRD h0
    simpa [conc] using this
  -- Upper bound, step 1: the time factor is `≤ 1`, so `C(t) ≤ R / (ke * V)`
  -- (the steady-state value).
  have hCss : conc R ke V t ≤ R / (ke * V) := by
    have h1 : 1 - Real.exp (-(ke * t)) ≤ 1 := by linarith
    have := mul_le_mul_of_nonneg_left h1 hRD
    simpa [conc] using this
  -- Upper bound, step 2: the steady-state value is `≤ T`, via the certificate
  -- condition at the worst-case corner.
  have hSsT : R / (ke * V) ≤ T := by
    rw [div_le_iff₀ hD]
    have hcert' : R ≤ T * (ke_lo * V_lo) := (div_le_iff₀ hD0).mp hcert
    have hTpos : 0 < T := lt_of_lt_of_le (div_pos hR hD0) hcert
    linarith [mul_le_mul_of_nonneg_left hden hTpos.le]
  exact ⟨hlow, le_trans hCss hSsT⟩

end Bio.PKPD.ConstantInfusion
