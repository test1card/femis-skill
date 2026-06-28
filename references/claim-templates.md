# Claim templates — phrase every result at the right altitude

The execution mode (SMOKE / DEBUG / ENGINEERING / SIGNOFF, see `SKILL.md`) sets what you are *allowed to
claim*. This file converts that into the exact words. **The phrasing is part of the gate:** an agent that
runs a SMOKE solve and then says "the stress is 180 MPa" has misrepresented its own confidence even if the
number is right. Use the template for the mode whose gates you actually passed — never a higher one. Keep the
`<slots>` qualifiers; they *are* the safety content.

> Run the **pre-claim self-check** in `SKILL.md` first. If any answer is "no/unknown", you are not in the mode
> you think you are — drop to the honest one and use its template (or `references/escalation-examples.md`).

## SMOKE — "the pipeline ran; no engineering conclusion"
Gates: env/deck/solve/parse ran; result file written and readable. You may NOT state an engineering number or tune anything.
> **SMOKE result.** The `<solver>` `<analysis>` deck ran to completion and a readable `<.rst/.rth/.op2>` was
> produced. This proves the pipeline (mesh → solve → parse), **not** any engineering quantity. No QoI is
> claimed and nothing is verified. Next step for a usable number: run in ENGINEERING mode with the gates.

## DEBUG — "diagnostic result only"
Gates: the one decisive test for the symptom; connectivity gate if thermal. You may NOT present the diagnostic solve as a result.
> **DEBUG / diagnostic only.** To isolate `<symptom>` I ran `<decisive test>`; it shows `<finding>`. These
> numbers are for cause-finding and are **not** verified for reporting. Root cause: `<cause>`. Fix: `<fix>`.
> A reportable value requires a clean ENGINEERING/SIGNOFF run.

## ENGINEERING — "usable result with stated checks and limitations"
Gates passed: units; connectivity; reaction/heat/mass balance; convergence; QoI extraction; singularity check. You may NOT claim sign-off.
> **ENGINEERING result (not a sign-off).** `<QoI>` = `<value> <units>` for `<load case / config>`.
> Checks: units `<1g / hand-calc>` ✓, balance `<Σreaction vs applied, %>` ✓, convergence
> `<residual orders / nonlinear tol>` ✓, singularity `<read N elem away / N/A>` ✓. Discretization error:
> `<single-mesh ZZ/SPR estimate or last-refinement Δ, %>` — **mesh independence NOT yet demonstrated (no GCI).**
> Margin: `<MoS>` vs `<NAMED criterion/code>`. Assumptions/limitations: `<list>`. Not valid for sign-off until
> the SIGNOFF gates are met.

## SIGNOFF — "traceable result with error bounds and evidence"
Gates passed: all ENGINEERING + mesh & time-step independence (GCI, asymptotic range) + traceable report + error bounds. You may NOT skip a gate or hand-wave uncertainty.
> **SIGNOFF-supporting result.** `<QoI>` = `<value>` ± `<error bound> <units>`, `<load case>`.
> Mesh independence: GCI_fine = `<%>` over `<N>` grids (r = `<ratio>`, p = `<observed order>`, asymptotic
> `<GCI23/(r^p·GCI12) ≈ 1>`). Time-step independence: `<verdict>`. Code verification: `<vs analytical /
> NAFEMS benchmark — this is VERIFICATION, not validation>`. Validation: `<vs independent EXPERIMENTAL test;
> u_val; |E| ≤ u_val — or state "NOT validated: no test data">` (benchmarks ≠ validation; calibration ≠
> validation). Margin of safety: `<MoS>` vs `<code/criterion>` with
> `<FoS + model-uncertainty factor>`. Evidence: `run_manifest.json <id>`, solver `<name + version>`, deck hash
> `<…>`, result hash `<…>`. Credibility: `<NASA CAS / Sandia PCMM weakest factor>`. **A qualified engineer,
> not this agent, accepts the sign-off.**

## When you cannot reach the mode you were asked for
> **Cannot state that yet.** You asked for `<an engineering/sign-off number>`, but `<gate>` is not satisfied
> (`<what's missing>`). What I currently have is a `<SMOKE/DEBUG>` output. To get there I need
> `<the missing gate(s)>`. See `references/escalation-examples.md` for the pattern.

## Reusable contract phrases (quote verbatim)
- **No autonomous sign-off:** "I do not self-authorize sign-off — it is a human engineering decision. I can
  assemble the GCI, error bounds, balance checks, validation, and manifest that support it; a qualified
  engineer must accept it."
- **Solve vs predict:** "A surrogate/ROM predicts only inside its training envelope; I re-solve the
  optimum/critical case on the full FE model before any ENGINEERING/SIGNOFF claim."
- **Calibration ≠ validation:** "Tuning knobs until the model matches data is calibration, not validation;
  validation is agreement on held-out data the calibration never saw."
- **Singular peak:** "That peak sits at a `<corner / point load / crack tip>` singularity — it rises without
  bound under refinement and is not a physical stress; I report the QoI read away from it / linearized (ASME)."
- **Solver-flag certainty:** "I have not verified `<flag / API>` against the installed `<solver version>`; I
  will confirm it in that version's `-help`/docs before relying on it rather than assert it."
