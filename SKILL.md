---
name: fem-cae
description: Finite element analysis (FEA / FEM) & CAE — structural, thermal, CFD, electromagnetics, vibro-acoustics/NVH, multibody, coupled multiphysics. Use when running, scripting, or automating solvers (Ansys, Abaqus, Nastran, LS-DYNA, COMSOL, OpenFOAM, Simcenter, Thermal Desktop and more); for mesh convergence / independence (GCI), simulation verification & validation (V&V / UQ), engineering sign-off, or the solver automation boundary (what an agent does headless vs what a human must do in the GUI). Triggers: static/modal/eigenvalue-buckling, nonlinear/contact/plasticity/creep/ratcheting, fatigue (S-N/strain-life), fracture (J-integral/XFEM/crack-growth), composites/delamination, explicit/crash/impact, steady/transient thermal & radiation, CFD turbulence/y+/multiphase, electromagnetics (eddy-current/full-wave), rotordynamics/Campbell, random-vibration/Miles, thermal contact resistance, bolted/welded/RBE2/RBE3 connections, mesh independence (GCI)/error estimation, substructuring/ROM/ML-surrogates, optimization & inverse calibration (transient T(t)), V&V/UQ & model credibility, choosing elements/solvers/units, parsing .rst/.rth/.op2/.f06. Also defines what an agent can do headless vs what a human must do in the GUI.
license: Apache-2.0
metadata:
  version: 1.0.0
---

# FEM / CAE — structural · thermal · CFD · multiphysics

> **This skill governs engineering claims — it does not drive solvers or sign off designs.** It pairs with a
> solver driver / MCP (PyMAPDL, PyMechanical, an Abaqus / OpenFOAM driver, Open FEM Agent, a CAE MCP) that
> *executes*; this skill decides **whether a result may be claimed, at what altitude, and when a human must
> decide.**

## Overview

Run and automate finite-element and CAE analysis end-to-end: locate the installed solver, build the
deck/script, launch **headless/batch**, tail the log for convergence, parse results, and apply professional
practice (idealization → meshing → connections → solve controls → convergence → mesh independence → V&V) on
every run. The **methodology is solver-agnostic**; worked depth here is Ansys / Simcenter / Thermal Desktop, with
breadth across Abaqus, LS-DYNA, MSC/Simcenter Nastran, COMSOL, OpenFOAM, Fluent, CFX, STAR-CCM+, CalculiX,
Code_Aster (see `references/software-landscape.md`).

**Core principles (enforce as gates):**
1. **No result is trusted until its discretization (mesh/time-step) error is addressed** — *bounded and stated* in ENGINEERING (e.g. last-refinement QoI change, or a single-mesh ZZ/SPR estimate), *fully demonstrated* with a GCI study in the asymptotic range for SIGNOFF; a single-mesh number reported without any error statement is never a result. Plus the convergence checks below.
2. **Converge the Quantity of Interest (QoI), not the peak** — peaks at sharp corners/point loads/crack tips are singularities that never converge.
3. **Most error is born in pre-processing** (idealization, BCs, connections) — front-load those decisions.
4. **Verification before validation; calibration ≠ validation** — and an agent must not claim sign-off without run evidence.

**This SKILL.md is the router.** Depth lives in `references/` — load a reference only when its topic is in play.

## When to use

- Structural (static/modal/buckling/nonlinear/explicit), thermal (steady/transient/radiation), **CFD** (RANS/LES, CHT), **electromagnetics** (low-/high-frequency), **vibro-acoustics/NVH**, **multibody**, and **coupled multiphysics** (thermo-mechanical, FSI, EM-thermal).
- **Failure & durability:** fracture / damage-tolerance, fatigue (incl. vibration/spectral), composites, plasticity / shakedown / ratcheting, buckling & stability, crash / impact / drop.
- Contact, thermal contact resistance, bolted/welded/rigid connections; meshing & mesh-independence (GCI); element/solver/unit selection.
- Headless/batch solving and result parsing; optimization, calibration, inverse parameter ID / model updating.
- V&V / UQ; substructuring / ROM; cryogenic / vacuum / spacecraft thermal.
- Deciding **what an agent can automate headless vs what a human must do** (next section).

**Not for:** pure CAD modeling or problems better served by a closed-form hand calc.

## ★ Agent capability & headless-vs-human contract

Precisely who does what. Buckets: **AGENT-HEADLESS** (fully scriptable/batch, no GUI) · **AGENT-VIA-API** (Python/journal API, needs a session + license) · **HUMAN-GUI** (must be interactive at least once) · **HUMAN-JUDGMENT** (engineering decision the agent must not make alone) · **LICENSE-GATED**. Full per-platform detail: `references/agent-automation-boundary.md`.

| Operation | Classification | How / why |
|---|---|---|
| CAD import | AGENT-VIA-API | PyMAPDL/PyMechanical/`run_journal` import STEP/Parasolid |
| Geometry cleanup / heavy defeature | AGENT-VIA-API + HUMAN-JUDGMENT | scriptable defeature/pinch; messy repair + *what to defeature* is judgment |
| Meshing | AGENT-HEADLESS (Ansys) · SEED-IN-GUI (NX) | PyMAPDL/PyMechanical mesh fully headless; **NX `.fem`/`.sim` templates don't resolve in batch → seed once in GUI** |
| Material create/assign | AGENT-HEADLESS | scriptable on all platforms; supply T-dependent data |
| Contacts / connections | AGENT-HEADLESS (build) + HUMAN-JUDGMENT (type) | defining is scriptable; **bonded vs frictional / RBE2 vs RBE3 is an engineering choice** |
| BCs & loads | AGENT-HEADLESS | scriptable; agent must not invent the load case |
| Expose params for optimization | AGENT-HEADLESS (PyMAPDL `*SET`) · HUMAN-GUI (Workbench `P#`, NX Expressions, HEEDS tags) | only PyMAPDL is GUI-free for parameterization |
| Solve (steady/transient/nonlinear) | AGENT-HEADLESS + LICENSE-GATED | `ansys -b`, `nastran.exe`, `tmgnx`, `abaqus job=`, `fluent -g`, OpenFOAM, `cfx5solve -batch`, `starccm+ -batch` |
| Electromagnetic solve (machines/RF/eddy) | AGENT-VIA-API + LICENSE-GATED | **PyAEDT** (`import ansys.aedt.core`, `non_graphical=True`), COMSOL/getDP batch; ports/excitations/sweeps are engineering setup |
| Optimization / DOE / calibration | AGENT-HEADLESS (PyMAPDL+SciPy, optiSLang `-b`, HEEDS CLI) + GUI-AUTHOR-ONCE | author the study/tags in GUI once, then run headless |
| Results extraction | AGENT-HEADLESS | PyDPF, pyNastran (`.op2`/`.f06`), `.odb`, SINDA `.out`, CGNS/VTK |
| Post images/plots | AGENT-HEADLESS | pyvista off-screen, ParaView `pvbatch` |
| Correlation / model-update (MAC, node pairing) | HUMAN-GUI | interactive test↔analysis node pairing is GUI work |
| Template / `.sim` / project authoring (NX) | HUMAN-GUI | template registry not initialized headless → pre-create a seed, then drive it |
| Licensing | LICENSE-GATED | each parallel solver instance consumes its own seat |

**An agent must NEVER auto-do:** choose idealization / element / contact-type / BC alone (HUMAN-JUDGMENT) · accept a calibration knob **pinned at its physical-corridor edge** · report a **singular peak** or an **unconverged** result as a result · claim verification / mesh-independence / sign-off **without the run evidence** · perform an irreversible push/overwrite without authorization.

## Pairing & executor contract

This skill is the **governance layer, not the executor.** Pair it with whatever drives the solver (PyMAPDL,
PyMechanical, an Abaqus / OpenFOAM driver, Open FEM Agent, a CAE MCP): **the executor runs; this skill governs
the claim.** Trust no solver output without provenance — a result is creditable only when the executor returns:

- **Run manifest** (`run_manifest.json`, template `scripts/run_manifest_template.json`) — the traceability spine (NAFEMS R0033).
- **Solver name + exact version** — read from the *detected* install's banner/`-help`, never assumed.
- **Input-deck hash + result-file hash** (e.g. SHA-256 of the `.inp`/`.dat`/`.cdb` and of the `.rst`/`.rth`/`.op2`) — ties a number to the exact deck and result that produced it.
- **Command + flag evidence** — the actual launch line, flags verified against that version (version-aligned-commands rule, Step 0).
- **Isolated workspace** — a clean working dir; outputs written there, never overwriting a prior "final" without a `superseded_by` pointer.

A result lacking this provenance is a SMOKE/DEBUG artifact at best — phrase it as such (`references/claim-templates.md`).

## Execution modes (pick one per task — sets the mandatory gates and what you may claim)

| Mode | Use when | Mandatory gates | Never |
|---|---|---|---|
| **SMOKE** | prove env/deck/solve/parse runs | Step 0; solve completes; result file written **and** readable | claim any engineering number; tune anything |
| **DEBUG** | find a failure's cause | the **one decisive test** for the symptom; connectivity gate if thermal | present a diagnostic solve as a result |
| **ENGINEERING** | usable result + sanity checks | units; connectivity; reactions/heat/mass balance; convergence; QoI extraction; singularity check | claim sign-off; report a singular peak |
| **SIGNOFF** | defensible deliverable | all ENGINEERING **+ mesh & time-step independence (GCI, asymptotic range)** + traceable report + error bounds | skip any gate; hand-wave uncertainty |

A SMOKE/DEBUG result is a pipeline/physics check, **never** an engineering conclusion — label it.

## ★ Pre-claim self-check — answer ALL before stating any engineering number

This is the gate that makes the skill trustworthy. **Before you type a stress, temperature, frequency, margin,
drag, or "it passes,"** answer these. If any answer is *no / unknown*, you do **not** have a result — you have
a SMOKE/DEBUG output: say so and stop.

1. **Mode?** Which execution mode am I in, and have *its* mandatory gates passed? (SMOKE/DEBUG ⇒ not an engineering conclusion.)
2. **Units?** Consistent system verified (1g-mass / hand-calc check); density not unit-corrupt?
3. **Discretization error addressed?** Mesh **and** time-step error bounded *and stated* (GCI for SIGNOFF; single-mesh ZZ/SPR estimate for ENGINEERING)? A lone single-mesh number is never a result.
4. **Singularity excluded?** Is the QoI at a corner / point-load / crack-tip artifact? Read away or linearize before quoting.
5. **Balance checked?** Reaction = applied; heat/mass/energy balance within tolerance; convergence from the *residual history*, not the exit code?
6. **Allowable named?** Is there a margin vs a NAMED criterion / design code — not a bare number?
7. **Human-judgment gate crossed?** Did I silently choose a load case, contact type, allowable, defeature, or sign-off? If yes — **STOP and escalate** (`references/escalation-examples.md`).

Then phrase the result with the matching template in `references/claim-templates.md`. **The agent never claims
sign-off without run evidence, and never self-authorizes an engineering decision.** Exact solver flags / API
calls are themselves a claim — confirm them per the version-aligned-commands rule in Step 0.

## Step 0 — ALWAYS first: environment discovery

Never assume a version or path. Find what's installed/licensed, then confirm platform + physics + QoI.

```powershell
Get-ChildItem "C:\Program Files\ANSYS Inc" -Recurse -Filter "ANSYS*.exe" -ErrorAction SilentlyContinue | Select FullName   # MAPDL/Mechanical/Fluent/CFX
Get-ChildItem "C:\Program Files\Siemens" -Recurse -Include "nastran.exe","run_journal.exe","tmgnx.cmd","ugraf.exe" -ErrorAction SilentlyContinue
Get-ChildItem "C:\Program Files" -Recurse -Filter "abq*.bat" -ErrorAction SilentlyContinue   # Abaqus; also `which icem`, OpenFOAM `foamVersion`
$env:ANSYSLMD_LICENSE_FILE; $env:LM_LICENSE_FILE
(Get-CimInstance Win32_Processor | Measure-Object NumberOfCores -Sum).Sum   # PHYSICAL cores
```

Linux: `ansysNNN -b`, `nastran`, `abaqus`, `simpleFoam`, `fluent -g`; check `$LM_LICENSE_FILE`, `nproc`.

**Version-aligned commands (rule):** never emit a solver command, flag, or API call you have not verified exists in the **detected** release — versions rename flags and drift APIs. Confirm against the installed version's `-help`/docs before relying on it, especially for ENGINEERING/SIGNOFF.

## Canonical workflow (run in order)

1. **Objective + QoI** — the scalar that drives the decision (margin, deflection, frequency, peak T, drag). Not "run the model."
2. **Analysis type** — static/modal/buckling/thermal/CFD/coupled; linear vs nonlinear (material? large-deflection? contact? turbulence?).
3. **Idealize** *(most consequential)* — 1D/2D/3D; symmetry only if geometry **and** loads **and** BCs are symmetric; defeature irrelevant features. → `references/meshing-convergence.md`.
4. **Materials** — correct constitutive model; **temperature-dependent properties**; at cryo use **∫α(T)dT**. → `references/material-modeling.md`.
5. **Mesh** — element order/family, refinement at concentrations, quality gate. → `references/meshing-convergence.md`.
6. **Connections & contact**. → `references/mechanical-connections.md`, `references/thermal-contact-resistance.md`.
7. **BCs & loads** — remove only the rigid-body modes appropriate to the model's dimensionality/type (an unconstrained **3D solid** has 6; 2D, axisymmetric, shell-only and cyclic-symmetric models differ); loads over realistic areas (never point loads/constraints → singularities); inertia relief for free bodies. → `references/advanced-methods.md`.
8. **Solve controls** — solver type, cores, substeps + tolerances. → `references/solver-numerics.md`.
9. **Verify** — equilibrium, mesh/time-step independence, convergence history. → `references/vv-uq.md`.
10. **Validate** — vs test / hand-calc / NAFEMS benchmark (calibration ≠ validation).
11. **Post & report** — right measure, averaged-vs-unaveraged check, margins, stated assumptions.

## Consistent units (pick ONE system; solvers are unit-free)

| System | Length | Force | Stress/E | Mass | Density (steel) | g |
|---|---|---|---|---|---|---|
| **SI (m)** | m | N | Pa | kg | 7850 kg/m³ | 9.81 m/s² |
| **mm-t-s (common CAE)** | mm | N | MPa | tonne | **7.85e-9 t/mm³** | **9810 mm/s²** |

**Density is the silent corruptor:** wrong-unit density passes statics but wrecks every dynamic/explicit/transient-thermal result. MAPDL `/UNITS` is metadata only. Verify with a 1g mass check or a hand-calc natural frequency.

## Element selection & mesh quality (depth: `references/meshing-convergence.md`)

- **Quadratic** (mid-side nodes) for stress/curved geometry, esp. tets — **avoid linear TET4 for stress** (overly stiff / shear-locks; acceptable only as filler well away from the QoI). Linear for explicit/large-deformation. Modern quadratic solids resolve *mild* bending with ~1 element through thickness as a starting point (curvature-driven — confirm by convergence); **linear** elements need several, and accuracy-critical bending wants ≥2 quadratic.
- **Shell** if thickness/length ≲ 1/10–1/20; solid for 3D stress/through-thickness; beam for slender. Account for shell/beam **offsets** (they induce real moments).
- **Locking/hourglass:** linear full-integration shear-locks (~+34% stiffer in the standard bending test — magnitude problem-dependent); linear reduced-integration hourglasses (over-soft, needs control); use quadratic / enhanced-strain / B-bar / mixed u–P (near-incompressible).
- **Quality gate (before solving) — thresholds depend on physics:** **structural FEA** prioritizes Jacobian (negative = fatal), skewness, and aspect ratio (high aspect is often fine for bending/shells); **CFD** is far stricter on orthogonal quality (>0.2, near-wall), skewness (reject >0.95), and growth ratio (≤1.2–1.5). Common starting guide: skewness ≤0.5 · orthogonal quality >0.2 · Jacobian 1–10 · aspect ratio <~20; **never place a transition in a high-gradient region** (per-physics depth: `references/meshing-convergence.md`).

## Mesh independence — GCI (ASME V&V 20 / Roache) — required for SIGNOFF

≥3 systematically refined meshes (ratio **r≥1.3**); track one QoI `f` (f₁ finest). `p = ln((f₃−f₂)/(f₂−f₁))/ln(r)`;
`f_exact ≈ f₁+(f₁−f₂)/(rᵖ−1)`; `GCI_fine = Fs·|ε|/(rᵖ−1)`, ε=(f₂−f₁)/f₁, **Fs=1.25** (≥3 grids)/3.0 (2). Asymptotic
check `GCI₂₃/(rᵖ·GCI₁₂)≈1`. Accept when QoI change <~1–2% and GCI_fine ≤~1–3%. **The closed form above assumes an _equal_ refinement ratio r; for unequal ratios solve the observed order p iteratively (Celik/Roache) — `scripts/gci.py` does this.** Runnable: `scripts/gci.py`. Same for time-step studies. (V&V/UQ depth: `references/vv-uq.md`.)

**Single-mesh alternatives & order-refinement:** recovery-based a-posteriori error estimation (**Zienkiewicz–Zhu / SPR**, effectivity index → 1) **estimates** error from ONE solve (asymptotically exact, *not* a guaranteed bound) and drives adaptivity; **p-/hp-refinement** raises element order (a fixed-mesh convergence study; **p-refinement is exponential for smooth fields**, and **properly graded hp** — fine low-order at the singularity, high order in the smooth region — recovers exponential rates for isolated singularities); goal-oriented (dual-weighted-residual) control targets the QoI directly. → `references/meshing-convergence.md`.

## Connections & thermal contact (depth: `references/mechanical-connections.md`, `references/thermal-contact-resistance.md`)

- **Bonded/glue** (small motion, linear) · **no-separation / frictionless / frictional** (nonlinear) · **RBE2** rigid (**adds stiffness — over-stiffens, common error**) vs **RBE3** distributed (no added stiffness — prefer for load spread).
- **Bolts:** preload `Fi≈0.7×proof`, `T=K·F·d` (K≈0.2); **VDI 2230**; preload scatter ±3% (ultrasonic) to ±35% (dry torque); **CTE mismatch changes preload** at cryo/thermal. **Welds:** spot/seam CWELD/CFAST; **hot-spot/structural stress for fatigue**, never raw peak toe stress.
- **Thermal contact:** `Q=h_c·A·ΔT`; **vacuum deletes the gas path, and h_c drops ~1 order as temperature falls (e.g. ~200 K → ~20 K)** and rises with contact pressure — never assume perfect contact in vacuum/cryo. MAPDL CONTA17x+`TCC`; Simcenter coupling; TD contactor.

## Solver, parallelism, convergence (depth: `references/solver-numerics.md`)

- **Cores = physical cores**; DMP > SMP for scaling (small models saturate ~4–8 cores; >4 needs HPC packs). **Direct sparse** for ill-conditioned/nonlinear/modal (keep in-core; out-of-core ~10× slower); **iterative PCG** for large well-conditioned 3D solids (don't loosen tolerance to force convergence — fix the model).
- **Nonlinear:** read the **residual history, never the exit code**; Newton-Raphson (+ line search); **arc-length/Riks** for snap-through; auto-time-step + bisection; converge force+displacement (energy). Decode pivots: negative/zero = singular (under-constraint/lost contact/bad props).
- **Time integration:** implicit Newmark/HHT-α (unconditional) for dynamics; explicit central-difference (**Δt≤L_min/c**, mass-scaling <~5%, hourglass energy <5–10%) for impact; backward-Euler for thermal.

## Structural integrity & failure (depth: dedicated references)

- **Fracture / damage tolerance:** LEFM (K, G=K²/E′) vs EPFM (J where K fails); interaction-integral K/T-stress, **J domain-integral with the contour path-independence gate**; XFEM vs VCCT vs CZM vs auto-remesh growth; **read J from the integral, not the singular tip stress**; crack growth Paris/Walker/NASGRO. → `references/fracture-mechanics.md`.
- **Fatigue / durability:** stress-life (mean-stress Goodman/Gerber/SWT) · strain-life (Coffin-Manson, Neuber/Glinka notch) · rainflow + Miner · multiaxial critical-plane · **vibration/spectral fatigue (Dirlik) from a random-vibration PSD** · TMF · FKM. Never fatigue a singular peak. → `references/fatigue-durability.md`.
- **Composites:** first-ply vs progressive-damage (CDM) vs last-ply; **characteristic-length fracture-energy regularization for mesh objectivity**; delamination (CZM/VCCT, B-K); sandwich (face wrinkling); draping → as-built angles/CTE; hot-wet/cold-dry knockdowns. → `references/composites-analysis.md`.
- **Plasticity & inelastic assessment:** shakedown vs ratcheting (Bree); limit-load; ASME elastic-plastic route; **stress linearization & categorization (P_m/P_L/P_b/Q/F → S_m code limits)**; forming/springback/FLD. → `references/plasticity-inelastic-assessment.md`.
- **Buckling / stability:** LBA (upper bound) → GNIA/GMNIA with **imperfection seeding + knockdown factors** (NASA SP-8007); snap-through via arc-length; local/global/crippling interaction; **a single symmetry model misses antisymmetric/complementary buckling modes — model the full structure or cover the symmetric + antisymmetric sets**. → `references/buckling-stability.md`.
- **Explicit dynamics / crash / impact / drop:** contact for explicit (single-surface / segment SOFT=2 / eroding), erosion + energy bookkeeping, hourglass-control type, mass-scaling strategy, **Lagrangian/SPH/ALE/CEL** choice, blast/drop/penetration; **energy-balance + added-mass gates** = the explicit analog of GCI. → `references/explicit-dynamics-impact.md`.

## Dynamics, NVH & acoustics (depth: `references/dynamics-nvh-acoustics.md`, `references/acoustics-fem.md`)

- **Modal:** extract to **≥80–90% cumulative effective mass** per direction + range ~1.5–2× f_excite; free-free → the dimensionality-correct rigid-body-mode count ≈0 (6 for a 3D solid; fewer in 2D/axisymmetric/shell models); **residual vectors ON** for force/stress recovery; prestressed modal carries static stress (tension raises freq).
- **Random (PSD):** Q=1/(2ζ); Miles `GRMS≈√(π/2·f_n·Q·ASD)`; **design to 3σ**. **Shock:** SRS (Q=10). Base excitation: large-mass (~10⁶×) or enforced motion.
- **Acoustics/vibro-acoustic:** interior FEM cavity vs exterior BEM radiation; **≥6 elements per wavelength** at f_max (a *minimum* floor, not a guarantee — pollution/dispersion error grows with frequency and domain size; confirm by convergence); coupled wet modes; duct/muffler TMM, absorption/impedance, infinite-elements vs PML → `references/acoustics-fem.md`. **Rotordynamics:** Campbell + gyroscopic, unbalance/ISO balance grades, bearing oil-whirl/whip, log-dec/API stability, torsional (critical speeds ≠ zero-speed modal).

## Thermal & coupling (depth: `references/thermal-and-coupling.md`)

- Steady vs transient (Biot `Bi=hL/k`<0.1 → lumped). Transient Δt has **accuracy, solver-formulation, and mesh-coupled** limits: an `Fo=αΔt/L²` accuracy bound **and** a non-obvious lower limit — too-small Δt on a coarse mesh oscillates with Crank–Nicolson/θ-schemes → **refine the mesh, don't shrink Δt** (the formulation nuance, incl. MAPDL, is in `references/thermal-and-coupling.md`). Backward-Euler default.
- **Radiation** T⁴-nonlinear: absolute T (`TOFFST`/`TABS`), solar α ≠ IR ε, enclosure row-sum→1, radiosity over-relaxation. **Steep cp(T)/phase change:** enthalpy + **Full** (not "Quasi") nonlinear formulation. **Energy balance closes <1%.**
- **Spacecraft/vacuum:** MLI effective emittance ε\*~0.01–0.05 (dominant uncertainty); ±10–20 K margin; **TVAC correlation**. **Coupling:** `.rth`→`LDREAD,TEMP` (needs TREF+CTE); meshes interpolate; the **transient gradient** drives distortion — validate per-sensor, not region-mean.

## CFD (depth: `references/cfd.md`)

- **Turbulence:** RANS k-ω **SST** (general default), k-ε (free shear), transition γ-Reθ; LES/DES/DDES/SBES when RANS is inadequate (cost ↑↑). **Near-wall y+:** wall functions y+≈30–300 **or** wall-resolved y+<1 — never the buffer layer; ≥10–15 inflation layers; estimate first-cell height up front.
- **Mesh:** poly/hex/prism; check skewness & orthogonal quality; **mesh independence via GCI**. **Discretization:** 2nd-order upwind + bounded schemes; transient **Courant/CFL** target. **Convergence:** scaled residuals ~1e-3…1e-6 **but monitor integrated quantities** (drag/lift/ṁ/ΔP) and **imbalances <~1%** — residuals alone lie.
- **Headless:** Fluent `fluent 3ddp -g -t N -i jou`; OpenFOAM text dicts + `Allrun` (`simpleFoam`/`pimpleFoam`); CFX `cfx5solve -batch`; STAR-CCM+ `starccm+ -batch macro.java`; SU2 `SU2_CFD`. **Coupling:** CHT, FSI one-way vs two-way (watch added-mass instability), mapping via preCICE/system coupling.

## Electromagnetics (depth: `references/electromagnetics.md`)

- **Pick the formulation by frequency:** electro-/magnetostatics; **low-frequency eddy-current/transient** (skin depth δ=√(2/ωμσ) — **mesh ≥2 elements into the skin depth**; A-V / T-Ω); **high-frequency full-wave** (**Nédélec edge elements** — nodal elements give spurious modes; wave/lumped ports & S-parameters; radiation via ABC/PML/FE-BI). Method: FEM (closed/inhomogeneous) vs MoM/BEM (open radiation/antennas) vs FDTD (broadband).
- **Applications:** electric machines (torque via Maxwell-stress/co-energy, cogging, Bertotti core loss, sliding mesh), power electronics, antennas/RF, EMI/EMC. **Coupling:** EM→thermal (Joule/induction/dielectric/microwave heating), EM→structural (Lorentz/Maxwell-stress, magnetostriction, motor NVH), piezo/MEMS. Headless: **PyAEDT**, COMSOL batch, getDP/Elmer/openEMS.

## Multiphysics, substructuring, optimization (depth: `references/advanced-methods.md`, `references/optimization-calibration.md`, `references/ml-surrogates-and-rom.md`)

- **Substructuring/CMS** (Craig-Bampton fixed-interface, free-interface) + **ROM** (Guyan, modal truncation, Krylov, state-space) for large/repeated assemblies, dynamic reduction, multibody flex bodies, digital twins.
- **Multibody:** rigid + flexible (modal/CMS), joints, **FMI/FMU co-sim**, loads recovery (modal stress recovery / quasi-static superposition).
- **Coupled process simulation:** battery electrochem+thermal+**runaway**, fuel cells, additive manufacturing (Goldak / inherent-strain), welding (thermal→metallurgical→mechanical), composite curing, injection molding, casting; sequential vs staggered vs monolithic coupling + field mapping. → `references/coupled-process-simulation.md`.
- **Optimization:** topology (SIMP p=3, density/sensitivity **filter = min member size**, manufacturing/AM constraints; **a topology result is a concept — interpret then re-solve the verified geometry** → `references/topology-optimization.md`), shape, sizing; DOE → surrogate → optimize → **re-solve the optimum on full FE**. **Calibration / inverse ID** incl. transient T(t): native in optiSLang & TMG Correlation, else wrap the solver in an optimizer with a time-series residual. Enforce the **calibration-objective gate** in `references/optimization-calibration.md` (fit the QoI not an aggregate; reject edge-pinned knobs).
- **ML surrogates & data-driven ROM** (Kriging/GP, PCE, POD/PODI, DMD, neural operators/PINNs, hyper-reduction DEIM/ECSW, certified reduced-basis) for DOE/optimization/digital-twins — but **a surrogate predicts only inside its training envelope: "solve vs predict" — re-solve the optimum/critical case on the full FE model before any ENGINEERING/SIGNOFF claim.** → `references/ml-surrogates-and-rom.md`.

## V&V, UQ & governance (depth: `references/vv-uq.md`)

Verification (solving equations right: MMS order test, NAFEMS LE/T benchmarks, GCI) **precedes** validation (right physics vs experiment: ASME V&V 20 `u_val²=u_num²+u_input²+u_D²`, `|E|≤u_val` — a *resolution floor* for detecting model error, **not** a binary pass/fail). **Calibration ≠ validation** (validate on held-out data). **UQ:** aleatory vs epistemic; Morris→Sobol sensitivity; MC/PCE propagation; Bayesian calibration/identifiability; **scale rigor to consequence** (V&V 40). **Model credibility — score it factor-by-factor:** NASA-STD-7009 CAS (8-factor, min-rollup → **weakest factor governs**) / Sandia PCMM (6-element; reports min/avg/max — does **not** force a single governing score); lifecycle governance via SPDM + NAFEMS QSS/ESQMS; domain margins per the governing standard (e.g. ECSS FoS + model-uncertainty-factor). Report provenance (NAFEMS R0033). → `references/vv-uq.md`.

## V&V — sanity gates to run automatically

| Gate | Criterion |
|---|---|
| **Equilibrium** | Σreactions = Σapplied per axis, < ~0.1–1% (`FSUM`/`PRRSOL`; SPCFORCES) |
| **Unit-gravity / mass** | 1g reaction = Σ(ρ·V)·g within ~1% (catches unit/density errors) |
| **Free-free modal** | dimensionality-correct rigid-body-mode count near 0 (< ~1e-4 Hz): 6 for an unconstrained 3D solid, fewer for 2D/axisymmetric/shell models |
| **3-2-1 + uniform ΔT** | single-material → thermal stress ≈ 0 (over-constraint detector) |
| **Thermal/flow connectivity** | all QoI bodies in one conducting component reaching the BC; symptom of failure = bodies stuck at **initial T**. → `references/ansys-thermal-contact-pitfalls.md` |
| **Convergence** | residuals down ≥3–4 orders; nonlinear force tol met; CFD imbalances <1% |
| **Mesh independence** | GCI gate above |
| **Singularity detector** | peak QoI rising monotonically with refinement → artifact; read 1–2 elements away / linearize (ASME) |
| **Benchmark / hand-calc** | within a few % of Roark / Timoshenko / NAFEMS |
| **Visual plausibility** | render the field (contour / deformed / streamlines): smooth where expected, jumps only at real interfaces, no checkerboard pressure or constraint hot-spots; write a `field.png` artifact |
| **Margin & allowables** | turn the QoI into a **margin of safety vs a NAMED criterion / design code** (yield/UTS, ASME / Eurocode / AISC, FKM, buckling KDF, fatigue allowable) — a stress number without an allowable is not a result |

**BC discipline:** under-constraint → singular; over-constraint → spurious reactions/stiffness. For modal/buckling a single symmetry model misses complementary (antisymmetric) modes — model the full structure, or combine the symmetric **and** antisymmetric (and cyclic-harmonic) solutions. Place BCs ≥1 characteristic dimension from regions of interest.

## Software landscape & cross-solver (depth: `references/software-landscape.md`)

Tool-by-tool use/license/**headless capability**/formats for the popular CAE stack — Ansys, Abaqus, LS-DYNA, MSC/Simcenter Nastran, OptiStruct, COMSOL, Fluent/CFX/STAR-CCM+/OpenFOAM/SU2, Adams/Motion, HFSS/Maxwell, and open-source (CalculiX, Code_Aster, FEniCSx, Elmer, Kratos, Gmsh, ParaView, preCICE) — plus a "which tool for which job" guide and interoperability (STEP, `.bdf`/`.dat`, `.inp`, `.cdb`/`.rst`/`.rth`, CGNS, VTK, MED, UNV).

## Output contract

Solver logs/results are large — **never dump them into context.** Parse with targeted extraction; return only QoI, convergence verdict, GCI/equilibrium, and a small table. Write artifacts per mode (template `scripts/run_manifest_template.json`): `run_manifest.json` (traceability spine — NAFEMS R0033), `qoi.csv`, `checks.md`, `assumptions.md`, `failure_triage.md` (on failure). **Provenance discipline:** every solve writes a manifest **and** appends to a `runs_index.csv`; never leave two "final" results without a `superseded_by` pointer.

## Failure triage (symptom → cause → decisive test → fix)

| Symptom | Likely cause | Decisive test | Fix |
|---|---|---|---|
| Transient thermal bodies stay **exactly** at initial T | isolated body / contact has no TEMP DOF | single-anchor transient; check pair `KEYOPT(1)` | author thermal contacts fresh / `KEYOPT(1)=2`; LINK33 network on defeatured import |
| Steady thermal **singular**, no `.rth` | isolated body / no BC reaches a component | `CNCHECK,DETAIL` + union-find on deck parse | connect the component / re-anchor at measured T |
| Changed contacts but result unchanged | mesh not rebuilt (contact elems **are** mesh) | elem count before/after | `ClearGeneratedData()` then `GenerateMesh()` |
| Peak stress **rises** with refinement | singularity | refine ×2–3 → plateau? | read ~1 char-dim away / fillet / sub-model / linearize |
| CFD "converged" but wrong | residuals low, integrals drifting | monitor drag/ṁ/imbalance | run to integral plateau + imbalance <1% |
| Reaction/heat/mass balance fails | under/over-constraint, lost contact, wrong load | `FSUM` vs applied | fix BC/contact |
| PyDPF empty result from valid `.rst` | `ansys-dpf-core` ↔ server mismatch | mesh non-empty? | match versions; `/FCOMP,RST,0` |
| Negative/zero pivot (nonlinear/static) | rigid-body mode / lost contact / over-soft material | `CNCHECK`; check constraints & contact status | constrain the DOF; stabilize/seat contact; fix props |
| Contact status flips every iteration (chatter) | penalty too stiff / no damping / marginal gap | watch contact-status history | lower `FKN`, add contact stabilization damping, refine pinball |
| Negative-volume / error termination (explicit) | element over-distorted at high strain | inspect deformation at the failure step | add erosion criterion, refine, reduce mass-scaling, hourglass control |
| Modes missing / extra near-zero (modal) | mechanism / unconnected part / repeated roots | free-free RBM count; connectivity | connect parts; expand the mode count past the cluster |
| GCI not asymptotic (p far from formal order) | grids not in asymptotic regime / noisy QoI | add a finer grid; check p≈ theoretical | refine systematically (r≥1.3); pick a smoother QoI |
| Radiation/enclosure won't converge | view-factor row-sum ≠ 1 / radiosity step too large | check enclosure closure & emissivities | close the enclosure; over-relax; smaller load step |

Ansys headless thermal-contact traps (CONTA174 KEYOPT(1)=0 thermally inert; `-dis` stragglers; batch non-convergence silently skips) → `references/ansys-thermal-contact-pitfalls.md`. Headless PyMechanical/Workbench gotchas → `references/pymechanical-headless.md`. Per-platform commands → `references/platform-commands.md`.

## Common mistakes

| Mistake | Fix |
|---|---|
| Single-mesh result | Mesh-independence + GCI first; state the verdict. |
| Trusting a singular peak | Converge QoI, read away, or linearize. |
| `-np` = logical cores | Use physical cores; HPC packs for DMP >4. |
| "Converged" by exit code / CFD residuals only | Read residual history; monitor integrated quantities + imbalance. |
| Perfect/bonded thermal contact in vacuum/cryo | Use finite h_c. |
| Reusing structural contacts in a thermal solve | `CONTA174 KEYOPT(1)=0` → zero conduction; author fresh. |
| RBE2 everywhere | Over-stiffens — RBE3 to spread load without stiffness. |
| Forgetting CTE in thermal stress | Define `ALPX`/`A`+`TREF` or thermal stress is silently zero. |
| Engineering (not true) stress–strain in plasticity | Convert; extend past UTS via a hardening law, not raw data. |
| Single-mode hyperelastic fit / flat cryo extrapolation | Multi-mode test data; T-dependent tables over the full range. |
| Calibrate then claim validation | Validate on held-out data; reject edge-pinned knobs. |
| Reporting a stress with no allowable | State a margin of safety vs a NAMED criterion / design code. |
| Trusting an ML surrogate outside its training envelope | Re-solve the optimum / critical case on the full FE model. |
| Linear buckling load taken as the real capacity | Apply a knockdown factor / run GNIA with seeded imperfections. |
| Fatiguing the singular peak stress | Use a fixed extraction (hot-spot) or notch correction — never the raw peak. |
| Pasting `.out`/`.f06` into chat | Parse with targeted extraction; return QoI only. |

## References

- `references/claim-templates.md` — per-mode (SMOKE/DEBUG/ENGINEERING/SIGNOFF) result-phrasing templates + reusable contract phrases (no-autonomous-sign-off, solve-vs-predict, calibration≠validation, singular-peak, solver-flag-certainty).
- `references/escalation-examples.md` — worked refuse/escalate cases (contact type, single-mesh peak, calibration boundary, surrogate optimum, load basis, sign-off, singularity, solver flags, equilibrium, defeature, non-convergence).
- `references/claims-validation.md` — external-source validation of the router's load-bearing claims (claim → authoritative standard/textbook/paper → verdict; 53 claims, deep-research traceability appendix).
- `references/meshing-convergence.md` — element tech, quality metrics, GCI, singularities, stress linearization.
- `references/material-modeling.md` — constitutive models (elastic/plastic/hyperelastic/visco/creep/damage/composite), data sources, calibration.
- `references/solver-numerics.md` — equation/eigen solvers, nonlinear, time integration, parallelism, diagnostics.
- `references/mechanical-connections.md` — contact types/formulations & tuning, RBE2 vs RBE3, bolts (VDI 2230)/welds (hot-spot fatigue)/bushings/joints, with cited numbers.
- `references/driving-live-sessions.md` — driving live solver sessions: inspect→step→re-inspect, debug-on-failure, getting data out of API sessions.
- `references/comsol.md` — COMSOL automation: JPype/Java API (tags-first), `.mph` offline introspection, batch, numeric results.
- `references/thermal-contact-resistance.md` — TCR/TCC physics, value tables, cryo, correlations.
- `references/thermal-and-coupling.md` — transient thermal, radiation, phase change, spacecraft/vacuum, thermo-mechanical coupling.
- `references/dynamics-nvh-acoustics.md` — modal/harmonic/random/shock, NVH, vibro-acoustics, rotordynamics (unbalance/bearings/stability/torsional), flutter.
- `references/acoustics-fem.md` — duct/muffler transfer-matrix, cut-on, absorption/impedance, infinite-elements vs PML, aeroacoustics basics, acoustics-FEM mistakes.
- `references/cfd.md` — turbulence, y+/near-wall, CFD meshing, discretization, convergence, multiphase, compressible, combustion, rotating mesh, adjoint, turbulence-UQ, CHT/FSI, headless run.
- `references/electromagnetics.md` — formulation-by-frequency (electro/magnetostatics, eddy-current, full-wave/edge-elements/S-params), machines/RF/EMI, EM-thermal & EM-structural coupling, PyAEDT headless.
- `references/specialized-analyses.md` — overview / quick-pointers (submodeling, hyperelastic, cyclic, creep); the deep failure disciplines have their own dedicated files (next).
- `references/fracture-mechanics.md` — LEFM/EPFM, K/G/J, interaction-integral & T-stress, J path-independence gate, XFEM/VCCT/CZM, crack growth (Paris/NASGRO), mixed-mode.
- `references/fatigue-durability.md` — stress-life/strain-life, mean-stress, Neuber/Glinka, rainflow+Miner, multiaxial critical-plane, spectral (Dirlik) vibration fatigue, TMF, FKM.
- `references/composites-analysis.md` — FPF/progressive-damage(CDM)/LPF, fracture-energy regularization, delamination CZM/VCCT, sandwich, draping/as-built, hot-wet/cold-dry.
- `references/plasticity-inelastic-assessment.md` — shakedown/ratcheting (Bree), limit-load, ASME elastic-plastic route, stress linearization & categorization, forming/FLD, creep-plasticity.
- `references/buckling-stability.md` — LBA/GNIA/GMNIA, knockdown factors (NASA SP-8007), imperfection seeding, snap-through (arc-length), local/global/crippling interaction.
- `references/explicit-dynamics-impact.md` — explicit contact, erosion, hourglass control, mass-scaling, Lagrangian/SPH/ALE/CEL, blast/drop/penetration, energy gates.
- `references/advanced-methods.md` — substructuring/CMS/ROM, multibody, optimization/topology, submodeling, loads & BC catalog (incl. inertia relief).
- `references/optimization-calibration.md` — optimizer/calibration tool map, transient-T(t) calibration, the calibration-objective gate.
- `references/topology-optimization.md` — SIMP/RAMP density methods, filtering & min-length-scale, manufacturing/AM constraints, stress/buckling-constrained, level-set/lattice; the interpret-then-re-solve discipline.
- `references/ml-surrogates-and-rom.md` — projection & data-driven ROM, hyper-reduction, certified reduced-basis, ML surrogates (GP/PCE/neural-operators/PINNs), digital twins; the solve-vs-predict rule.
- `references/coupled-process-simulation.md` — process-coupled physics: battery/runaway, fuel cells, additive manufacturing, welding, composite curing, injection molding, casting; coupling strategies & field mapping.
- `references/vv-uq.md` — verification/validation/UQ, ASME V&V 10/20/40, NAFEMS, benchmarks, governance.
- `references/software-landscape.md` — popular CAE tools: use/license/headless/formats + which-tool-for-which-job + interoperability.
- `references/agent-automation-boundary.md` — per-operation agent-headless vs human-GUI contract across every platform.
- `references/platform-commands.md` — MAPDL/Mechanical/Nastran/NX-Open/OpenTD command cheat-sheet.
- `references/pymechanical-headless.md` — PyMechanical/Workbench headless gotchas.
- `references/ansys-thermal-contact-pitfalls.md` — Ansys headless thermal-contact traps (CONTA17x KEYOPT(1) inert, `-dis` stragglers, silently-skipped non-convergence) [VERIFIED].
- `scripts/gci.py` — Grid Convergence Index. `scripts/yplus.py` — y+ first-cell height. `scripts/units_check.py` — consistent-units + 1g mass check. `scripts/rainflow.py` — ASTM E1049 rainflow + Miner damage. `scripts/mac.py` — Modal Assurance Criterion + COMAC. `scripts/hourglass_check.py` — explicit-dynamics energy-quality gate. `scripts/run_skill_evals.py` — validate the activation/behavior eval set (`evals/prompts.json`) + score live agent responses. `scripts/run_manifest_template.json` — manifest template.
