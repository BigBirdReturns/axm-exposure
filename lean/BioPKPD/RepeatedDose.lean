import Mathlib

/-!
# PK/PD flagship 2: a repeated-dose therapeutic-window certificate

The second vertical from the project handoff roadmap (§5 step 1): **steady-state
therapeutic window under parameter uncertainty.** Where `ConstantInfusion.lean`
certifies a one-sided exposure ceiling, this certifies a *two-sided window* — the
question a pharmacometrician actually asks for a repeated-dose regimen:

> Across the whole fitted confidence box for the parameters, does the
> steady-state trough stay **above** the efficacy threshold `Ceff` *and* the
> steady-state peak stay **below** the toxicity threshold `Ctox`?

## The model

One-compartment model, repeated IV bolus of dose `D` every interval `τ`, with
first-order elimination rate `ke` and distribution volume `V`. Each bolus raises
central concentration by `D / V`; between doses concentration decays by the
factor `exp (-(ke * τ))`. Summing the geometric series gives the standard
steady-state peak and trough (immediately after / immediately before a dose):

  `Cmax_ss(ke, V) = D / (V * (1 - exp (-(ke * τ))))`
  `Ctrough_ss(ke, V) = D * exp (-(ke * τ)) / (V * (1 - exp (-(ke * τ))))`.

`D` and `τ` are the *regimen* (chosen, known exactly). `ke` and `V` are
*fitted with uncertainty*, known only to lie in a box
`[ke_lo, ke_hi] × [V_lo, V_hi]` with strictly positive lower endpoints.

## Why this needs the full box (not one corner)

Steady-state peak and trough move in **opposite worst-case directions**:

* `Cmax_ss` is decreasing in both `ke` and `V` (larger clearance / volume ⇒
  lower peak), so it is **largest** at the corner `(ke_lo, V_lo)`. Controlling
  that one corner controls the toxicity ceiling over the whole box.
* `Ctrough_ss` is also decreasing in both `ke` and `V`, so it is **smallest** at
  the opposite corner `(ke_hi, V_hi)`. Controlling that corner controls the
  efficacy floor over the whole box.

The certificate therefore checks the toxicity condition at `(ke_lo, V_lo)` and
the efficacy condition at `(ke_hi, V_hi)`, and the theorem propagates both to
every parameter value in between.

## What is and isn't claimed

A machine-checked proof of **model consistency under explicitly stated, bounded
assumptions** — not a claim that any dose is safe or effective for a patient.
The proof is about the model, not the patient (handoff §2.3). Kernel-checked by
Lean + Mathlib in CI; see `.github/workflows/lean.yml`.
-/

namespace Bio.PKPD.RepeatedDose

/-- Steady-state **peak** concentration (immediately after a dose) for a
one-compartment repeated-IV-bolus regimen of dose `D` every interval `τ`, with
first-order elimination rate `ke` and volume `V`:

  `Cmax_ss = D / (V * (1 - exp (-(ke * τ))))`. -/
noncomputable def cmax (D V ke τ : ℝ) : ℝ :=
  D / (V * (1 - Real.exp (-(ke * τ))))

/-- Steady-state **trough** concentration (immediately before the next dose) for
the same regimen:

  `Ctrough_ss = D * exp (-(ke * τ)) / (V * (1 - exp (-(ke * τ))))`. -/
noncomputable def ctrough (D V ke τ : ℝ) : ℝ :=
  D * Real.exp (-(ke * τ)) / (V * (1 - Real.exp (-(ke * τ))))

/-- **Repeated-dose therapeutic-window certificate.**

For a one-compartment repeated-IV-bolus regimen (dose `D > 0` every `τ > 0`),
where the elimination rate `ke` and volume `V` are known only to lie in a fitted
box `[ke_lo, ke_hi] × [V_lo, V_hi]` with strictly positive lower endpoints, the
steady-state trough stays at or above the efficacy threshold `Ceff` and the
steady-state peak stays at or below the toxicity threshold `Ctox` for **every**
parameter value in the box — provided the two **certificate conditions** hold at
the worst-case corners:

* toxicity, at the smallest-clearance corner: `cmax D V_lo ke_lo τ ≤ Ctox`;
* efficacy, at the largest-clearance corner: `Ceff ≤ ctrough D V_hi ke_hi τ`.

Both peak and trough are monotone decreasing in `ke` and `V`, so these two
corners dominate the whole box; the proof transports each bound inward. -/
theorem repeated_dose_window
    (D V ke τ Ceff Ctox ke_lo ke_hi V_lo V_hi : ℝ)
    (hD : 0 < D) (hτ : 0 < τ)
    (hke_lo : 0 < ke_lo) (hke1 : ke_lo ≤ ke) (hke2 : ke ≤ ke_hi)
    (hV_lo : 0 < V_lo) (hV1 : V_lo ≤ V) (hV2 : V ≤ V_hi)
    (hcert_tox : cmax D V_lo ke_lo τ ≤ Ctox)
    (hcert_eff : Ceff ≤ ctrough D V_hi ke_hi τ) :
    Ceff ≤ ctrough D V ke τ ∧ cmax D V ke τ ≤ Ctox := by
  -- Positivity of the three exponential decay factors.
  have he_pos : 0 < Real.exp (-(ke * τ)) := Real.exp_pos _
  -- Volumes are positive throughout the box.
  have hV0 : 0 < V := lt_of_lt_of_le hV_lo hV1
  have hVhi0 : 0 < V_hi := lt_of_lt_of_le hV0 hV2
  -- `ke ↦ ke * τ` is monotone (τ > 0), so the decay factors are ordered
  -- `exp(-ke_hi τ) ≤ exp(-ke τ) ≤ exp(-ke_lo τ)`.
  have hkeτ1 : ke_lo * τ ≤ ke * τ := mul_le_mul_of_nonneg_right hke1 hτ.le
  have hkeτ2 : ke * τ ≤ ke_hi * τ := mul_le_mul_of_nonneg_right hke2 hτ.le
  have he_le_elo : Real.exp (-(ke * τ)) ≤ Real.exp (-(ke_lo * τ)) :=
    Real.exp_le_exp.mpr (by linarith)
  have hehi_le_e : Real.exp (-(ke_hi * τ)) ≤ Real.exp (-(ke * τ)) :=
    Real.exp_le_exp.mpr (by linarith)
  -- The smallest-clearance decay factor is `< 1`, so every `1 - exp(..)` is `> 0`.
  have helo_lt1 : Real.exp (-(ke_lo * τ)) < 1 := by
    have h0 : -(ke_lo * τ) < 0 := by nlinarith [mul_pos hke_lo hτ]
    calc Real.exp (-(ke_lo * τ)) < Real.exp 0 := Real.exp_lt_exp.mpr h0
      _ = 1 := Real.exp_zero
  have ha_pos : 0 < 1 - Real.exp (-(ke * τ)) := by linarith [he_le_elo]
  have ha_lo_pos : 0 < 1 - Real.exp (-(ke_lo * τ)) := by linarith
  have ha_hi_pos : 0 < 1 - Real.exp (-(ke_hi * τ)) := by linarith [hehi_le_e]
  -- Denominators are positive at each corner we use.
  have hden_max : 0 < V * (1 - Real.exp (-(ke * τ))) := mul_pos hV0 ha_pos
  have hden_maxlo : 0 < V_lo * (1 - Real.exp (-(ke_lo * τ))) := mul_pos hV_lo ha_lo_pos
  have hden_eff : 0 < V_hi * (1 - Real.exp (-(ke_hi * τ))) := mul_pos hVhi0 ha_hi_pos
  -- Monotone denominators: peak's worst corner has the smallest denominator,
  -- trough's worst corner the largest.
  have hmono_max :
      V_lo * (1 - Real.exp (-(ke_lo * τ))) ≤ V * (1 - Real.exp (-(ke * τ))) :=
    mul_le_mul hV1 (by linarith [he_le_elo]) ha_lo_pos.le hV0.le
  have hmono_eff_den :
      V * (1 - Real.exp (-(ke * τ))) ≤ V_hi * (1 - Real.exp (-(ke_hi * τ))) :=
    mul_le_mul hV2 (by linarith [hehi_le_e]) ha_pos.le hVhi0.le
  -- Trough numerator is monotone in `ke` as well.
  have hnum_eff : D * Real.exp (-(ke_hi * τ)) ≤ D * Real.exp (-(ke * τ)) :=
    mul_le_mul_of_nonneg_left hehi_le_e hD.le
  -- Clear the certificate denominators once (the fitted thresholds in product form).
  have hcert_tox' : D ≤ Ctox * (V_lo * (1 - Real.exp (-(ke_lo * τ)))) := by
    have h := hcert_tox
    simp only [cmax] at h
    rwa [div_le_iff₀ hden_maxlo] at h
  have hcert_eff' :
      Ceff * (V_hi * (1 - Real.exp (-(ke_hi * τ)))) ≤ D * Real.exp (-(ke_hi * τ)) := by
    have h := hcert_eff
    simp only [ctrough] at h
    rwa [le_div_iff₀ hden_eff] at h
  -- The toxicity threshold is non-negative (its product bound exceeds `D > 0`).
  have hCtox_nn : 0 ≤ Ctox := by nlinarith [hcert_tox', hden_maxlo, hD]
  -- Toxicity ceiling: peak at `(ke, V)` is `≤` peak at the worst corner `≤ Ctox`.
  have hmax : cmax D V ke τ ≤ Ctox := by
    simp only [cmax]
    rw [div_le_iff₀ hden_max]
    have hstep : Ctox * (V_lo * (1 - Real.exp (-(ke_lo * τ))))
        ≤ Ctox * (V * (1 - Real.exp (-(ke * τ)))) :=
      mul_le_mul_of_nonneg_left hmono_max hCtox_nn
    linarith [hcert_tox', hstep]
  -- Efficacy floor: trough at `(ke, V)` is `≥` trough at the worst corner `≥ Ceff`.
  have htrough : Ceff ≤ ctrough D V ke τ := by
    simp only [ctrough]
    rw [le_div_iff₀ hden_max]
    rcases le_or_lt 0 Ceff with hCeff | hCeff
    · -- `Ceff ≥ 0`: scale the monotone denominator, then chain to the worst corner.
      have h1 : Ceff * (V * (1 - Real.exp (-(ke * τ))))
          ≤ Ceff * (V_hi * (1 - Real.exp (-(ke_hi * τ)))) :=
        mul_le_mul_of_nonneg_left hmono_eff_den hCeff
      linarith [hcert_eff', hnum_eff, h1]
    · -- `Ceff < 0`: the floor is below zero while the trough is strictly positive.
      have hneg : 0 < -Ceff := neg_pos.mpr hCeff
      nlinarith [mul_pos hneg hden_max, mul_pos hD he_pos]
  exact ⟨htrough, hmax⟩

end Bio.PKPD.RepeatedDose
