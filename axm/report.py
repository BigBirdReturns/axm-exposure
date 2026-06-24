"""axm report — a MIDD-style certificate report for a PK/PD model spec.

Roadmap step 3 from the handoff (§5): wrap a certify outcome in the artifact a
pharmacometrician would actually attach to a Model-Informed Drug Development
package or hand to a reviewer. It states, in one legible document:

  * the theorem (what was proved, model-relative and conditional);
  * the assumptions (parameter box, positivity, threshold);
  * the worst-case-corner computation, as an exact rational;
  * parameter provenance (which fit, which dataset, which method, which CI);
  * proof identity (a content hash of the emitted Lean + the schema + the exact
    toolchain it is kernel-checked under);
  * a model-risk note (handoff §2.3): a certificate is about the model under
    stated assumptions, never a claim about a patient.

The report is honest about what the hash is and is not: it is *content identity*
for the emitted artifact, not a kernel attestation. The kernel attestation is the
green CI check that builds the artifact; the hash lets you tie this report to the
exact text that was checked.
"""

from __future__ import annotations

import hashlib
import pathlib

from .certify import CERTIFIED_SUBSET, Outcome

# Read the toolchain pin so the report names the exact prover the artifact is
# kernel-checked under; fall back to a sentinel if the file is not alongside.
_TOOLCHAIN_FILE = pathlib.Path(__file__).resolve().parent.parent / "lean" / "lean-toolchain"

# verified schema (Lean theorem, source file) per certify schema tag.
_SCHEMA_INFO = {
    "constant_infusion": (
        "Bio.PKPD.ConstantInfusion.infusion_safety_bound",
        "lean/BioPKPD/ConstantInfusion.lean",
    ),
    "repeated_dose_rational": (
        "Bio.PKPD.RepeatedDose.repeated_dose_window_rational",
        "lean/BioPKPD/RepeatedDoseRational.lean",
    ),
    "two_compartment_ss": (
        "Bio.PKPD.TwoCompartmentInfusion.central_steady_state_bound",
        "lean/BioPKPD/TwoCompartmentInfusion.lean",
    ),
}


def _toolchain() -> str:
    try:
        return _TOOLCHAIN_FILE.read_text().strip()
    except OSError:
        return "leanprover/lean4 (see lean/lean-toolchain)"


def proof_hash(lean: str) -> str:
    """SHA-256 of the emitted Lean artifact — content identity, not attestation."""
    return hashlib.sha256(lean.encode("utf-8")).hexdigest()


def _provenance_block(spec: dict) -> str:
    prov = spec.get("provenance")
    if not isinstance(prov, dict) or not prov:
        return ("_No parameter provenance supplied in the spec._ A real MIDD "
                "submission must record which fit, dataset, estimation method, "
                "and confidence interval the parameter box came from.")
    labels = {
        "fit": "Model / run",
        "dataset": "Dataset",
        "method": "Estimation method",
        "ci": "Interval origin",
    }
    rows = []
    for key, label in labels.items():
        if key in prov:
            rows.append(f"| {label} | {prov[key]} |")
    # Include any extra provenance keys verbatim.
    for key, val in prov.items():
        if key not in labels:
            rows.append(f"| {key} | {val} |")
    body = "\n".join(rows)
    return f"| Field | Value |\n|---|---|\n{body}"


def report(spec: dict, outcome: Outcome) -> str:
    """Render a Markdown MIDD certificate report for ``outcome``."""
    name = outcome.detail.get("name") or str(spec.get("name", "model"))
    status = outcome.status.upper()
    lines: list[str] = []
    lines.append(f"# Exposure-safety certificate report — `{name}`")
    lines.append("")
    lines.append(f"**Verdict:** `{status}`  ")
    lines.append(f"**Target certified class:** "
                 f"{outcome.detail.get('subset', CERTIFIED_SUBSET)}")
    lines.append("")

    if outcome.status == "refused":
        lines.append("## Outcome: refused (fail closed)")
        lines.append("")
        lines.append("This model is **outside the auto-emittable certified "
                     "subset**. No proof was emitted.")
        lines.append("")
        lines.append(f"> {outcome.reason}")
        lines.append("")
        lines.append(_model_risk_note())
        return "\n".join(lines) + "\n"

    if outcome.status == "failed":
        d = outcome.detail
        lines.append("## Outcome: certificate does **not** hold (fail closed)")
        lines.append("")
        lines.append("The model is inside the certified subset, but a corner "
                     "condition is violated, so no safety certificate can be "
                     "emitted. **This is a finding, not an error:** under the "
                     "fitted parameter box the model can leave the declared "
                     "window.")
        lines.append("")
        if d.get("schema") == "repeated_dose_rational":
            lines.append(f"- rational peak ceiling "
                         f"`D·(1+ke_lo·τ)/(V_lo·ke_lo·τ) = {d['tox_ceiling']}` "
                         f"vs `Ctox = {d['Ctox']}`")
            lines.append(f"- rational trough floor "
                         f"`D·(1−ke_hi·τ)/(V_hi·ke_hi·τ) = {d['eff_floor']}` "
                         f"vs `Ceff = {d['Ceff']}`")
        else:
            lines.append(f"- worst-case steady-state exposure "
                         f"`R/(ke_lo·V_lo) = {d['worst_case_exposure']}`")
            lines.append(f"- toxicity threshold `T = {d['threshold']}`")
        lines.append("")
        lines.append("## Parameter provenance")
        lines.append("")
        lines.append(_provenance_block(spec))
        lines.append("")
        lines.append(_model_risk_note())
        return "\n".join(lines) + "\n"

    # Certified.
    assert outcome.lean is not None
    d = outcome.detail
    h = proof_hash(outcome.lean)
    schema = d.get("schema", "constant_infusion")
    lines.append("## Theorem (model-relative, conditional)")
    lines.append("")
    if schema == "repeated_dose_rational":
        lines.append("For a one-compartment repeated-IV-bolus regimen (dose `D` "
                     "every interval `τ`), at steady state")
        lines.append("")
        lines.append("```")
        lines.append("Cmax_ss = D / (V · (1 − exp(−ke·τ))),")
        lines.append("Ctrough_ss = D · exp(−ke·τ) / (V · (1 − exp(−ke·τ))),")
        lines.append("```")
        lines.append("")
        lines.append(f"the model's steady-state trough stays `≥ Ceff = "
                     f"{d['Ceff']}` and peak stays `≤ Ctox = {d['Ctox']}` for "
                     f"**every** parameter value with `ke_lo ≤ ke ≤ ke_hi` and "
                     f"`V_lo ≤ V ≤ V_hi`.")
        lines.append("")
        lines.append("## Assumptions")
        lines.append("")
        lines.append(f"- dose `D = {d['D']}` (> 0), interval `τ = {d['tau']}` (> 0)")
        lines.append(f"- fitted box `ke ∈ [{d['ke_lo']}, {d['ke_hi']}]`, "
                     f"`V ∈ [{d['V_lo']}, {d['V_hi']}]`")
        lines.append(f"- validity: `ke_hi·τ < 1` (rational efficacy floor)")
        lines.append(f"- **certificate conditions** (rational/conservative corner "
                     f"conditions from `1 + x ≤ exp x`):")
        lines.append(f"  - peak ceiling `D·(1+ke_lo·τ)/(V_lo·ke_lo·τ) = "
                     f"{d['tox_ceiling']} ≤ Ctox = {d['Ctox']}` ✓")
        lines.append(f"  - trough floor `Ceff = {d['Ceff']} ≤ "
                     f"D·(1−ke_hi·τ)/(V_hi·ke_hi·τ) = {d['eff_floor']}` ✓")
    elif schema == "two_compartment_ss":
        lines.append("For a two-compartment constant continuous IV infusion model "
                     "(central volume `V1`, peripheral compartment, any "
                     "`k12, k21 > 0`), at steady state the peripheral flux "
                     "cancels and the central concentration is")
        lines.append("")
        lines.append("```")
        lines.append("C1_ss = A1 / V1 = R / (ke · V1),")
        lines.append("```")
        lines.append("")
        lines.append(f"so the steady-state central exposure stays in "
                     f"`[0, {d['threshold']}]` for **every** parameter value with "
                     f"`ke_lo ≤ ke` and `V1_lo ≤ V1` — the peripheral compartment "
                     f"does not raise the steady-state ceiling. (Steady state "
                     f"only; the no-overshoot transient is argued on paper.)")
        lines.append("")
        lines.append("## Assumptions")
        lines.append("")
        lines.append(f"- infusion rate `R = {d['R']}` (> 0)")
        lines.append(f"- fitted lower bounds `ke_lo = {d['ke_lo']}` (> 0), "
                     f"`V1_lo = {d['V1_lo']}` (> 0)")
        lines.append(f"- steady-state balance: `k12·A1 = k21·A2` and "
                     f"`R + k21·A2 = (ke+k12)·A1`")
        lines.append(f"- toxicity threshold `T = {d['threshold']}`")
        lines.append(f"- **certificate condition** (worst-case / smallest-clearance "
                     f"corner): `R/(ke_lo·V1_lo) = {d['worst_case_exposure']} ≤ "
                     f"{d['threshold']}` ✓")
    else:
        lines.append("For a one-compartment constant continuous IV infusion model")
        lines.append("")
        lines.append("```")
        lines.append("C(t) = (R / (ke · V)) · (1 − exp(−ke · t)),")
        lines.append("```")
        lines.append("")
        lines.append(f"the plasma concentration the model predicts stays in "
                     f"`[0, {d['threshold']}]` for **every** time `t ≥ 0` and "
                     f"**every** parameter value with `ke_lo ≤ ke` and `V_lo ≤ V`.")
        lines.append("")
        lines.append("## Assumptions")
        lines.append("")
        lines.append(f"- infusion rate `R = {d['R']}` (> 0)")
        lines.append(f"- fitted lower bounds `ke_lo = {d['ke_lo']}` (> 0), "
                     f"`V_lo = {d['V_lo']}` (> 0)")
        lines.append(f"- toxicity threshold `T = {d['threshold']}`")
        lines.append(f"- **certificate condition** (worst-case / smallest-clearance "
                     f"corner): `R/(ke_lo·V_lo) = {d['worst_case_exposure']} ≤ "
                     f"{d['threshold']}` ✓")
    lines.append("")
    lines.append("## Parameter provenance")
    lines.append("")
    lines.append(_provenance_block(spec))
    lines.append("")
    lines.append("## Proof identity")
    lines.append("")
    _schema_thm, _schema_file = _SCHEMA_INFO.get(
        schema, _SCHEMA_INFO["constant_infusion"])
    lines.append(f"- verified schema: `{_schema_thm}` (`{_schema_file}`)")
    lines.append(f"- kernel-checked under: `{_toolchain()}` + Mathlib")
    lines.append(f"- emitted-artifact SHA-256: `{h}`")
    lines.append("")
    lines.append("The hash is content identity for the emitted Lean, **not** a "
                 "kernel attestation. The attestation is the green CI run that "
                 "builds the artifact; the hash ties this report to the exact "
                 "text that was checked. Verify it yourself:")
    lines.append("")
    lines.append("```bash")
    lines.append(f"python -m axm certify <spec.json> --lean-only | sha256sum")
    lines.append("cd lean && lake exe cache get && lake build   # kernel check")
    lines.append("```")
    lines.append("")
    lines.append(_model_risk_note())
    return "\n".join(lines) + "\n"


def _model_risk_note() -> str:
    return (
        "## Model-risk note\n"
        "\n"
        "This is a machine-checked statement about a **model under explicitly "
        "stated, bounded assumptions** — that the concentration the model "
        "predicts cannot exceed the declared threshold for any parameter value "
        "in the fitted box. It is **not** a claim that a drug or dose is safe "
        "for a patient. The proof is about the model, not the patient. Model "
        "misspecification, parameter-CI miscalibration, and off-model "
        "physiology are out of scope of the certificate."
    )
