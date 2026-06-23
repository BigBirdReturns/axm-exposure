# axm-exposure — PK/PD exposure-safety certificates

A narrow, additive vertical spun out of [`GSK-LeanBio`](docs/HANDOFF.md): **machine-checked,
parameter-bounded exposure-safety certificates for Model-Informed Drug Development (MIDD).**

`GSK-LeanBio` demonstrated that you *can* kernel-check biochemical-model properties, and in
doing so exposed the ceiling: formal proof certifies a **model under stated assumptions**,
never biological truth. A general "formal verification for biology" tool therefore has a
structural value mismatch — formal methods pay off where the spec is exact and error is
catastrophic. PK/PD dosing is one place that actually holds:

- **The spec is exact** — an exposure safety threshold (`C_plasma ≤ C_toxic`) or a
  therapeutic window.
- **The error is catastrophic** — toxicity or loss of efficacy.
- **The model is well understood** — a compartment ODE with decades of validation.
- **The parameters are fitted with known uncertainty** — a confidence interval.
- **The decision is regulatory and legible** — *can we justify this dose for all parameter
  values in the fitted CI?*

## What's here

This repo is the **first move** from the handoff (§9): the smallest non-trivial PK/PD case,
built as a Mathlib flagship and kernel-checked in CI.

| Piece | Where | Status |
|---|---|---|
| Constant-infusion → steady-state exposure-safety bound (ℝ, Mathlib) | [`lean/BioPKPD/ConstantInfusion.lean`](lean/BioPKPD/ConstantInfusion.lean) | written; kernel-checked in CI |
| Mathlib-in-CI kernel check | [`.github/workflows/lean.yml`](.github/workflows/lean.yml) | runs on every push to `lean/**` |
| Project handoff (lineage, discipline, roadmap) | [`docs/HANDOFF.md`](docs/HANDOFF.md) | reference |

### The theorem

> For a one-compartment constant-infusion model `C(t) = (R / (ke·V))·(1 − exp(−ke·t))`,
> with infusion rate `R > 0` and parameters known only to lie in fitted intervals with
> positive lower endpoints (`0 < ke_lo ≤ ke`, `0 < V_lo ≤ V`), the model's plasma
> concentration stays in `[0, T]` for **every** `t ≥ 0` and **every** parameter value in
> the box — provided the certificate condition `R / (ke_lo · V_lo) ≤ T` holds.

Constant infusion (not a single IV bolus) is the deliberate starting point: a bolus
`C(t) = C0·e^(−ke·t)` decays, so its max is just `C0` and the "safety bound" collapses to
`C0 ≤ T` — the same triviality trap as a decaying toy. Infusion-to-steady-state is real,
non-trivial, parameter-bounded, and maps to an actual exposure-safety question.

## The discipline (carried from the handoff §2)

1. **Real ≠ valuable.** A kernel-checked theorem proves the *machine* works, not that anyone
   needs it. The named user is a pharmacometrics / quantitative-clinical-pharmacology lead
   preparing an FDA MIDD package; the decision a green check changes is dose justification /
   safety margin.
2. **Stay model-relative and conditional.** "For all parameters in the stated interval, the
   model cannot cross the declared bound." Never "the drug is safe." The proof is about the
   model, not the patient.
3. **Verify-it-yourself is the standard.** Open, local, reproducible, CI-checked. No "trust
   me," no proprietary-infra dependency.
4. **CI is the authority.** Mathlib's `.olean` cache is firewalled in the restricted dev
   sandbox, so ℝ/Mathlib proofs cannot be kernel-checked locally there; the GitHub-runner CI
   job (`lake exe cache get` → `lake build`) is the verdict. A `sorry`/`admit` grep gate
   guards the build.

## The open question (handoff §9 — build and user-discovery run in parallel)

Feasibility is not the bottleneck; **adoption** is. Before building the rest of the vertical,
the question for a real pharmacometrician is:

> *Would a machine-checked certificate that your model's exposure stays below threshold for
> all parameters in your fitted CI change anything about your MIDD package or review?*

If the answer is no, that is the most valuable finding available — and the signal to stop.

## Next (handoff §5, in order)

1. **Repeated-dose accumulation / therapeutic window** — prove `C_trough ≥ C_eff ∧ C_max ≤
   C_tox` at steady state for all params in the CI.
2. **A recognizer + certificate report** — classify a one-compartment, first-order,
   constant-input model with parameter intervals + threshold, emit the Lean instance, **fail
   closed** on anything outside the subset (mirroring `bsl certify`).
3. **A MIDD-style report artifact** — theorem statement, assumptions, parameter provenance
   (which fit, which dataset, which method, which CI), proof hash, model-risk note.

## Building locally

```bash
cd lean
lake exe cache get   # needs open network for Mathlib's prebuilt cache
lake build           # kernel-checks Bio.PKPD.ConstantInfusion.infusion_safety_bound
```

Not affiliated with or endorsed by GSK. The critique that motivated this work is structural
and conditional, never a claim about any person's intent.

License: Apache-2.0
