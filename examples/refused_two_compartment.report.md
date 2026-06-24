# Exposure-safety certificate report — `drugZ_two_compartment`

**Verdict:** `REFUSED`  
**Target certified class:** one-compartment, first-order elimination, constant continuous IV infusion

## Outcome: refused (fail closed)

This model is **outside the auto-emittable certified subset**. No proof was emitted.

> 2-compartment model is outside the certified subset (one-compartment, first-order elimination, constant continuous IV infusion)

## Model-risk note

This is a machine-checked statement about a **model under explicitly stated, bounded assumptions** — that the concentration the model predicts cannot exceed the declared threshold for any parameter value in the fitted box. It is **not** a claim that a drug or dose is safe for a patient. The proof is about the model, not the patient. Model misspecification, parameter-CI miscalibration, and off-model physiology are out of scope of the certificate.
