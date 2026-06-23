import BioPKPD.RepeatedDose

/-!
# Repeated-dose therapeutic window with a *rational* certificate

`RepeatedDose.lean` proves the steady-state therapeutic-window certificate, but
its two corner conditions are **transcendental in `ke`**: they contain
`exp(-(ke · τ))`. That blocks automatic emission — a generated concrete instance
cannot discharge `D / (V_lo · (1 − exp(−ke_lo·τ))) ≤ Ctox` with `norm_num`.

This module removes that block. Using the elementary envelope `1 + x ≤ exp x`
(`Real.add_one_le_exp`) we replace each transcendental corner condition with a
strictly more conservative **rational** one:

* toxicity: `exp(−x) ≤ 1/(1+x)`, so `1 − exp(−x) ≥ x/(1+x)`, giving the rational
  ceiling `D·(1 + ke_lo·τ) / (V_lo · ke_lo·τ) ≤ Ctox`;
* efficacy: `1 − x ≤ exp(−x)` (and `1 − exp(−x) ≤ x`), giving the rational floor
  `Ceff ≤ D·(1 − ke_hi·τ) / (V_hi · ke_hi·τ)` (valid when `ke_hi·τ < 1`).

If the rational conditions hold, the transcendental ones hold, so the full
`repeated_dose_window` conclusion follows for **every** parameter value in the
fitted box. The rational conditions are closed by `norm_num` on concrete inputs —
exactly what `axm certify` needs to auto-emit a kernel-checkable repeated-dose
certificate. Conservatism is the price: a regimen near the threshold may pass the
true window yet fail the rational test, in which case the tool fails closed.
-/

namespace Bio.PKPD.RepeatedDose

open Bio.PKPD.RepeatedDose

/-- `x / (1 + x) ≤ 1 - exp(-x)` for `x > 0`, from `1 + x ≤ exp x`. -/
private lemma one_sub_exp_neg_lower (x : ℝ) (hx : 0 < x) :
    x / (1 + x) ≤ 1 - Real.exp (-x) := by
  have h1x : (0 : ℝ) < 1 + x := by linarith
  have hexp : 1 + x ≤ Real.exp x := by linarith [Real.add_one_le_exp x]
  have hbound : Real.exp (-x) ≤ 1 / (1 + x) := by
    rw [Real.exp_neg, inv_eq_one_div]
    exact one_div_le_one_div_of_le h1x hexp
  have heq : 1 - 1 / (1 + x) = x / (1 + x) := by field_simp
  linarith [hbound, heq]

/-- `1 - x ≤ exp(-x)`, from `1 + (-x) ≤ exp(-x)`. -/
private lemma one_sub_le_exp_neg (x : ℝ) : 1 - x ≤ Real.exp (-x) := by
  linarith [Real.add_one_le_exp (-x)]

/-- **Repeated-dose therapeutic-window certificate, rational form.**

Same conclusion as `repeated_dose_window`, but the two hypotheses are rational
(`norm_num`-dischargeable on concrete inputs): a worst-case-corner toxicity
ceiling and efficacy floor obtained from the `1 + x ≤ exp x` envelope. Requires
`ke_hi · τ < 1` so the efficacy floor's numerator stays non-negative. -/
theorem repeated_dose_window_rational
    (D V ke τ Ceff Ctox ke_lo ke_hi V_lo V_hi : ℝ)
    (hD : 0 < D) (hτ : 0 < τ)
    (hke_lo : 0 < ke_lo) (hke1 : ke_lo ≤ ke) (hke2 : ke ≤ ke_hi)
    (hV_lo : 0 < V_lo) (hV1 : V_lo ≤ V) (hV2 : V ≤ V_hi)
    (hkehi_lt : ke_hi * τ < 1)
    (hcert_tox_rat : D * (1 + ke_lo * τ) / (V_lo * (ke_lo * τ)) ≤ Ctox)
    (hcert_eff_rat : Ceff ≤ D * (1 - ke_hi * τ) / (V_hi * (ke_hi * τ))) :
    Ceff ≤ ctrough D V ke τ ∧ cmax D V ke τ ≤ Ctox := by
  have hke_hi : 0 < ke_hi := lt_of_lt_of_le hke_lo (le_trans hke1 hke2)
  have hVhi0 : 0 < V_hi := lt_of_lt_of_le (lt_of_lt_of_le hV_lo hV1) hV2
  have ha : 0 < ke_lo * τ := mul_pos hke_lo hτ
  have hb : 0 < ke_hi * τ := mul_pos hke_hi hτ
  -- ===== toxicity corner: derive the transcendental ceiling from the rational one =====
  have h1a : (0 : ℝ) < 1 + ke_lo * τ := by linarith
  have hkeyA : (ke_lo * τ) / (1 + ke_lo * τ) ≤ 1 - Real.exp (-(ke_lo * τ)) :=
    one_sub_exp_neg_lower (ke_lo * τ) ha
  have h1e_lo : 0 < 1 - Real.exp (-(ke_lo * τ)) := by
    have : 0 < (ke_lo * τ) / (1 + ke_lo * τ) := div_pos ha h1a
    linarith
  have hden_lo : 0 < V_lo * (1 - Real.exp (-(ke_lo * τ))) := mul_pos hV_lo h1e_lo
  have hkeyA' : ke_lo * τ ≤ (1 - Real.exp (-(ke_lo * τ))) * (1 + ke_lo * τ) := by
    rw [div_le_iff₀ h1a] at hkeyA; linarith
  have hVa : 0 < V_lo * (ke_lo * τ) := mul_pos hV_lo ha
  have hrat_t : D * (1 + ke_lo * τ) ≤ Ctox * (V_lo * (ke_lo * τ)) := by
    rw [div_le_iff₀ hVa] at hcert_tox_rat; linarith
  have hCtox_nn : 0 ≤ Ctox := by nlinarith [hrat_t, hVa, mul_pos hD h1a]
  have hcert_tox : cmax D V_lo ke_lo τ ≤ Ctox := by
    simp only [cmax]
    rw [div_le_iff₀ hden_lo]
    nlinarith [hrat_t, mul_le_mul_of_nonneg_left hkeyA' (mul_nonneg hCtox_nn hV_lo.le),
      mul_pos hD h1a]
  -- ===== efficacy corner: derive the transcendental floor from the rational one =====
  have he_pos : 0 < Real.exp (-(ke_hi * τ)) := Real.exp_pos _
  have hb1 : 1 - ke_hi * τ ≤ Real.exp (-(ke_hi * τ)) := one_sub_le_exp_neg (ke_hi * τ)
  have hb2 : 1 - Real.exp (-(ke_hi * τ)) ≤ ke_hi * τ := by linarith [hb1]
  have h1e_hi : 0 < 1 - Real.exp (-(ke_hi * τ)) := by
    have hlt : Real.exp (-(ke_hi * τ)) < 1 := by
      have : Real.exp (-(ke_hi * τ)) < Real.exp 0 := Real.exp_lt_exp.mpr (by linarith)
      simpa using this
    linarith
  have hden_hi : 0 < V_hi * (1 - Real.exp (-(ke_hi * τ))) := mul_pos hVhi0 h1e_hi
  have hVb : 0 < V_hi * (ke_hi * τ) := mul_pos hVhi0 hb
  have hrat_e : Ceff * (V_hi * (ke_hi * τ)) ≤ D * (1 - ke_hi * τ) := by
    rw [le_div_iff₀ hVb] at hcert_eff_rat; linarith
  have hcert_eff : Ceff ≤ ctrough D V_hi ke_hi τ := by
    simp only [ctrough]
    rw [le_div_iff₀ hden_hi]
    rcases le_total 0 Ceff with hCeff | hCeff
    · nlinarith [mul_le_mul_of_nonneg_left hb2 (mul_nonneg hCeff hVhi0.le),
        hrat_e, mul_le_mul_of_nonneg_left hb1 hD.le]
    · nlinarith [mul_nonneg (neg_nonneg.mpr hCeff) (mul_nonneg hVhi0.le h1e_hi.le),
        mul_pos hD he_pos]
  -- ===== conclude via the already-proved transcendental window =====
  exact repeated_dose_window D V ke τ Ceff Ctox ke_lo ke_hi V_lo V_hi
    hD hτ hke_lo hke1 hke2 hV_lo hV1 hV2 hcert_tox hcert_eff

end Bio.PKPD.RepeatedDose
