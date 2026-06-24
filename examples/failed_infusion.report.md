# Exposure-safety certificate report — `drugX_infusion_aggressive`

**Verdict:** `FAILED`  
**Target certified class:** one-compartment, first-order elimination, constant continuous IV infusion

## Outcome: certificate does **not** hold (fail closed)

The model is inside the certified subset, but a corner condition is violated, so no safety certificate can be emitted. **This is a finding, not an error:** under the fitted parameter box the model can leave the declared window.

- worst-case steady-state exposure `R/(ke_lo·V_lo) = 200/3`
- toxicity threshold `T = 40`

## Parameter provenance

| Field | Value |
|---|---|
| Model / run | popPK base model, run 14 |
| Dataset | PHASE1-SAD/MAD pooled |
| Estimation method | FOCEI (NONMEM) |
| Interval origin | 90% profile-likelihood on ke, V |

## Model-risk note

This is a machine-checked statement about a **model under explicitly stated, bounded assumptions** — that the concentration the model predicts cannot exceed the declared threshold for any parameter value in the fitted box. It is **not** a claim that a drug or dose is safe for a patient. The proof is about the model, not the patient. Model misspecification, parameter-CI miscalibration, and off-model physiology are out of scope of the certificate.
