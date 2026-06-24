# axm-exposure — PK/PD exposure-safety certificates

[![lean CI](https://github.com/BigBirdReturns/axm-exposure/actions/workflows/lean.yml/badge.svg?branch=claude/amazing-ptolemy-8tzwf8)](https://github.com/BigBirdReturns/axm-exposure/actions/workflows/lean.yml)
[![python CI](https://github.com/BigBirdReturns/axm-exposure/actions/workflows/python.yml/badge.svg?branch=claude/amazing-ptolemy-8tzwf8)](https://github.com/BigBirdReturns/axm-exposure/actions/workflows/python.yml)

A narrow, additive vertical spun out of [`GSK-LeanBio`](docs/HANDOFF.md): **machine-checked,
parameter-bounded exposure-safety certificates for Model-Informed Drug Development (MIDD).**

> **▶ Live demo — run the real tool in your browser:** <https://bigbirdreturns.github.io/axm-exposure/>
> Pick a model spec, hit *Certify*, and watch it emit kernel-checkable Lean (or fail closed).
> The package runs client-side via Pyodide — byte-identical to the CI-tested source (the demo
> bundle is diffed against the tree in CI). Enable it once at **Settings → Pages → Source = GitHub Actions**.

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

## Quickstart (5 minutes, for a reviewer)

No Lean toolchain needed to *try* it; you need it only to re-check the proofs yourself.

```bash
# 1. A certifiable constant-infusion model -> emits kernel-checkable Lean (exit 0)
python -m axm certify examples/drugX_infusion.json

# 2. A repeated-dose regimen, and a two-compartment infusion -> also certified (exit 0)
python -m axm certify examples/drugY_repeated.json
python -m axm certify examples/drugW_two_compartment.json

# 3. Fail-closed: a model whose exposure can exceed the threshold (exit 2, no Lean)
python -m axm certify examples/failed_infusion.json

# 4. Fail-closed: a model outside the certified subset (exit 3, no Lean)
python -m axm certify examples/refused_three_compartment.json

# A full MIDD report for any of them (theorem, assumptions, provenance, proof hash):
python -m axm report examples/drugX_infusion.json
```

Pre-rendered reports for all outcomes are committed so you can read them without running
anything: [`drugX_infusion`](examples/drugX_infusion.report.md) (certified, 1-cpt infusion),
[`drugY_repeated`](examples/drugY_repeated.report.md) (certified, repeated dose),
[`drugW_two_compartment`](examples/drugW_two_compartment.report.md) (certified, 2-cpt infusion),
[`failed_infusion`](examples/failed_infusion.report.md) (in-subset finding),
[`refused_three_compartment`](examples/refused_three_compartment.report.md) (out of subset).

### How to read a verdict

| Verdict | Exit | Meaning | Emits Lean? |
|---|---|---|---|
| `certified` | 0 | The model's exposure provably stays in the declared window for **every** parameter value in the fitted box. | yes — a kernel-checkable proof |
| `failed` | 2 | In the certified subset, but a corner condition is violated: the model *can* leave the window. **A finding, not an error.** | no |
| `refused` | 3 | Outside the auto-emittable subset (e.g. 2-compartment, nonlinear elimination). The tool won't certify what it can't prove. | no |

### What a green check means — and what it does not

- **It means:** under the stated one-compartment model and the fitted parameter box, the
  concentration the model predicts cannot cross the declared threshold — machine-checked by
  the Lean kernel against Mathlib, reproducibly, in CI.
- **It does not mean** the drug or dose is safe for a patient. The proof is about the *model*,
  not the patient. Model misspecification, CI miscalibration, and off-model physiology are out
  of scope. (See every report's *Model-risk note*.)
- **You don't have to trust us.** The proof object is checked by CI on each push; the emitted
  Lean is itself kernel-checked; and each report carries the `sha256` of the exact artifact
  that was checked. `cd lean && lake exe cache get && lake build` re-checks everything locally.

## What's here

This repo is the **first move** from the handoff (§9): the smallest non-trivial PK/PD case,
built as a Mathlib flagship and kernel-checked in CI.

| Piece | Where | Status |
|---|---|---|
| Constant-infusion → steady-state exposure-safety bound (ℝ, Mathlib) | [`lean/BioPKPD/ConstantInfusion.lean`](lean/BioPKPD/ConstantInfusion.lean) | written; kernel-checked in CI |
| Repeated-dose steady-state therapeutic window (ℝ, Mathlib) | [`lean/BioPKPD/RepeatedDose.lean`](lean/BioPKPD/RepeatedDose.lean) | written; kernel-checked in CI |
| Repeated-dose window, *rational* corner conditions (auto-emittable) | [`lean/BioPKPD/RepeatedDoseRational.lean`](lean/BioPKPD/RepeatedDoseRational.lean) | written; kernel-checked in CI |
| Two-compartment infusion → steady-state central exposure bound (ℝ, Mathlib) | [`lean/BioPKPD/TwoCompartmentInfusion.lean`](lean/BioPKPD/TwoCompartmentInfusion.lean) | written; kernel-checked in CI |
| `axm certify` — recognizer + fail-closed certificate emitter (three schemas) | [`axm/certify.py`](axm/certify.py) | working; tested in CI |
| `axm report` — MIDD-style certificate report | [`axm/report.py`](axm/report.py) | working; tested in CI |
| Emitted certificate instances (kernel-checked end-to-end) | [`CertExample.lean`](lean/BioPKPD/CertExample.lean), [`CertExampleRepeated.lean`](lean/BioPKPD/CertExampleRepeated.lean), [`CertExampleTwoCompartment.lean`](lean/BioPKPD/CertExampleTwoCompartment.lean) | generated; kernel-checked in CI |
| Worked MIDD report artifacts | [`drugX_infusion`](examples/drugX_infusion.report.md), [`drugY_repeated`](examples/drugY_repeated.report.md), [`drugW_two_compartment`](examples/drugW_two_compartment.report.md) | generated; synced in CI |
| Mathlib-in-CI kernel check | [`.github/workflows/lean.yml`](.github/workflows/lean.yml) | runs on every push to `lean/**` |
| `axm certify` test suite | [`.github/workflows/python.yml`](.github/workflows/python.yml) | runs on every push to `axm/**` |
| Browser demo — runs the real package in-browser (Pyodide) | [`docs/index.html`](docs/index.html), [`tools/build_site.py`](tools/build_site.py) | bundle diffed in CI; deployed via [`pages.yml`](.github/workflows/pages.yml) |
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

1. ~~**Repeated-dose accumulation / therapeutic window**~~ — *done* ([`RepeatedDose.lean`](lean/BioPKPD/RepeatedDose.lean)):
   proves `C_trough ≥ C_eff ∧ C_max ≤ C_tox` at steady state for **all** params in the fitted
   box `[ke_lo, ke_hi] × [V_lo, V_hi]`, with each bound certified at its worst-case corner.
2. ~~**A recognizer + certificate report**~~ — *done* ([`axm/certify.py`](axm/certify.py)):
   classifies a one-compartment, first-order, constant-infusion model with parameter
   intervals + threshold, computes the worst-case-corner condition as an exact rational,
   emits a `norm_num`-closed Lean instance of the proved schema, and **fails closed** on
   everything else (multi-compartment, nonlinear elimination, non-positive bounds, certificate
   violations) with a precise reason and no Lean. The emitted artifact is itself kernel-checked
   in CI, and a test asserts the emitter reproduces it byte-for-byte. Both the constant-infusion
   and repeated-dose schemas are auto-emittable. Try: `python -m axm certify
   examples/drugX_infusion.json` or `examples/drugY_repeated.json`.
3. ~~**A MIDD-style report artifact**~~ — *done* ([`axm/report.py`](axm/report.py),
   [`examples/drugX_infusion.report.md`](examples/drugX_infusion.report.md)): theorem statement,
   assumptions, parameter provenance (which fit, which dataset, which method, which CI), proof
   identity (SHA-256 of the emitted artifact + the schema + the exact toolchain it's
   kernel-checked under), and a model-risk note. The hash is content identity, not a kernel
   attestation — the attestation is the green CI run; CI re-renders the report and checks the
   hash equals `sha256` of the kernel-checked artifact. Try: `python -m axm report
   examples/drugX_infusion.json`.

With §5 steps 0–3 done — and the repeated-dose schema since folded into the auto-emittable subset
via rational `exp` enclosures ([`RepeatedDoseRational.lean`](lean/BioPKPD/RepeatedDoseRational.lean),
`1 + x ≤ exp x`) — the build side of the vertical is complete. What remains is further **breadth**
(more model classes) and the open **adoption** question below.

## Building locally

```bash
cd lean
lake exe cache get   # needs open network for Mathlib's prebuilt cache
lake build           # kernel-checks Bio.PKPD.ConstantInfusion.infusion_safety_bound
```

Not affiliated with or endorsed by GSK. The critique that motivated this work is structural
and conditional, never a claim about any person's intent.

License: Apache-2.0
