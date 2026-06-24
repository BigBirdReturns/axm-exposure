import Mathlib

/-!
# PK/PD flagship: a two-compartment constant-infusion exposure certificate

The third model class in the certified subset (handoff §5 "breadth"). Where
`ConstantInfusion.lean` handles a one-compartment model, real popPK fits are very
often **two-compartment**: a central compartment (where drug is dosed and
measured) exchanging with a peripheral compartment.

## The model

Central amount `A1` (volume `V1`, concentration `C1 = A1 / V1`) and peripheral
amount `A2`, under a constant continuous IV infusion of rate `R` into the central
compartment, with first-order elimination `ke` from the central compartment and
first-order inter-compartmental transfer `k12` (central → peripheral) and `k21`
(peripheral → central):

  `A1' = R - (ke + k12)·A1 + k21·A2`
  `A2' = k12·A1 - k21·A2`.

## What is proved here

The **steady-state** central exposure certificate. At steady state (`A1' = A2' =
0`) the peripheral flux balances (`k12·A1 = k21·A2`), and substituting into the
central balance the peripheral terms **cancel exactly**:

  `R = ke·A1`,  so  `C1_ss = A1 / V1 = R / (ke·V1)`.

That is the content worth stating: *adding a peripheral compartment does not
change the steady-state central exposure* — the steady-state ceiling is still set
by clearance `CL = ke·V1` alone, for any `k12, k21 > 0`. The certificate then
bounds it at the worst-case (smallest-clearance) corner: `R/(ke_lo·V1_lo) ≤ T`.

## Scope (stated honestly)

This module proves two complementary facts:

* `central_steady_state_bound` — the **steady-state** central exposure
  certificate (the relevant quantity for chronic / maintenance infusion): the
  peripheral compartment cancels and `C1_ss = R/(ke·V1) ≤ T`.
* `central_transient_bound` — the **all-time** bound `0 ≤ C1(t) ≤ T` for every
  `t ≥ 0`, from the model's modal (two-exponential) step-response structure
  `C1(t) = C1_ss·(1 − g₁·e^{−αt} − g₂·e^{−βt})` with non-negative modal
  coefficients summing to one (`g₁, g₂ ≥ 0`, `g₁ + g₂ = 1`, decay rates
  `α, β ≥ 0`). This machine-checks the "no overshoot" property: the central
  concentration never exceeds its steady state, so `C1_ss` is also the all-time
  maximum.

What remains argued on paper (not re-proved here) is only that the *mammillary
micro-constants* `(ke, k12, k21)` yield such a decomposition with non-negative
coefficients summing to one — a standard property of the central step response
(the residues at the two real poles have the required signs). Given that
structure, the exposure bound itself is now kernel-checked, not asserted.

As always (handoff §2.3): a statement about the model under stated assumptions,
never a claim about a patient.

Kernel-checked by Lean + Mathlib in CI; see `.github/workflows/lean.yml`.
-/

namespace Bio.PKPD.TwoCompartmentInfusion

/-- **Two-compartment constant-infusion steady-state exposure certificate.**

For central amount `A1` (volume `V1`) and peripheral amount `A2` at steady state
(peripheral balance `k12·A1 = k21·A2` and central balance
`R + k21·A2 = (ke + k12)·A1`), with `R > 0`, positive rates, and `ke`, `V1`
known only to lie above fitted lower bounds `0 < ke_lo ≤ ke`, `0 < V1_lo ≤ V1`,
the central steady-state concentration `A1 / V1` stays within `[0, T]` provided
the **certificate condition** `R / (ke_lo · V1_lo) ≤ T` holds.

The peripheral parameters `k12, k21` may be anything positive: they cancel at
steady state, so the bound holds for the whole fitted box regardless of them. -/
theorem central_steady_state_bound
    (R ke k12 k21 V1 A1 A2 T ke_lo V1_lo : ℝ)
    (hR : 0 < R)
    (hke_lo : 0 < ke_lo) (hke : ke_lo ≤ ke)
    (hV1_lo : 0 < V1_lo) (hV1 : V1_lo ≤ V1)
    (hk12 : 0 < k12) (hk21 : 0 < k21)
    (hA1 : 0 ≤ A1) (hA2 : 0 ≤ A2)
    (hbal_periph : k12 * A1 = k21 * A2)
    (hbal_central : R + k21 * A2 = (ke + k12) * A1)
    (hcert : R / (ke_lo * V1_lo) ≤ T) :
    0 ≤ A1 / V1 ∧ A1 / V1 ≤ T := by
  have hke0 : 0 < ke := lt_of_lt_of_le hke_lo hke
  have hV10 : 0 < V1 := lt_of_lt_of_le hV1_lo hV1
  have hD0 : 0 < ke_lo * V1_lo := mul_pos hke_lo hV1_lo
  -- Peripheral flux cancels at steady state, leaving the clearance relation.
  have hkeA1 : ke * A1 = R := by
    have h := hbal_central
    rw [← hbal_periph] at h          -- h : R + k12 * A1 = (ke + k12) * A1
    linear_combination -h
  -- Clear the worst-case-corner denominator.
  have hcert' : R ≤ T * (ke_lo * V1_lo) := (div_le_iff₀ hD0).mp hcert
  have hT0 : 0 < T := by nlinarith [hcert', hR, hD0]
  have hden : ke_lo * V1_lo ≤ ke * V1 := mul_le_mul hke hV1 hV1_lo.le hke0.le
  refine ⟨div_nonneg hA1 hV10.le, ?_⟩
  rw [div_le_iff₀ hV10]
  -- `R = ke·A1 ≤ T·(ke·V1) = ke·(T·V1)`, cancel `ke > 0`.
  have hRle : R ≤ T * (ke * V1) := le_trans hcert' (mul_le_mul_of_nonneg_left hden hT0.le)
  nlinarith [hRle, hkeA1, hke0]

/-- Central concentration under the modal (two-exponential) step response of the
two-compartment model: `C1(t) = C1_ss · (1 − g₁·e^{−αt} − g₂·e^{−βt})`, with
`Css = C1_ss` the steady-state value, `g₁, g₂` the modal coefficients, and
`α, β` the (positive) hybrid decay rates. -/
noncomputable def c1 (Css g1 g2 α β t : ℝ) : ℝ :=
  Css * (1 - g1 * Real.exp (-(α * t)) - g2 * Real.exp (-(β * t)))

/-- **Two-compartment all-time central exposure bound (no overshoot).**

Given the modal step-response decomposition with non-negative coefficients
summing to one (`g₁, g₂ ≥ 0`, `g₁ + g₂ = 1`), non-negative decay rates, and a
non-negative steady-state value `Css ≤ T`, the central concentration `c1` stays
within `[0, T]` for **every** `t ≥ 0`. The convex combination of decaying
exponentials lies in `[0, 1]`, so `C1(t)` never exceeds its steady state `Css`:
the steady-state ceiling is also the all-time maximum. -/
theorem central_transient_bound
    (Css g1 g2 α β t T : ℝ)
    (hCss : 0 ≤ Css)
    (hg1 : 0 ≤ g1) (hg2 : 0 ≤ g2) (hsum : g1 + g2 = 1)
    (hα : 0 ≤ α) (hβ : 0 ≤ β) (ht : 0 ≤ t)
    (hcert : Css ≤ T) :
    0 ≤ c1 Css g1 g2 α β t ∧ c1 Css g1 g2 α β t ≤ T := by
  have e1le1 : Real.exp (-(α * t)) ≤ 1 := by
    have h : Real.exp (-(α * t)) ≤ Real.exp 0 :=
      Real.exp_le_exp.mpr (by nlinarith [mul_nonneg hα ht])
    simpa using h
  have e2le1 : Real.exp (-(β * t)) ≤ 1 := by
    have h : Real.exp (-(β * t)) ≤ Real.exp 0 :=
      Real.exp_le_exp.mpr (by nlinarith [mul_nonneg hβ ht])
    simpa using h
  have e1pos : 0 < Real.exp (-(α * t)) := Real.exp_pos _
  have e2pos : 0 < Real.exp (-(β * t)) := Real.exp_pos _
  -- the decaying convex combination lies in `[0, 1]`
  have hlo : 0 ≤ g1 * Real.exp (-(α * t)) + g2 * Real.exp (-(β * t)) :=
    add_nonneg (mul_nonneg hg1 e1pos.le) (mul_nonneg hg2 e2pos.le)
  have hhi : g1 * Real.exp (-(α * t)) + g2 * Real.exp (-(β * t)) ≤ 1 := by
    nlinarith [mul_le_mul_of_nonneg_left e1le1 hg1,
      mul_le_mul_of_nonneg_left e2le1 hg2, hsum]
  refine ⟨?_, ?_⟩
  · have hfac : 0 ≤ 1 - g1 * Real.exp (-(α * t)) - g2 * Real.exp (-(β * t)) := by linarith
    simpa [c1] using mul_nonneg hCss hfac
  · have hub : c1 Css g1 g2 α β t ≤ Css := by
      have hfac : 1 - g1 * Real.exp (-(α * t)) - g2 * Real.exp (-(β * t)) ≤ 1 := by linarith
      simpa [c1] using mul_le_mul_of_nonneg_left hfac hCss
    linarith

end Bio.PKPD.TwoCompartmentInfusion
