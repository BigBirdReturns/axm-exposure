# Exposure-safety certificate report — `drugX_infusion`

**Verdict:** `CERTIFIED`  
**Target certified class:** one-compartment, first-order elimination, constant continuous IV infusion

## Theorem (model-relative, conditional)

For a one-compartment constant continuous IV infusion model

```
C(t) = (R / (ke · V)) · (1 − exp(−ke · t)),
```

the plasma concentration the model predicts stays in `[0, 80]` for **every** time `t ≥ 0` and **every** parameter value with `ke_lo ≤ ke` and `V_lo ≤ V`.

## Assumptions

- infusion rate `R = 100` (> 0)
- fitted lower bounds `ke_lo = 3/10` (> 0), `V_lo = 5` (> 0)
- toxicity threshold `T = 80`
- **certificate condition** (worst-case / smallest-clearance corner): `R/(ke_lo·V_lo) = 200/3 ≤ 80` ✓

## Parameter provenance

| Field | Value |
|---|---|
| Model / run | popPK base model, run 14 |
| Dataset | PHASE1-SAD/MAD pooled |
| Estimation method | FOCEI (NONMEM) |
| Interval origin | 90% profile-likelihood on ke, V |

## Proof identity

- verified schema: `Bio.PKPD.ConstantInfusion.infusion_safety_bound` (`lean/BioPKPD/ConstantInfusion.lean`)
- kernel-checked under: `leanprover/lean4:v4.31.0` + Mathlib
- emitted-artifact SHA-256: `26bf053a8d0a4081a2305ba2ef2988fa1a243b744da7cb3cae363fef61783928`

The hash is content identity for the emitted Lean, **not** a kernel attestation. The attestation is the green CI run that builds the artifact; the hash ties this report to the exact text that was checked. Verify it yourself:

```bash
python -m axm certify <spec.json> --lean-only | sha256sum
cd lean && lake exe cache get && lake build   # kernel check
```

## Model-risk note

This is a machine-checked statement about a **model under explicitly stated, bounded assumptions** — that the concentration the model predicts cannot exceed the declared threshold for any parameter value in the fitted box. It is **not** a claim that a drug or dose is safe for a patient. The proof is about the model, not the patient. Model misspecification, parameter-CI miscalibration, and off-model physiology are out of scope of the certificate.
