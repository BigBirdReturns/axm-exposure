# Exposure-safety certificate report — `drugW_two_compartment`

**Verdict:** `CERTIFIED`  
**Target certified class:** two-compartment, first-order elimination, constant continuous IV infusion (steady state)

## Theorem (model-relative, conditional)

For a two-compartment constant continuous IV infusion model (central volume `V1`, peripheral compartment, any `k12, k21 > 0`), at steady state the peripheral flux cancels and the central concentration is

```
C1_ss = A1 / V1 = R / (ke · V1),
```

so the steady-state central exposure stays in `[0, 80]` for **every** parameter value with `ke_lo ≤ ke` and `V1_lo ≤ V1` — the peripheral compartment does not raise the steady-state ceiling. (Steady state only; the no-overshoot transient is argued on paper.)

## Assumptions

- infusion rate `R = 100` (> 0)
- fitted lower bounds `ke_lo = 3/10` (> 0), `V1_lo = 5` (> 0)
- steady-state balance: `k12·A1 = k21·A2` and `R + k21·A2 = (ke+k12)·A1`
- toxicity threshold `T = 80`
- **certificate condition** (worst-case / smallest-clearance corner): `R/(ke_lo·V1_lo) = 200/3 ≤ 80` ✓

## Parameter provenance

| Field | Value |
|---|---|
| Model / run | popPK 2-cpt model, run 22 |
| Dataset | PHASE1-SAD/MAD pooled |
| Estimation method | FOCEI (NONMEM) |
| Interval origin | 90% profile-likelihood on ke, V1 |

## Proof identity

- verified schema: `Bio.PKPD.TwoCompartmentInfusion.central_steady_state_bound` (`lean/BioPKPD/TwoCompartmentInfusion.lean`)
- kernel-checked under: `leanprover/lean4:v4.31.0` + Mathlib
- emitted-artifact SHA-256: `f4e96de259e7e02fbdc32ec3c417a61647f6cb116c737a13fed1b4ed61700c4d`

The hash is content identity for the emitted Lean, **not** a kernel attestation. The attestation is the green CI run that builds the artifact; the hash ties this report to the exact text that was checked. Verify it yourself:

```bash
python -m axm certify <spec.json> --lean-only | sha256sum
cd lean && lake exe cache get && lake build   # kernel check
```

## Model-risk note

This is a machine-checked statement about a **model under explicitly stated, bounded assumptions** — that the concentration the model predicts cannot exceed the declared threshold for any parameter value in the fitted box. It is **not** a claim that a drug or dose is safe for a patient. The proof is about the model, not the patient. Model misspecification, parameter-CI miscalibration, and off-model physiology are out of scope of the certificate.
