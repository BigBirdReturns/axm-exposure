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

This certifies the **steady-state** central concentration, the relevant exposure
for chronic / maintenance infusion. It is *not* a statement about the transient
`C1(t)`. For the mammillary model above the central concentration is known to
rise **monotonically** to `C1_ss` under a constant infusion from rest (the step
response has non-negative modal coefficients), so the steady state is also the
all-time maximum — but that transient fact is argued on paper, not yet
machine-checked here. As always (handoff §2.3): a statement about the model under
stated assumptions, never a claim about a patient.

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

end Bio.PKPD.TwoCompartmentInfusion
