# Escalation & refusal examples — when the right move is "no" or "ask first"

Trustworthy behavior is **not** answering every prompt — it is recognizing the prompts where answering alone
would be malpractice. Each case gives the **prompt**, why it is a **trap**, the **gate** it hits (see
`SKILL.md`), and a **response template**. The pattern is always the same: *do the scriptable part, surface the
judgment, escalate the decision.* Phrase the eventual result with `references/claim-templates.md`.

## 1. "Just pick bonded or frictional contact and run it."
Gate: contact **type** is HUMAN-JUDGMENT (building it is AGENT-HEADLESS).
> I can build either, but the **type** changes the answer — bonded allows no separation/slip, frictional is a
> nonlinear load path. That's an engineering decision tied to how `<joint>` actually behaves. Which governs,
> or should I run both as a bounding study and show the spread? I won't pick silently.

## 2. "Use this single-mesh stress peak for the margin."
Gate: a single-mesh number with no error statement is never a result; the peak may be singular.
> One mesh doesn't bound discretization error, and `<location>` looks like a stress concentration that may not
> converge. Before this is a margin I need a GCI study (SIGNOFF) or at least a single-mesh ZZ/SPR estimate plus
> a read away from the peak (ENGINEERING). Want me to run the refinement?

## 3. "Tune the thermal contact conductance until the model matches the test."
Gate: calibration ≠ validation; reject edge-pinned knobs; check the knob is even the lever.
> I can calibrate h_c, with two cautions: (1) matching the test by tuning is **calibration, not validation** —
> I'd validate on held-out data afterward; (2) if h_c lands at its physical-corridor edge, it's masking a
> different error. First I'll check it's even the lever (set all junctions high — if the QoI barely moves the
> response is solid-conduction-limited and h_c is not the knob). Proceed on that basis?

## 4. "The surrogate optimum is good enough — report it as the result."
Gate: solve vs predict — a surrogate predicts only inside its training envelope.
> The surrogate found `<x*>`, but that's a *prediction*, and optimizers exploit surrogate artifacts so error
> is largest exactly at the optimum. Before it's an ENGINEERING/SIGNOFF result I must re-solve `<x*>` on the
> full FE model. I'll run that confirmation solve and report its number.

## 5. "Which load case governs? Just use the worst one."
Gate: the load basis is a requirement the agent does not own.
> I can rank the cases I'm given, but I can't invent the load set — "governing" depends on the design
> requirements / mission load spec. Point me to the load basis (requirements doc, spectrum, factors) and I'll
> screen all cases and identify the driver with evidence.

## 6. "Can you sign this off?"
Gate: no autonomous sign-off — the agent assembles evidence, it does not authorize.
> I don't self-authorize sign-off. I can produce everything it needs — GCI/error bounds, balance checks,
> validation vs `<benchmark>`, margins vs `<code>`, and a traceable manifest — but a qualified engineer
> accepts it. Current SIGNOFF gate status: `<checklist>`. Still open: `<…>`.

## 7. "Report the peak stress at the re-entrant corner."
Gate: singularity detector.
> That corner is a geometric singularity — its peak rises without bound as the mesh refines, so it is not a
> physical stress. I'll report `<QoI>` read ~1 element away / linearized per ASME, or we add the real fillet
> radius `<r>` and converge that. Which do you want?

## 8. "Use `-np 8` / `<flag>` to speed it up."
Gate: solver-flag certainty + physical-vs-logical cores.
> Two checks first: (1) core counts should map to **physical** cores, not logical/HT, or scaling degrades; and
> (2) I haven't verified `<flag>` against the installed `<solver version>` — flags drift between releases. I'll
> confirm it in `-help`/docs before using it, rather than risk a silently-ignored or wrong flag.

## 9. "Skip mesh independence, we're short on time — just give the number."
Gate: SIGNOFF requires GCI; skipping it changes the claim altitude, not just the schedule.
> I can give a faster number, but then it's an **ENGINEERING** result with a single-mesh error estimate and
> stated limitations — not a sign-off. If `<decision>` needs sign-off, the GCI study isn't optional. Tell me
> which altitude you need and I'll label it honestly.

## 10. "The reaction doesn't quite balance but the stress looks reasonable — just report the stress."
Gate: equilibrium. A failed balance gate invalidates the field however plausible it renders.
> A reaction-vs-applied imbalance of `<%>` means the model isn't in equilibrium — under/over-constraint or a
> lost contact — so the stress field isn't trustworthy yet. I'll locate the imbalance (`FSUM` vs applied, BC
> and contact status) before quoting any stress.

## 11. "Defeature that fillet/hole, it's slowing the mesh."
Gate: *what* to defeature is HUMAN-JUDGMENT (the operation is scriptable).
> I can defeature it, but removing `<feature>` may delete the very stress raiser the QoI depends on. Is
> `<feature>` away from the region of interest and load path? If it's near `<QoI location>` I'd keep it (or
> sub-model). Confirm and I'll proceed.

## 12. "It didn't converge — just loosen the tolerance so it finishes."
Gate: don't loosen tolerance to force convergence — fix the model.
> Loosening the tolerance produces a "converged" run that isn't solved. The residual history points to
> `<cause: lost contact / rigid-body mode / over-soft material>`. I'll fix that (stabilize contact, constrain
> the DOF, correct props) rather than hide non-convergence behind a looser tol.
