# FEMis — an Agent Skill for FEM/CAE (structural · thermal · CFD · EM · multiphysics, across many solvers)

> **FEMis** is an open-source [Claude Agent Skill](https://code.claude.com/docs/en/skills) for **finite-element
> analysis (FEA / FEM) and CAE governance**: mesh-independence (GCI), verification & validation (V&V), and a precise
> headless-vs-human automation contract across **Ansys, Abaqus, MSC / Simcenter Nastran, OpenFOAM, COMSOL, LS-DYNA,
> Simcenter and Thermal Desktop**. It is a **governance / decision layer, not a solver driver.**

<!-- Machine-readable skill metadata for AI agents and search engines. Canonical manifest: skills_index.json -->
```yaml
name: femis
kind: Claude Agent Skill — CAE/FEM governance & V&V layer
entrypoint: SKILL.md
purpose: Turn an AI coding agent into a disciplined FEM/CAE analyst that governs engineering claims.
when_to_use:
  - finite-element (FEM / FEA) and CAE analysis; element / solver / unit selection
  - mesh-independence / Grid Convergence Index (GCI); verification & validation (V&V) and UQ
  - headless / batch solving; parsing .rst / .rth / .op2 / .f06 results
  - deciding what an agent may run headless vs what a human must decide or sign off
not_for: [driving solvers (pair with an executor), pure CAD modeling, closed-form hand calcs]
pair_with: [PyMAPDL, PyMechanical, PyFluent, Abaqus, OpenFOAM, MSC/Simcenter Nastran, COMSOL, Open FEM Agent, CAE MCP]
physics: [structural, thermal, CFD, electromagnetics, vibro-acoustics/NVH, multibody, multiphysics, fracture, fatigue, composites, buckling, explicit-dynamics]
manifests: [skills_index.json, references_index.json, agents/openai.yaml]
license: Apache-2.0
repo: https://github.com/test1card/femis-skill
```

A [Claude Code Agent Skill](https://code.claude.com/docs/en/skills) that turns an AI coding agent into a
disciplined finite-element analyst. It encodes the full CAE workflow — idealization → meshing → connections →
solve controls → convergence → mesh independence → V&V — plus the **headless/batch automation and result-parsing
gotchas** that usually cost hours to rediscover.

Two things set it apart from a textbook: a precise **agent-headless-vs-human contract** (what an automation
agent may run unattended versus what a person must do in the GUI), and a set of **field-derived,
confidence-tagged failure-mode recipes** — e.g. headless thermal-contact pitfalls that silently produce wrong
results — rarely collected in one place. Recipes carry a provenance tag (`[AUTHOR-VERIFIED]` / `[DOCS-ONLY]` /
`[VERIFIED-web]`) so you can see how far each has been checked.

**How it fits:** femis is the *methodology / decision layer*, not a solver driver. Pair it with an executor —
PyMAPDL / PyMechanical / PyFluent, a driver skill, or an Ansys / Abaqus / OpenFOAM MCP server — which femis
**governs**: it guides and audits the idealization, element, mesh, and connection choices, enforces the execution-mode gates and
V&V, and tells you (via the headless-vs-human contract) what the executor may run unattended versus what needs a
person — while **human-judgment choices (load basis, contact type, defeature scope, allowables, and sign-off) remain with a qualified engineer.** It is the brain on top of the hands.

It covers **structural / mechanical, thermal, CFD/fluids, electromagnetics, vibro-acoustics/NVH, multibody,
coupled multiphysics, and the failure & durability disciplines** (fracture, fatigue, composites, buckling,
crash/explicit dynamics). The methodology is **solver-agnostic**; worked depth is in Ansys (Mechanical/MAPDL, Fluent,
CFX), Siemens Simcenter (3D, Nastran, STAR-CCM+, TMG) and Ansys Thermal Desktop (SINDA/FLUINT), with breadth +
a cross-solver map for **Abaqus, LS-DYNA, MSC Nastran, COMSOL, OpenFOAM, SU2, CalculiX, Code_Aster** and more.
It also includes the **optimization / calibration / model-updating** layer (optiSLang, DesignXplorer,
PyMAPDL+SciPy, HEEDS/SHERPA, Simcenter & TMG Correlation, Nastran SOL 200) incl. **transient T(t) curve
calibration**, a **V&V/UQ** layer (ASME V&V 10/20/40, NAFEMS), and — importantly — a precise
**agent-can/can't + headless-vs-human contract** so it's unambiguous what an automation agent runs headless
versus what a person must do in the GUI.

## Why it exists

Most FEA mistakes are born in pre-processing and hidden by a solver that "ran successfully." This skill makes the
agent enforce gates instead: it won't trust a single-mesh result, it converges the *quantity of interest* (not a
singular peak), it checks equilibrium and energy balance, and it labels every run with an **execution mode**
(SMOKE / DEBUG / ENGINEERING / SIGNOFF) that dictates which gates are mandatory and what may be claimed. Before stating any number the agent runs a **pre-claim self-check**, phrases the result with **claim templates**, and — on load-case / allowable / contact-type / sign-off decisions — **escalates** to a human instead of guessing (`references/claim-templates.md`, `references/escalation-examples.md`). An adversarial **eval set** (`evals/prompts.json`) encodes the expected behavior; CI validates the eval set's **structure** (schema, valid modes/behaviors, and that every referenced file exists) — not agent behavior — and `scripts/live_eval.py` runs a live **skill-on vs skill-off A/B** to *measure* the actual behavior change (see `evals/RESULTS.md`).

## What's inside

```
SKILL.md                 # the router: agent contract, execution modes, workflow, decision tables, V&V, triage
references/
  # — governance / claim discipline (the moat) —
  claim-templates.md              # per-mode (SMOKE/DEBUG/ENGINEERING/SIGNOFF) result-phrasing templates + reusable contract phrases
  escalation-examples.md          # worked refuse/escalate cases (contact type, single-mesh peak, calibration, sign-off, singularity, ...)
  claims-validation.md            # external-source validation of the router's load-bearing claims (claim -> standard/textbook -> verdict)
  # — core workflow —
  meshing-convergence.md          # element tech, quality metrics, mesh independence (GCI/ZZ-SPR), p-/hp-refinement, DWR, singularities
  material-modeling.md            # constitutive models (plasticity/creep/hyperelastic/composite/damage), data sources, calibration
  solver-numerics.md              # equation/eigen solvers, nonlinear, time integration (implicit/explicit), parallelism, diagnostics
  mechanical-connections.md       # contact types/formulations, mortar/Nitsche, RBE2 vs RBE3, bolts (VDI 2230)/welds (hot-spot)/joints
  thermal-contact-resistance.md   # TCR/TCC physics, value tables, cryo, correlations
  thermal-and-coupling.md         # transient thermal, radiation, phase change, spacecraft/vacuum, ECSS correlation, coupling
  dynamics-nvh-acoustics.md       # modal/harmonic/random/shock, NVH, vibro-acoustics, rotordynamics, flutter
  cfd.md                          # turbulence (+UQ), y+/near-wall, CFD meshing, discretization, multiphase, compressible, CHT/FSI
  # — failure & durability disciplines —
  fracture-mechanics.md           # LEFM/EPFM, K/J extraction, crack-tip mesh, contour-integral vs VCCT/XFEM/CZM/SMART, FCG
  fatigue-durability.md           # S-N / ε-N, notch & mean-stress, rainflow/Miner, multiaxial critical-plane, spectral, TMF, FKM
  composites-analysis.md          # progressive damage (Hashin/Puck/LaRC), crack-band regularization, delamination, sandwich, draping
  plasticity-inelastic-assessment.md # shakedown/ratcheting/Bree, limit-load, ASME VIII-2 elastic-plastic, stress linearization, springback
  buckling-stability.md           # LBA vs GNA-GNIA vs GMNIA, knockdown factors, imperfection seeding, post-buckling, stiffened panels
  explicit-dynamics-impact.md     # when explicit, contact for explicit, erosion, hourglass, mass-scaling, Lagrangian/SPH/ALE/CEL, blast/drop/ballistic
  # — additional physics —
  electromagnetics.md             # CEM by frequency regime, FEM-vs-MoM/FDTD, edge elements, ports/radiation BCs, machines/antenna/RF
  acoustics-fem.md                # duct acoustics, mufflers, absorption, infinite elements vs PML, acoustics-FEM mistakes
  coupled-process-simulation.md   # battery/fuel-cell, additive manufacturing, welding, curing, molding, casting/forming process coupling
  ml-surrogates-and-rom.md        # data-driven ROM (POD/DMD/operator-inference), GP/PCE/neural-operator/PINN surrogates, digital twins
  # — overview, optimization, V&V —
  specialized-analyses.md         # overview/router to failure disciplines + submodeling, hyperelastic, cyclic symmetry, creep, DOE/topology
  advanced-methods.md             # substructuring/CMS/ROM, multibody, optimization/topology, loads & BC catalog
  optimization-calibration.md     # optimizer/calibration tool map (PyAEDT/OSS too); transient-T(t) calibration; objective gate
  topology-optimization.md        # SIMP/RAMP density methods, filtering & min-length-scale, manufacturing/AM constraints, level-set/lattice
  vv-uq.md                        # V&V/UQ, credibility scales, ASME V&V 10/20/40, ECSS, SPDM, Bayesian calibration, NAFEMS, governance
  software-landscape.md           # popular CAE tools (+Physics-AI): use/license/headless/formats + which-tool-for-which-job
  # — automation & platform —
  agent-automation-boundary.md    # per-operation agent-headless vs human-GUI contract across every platform
  platform-commands.md            # MAPDL / Mechanical / Nastran / NX-Open / OpenTD cheat-sheet
  pymechanical-headless.md        # PyMechanical/Workbench headless gotchas
  ansys-thermal-contact-pitfalls.md # headless fix for thermally-inert structural contacts (CONTA174 KEYOPT(1))
  driving-live-sessions.md        # driving live solver sessions: inspect→step→re-inspect, debug-on-failure
  comsol.md                       # COMSOL automation: JPype/Java API, .mph offline introspection, batch
scripts/
  gci.py                          # Grid Convergence Index (mesh/time-step independence) calculator
  yplus.py                        # y+ first-cell-height estimator for wall-bounded CFD meshing
  units_check.py                  # consistent-units + 1g mass sanity check (catches wrong-system density)
  rainflow.py                     # ASTM E1049 rainflow cycle counting + Palmgren-Miner damage
  mac.py                          # Modal Assurance Criterion + COMAC (auto/cross-MAC, complex modes, mode pairing)
  hourglass_check.py              # explicit-dynamics energy-quality gate (hourglass % / energy balance / KE-IE)
  run_skill_evals.py              # validate the activation/behavior eval set + score live agent responses
  live_eval.py                    # optional live A/B harness (skill-on vs skill-off) — measures behavior change
  run_manifest_template.json      # per-solve traceability manifest (NAFEMS R0033)
evals/
  prompts.json                    # 22 adversarial activation/behavior eval cases (expected refs, mode, refuse/claim/escalate)
  RESULTS.md                      # measured skill-on vs skill-off A/B results (live behavior-change evidence)
skills_index.json                 # master machine-readable manifest (router, references, scripts, evals)
references_index.json             # machine-readable index of references/ (file → title)
tests/
  test_scripts.py                 # 56 pytest checks across the 6 calculator scripts (known-good values + error paths)
.github/workflows/
  ci.yml                          # CI: pytest + script self-tests + eval-set validation + source-hygiene gate (placeholders/caches/links/banned-domains/TOCs), Python 3.10-3.13
```

Progressive disclosure: `SKILL.md` stays lean (a routing layer); the agent loads a `references/` file only when
that topic is in play.

The `scripts/` are covered by a `pytest` suite (`tests/test_scripts.py`, 56 checks) run in CI across Python
3.10–3.13 — so the runnable calculators stay correct, not just illustrative.

## Recommended Agentic CAE Workflow

`femis` is designed to sit at the top of an agentic CAE stack as the **governance layer**. It works best when
paired with solver executors, geometry/mesh tools, and post-processing scripts.

A robust workflow looks like this:

1. **Intake / requirements** — define the objective, quantity of interest, load cases, constraints, materials,
   environment, acceptance criteria, solver, and consequence level.
   *Human-owned decisions:* load basis, allowables, design code, idealization, and sign-off authority.

2. **Governance / claim discipline** — use `femis` to choose the execution mode (SMOKE, DEBUG, ENGINEERING,
   SIGNOFF). The mode determines which gates are mandatory and what the agent may claim.

3. **Geometry and meshing** — use the appropriate geometry/meshing tool (FreeCAD, Gmsh, PyPrimeMesh,
   PyMechanical, or a commercial meshing API). `femis` governs mesh adequacy; it is not itself a mesher.

4. **Solver execution** — pair with an executor that runs models, for example:
   - Open FEM Agent
   - PyMAPDL / PyMechanical / PyFluent
   - Abaqus Python or `noGUI`
   - OpenFOAM scripts or MCPs
   - COMSOL batch / API workflows
   - Nastran + pyNastran
   - PyAEDT for electromagnetics
   - internal CAE driver skills or MCP servers

   The executor runs the solve. `femis` governs the claim.

5. **Verification** — run units, mass, reaction/balance, convergence, singularity, mesh/time-step, and
   provenance checks. For sign-off-supporting claims, require GCI or an equivalent documented error bound.

6. **Post-processing** — extract only the quantities of interest and evidence (`qoi.csv`, `checks.md`, plots,
   convergence tables, `run_manifest.json`). Do not paste full solver logs into the agent context.

7. **V&V / credibility review** — state validation evidence, uncertainty, applicability limits, model-form
   risk, and the weakest credibility factor.

8. **Human sign-off** — the agent prepares the evidence package; a qualified engineer accepts or rejects the result.

This separation is intentional: solver executors run models; `femis` decides whether the resulting numbers
are only SMOKE/DEBUG artifacts, usable ENGINEERING results, or sign-off-supporting evidence.

### Pairing With Open FEM Agent

[Open FEM Agent](https://github.com/alhermann/open-fem-agent) is a natural companion for open-source FEM
execution. It focuses on running and interrogating FEM backends; `femis` sits above that layer and governs
claim quality, convergence evidence, provenance, and human-judgment boundaries. **Use Open FEM Agent to
execute; use `femis` to decide what may be claimed** — one recommended executor, not a blessed default.

## Install

This repository **is** the skill: `SKILL.md` lives at the repo root, with `references/` and `scripts/`
beside it. Install it by placing the repo contents into a directory named `femis` under a `skills/`
folder, so the path ends up `…/skills/femis/SKILL.md`.

**Personal (all projects):** copy the repo contents into `~/.claude/skills/femis/` (macOS/Linux) or
`%USERPROFILE%\.claude\skills\femis\` (Windows), with `SKILL.md` at that folder's root.

**Project-scoped:** copy the repo contents into `./.claude/skills/femis/` (again with `SKILL.md` at
that folder's root).

**Pin a version** for reproducibility — install from a known tag or commit so an analysis always runs
against a fixed revision of the methodology (after cloning a published copy: `git -C <skill-dir> checkout <tag-or-sha>`).

Or **clone it directly** into the skill path — note the repo is `femis-skill` but the skill folder is
`femis`:

```bash
# personal (all projects)
git clone https://github.com/test1card/femis-skill ~/.claude/skills/femis
# project-scoped
git clone https://github.com/test1card/femis-skill .claude/skills/femis
```

Then pin a revision for reproducibility: `git -C <skill-dir> checkout <tag-or-sha>`. See
[`PRE-PUBLISH.md`](PRE-PUBLISH.md) for the publishing checklist (the repo must be created and pushed first).

The skill activates automatically when the agent's task matches the `description` in `SKILL.md` (e.g. "run a
transient thermal solve", "calibrate a cooldown curve", "mesh-independence study", ".rth parse"). No manual
invocation needed.

> Layout note: a bare skill is just the `femis/` folder (with `SKILL.md` at its root) dropped into a
> `skills/` directory. To distribute it as an installable Claude Code **plugin** (`/plugin` + a marketplace
> listing), wrap it with a `.claude-plugin/plugin.json`.

## Scope

**Use for:** static / modal / buckling / nonlinear structural; steady & transient thermal & radiation; **CFD**
(RANS/LES, conjugate heat transfer); **vibro-acoustics / NVH**; **electromagnetics** (machines, antenna/RF);
**multibody**; coupled multiphysics (thermo-mechanical, FSI) and **coupled process simulation** (AM, welding,
curing, battery/fuel-cell); **failure & durability** (fracture, fatigue, composites, crash/explicit-dynamics);
contact & thermal contact resistance; bolted/welded/rigid connections; meshing & GCI; substructuring / ROM and
**ML-surrogates / data-driven ROM / digital twins**; headless/batch solving and result parsing; optimization,
calibration / inverse parameter ID & model updating; V&V/UQ; cryogenic / vacuum / spacecraft thermal.

**Not for:** pure CAD modeling, or problems better served by a closed-form hand calc.

## Provenance & honesty

The headless/automation recipes are tagged by confidence: `[AUTHOR-VERIFIED]` (run on a real model), `[DOCS-ONLY]`
(from documentation, not executed here), `[VERIFIED-web]` / `[NEEDS-HW-TEST]` (vendor-documented; reproduce on
your licensed install before relying on it for ENGINEERING/SIGNOFF). Treat any non-`[AUTHOR-VERIFIED]` recipe as a
hypothesis and run a SMOKE reproducer first.

## License

Apache-2.0 — see [LICENSE](LICENSE). (MIT is an equally fine choice if you prefer maximal permissiveness; swap
the file if so.) Engineering values quoted are textbook orders-of-magnitude; verify against your own materials
and standards.

## Contributing

Issues and PRs welcome — especially additional `[AUTHOR-VERIFIED]` headless recipes and platform gotchas. Keep
`SKILL.md` a lean router; put depth in `references/`. Follow the skill-authoring conventions in
Anthropic's [Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).
