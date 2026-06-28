# Explicit dynamics, crash & impact — practitioner-grade best-practices brief

Scope: the **application discipline** of explicit transient dynamics — *when* to reach for an explicit solver, **contact for explicit**, **element erosion/deletion**, **hourglass-control selection**, **mass-scaling strategy**, the **Lagrangian / SPH / ALE / CEL** method choice, and the analysis recipes for **blast, drop test, and penetration/ballistic/bird-strike**, ending in the **acceptance gates** that decide whether a crash run is trustworthy. Cross-verified against the LS-DYNA theory/user guides, the Abaqus/Explicit Analysis User's Manual, Altair Radioss and ESI PAM-CRASH documentation, NASA impact-dynamics reports, and NAFEMS. Vendor-neutral throughout (LS-DYNA / Abaqus-Explicit / Radioss / PAM-CRASH); the named cards (`*CONTACT_AUTOMATIC_SINGLE_SURFACE`, `SOFT=2`, `*MAT_ADD_EROSION`, `DT2MS`, `*LOAD_BLAST_ENHANCED`) are LS-DYNA examples — every solver has an equivalent. Citations are bracketed `[n]` → SOURCES at end.

> **This file is the application layer; the numerics live next door.** The conditional-stability time step (CFL `Δt = L_min/c`), the mass-scaling **%-added-mass budget**, the **hourglass-energy <5–10 %** gate, and the **total-energy-balance** check are all developed in **solver-numerics.md §4** ("Time integration → Explicit"). This brief assumes those numbers and tells you how to *set up the physics* that they police. Where a number is purely numerical it is **cross-referenced, not repeated**. Material laws for high-rate metals and damage (Johnson-Cook flow + damage, Cowper-Symonds rate scaling, GISSMO) live in **material-modeling.md §2/§5** — also cross-referenced, not repeated.

The governing rule for the whole topic: **an explicit crash result is only as good as its contact, its hourglass control, and its energy balance — in that order.** A converged-looking d3plot with 15 % hourglass energy, leaking contact, or 30 % added mass is a wrong answer that animates beautifully. Read the global energy report (`glstat`/`matsum`, Abaqus `*OUTPUT, HISTORY` ALLIE/ALLKE/ALLAE) before you read a single stress.

---

## 1. When explicit (and when not)

Explicit central-difference integration (solver-numerics.md §4) does **no equilibrium iteration and no matrix factorization** — each step is a cheap, fully-vectorized force recovery and a lumped-mass `a = M⁻¹·(F_ext − F_int)`. That makes it ideal exactly where implicit Newton struggles: events that are **short, fast, and savagely nonlinear with constantly-changing status.**

Reach for explicit when **two or more** of these hold:

- **Short duration** — the event is over in roughly **µs to ~0.1–1 s** (crash pulse ~80–150 ms, drop impact ~1–10 ms, ballistic ~tens of µs). Cost scales as `#elements × #steps`, and `#steps = T_event / Δt_crit`; long events make the step count explode (use implicit, or implicit→explicit handoff).
- **High strain rate** — wave-propagation / inertia-dominated response where rate-dependent material (Johnson-Cook, Cowper-Symonds; material-modeling.md §2) actually matters.
- **Severe, simultaneous nonlinearity** — large deformation, buckling/folding, fracture, **and** thousands of contact status changes per step (self-contact during crush). Implicit tangent stiffness becomes indefinite and Newton diverges; explicit just marches.
- **Fragmentation / material separation** — tearing, spall, penetration, where elements fail and the topology changes.

| Event class | Typical duration | Why explicit | Implicit alternative? |
|---|---|---|---|
| Automotive/aero crash, crush, folding | 50–200 ms | self-contact, buckling, plasticity, airbags | no (status changes kill Newton) |
| Drop / shock (electronics, packaging) | 0.5–10 ms | wave propagation, contact, foam crush | rarely |
| Ballistic / penetration / blast | µs–ms | erosion, very high rate, fragmentation | no |
| Metal forming (stamping) | quasi-static | severe contact + large strain | implicit also common; explicit avoids contact convergence |
| Sheet springback, slow assembly preload | seconds+ | — | **use implicit** (explicit needs millions of steps) |
| Long structural transient / seismic | seconds | — | **use implicit** Newmark/HHT (solver-numerics.md §4) |

**Quasi-static-via-explicit** is a legitimate fourth use (forming, slow crush, snap-through that defeats arc-length): apply the load slowly via a smooth velocity/displacement ramp and **prove kinetic energy ≪ internal energy (KE/IE < ~5–10 %)** throughout (solver-numerics.md §4). If KE is not small, you ran a dynamic event and called it static.

**The single-element tax.** The whole model marches at the **smallest element's** `Δt_crit` (solver-numerics.md §4). One sliver from a defeaturing miss, a bad boolean, or an over-refined fillet throttles the entire solve. In explicit, **mesh quality at small features is a runtime lever, not just an accuracy one** — find and fix (or mass-scale) the controlling elements before blaming the solver.

**Top mistakes:** using explicit for a multi-second quasi-static problem with no mass scaling (millions of steps); using implicit for a high-rate fragmenting impact (won't converge); forgetting that a single tiny element sets Δt for the whole model.

---

## 2. Contact for explicit — the make-or-break

Contact is where most explicit models are won or lost. Unlike an implicit contact solve (constraint enforcement inside Newton), explicit contact is almost always **penalty-based**: when a slave node penetrates a master segment, a spring pushes it back, `F = k·penetration`. The penalty stiffness `k` is auto-scaled from the segment stiffness, mass, and the time step so it does not itself shrink `Δt`. Get the contact **type, scope, and stiffness** right and the rest of the model usually behaves.

### 2.1 Penalty vs kinematic, and the contact-stiffness knob

- **Penalty** (default, robust, energy-trackable) — soft constraint; allows a small physical penetration; conserves momentum; works with self-contact and erosion. The **contact stiffness scale factor** (LS-DYNA `SLSFAC`/`SFS`/`SFM`; Abaqus penalty stiffness) trades penetration depth against the risk of high-frequency contact noise and step reduction. Raise it only if penetration is visibly too deep; cranking it causes hourglassing-like contact chatter.
- **Kinematic** (Abaqus default for some pairs) — enforces no-penetration exactly on the slave; can be stiffer/less forgiving with rough meshes. Penalty is the general explicit default.
- **Contact thickness / offset** — shells contact at their **mid-surface ± half-thickness**; set the contact thickness explicitly when the auto value is wrong (thin shells, offset shells) or parts will visibly overlap or float apart. This is the #1 cause of "the parts pass through each other."

### 2.2 Choose the contact *type* by the phenomenon

| Situation | Contact type | Why |
|---|---|---|
| A part folds/crushes onto **itself** (rails, crush cans, B-pillars) | **Single-surface / automatic-general** (`*CONTACT_AUTOMATIC_SINGLE_SURFACE`) | one surface checks every facet against every other — catches self-contact without you predicting where folds touch |
| Whole-model "everything can hit everything" (full vehicle, cluttered assembly) | **Automatic single-surface over all parts** | one robust card; expensive but bullet-proof for unknown contact |
| Two known distinct bodies (impactor ↔ target, two clean parts) | **Automatic surface-to-surface** | cheaper, directional, fine when you know who hits whom |
| **Soft-vs-stiff**, foam-vs-metal, sharp angles, **dissimilar / non-matching mesh** | **Segment-based, `SOFT=2`** | segment-to-segment (not node-to-segment); far more robust for stiffness mismatch and poorly-matched meshes than `SOFT=0/1` |
| Surface elements **delete** during the run (tearing, penetration) | **Eroding contact** (`*CONTACT_ERODING_*`) | when a skin element erodes, the newly-exposed interior is added to the contact surface so contact survives material loss |
| Bonded/tied that may fail | **Tied with failure / cohesive contact** | spot-welds, adhesives (cross-ref mechanical-connections) |

`SOFT=0/1` use node-to-segment penalty scaled from material stiffness (`SOFT=0`) or from nodal mass and the step (`SOFT=1`, better for big stiffness contrasts). **`SOFT=2` (segment-based)** is the modern default for crash because it handles soft-on-stiff, edge-to-edge, and dissimilar meshes that node-to-segment misses or leaks through. When a model "explodes" or shows interpenetration at a foam-metal or fine-coarse interface, switch the offending interface to `SOFT=2` before anything else.

### 2.3 Self-contact, edge-to-edge, and rigid-body mesh density

- **Self-contact** during buckling/folding is the whole reason crash needs single-surface/automatic-general contact — a node-to-segment pair defined "part A on part B" will not catch part A touching part A. Use single-surface for any part that crushes.
- **Edge-to-edge** contact (shell edges, sharp corners) is missed by surface-only penalty; automatic-general / `SOFT=2` adds edge treatment — needed for thin shells that fold sharply.
- **Mesh a rigid body at least as fine as the deformable part it strikes.** Penalty contact distributes force through master *segments*; a coarse rigid wall against a fine deformable part lets fine nodes slip between coarse segments (leakage) and spikes contact force on the few nodes that do engage. Rigid impactors and barriers are cheap (no internal energy) — mesh them finely.

### 2.4 Monitor sliding-interface energy — the contact integrity gate

Penalty contact does work; that work is tracked as **sliding-interface / contact energy** (LS-DYNA `sleout`, the `glstat` slide energy; Abaqus ALLCD/contact dissipation).

> **Sliding-interface energy should be small and (for friction) non-negative. Large *negative* contact energy = initial penetration or leakage — fix the model, do not damp it.** Negative slide energy means the penalty springs are *releasing* stored energy from pre-existing penetrations at t=0 (parts modeled overlapping) or nodes that tunneled through. The cure is geometry (remove initial overlap, set correct contact thickness, refine the master, switch to `SOFT=2`), never adding contact damping to hide it. Contact **damping** is for legitimate high-frequency contact ringing, not for masking penetration.

A healthy contact has slide energy that is a small fraction of internal energy and trends consistently with friction work. Spiking, oscillating, or strongly-negative slide energy is a red flag even if the run "completes."

**Top mistakes:** node-to-segment contact on a self-folding part (misses self-contact → interpenetration); coarse rigid wall vs fine target (leakage + force spikes); ignoring negative slide energy; cranking penalty stiffness to fix penetration (causes chatter/step reduction) instead of fixing contact thickness or switching to `SOFT=2`; forgetting eroding contact so a penetrating projectile stops contacting once skin elements delete.

---

## 3. Element erosion / deletion

Tearing, perforation, fragmentation, and cutting are modeled by **deleting** elements that meet a failure criterion ("erosion"). Done right it is the only way to get penetration and fragmentation; done lazily it is the easiest way to fake a result.

### 3.1 What drives deletion

A failure/erosion criterion removes an element when a state variable crosses a limit. Common drivers (LS-DYNA `*MAT_ADD_EROSION` collects many; Abaqus uses element-deletion in the damage law):

- **Effective plastic strain** at failure — simplest; mesh-size-dependent (calibrate the failure strain to the element size or regularize, material-modeling.md §5).
- **Stress-triaxiality-dependent failure** — Johnson-Cook damage, **GISSMO** (instability + damage accumulation with mesh regularization `LCREGD`), or a fracture-locus (material-modeling.md §5). This is the physically-defensible route: failure strain varies with triaxiality and Lode angle, not a single number.
- **Minimum time step** — delete an element whose `Δt` collapses (about to invert). A runtime safety valve, **not** a physics criterion.
- **Pressure / volumetric strain / principal stress / min element dimension** — spall, tensile cutoff, geometric collapse.

### 3.2 Mass and energy bookkeeping — erosion is not free

> **Deleting an element removes its mass and its internal (and kinetic) energy from the model.** Both must be tracked and stay small relative to the total. A run that erodes 8 % of its mass has thrown away 8 % of its momentum and is no longer the structure you meshed.

- Watch **eroded mass** and **eroded internal energy** in the global report; they should be a small, physically-justified fraction (the material that actually fragmented), not a large bleed.
- **Energy balance must still close** including the erosion/sliding terms (solver-numerics.md §4): `total ≈ constant`. A sudden energy drop at erosion onset that does not match expected fracture energy means the criterion is firing too early/cheaply.

### 3.3 The cardinal sin and the debris fix

> **Never erode elements just to keep the time step up.** Using a `Δt`/min-element criterion as your *primary* failure model deletes load-bearing material that has not actually failed — it removes the throttling sliver and silently softens the structure. Mass-scale the controlling element instead (§5), or refine/repair the mesh. Erosion is a *physics* model; `Δt`-erosion is an emergency brake.

When erosion is physically correct but the deleted material still carries load (a plug, a spall fragment, residual debris that re-impacts), retain it:

- **Debris → SPH / free nodes** — convert eroded solid elements to **SPH particles** (or mesh-free node masses) so their mass, momentum, and subsequent impacts survive deletion (LS-DYNA node-to-SPH conversion; §4). Essential for ballistic plugging, fragment fields, and bird/soft-body splash that must keep pushing after the Lagrangian mesh fails.

**Top mistakes:** single failure-strain criterion not regularized for mesh size (mesh-dependent perforation); using min-`Δt` erosion as the failure model; not tracking eroded mass/energy; losing the load path because debris was deleted instead of converted to SPH; failure strain calibrated at one element size then run at another.

---

## 4. Hourglass control — *which* type, not just *how much*

Reduced-integration solids (1 point) and shells develop **zero-energy hourglass modes** — deformation patterns that produce no strain at the single integration point, so they are unresisted and grow unphysically (the "keystone"/hourglass shape). The **energy gate** (hourglass energy **< 5 % preferred, ≤ 10 % limit** of internal energy) lives in solver-numerics.md §4. This section is about **choosing the control mechanism and the element formulation** so you do not have to fight that gate.

### 4.1 The two families and when each fits

| Control | LS-DYNA type | Mechanism | Best for |
|---|---|---|---|
| **Viscous** | type 1 (std), 2, 3 | resists the *rate* of the hourglass mode (damping force ∝ hourglass velocity) | **high velocity / high strain rate** (ballistic, blast, very fast impact) — damps fast modes without over-stiffening |
| **Stiffness (Flanagan–Belytschko)** | type 4, 5 | resists the *displacement* of the hourglass mode (elastic restoring force) | **lower-rate, larger-deformation, coarse mesh** (crash crush, forming) — keeps shape under sustained deformation; type 5 is the FB stiffness form with exact volume |
| **Type 6 (assumed-strain / FB with exact integration)** | type 6 | physically-based, exact for elastic & constant-stress | **accuracy-critical** solids, stiff elastic response; the default recommendation for solids where accuracy matters |

Rule of thumb: **viscous for high-rate, stiffness for low-rate/large-deformation, type 6 when accuracy dominates.** Match the *coefficient* too (the hourglass coefficient, default ~0.1) — too high over-stiffens (locks, raises hourglass energy paradoxically by adding artificial work), too low lets modes grow.

### 4.2 Prefer real integration over cranking hourglass control

> **If hourglass energy is high, the first move is full (or selective-reduced) integration, not more hourglass stiffness.** Fully-integrated solids/shells (LS-DYNA solid `ELFORM=2`, shell `ELFORM=16`) have **no hourglass modes** — no control needed — at the cost of higher per-element work and a risk of shear/volumetric **locking**. Cranking hourglass stiffness on a reduced-integration element to suppress visible hourglassing adds artificial stiffness that **stiffens the global response** and corrupts energy and peak forces.

Practical ladder when hourglass energy exceeds the gate:
1. **Refine the mesh** locally (hourglass modes shrink with element size; usually the real fix).
2. **Switch the offending parts to fully-integrated** elements (ELFORM 2/16), watching for locking in bending/near-incompressible regions.
3. Only then **tune the hourglass type/coefficient** to match the rate.

Reduced integration + good hourglass control is still the crash workhorse (cheap, no locking, robust in large deformation) — but it is a *control* problem to be monitored, never ignored.

**Top mistakes:** one global hourglass type for a model spanning blast (needs viscous) and slow crush (needs stiffness); raising hourglass stiffness to hide hourglassing instead of refining/using full integration; ignoring hourglass energy because "the animation looks fine"; full integration everywhere then fighting shear locking in bending.

---

## 5. Mass-scaling strategy

Mass scaling raises `Δt_crit` by **adding non-physical mass** to the time-step-controlling elements (`F = ma`, so a heavier element has a slower wave speed and a larger stable step). The **%-added-mass budget (<1–5 % global)** and the **read-it-from-glstat/d3hsp** check are in solver-numerics.md §4. This section is the *strategy*: which form, where, and how to keep it honest.

### 5.1 Conventional vs selective

- **Conventional mass scaling** — scale *every* element below `Δt_target` up to that step. Simple but blunt: it can add mass broadly, including to elements you care about, shifting inertia globally.
- **Selective mass scaling (`DT2MS < 0`)** — add mass **only** to the elements whose `Δt` is below `TSSF·|DT2MS|`, leaving the rest untouched. This is the recommended form: the few throttling slivers get heavier, the bulk of the model stays at true mass. Always prefer the negative-`DT2MS` form (solver-numerics.md §4).
- **Selective/global advanced mass scaling** (some solvers) redistributes added mass within an element to preserve translational inertia better — useful when even selective scaling perturbs the dynamics.

### 5.2 Budget per part, not just globally

> **A global added-mass of 2 % can hide a single part at +40 %.** A crush rail, a thin gusset, or a fine-meshed weld flange can absorb almost all the added mass while the global number looks fine — and that part's crush force, fold timing, and energy absorption are now wrong. **Budget added mass per part** and inspect the per-part `glstat`/`d3hsp` (or matsum) table, not only the model total. The acceptance check is *both* global (<~5 %) *and* per-critical-part (a few %).

### 5.3 Read the report, and watch rate-dependent materials

- **Where to read it:** LS-DYNA `glstat` (global added mass and %), `d3hsp` (per-element/part at startup), matsum (per-part energy). Abaqus prints mass-scaling messages and `*OUTPUT` for added mass. Confirm the number *after* the run, not just the request.
- **Rate-dependent materials shift under mass scaling.** Adding mass slows the local wave speed and can lower the **strain rate** seen by a Cowper-Symonds/Johnson-Cook material (material-modeling.md §2), softening its dynamic flow stress. Heavy scaling on rate-sensitive parts changes the *material* answer, not just the step — keep scaling off the high-rate-critical parts.
- **Quasi-static-via-explicit:** mass scaling is most defensible here (low velocities), but still verify **KE ≪ IE** (solver-numerics.md §4) — too much added mass injects spurious inertia that violates the quasi-static premise.

### 5.4 Always run the sensitivity pass

Re-run with **reduced (or zero) mass scaling** (and/or a refined mesh) and confirm the QoIs (peak force, intrusion, acceleration, energy split) are unchanged within tolerance. This is the explicit analog of a mesh-convergence / GCI study (§8, and vv-uq) — a single mass-scaled run is never self-validating.

**Top mistakes:** conventional scaling that adds mass to load-bearing parts; a clean global % hiding a single over-scaled critical part; mass-scaling a rate-dependent crush member and softening its flow stress; never running the reduced-scaling sensitivity pass; requesting scaling but never reading the achieved added mass.

---

## 6. Lagrangian / SPH / ALE / CEL — the method decision

Most crash is **Lagrangian** (the mesh moves with the material — accurate stress, cheap, contact-native). You leave Lagrangian only when material distortion would tangle or invert the mesh: fluids, splash, fragmentation, penetration, blast in air/water. Each alternative buys distortion-tolerance at a real cost.

| Phenomenon | Method | Why it wins | Cost / caveat |
|---|---|---|---|
| Solid-on-solid crush, folding, contact-dominated structure | **Lagrangian** | mesh tracks material; accurate stress/strain; native contact; cheapest | mesh tangles under extreme distortion → erosion or remap |
| Fragmentation, splash, severe distortion, penetration debris, soft-body (bird, water) | **SPH** (smoothed-particle hydrodynamics, mesh-free) | no mesh to tangle; particles flow and separate freely; couples to Lagrangian via contact | needs enough particles per smoothing length; **tensile instability** (spurious clumping) needs control (artificial stress / corrected kernels); costlier than Lagrangian |
| Air-blast / underwater blast, sloshing, high-velocity fluid driving a structure | **ALE** (arbitrary Lagrangian-Eulerian: material advects through a mesh that can move independently) + **FSI coupling** | mesh stays well-shaped while fluid flows through it; explicit fluid-structure interaction at the interface | advection adds diffusion/cost; needs a fine interface and care with the coupling (leakage); large fluid domains are expensive |
| Severe Eulerian flow into/around a structure (Abaqus ecosystem) | **CEL** (coupled Eulerian-Lagrangian) | Eulerian material (fluid, very-large-deformation solid) on a fixed grid, Lagrangian structure on top, automatic contact coupling | Eulerian stress less accurate than Lagrangian; fixed grid must span all material motion |

Decision heuristics:

- **Default to Lagrangian.** Use erosion (§3) for the *local* distortion of an otherwise-Lagrangian part before reaching for a mesh-free method.
- **SPH** for things that *flow, splash, or fragment* — bird strike (bird ≈ water, SPH), water impact/ditching, soil/sand, behind-armor debris, severe penetration plugs. Couple SPH projectile/soft-body to a Lagrangian structure through contact; convert eroded Lagrangian debris to SPH (§3.3).
- **ALE / CEL** for **fluid-structure** where the fluid domain matters (blast pressure field, UNDEX bubble, tank slosh). ALE is the classic LS-DYNA blast/UNDEX route; CEL is the Abaqus equivalent. Both are far costlier than empirical blast (§7) — use only when the gas/water dynamics genuinely couple to the structure.
- **NASA drop/impact studies** (e.g. vertical-drop of composite/airframe sections, water-ditching) directly compared **ALE vs SPH** for the fluid/soft phase: SPH is leaner and natural for the splash/fragmentation but needs particle-resolution and tensile-instability care; ALE captures the continuous fluid field but costs more and needs interface fidelity. Pick by whether you need a resolved *pressure field* (ALE/CEL) or just the *momentum exchange of a splashing/fragmenting medium* (SPH). [3]

**Top mistakes:** using ALE/CEL where Lagrangian + erosion would do (10× cost for no benefit); under-resolving SPH (too few particles per smoothing length → wrong response) or ignoring tensile instability; a CEL/ALE Eulerian domain too small to contain the material motion (material exits the grid); expecting Eulerian stress to match Lagrangian accuracy in the structure.

---

## 7. Blast

Blast loading splits into **empirical pressure loading** (cheap, no fluid mesh — for un-confined far-field) and **physical fluid simulation** (ALE/CEL/particle — for confined, close-in, or strongly-coupled cases).

### 7.1 Empirical: CONWEP / `*LOAD_BLAST`

- **CONWEP / `*LOAD_BLAST_ENHANCED`** applies an empirical pressure-time history to wetted surfaces from just the **charge mass (TNT-equivalent) and standoff**, using the Kingery-Bulmash free-air / surface-burst curves (incident + reflected pressure, angle-of-incidence correction). No air mesh, no fluid solve — milliseconds of setup, seconds of run. Use it for **un-confined, far-field** air blast on a structure that does not significantly disturb the flow (a wall, a panel, a vehicle floor from a standoff charge).
- Inputs: equivalent charge weight, standoff distance, surface-vs-air-burst flag, blast surface set. Outputs: pressure-time at each facet → structural response.
- **Limits:** assumes the structure does not alter the blast (no shadowing, no confinement, no re-reflection), and no afterburn/venting. Invalid for close-in (the charge is not a point at small standoff), confined/internal, or vented geometries.

### 7.2 Physical: particle-blast / ALE for confined & close-in

- **Particle-blast method** (corpuscular / `*PARTICLE_BLAST`) or **ALE air** models the detonation products and shock as a medium that interacts with the structure — captures **confinement, venting, channeling, shadowing, multiple reflections, and gas-structure coupling** that CONWEP cannot. Use for internal blast (cabin, container), close-in charges, buried charges (soil ejecta — couple with SPH/ALE soil), and any case where the structure deforms enough to change the load.
- **UNDEX (underwater explosion)** adds the **shock wave + the oscillating gas-bubble pulse** and **cavitation** at the structure — model with ALE/acoustic-fluid coupling; the bubble pulse and bulk cavitation reload the hull after the initial shock, so a shock-only model under-predicts. [2]

### 7.3 Reporting

Report **incident and reflected pressure, impulse (∫p dt — often more damage-relevant than peak pressure), and the pressure-time at gauge points**, plus the structural QoIs (peak deflection, plastic strain, breach). Impulse and pressure-time at gauges are how blast models are validated against arena tests.

**Top mistakes:** CONWEP for a confined/internal or close-in blast (it cannot see confinement or near-field non-uniformity); reporting peak pressure but not impulse; UNDEX with shock only (missing the bubble pulse and cavitation reload); ALE air domain too small or too coarse to carry the shock to the structure without numerical diffusion.

---

## 8. Drop test

Drop / shock analysis (consumer electronics, packaged goods, equipment) is a focused explicit recipe: a product hits a rigid (or compliant) floor at a known velocity, and you check whether critical components survive the deceleration.

### 8.1 How to start the impact — initial velocity vs gravity prestress

- **Initial velocity** — skip the free fall entirely: set every node's velocity to the impact speed **v = √(2gh)** at t=0, just above the floor. Cheap (no wasted free-fall steps), the standard approach. Keep a small gap and let contact engage in the first steps.
- **Gravity prestress then release** — apply gravity, reach static equilibrium (implicit or slow explicit), then release at the drop height; needed when **pre-impact stress state matters** (pre-tensioned packaging, sagging cantilevers) or when the free-fall orientation/rotation matters. More expensive; use only when the prestress is real.
- Add **gravity during impact** as a body force if the event is long enough for it to matter (usually negligible over a few ms).

### 8.2 Floor, orientation, and cushioning

- **Floor:** a rigid wall is standard (concrete/steel test surface); model a **compliant floor** only if the surface deforms (carpet, wood) and changes the pulse. Mesh a rigid floor (or use a rigid-wall card) fine enough that the product's contact nodes engage cleanly (§2.3).
- **Multiple orientations are mandatory.** The worst case is orientation-dependent and rarely the flat-face drop — run **face, edge, and corner** impacts (and the standardized set, e.g. the 1m/26-drop sequences of IEC/ISTA for packages). For electronics, **corner and edge drops** usually produce the highest local acceleration and PCB flexure.
- **Cushioning / packaging:** model foam and dunnage with a **crushable-foam** material (low-density foam, honeycomb; material-modeling.md) — its crush plateau is what limits the transmitted deceleration. The whole point of packaging design is to keep the product below its fragility limit.

### 8.3 Acceptance: peak-G vs fragility

> **The deliverable is the peak acceleration (G) and its duration at the critical component, checked against that component's fragility/damage boundary** (the shock-response / damage-boundary curve — critical velocity change + critical acceleration). A drop "passes" when the transmitted shock pulse stays under the component's fragility limit, not merely when nothing visibly breaks. Report filtered acceleration (use a defined SAE/CFC filter class — raw explicit acceleration is noisy and the filter choice changes the peak), velocity change, and any plastic strain / solder-joint strain at sensitive parts.

**Top mistakes:** dropping only flat-face (missing the worse corner/edge case); reading unfiltered (noise-spiked) acceleration and over- or under-stating peak G; rigid floor far too coarse (contact leakage); ignoring the prestress when it actually matters; foam modeled with a wrong/uncalibrated crush curve so the transmitted G is meaningless.

---

## 9. Penetration, ballistic & bird-strike

High-rate localized impact where the target may perforate. The recipe is **rate- and damage-aware material + the right kinematic treatment of the projectile + a target meshed to resolve the failure.**

### 9.1 Material and target

- **Material:** Johnson-Cook flow stress (strain, strain-rate, temperature softening) with **Johnson-Cook damage or GISSMO** for failure/erosion (material-modeling.md §2/§5). Adiabatic heating at high rate matters (thermal softening, shear bands) — use the coupled JC thermal term for ballistic metals.
- **Target mesh:** resolve the **through-thickness** failure — several elements through the plate thickness, refined in the impact zone, so the perforation/plugging/petalling mode is captured (one element through thickness cannot represent a plug). **Calibrate/regularize the failure strain to the element size** (§3, material-modeling.md §5) or perforation becomes mesh-dependent.

### 9.2 Projectile treatment

- **Rigid or eroding Lagrangian projectile** into an **eroding-contact** target (§2.2, §3) for hard projectiles — the projectile pushes, the target erodes, eroding contact keeps the projectile in contact with the freshly-exposed interior.
- **SPH projectile** for **soft/fluid-like impactors**: a **bird strike** is modeled as an **SPH "bird"** (water-like ρ, low shear, hydrodynamic EOS) splashing onto a Lagrangian leading edge / fan blade / canopy — SPH avoids the catastrophic mesh tangling a Lagrangian bird would suffer. Soft-body penetrators, slurry, and water-jet impacts are likewise SPH. [3]
- **Behind-target debris** (plug, spall, fragment field): convert eroded target elements to SPH (§3.3) so the debris keeps carrying momentum and can re-impact downstream structure.

### 9.3 Reporting

Report **residual velocity** (V_residual after perforation), the **V50 / ballistic limit** (the velocity with 50 % perforation probability — the standard armor metric, swept across impact velocities), **back-face deformation** (for non-perforating / behind-armor blunt trauma), and the **damage/penetration mode** (plugging, petalling, spall, ductile hole growth). A V50 study sweeps impact velocity and looks for the perforation/no-perforation boundary.

**Top mistakes:** one element through the target thickness (cannot resolve plugging/petalling); failure strain not regularized → mesh-dependent ballistic limit; Lagrangian bird (mesh inverts) instead of SPH; no eroding contact (projectile stops interacting once skin erodes); reporting only "perforated/not" without V50 or residual velocity.

---

## 10. Acceptance gates (explicit) — the integrity checklist

Run these on **every** explicit job before trusting a result. They are the explicit analog of the implicit residual-history / convergence gates (solver-numerics.md §3) and the V&V mesh-convergence study (vv-uq).

- [ ] **Energy balance closes.** Total energy ≈ constant — a few % drift maximum (solver-numerics.md §4). Account for external work, internal, kinetic, sliding, hourglass, eroded, and stabilization/damping terms. Growing total energy = instability; dropping = unmodeled loss.
- [ ] **Hourglass energy < 5 % (≤ 10 %) of internal energy** (solver-numerics.md §4) **and** the *right hourglass type* for the rate (§4). High HG → refine / full-integration before tuning.
- [ ] **Sliding-interface (contact) energy small and non-negative** (§2.4). Large negative = initial penetration/leakage → fix the model.
- [ ] **Added mass within budget** — **<~1–5 % global AND a few % per critical part** (§5; solver-numerics.md §4); read it from `glstat`/`d3hsp`, do not assume.
- [ ] **KE ≪ IE if quasi-static** (KE/IE < ~5–10 %; solver-numerics.md §4). If not, it was a dynamic event.
- [ ] **Eroded mass and energy small and physically justified** (§3.2). No `Δt`-erosion masquerading as a failure model.
- [ ] **Contact is the right type and not leaking** — self-contact for crushing parts, `SOFT=2` for soft/dissimilar interfaces, eroding contact where elements delete, rigid bodies meshed finely (§2).
- [ ] **Sensitivity / convergence pass** — **re-run with reduced (or zero) mass scaling and/or a refined mesh** and confirm the QoIs (peak force, intrusion, acceleration, energy absorption, residual velocity) are stable within tolerance (§5.4). **This is the explicit analog of a GCI study** — a single explicit run is never self-validating.
- [ ] **Reported QoI came from the right time** — filtered (defined SAE/CFC class) where acceleration is reported; pulled at the event peak, not the last written state.

> **Golden rule (mirrors solver-numerics.md §6): never trust the animation.** A crash that looks physical can still have 15 % hourglass energy, leaking contact, or 30 % added mass. Read the energy report and the added-mass table first; the stresses and accelerations are only meaningful once the integrity gates pass.

**Top mistakes:** declaring success on a completed run without reading energy balance / added mass / hourglass; no reduced-scaling or mesh sensitivity pass; reporting unfiltered acceleration; trusting a beautiful d3plot over a leaking energy budget.

---

## 11. Condensed quick-reference

- **When explicit:** short (µs–~1 s), high-rate, severe nonlinearity, fragmentation. Cost = elements × steps; one sliver sets Δt (solver-numerics.md §4). Quasi-static via explicit needs KE ≪ IE.
- **Contact:** penalty is the norm; single-surface/automatic-general for self-contact during crush; `SOFT=2` (segment-based) for soft-vs-stiff & dissimilar mesh; eroding contact where elements delete; mesh rigid bodies finely; **negative slide energy = penetration, fix don't damp.**
- **Erosion:** triaxiality-aware (JC-damage/GISSMO, regularized to mesh) — not bare failure strain, never min-Δt-as-failure. Track eroded mass/energy; convert debris to SPH.
- **Hourglass:** viscous (high rate) vs stiffness/Flanagan-Belytschko (low rate/coarse) vs type 6 (accuracy); **prefer full integration over cranking HG**; keep HG energy <5–10 % (solver-numerics.md §4).
- **Mass scaling:** selective `DT2MS<0`, budget per part not just global, read glstat/d3hsp, watch rate-dependent materials, always run the reduced-scaling sensitivity pass.
- **Method:** Lagrangian default; SPH for splash/fragmentation/soft-body; ALE/CEL for fluid-structure blast/UNDEX/slosh; don't pay for Eulerian where Lagrangian+erosion suffices.
- **Blast:** CONWEP/*LOAD_BLAST (empirical, un-confined far-field, cheap) vs particle/ALE (confined, close-in, coupled); UNDEX adds bubble pulse + cavitation; report impulse.
- **Drop:** initial velocity v=√(2gh) (or gravity prestress if it matters); rigid floor; **multiple orientations** (corner/edge worst); crushable foam; peak-G (filtered) vs fragility.
- **Penetration/ballistic/bird:** JC + damage, target resolved through-thickness & regularized; eroding Lagrangian or SPH (bird=SPH); report V50 / residual velocity / back-face deformation.
- **Gates:** energy ±~5 %; HG <5–10 %; slide energy small & non-negative; added mass <1–5 % (global + per part); KE≪IE if quasi-static; erosion small; reduce-scaling/refine sensitivity = explicit GCI; trust the energy report, not the animation.

---

## SOURCES

Reliability key: **H** = primary vendor theory/user manual or peer-reviewed/standards/agency report (highest); **M** = vendor knowledge-base / reputable practitioner / encyclopedic reference cross-checked; **L** = forum/secondary (used only corroboratively).

1. Ansys LS-DYNA Explicit Technical Guide v1.5 (contact types incl. single-surface/automatic/segment-based SOFT options, hourglass types viscous/stiffness/type-6, mass scaling DT2MS, energy/hourglass balance, eroding contact). https://lsdyna.ansys.com/wp-content/uploads/2025/03/LSDYNA_Explicit_Technical_Guide_v1.5.pdf — **H** (Ansys/LST guide).
2. LS-DYNA User's Guide / Keyword Manual 2025R1 (segment-based contact SOFT=2, *MAT_ADD_EROSION erosion criteria, *LOAD_BLAST_ENHANCED/CONWEP, *PARTICLE_BLAST, ALE/SPH, UNDEX/bubble, node-to-SPH conversion). https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/pdf/LS-DYNA_Users_Guide.pdf — **H** (vendor manual).
3. NASA — comparison of ALE and SPH methods for vertical-drop / water-impact simulation of airframe structures (fluid/soft-phase method trade-offs, SPH for splash/fragmentation vs ALE for the continuous fluid field). https://ntrs.nasa.gov/api/citations/20080022946/downloads/20080022946.pdf — **H** (NASA technical report).
4. (Numerics cross-reference) solver-numerics.md §4 "Time integration — Explicit" — CFL Δt = L_min/c, mass-scaling %-budget, hourglass-energy 5–10 % gate, KE≪IE, energy-balance check. In-skill reference (derived from LS-DYNA Mass Scaling FAQ, the LS-DYNA Explicit Technical Guide v1.5, and EDR Medeso quasi-static guidance). — **H**.
5. (Materials cross-reference) material-modeling.md §2/§5 — Johnson-Cook flow + damage, Cowper-Symonds rate scaling, GISSMO damage with mesh regularization (LCREGD), crushable-foam models. In-skill reference. — **H**.
6. LS-DYNA hourglass / energy-balance best practice (hourglass energy ≤10 %, ≤5 % preferred; viscous vs stiffness vs type-6 selection; full-integration alternative) — LS-DYNA Explicit Technical Guide v1.5 and DynaSupport hourglass notes. https://www.dynasupport.com/howtos/element/hourglass — **M/H**.
7. NAFEMS — explicit dynamics / crash & impact analysis guidance (Lagrangian vs mesh-free choice, energy-based verification of crash models). https://www.nafems.org/ — **H** (engineering-analysis standards/education body; topic canon).
