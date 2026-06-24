# Exposure-safety certificate report — `drugY_repeated`

**Verdict:** `CERTIFIED`  
**Target certified class:** one-compartment, first-order elimination, repeated IV bolus (steady state)

## Theorem (model-relative, conditional)

For a one-compartment repeated-IV-bolus regimen (dose `D` every interval `τ`), at steady state

```
Cmax_ss = D / (V · (1 − exp(−ke·τ))),
Ctrough_ss = D · exp(−ke·τ) / (V · (1 − exp(−ke·τ))),
```

the model's steady-state trough stays `≥ Ceff = 1/20` and peak stays `≤ Ctox = 3/2` for **every** parameter value with `ke_lo ≤ ke ≤ ke_hi` and `V_lo ≤ V ≤ V_hi`.

## Assumptions

- dose `D = 20` (> 0), interval `τ = 8` (> 0)
- fitted box `ke ∈ [2/25, 1/10]`, `V ∈ [40, 60]`
- validity: `ke_hi·τ < 1` (rational efficacy floor)
- **certificate conditions** (rational/conservative corner conditions from `1 + x ≤ exp x`):
  - peak ceiling `D·(1+ke_lo·τ)/(V_lo·ke_lo·τ) = 41/32 ≤ Ctox = 3/2` ✓
  - trough floor `Ceff = 1/20 ≤ D·(1−ke_hi·τ)/(V_hi·ke_hi·τ) = 1/12` ✓

## Parameter provenance

| Field | Value |
|---|---|
| Model / run | popPK base model, run 22 |
| Dataset | PHASE1-MAD q8h cohort |
| Estimation method | FOCEI (NONMEM) |
| Interval origin | 90% profile-likelihood on ke, V |

## Proof identity

- verified schema: `Bio.PKPD.RepeatedDose.repeated_dose_window_rational` (`lean/BioPKPD/RepeatedDoseRational.lean`)
- kernel-checked under: `leanprover/lean4:v4.31.0` + Mathlib
- emitted-artifact SHA-256: `1863f3b853994b30b5d36a3c48df95957a47ecb5bf6c6f17b967553e6352be8a`

The hash is content identity for the emitted Lean, **not** a kernel attestation. The attestation is the green CI run that builds the artifact; the hash ties this report to the exact text that was checked. Verify it yourself:

```bash
python -m axm certify <spec.json> --lean-only | sha256sum
cd lean && lake exe cache get && lake build   # kernel check
```

## Model-risk note

This is a machine-checked statement about a **model under explicitly stated, bounded assumptions** — that the concentration the model predicts cannot exceed the declared threshold for any parameter value in the fitted box. It is **not** a claim that a drug or dose is safe for a patient. The proof is about the model, not the patient. Model misspecification, parameter-CI miscalibration, and off-model physiology are out of scope of the certificate.
