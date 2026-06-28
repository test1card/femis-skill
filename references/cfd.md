# Computational Fluid Dynamics (CFD) — Practitioner Brief

Scope: solver-agnostic best practices for CFD (incompressible/compressible, steady/transient,
single/multiphase, conjugate heat transfer, FSI), with the numbers, criteria, and failure
modes that decide whether a flow result is trustworthy — plus headless/batch execution for the
four dominant codes (Ansys Fluent/CFX, OpenFOAM, Siemens STAR-CCM+). Vendor specifics are
called out only where they diverge. Citations are keyed to the SOURCES list at the end.

> The single most important idea: **a CFD result is not valid because residuals dropped
> (iterative convergence) — it is valid only when (a) the *integrated quantities of interest*
> (drag, lift, ṁ, ΔP, Nu) have flat-lined, (b) **global imbalances** of mass/momentum/energy
> are < ~1 %, and (c) the QoI stops changing under **mesh refinement** (discretization
> convergence, reported as a GCI band). Residuals, mesh independence, and physical-modeling
> adequacy are three independent things — report all three.** [S1][S2][S10][S17]

This is the companion to the meshing/convergence brief (GCI/ASME V&V 20 procedure, element
quality metrics) — that material is referenced here, not repeated. [S17]

---

## Contents

**Core workflow (1–13):**
1. Governing equations & the modeling ladder · 2. Solver formulation (pressure- vs density-based,
coupling, steady/transient) · 3. Turbulence modeling (RANS, transition, LES/DES) · 4. Near-wall
treatment & y⁺ · 5. CFD meshing (FVM quality) · 6. Discretization schemes & Courant ·
7. Convergence · 8. Boundary conditions · 9. Specialized physics (multiphase/compressible/CHT/FSI —
brief) · 10. Verification & Validation · 11. Headless/batch execution · 12. Top mistakes ·
13. Quick-reference defaults.

**Advanced / deep-dive (14–22) — added below, cross-linked to the brief sections above:**
- **14. Multiphase in depth** — VOF, Eulerian–Eulerian, mixture, Lagrangian DPM, CFD-DEM,
  cavitation (Schnerr–Sauer / Zwart-Gerber-Belamri / Singhal); regime→model selection table.
  (extends §9.1)
- **15. Compressible / high-speed in depth** — density- vs pressure-based revisited, Mach regimes,
  flux schemes (Roe / AUSM / van Leer), shock capturing, total-vs-static BCs. (extends §9.2)
- **16. Reacting flow / combustion (pointer-depth)** — species transport, EDM/EDC, mixture-fraction
  /flamelet/FGM, PDF transport, premixed vs non-premixed.
- **17. Rotating machinery & moving mesh** — MRF (frozen rotor) vs mixing-plane vs sliding mesh vs
  overset/Chimera vs dynamic/morphing; when each.
- **18. Adjoint methods & shape/topology optimization for fluids** — continuous vs discrete adjoint,
  sensitivity fields, drag / pressure-drop objectives, porosity-based topology optimization.
- **19. Turbulence-model uncertainty quantification (RANS model-form error)** — parametric
  closure-coefficient UQ (NIPC/Sobol) **and** Reynolds-stress eigenspace (structural) perturbation
  (Emory–Iaccarino); the dominant RANS uncertainty. (extends §3.1)
- **20. Porous media & heat exchangers** — Darcy–Forchheimer (viscous + inertial resistance),
  macro/dual-cell HX models, LTE vs LTNE. (links §9.3)
- **21. Wall-modeled LES (WMLES) & free-surface vs interface-tracking** — Re-scaling cost relief;
  interface-capturing vs interface-tracking taxonomy. (extends §3.3, §14)
- **22. Aeroacoustics (pointer)** — Lighthill analogy / Ffowcs Williams–Hawkings; cross-link to the
  dynamics-NVH-acoustics brief.

GCI-for-CFD and the full V&V hierarchy live in §10 and the meshing/convergence brief; every
advanced section below points back to them rather than repeating.

---

## 1. Governing equations & the modeling ladder (orient first)

CFD solves conservation of mass, momentum (Navier–Stokes), and energy on a discretized domain,
almost always by the **finite-volume method (FVM)** — fluxes are balanced over each control
volume, which makes the scheme **conservative by construction** (the right property for flows).
[S1][S2]

The cost/fidelity ladder for turbulence (the dominant modeling choice):
- **RANS** (Reynolds-Averaged NS) — models *all* turbulence; cheapest; steady or unsteady
  (URANS). Default for engineering. [S5][S1]
- **Hybrid RANS-LES** (DES / DDES / SBES / SAS) — RANS in attached boundary layers, LES in
  separated/wake regions. 10–100× RANS cost. [S8][S1]
- **LES** (Large-Eddy Simulation) — resolves large eddies, models only sub-grid scales.
  100–1000× RANS. [S7][S1]
- **DNS** — resolves all scales down to Kolmogorov η; cost ∝ Re^≈3 (Re^(9/4) in space ×
  Re^(3/4) in time); research-only, low Re. [S1][S6]

**Default rule:** start RANS (k-ω SST). Escalate to scale-resolving **only** when the QoI is
governed by *unsteady separated turbulence* RANS cannot represent (massive separation, bluff-body
wakes, jets/mixing, aeroacoustics, combustion instability). Most industrial answers (forces,
pressure drop, heat transfer in attached/mildly-separated flow) are RANS problems. [S5][S8]

---

## 2. Solver formulation (the first numerical decision)

### 2.1 Pressure-based vs density-based
- **Pressure-based** (segregated or coupled): the historical incompressible/low-speed solver.
  Pressure is recovered from a pressure(-correction) equation derived from continuity. **Default
  for incompressible and mildly compressible flow (Mach ≲ 0.3, and works to transonic with
  coupling).** [S3][S1]
- **Density-based**: solves continuity, momentum, energy as a coupled set; pressure from an
  equation of state. **Use for high-speed compressible flow (transonic/supersonic/hypersonic,
  shocks, strong compressibility/combustion-driven density change).** Captures shocks crisply;
  poor conditioning at low Mach (use preconditioning or switch to pressure-based). [S1]
- Rule of thumb: **Ma < 0.3 → incompressible/pressure-based; Ma > ~0.3 → compressible;
  Ma ≳ 0.7–1 with shocks → density-based.** (Ma 0.3 ⇒ ~5 % density change, the classic
  incompressibility cut-off.) [S1]

### 2.2 Pressure–velocity coupling (pressure-based)
The pressure-correction family. Know which one and why: [S3][S4]
- **SIMPLE** (Semi-Implicit Method for Pressure-Linked Equations): the workhorse for
  **steady-state**. Neglects a velocity-correction term, so it **requires under-relaxation**
  (typical: p ≈ 0.3, U/momentum ≈ 0.7; they should roughly sum to ~1). Robust, slow. [S3][S4]
- **SIMPLEC** (SIMPLE-Consistent): drops the same term more consistently → tolerates **higher
  relaxation** (often p ≈ 0.7–1, U ≈ 0.9) and converges faster on well-behaved meshes; can be
  less robust on bad meshes. [S4]
- **PISO** (Pressure-Implicit Splitting of Operators): adds extra pressure-correction (neighbor +
  skewness) loops → designed for **transient** runs; allows larger time steps without sub-loops;
  bounded by accuracy (Courant), not stability, when used with implicit time. [S4]
- **PIMPLE** (OpenFOAM merged PISO-SIMPLE): the **transient default for stiff/large-Δt cases.**
  Runs an outer SIMPLE loop (with under-relaxation) inside each time step so you can run at
  **Courant > 1** while staying stable — trades inner iterations for a bigger Δt. Set
  `nOuterCorrectors` > 1 to activate true PIMPLE; `nOuterCorrectors=1` degenerates to PISO.
  `nCorrectors` ≈ 2 (pressure corrections), `nNonOrthogonalCorrectors` = 1–2 on
  non-orthogonal meshes. [S4]
- **Coupled** (pressure-based coupled, Fluent/CFX/STAR-CCM+): solves momentum + pressure
  **simultaneously** → far faster convergence (fewer iterations) and more robust for
  high-aspect-ratio/poor meshes and strongly coupled body-force flows (buoyancy, swirl,
  rotation), at higher memory (~1.5–2×). **Increasingly the recommended default** when memory
  allows; CFX is coupled-only by design. [S1][S3]

### 2.3 Steady vs transient
- Use **steady** if the QoI is a time-mean and the flow has a steady attractor (attached external
  aero at fixed conditions, internal duct ΔP). [S1]
- Use **transient (URANS/scale-resolving)** if the flow is **inherently unsteady** (vortex
  shedding, buffeting, sloshing, any LES/DES). A "steady" run that **won't converge — residuals
  and force monitors oscillate at a fixed period** — is usually telling you the physics is
  unsteady; switch to transient rather than forcing it. [S1][S10]

---

## 3. Turbulence modeling (the dominant accuracy lever in RANS)

### 3.1 RANS eddy-viscosity models (the Boussinesq family)
All linear eddy-viscosity models assume the Reynolds stress is proportional to mean strain rate
(**Boussinesq hypothesis**, an isotropic-eddy-viscosity approximation) — the root cause of most
RANS failures in swirling/anisotropic/curved flows. [S5][S6]

| Model | Eqns | Strengths | Weaknesses / when it fails | Use for |
|---|---|---|---|---|
| **Spalart–Allmaras (S-A)** | 1 | Cheap, robust; tuned for attached aero boundary layers, adverse pressure gradients | Poor for free shear/jets, separation, decay of isotropic turbulence | External aero, airfoils, turbomachinery; DES base model [S5] |
| **Standard k-ε** | 2 | Robust, cheap, well-validated free-shear/fully-turbulent core; the historical default | **Inaccurate in adverse pressure gradient & separation; needs wall functions (not valid to the wall); over-predicts spreading of round jets** | Internal flows, mixing, far-field; not near-wall-critical cases [S5][S6] |
| **Realizable / RNG k-ε** | 2 | Fix k-ε's round-jet & rotation/strain defects; better separation than standard | Still wall-function-dependent near wall | Swirl, rotation, separation where k-ε family preferred [S5] |
| **Wilcox k-ω** | 2 | Integrates to the wall (good viscous sublayer & adverse-pressure-gradient/ separation); no damping functions | **Strongly sensitive to freestream/inlet ω** (spurious changes in μ_t, skin friction, early separation) | Near-wall-critical, low-Re [S6][S11] |
| **k-ω SST (Menter)** | 2 | **The general-purpose default.** k-ω near the wall + k-ε in freestream via blending fn F₁ → removes k-ω freestream sensitivity; SST limiter on μ_t gives **accurate adverse-pressure-gradient separation onset & size** | More expensive than S-A; can over-produce turbulence at stagnation (use production limiter) | **Default for most external/internal, separation, heat transfer, turbomachinery** [S11][S12][S5] |
| **RSM (Reynolds Stress Model)** | 5–7 | **Drops Boussinesq — transports each Reynolds stress** → captures anisotropy, strong swirl, secondary flows, streamline curvature | Expensive, fragile convergence, more BCs; sensitive to initialization | Cyclone separators, strongly swirling combustors, square-duct secondary flow [S6][S16] |

**Practical default:** **k-ω SST** unless you have a specific reason. Use **RSM** only when
anisotropy/swirl is the physics of interest and you can afford the convergence pain. **k-ε** is
fine for fully-turbulent internal/mixing flow where the wall is not the QoI. [S5][S11][S12]

### 3.2 Transition modeling (don't assume fully turbulent)
Standard RANS models assume the boundary layer is **turbulent everywhere** — they cannot predict
laminar→turbulent transition, so they **over-predict skin friction and heat transfer** on bodies
with significant laminar runs (low-Re aero, turbine blades, UAV/wind-turbine airfoils, hydrofoils).
[S5][S6]
- **γ–Re_θ (Langtry–Menter 4-equation Transition SST):** correlation-based, **local** (Galilean-
  invariant, no search for boundary-layer integral quantities) → robust and parallel-friendly;
  the de-facto industrial transition model. Adds intermittency γ and transition-onset Re_θ
  transport eqns on top of SST. [S5][S12]
- **γ (1-equation) / k-kL-ω:** lighter alternatives. [S5]
- **Requirement:** transition models **demand a wall-resolved mesh (y⁺ ≲ 1)** and well-specified
  inlet turbulence intensity/length scale — they are sensitive to freestream turbulence (Tu). Get
  the inlet Tu right or transition location is meaningless. [S12]

### 3.3 Scale-resolving simulation (LES / DES / DDES / SBES)
Escalate here only when unsteady resolved turbulence is the QoI. Cost is dominated by the
near-wall resolution requirement and the time-step (Courant) constraint. [S7][S8]
- **LES:** resolves eddies larger than the filter (grid), models sub-grid stress (SGS).
  - SGS models: **Smagorinsky** (needs van-Driest wall damping; over-dissipative),
    **Dynamic Smagorinsky** (Germano — computes the coefficient locally, much better),
    **WALE** (Nicoud–Ducros — correct near-wall scaling, no dynamic procedure; popular default).
    [S7]
  - **Cost:** **wall-resolved LES (WRLES)** needs ~y⁺≈1 and streamwise/spanwise Δx⁺≈50–150,
    Δz⁺≈15–40 → cost scales ~Re^1.8 near walls; **100–1000× RANS.** Use **wall-modeled LES
    (WMLES)** to relax the wall cost for high-Re. Always run LES **transient with Courant ≲ 1**
    and average over many flow-through times after statistics stationarize. [S7]
- **DES (Spalart 1997):** RANS in attached boundary layer (length scale < grid), LES in
  separation (length scale > grid). ~10–100× RANS; **non-zonal, single smooth field.** [S8][S1]
  - **Pitfall — Grid-Induced Separation / Modeled-Stress Depletion:** if the mesh is refined
    *parallel to the wall* inside the boundary layer, classic DES switches to LES mode there,
    drains modeled stress without resolving real eddies → **artificial early separation.** [S8]
  - **DDES (Delayed DES):** adds a shielding function to keep RANS mode in the boundary layer
    regardless of grid → fixes GIS/MSD. **Prefer DDES over original DES.** [S8]
  - **IDDES** adds WMLES capability (resolves log layer if mesh allows). [S8]
- **SBES (Stress-Blended Eddy Simulation, Ansys) / SAS:** more aggressive, cleaner RANS↔LES
  shielding/blending; **SBES is the recommended modern hybrid in Fluent.** [S8]
- **Meshing for hybrid/LES:** the **focus (LES) region needs near-isotropic cells** (Δx≈Δy≈Δz);
  high-aspect cells that are fine for RANS boundary layers are wrong in the LES region.
  RANS↔LES interface meshing is the hard part. [S7][S8]

---

## 4. Near-wall treatment & y⁺ (the most common single mistake in CFD)

The turbulent boundary layer has a universal inner structure (law of the wall), and **how you
mesh and model the first cell decides whether wall shear/heat transfer is right.** [S9][S13]

### 4.1 Definitions & the wall layers
- **y⁺ = u_τ · y / ν**, where **u_τ = √(τ_w/ρ)** is the friction velocity, y the wall-normal
  distance of the **first cell centroid**, ν kinematic viscosity. y⁺ is a *result* — you can only
  *estimate* it before solving and must *verify* it after. [S9]
- Inner-layer structure (in wall units):
  - **Viscous sublayer y⁺ ≲ 5** — linear: u⁺ = y⁺.
  - **Buffer layer 5 ≲ y⁺ ≲ 30** — **neither law holds; the worst place to put your first cell.**
  - **Log-law region 30 ≲ y⁺ ≲ ~300** — u⁺ = (1/κ)·ln(E·y⁺), with **κ ≈ 0.41** (von Kármán),
    **E ≈ 9.8** (smooth wall). [S13]

### 4.2 Two strategies — pick one and mesh for it
- **Wall-resolved (low-Re / LRN):** put the **first cell centroid at y⁺ ≈ 1 (target ≤ 1, accept
  ≤ ~5)** and **integrate the model through the viscous sublayer.** Required for: accurate skin
  friction, **heat transfer (CHT, Nu)**, separation onset, transition models, any k-ω/SST run
  where the wall is the QoI. Costs many fine near-wall cells. [S13][S9]
- **Wall-function (high-Re / HRN):** put the first cell in the **log layer (30 ≲ y⁺ ≲ 300, often
  aim 30–100)** and **bridge the sublayer analytically** with a wall function. Cheaper; standard
  for large external/industrial RANS where wall heat transfer is secondary. **Never land the
  first cell in the buffer layer (5–30).** [S13][S9]
- **Hybrid / all-y⁺ / enhanced / scalable wall treatment (SST, Fluent EWT, CFX/STAR-CCM+ all-y⁺):**
  modern blends that **degrade gracefully across the whole y⁺ range** so you are not punished for
  a mesh that wanders out of the target band. **k-ω SST with all-y⁺ treatment is the robust
  default** — but it is still *most accurate* at y⁺≈1, so wall-resolve when wall quantities matter.
  [S11][S12]

### 4.3 First-cell-height estimate (do this before meshing)
1. Reynolds number **Re_L = ρ U L / μ**.
2. Skin-friction correlation (flat plate, turbulent): **C_f ≈ 0.058·Re_L^(−0.2)** (or
   0.026·Re_x^(−1/7)). [S9]
3. Wall shear **τ_w = ½ C_f ρ U²**; friction velocity **u_τ = √(τ_w/ρ)**.
4. First-cell **height y = y⁺_target · ν / u_τ** (use the *full* cell height ≈ 2× centroid distance
   depending on code convention). [S9]
   → Use one of the many online "y⁺ calculators" but **always verify the achieved y⁺ field in
   post** and re-mesh if out of band. [S9]

### 4.4 Boundary-layer inflation (prism) layers
- Grow **structured prism/hex inflation layers** off all viscous walls; the high-aspect-ratio
  cells are *correct* here because gradients are wall-normal. [S17]
- **≥ 10–15 layers** through the boundary layer is the common target (more for wall-resolved /
  adverse-pressure-gradient / heat transfer; ~10 minimum). Resolve enough layers that **15–20
  cells span the boundary-layer thickness δ.** [S17]
- **Growth (expansion) ratio ≈ 1.1–1.2** (≤ 1.3) between successive layers — too aggressive a jump
  smears the gradient and hurts accuracy. [S17]
- **First layer height** set from the y⁺ estimate above; **total prism thickness ≈ δ** so the last
  prism matches the core cell size (avoid a size jump at the prism-to-core interface). [S17][S9]
- Maintain prism quality at curvature and corners (the classic place prisms collapse/self-intersect
  → negative volumes → divergence). [S17]

---

## 5. CFD meshing (FVM-specific quality rules)

Element-type and the GCI procedure are covered in the meshing brief; the CFD-specific differences:
[S17][S14]
- **Cell types:** **poly (polyhedral)** meshes are increasingly the CFD default — fewer cells than
  tets for equivalent accuracy, more neighbors per cell (better gradient accuracy), robust on dirty
  CAD; **hex** (sweep/trimmed-hex/Cartesian-cut-cell) gives best accuracy-per-cell and lowest
  numerical diffusion where the geometry allows; **tet** cores are fine but diffuse and cell-hungry —
  pair with prism layers. **Hex/poly core + prism boundary layers** is the standard production
  recipe. [S17][S14]
- **The two metrics that decide CFD convergence (FVM):**
  - **Orthogonal quality / non-orthogonality** — the angle between the cell-face normal and the
    line joining the two cell centroids. The dominant FVM metric (it controls the diffusion-term
    discretization). **Non-orthogonality < ~70° is healthy; SimScale's hard divergence threshold
    is 88°.** Above ~70–80°, add **non-orthogonal correctors** and **drop to first-order or bounded
    schemes** to keep the run stable. [S14]
  - **Skewness** — offset between the face center and the centroid-connecting line; high skewness
    (> ~0.85–0.95) corrupts interpolation and causes divergence. [S14][S17]
  - **Aspect ratio** — unbounded in CFD *only along low-gradient directions* (boundary layers);
    excessive AR in the core hurts convergence. **Negative/zero cell volume = fatal.** [S14][S17]
- **Mesh independence is mandatory and is the #1 credibility gate** — run ≥ 3 systematically
  refined grids (refinement ratio r ≥ 1.3), report **GCI (F_s = 1.25 for 3 grids)** and the
  asymptotic-range check on the *integrated* QoI (drag/lift/ΔP/Nu). See the meshing brief for the
  full Roache/ASME V&V 20 procedure. [S17][S18]

---

## 6. Discretization schemes (accuracy vs boundedness)

The convection-term scheme is where CFD accuracy and stability fight. [S1][S14]
- **First-order upwind:** unconditionally bounded, easy to converge — but **highly diffusive
  (numerical/false diffusion smears gradients, shear layers, interfaces).** **Use only to
  *initialize*/stabilize, then switch to second order.** Reporting first-order results as final is
  a classic blunder. [S1][S14]
- **Second-order upwind (default for production):** the standard accurate scheme; can overshoot/
  oscillate at steep gradients → pair with a **gradient limiter** (Barth–Jespersen / Venkatakrishnan)
  for boundedness. **Default for momentum, energy, turbulence in steady RANS.** [S1][S14]
- **Central differencing:** 2nd-order, low dissipation — **required for LES** (upwind dissipation
  kills resolved eddies), but unbounded → only on good meshes / scale-resolving with sufficient
  resolution; **bounded-central** blends are the practical LES choice. [S7][S1]
- **Bounded / TVD / NVD schemes** (e.g. OpenFOAM `limitedLinear`, `linearUpwind`,
  `Gauss linearUpwindV`): 2nd-order accuracy with a limiter to preserve boundedness — the right
  default on real (non-orthogonal) industrial meshes. SimScale guidance: **non-orth 75–80 → 2nd-order
  bounded (Gauss linearUpwind / limitedLinear); > 80 → bounded first-order (Bounded Gauss upwind).**
  [S14]
- **Interface schemes (VOF):** need **compressive / geometric-reconstruction** schemes
  (Geo-Reconstruct, CICSAM, HRIC, OpenFOAM `interFoam` MULES) — first-order smears the interface,
  pure higher-order oscillates; the scheme must keep the volume fraction **sharp and bounded
  in [0,1].** [S15]
- **Gradient evaluation:** Green-Gauss (node-based) or **Least-Squares cell-based** (better on
  skewed/poly meshes — common default). [S1]

### Transient time-integration & the Courant (CFL) number
- **Courant number C = u·Δt/Δx** (per cell; sum over directions in multi-D). It measures how many
  cells a fluid particle crosses per time step. [S19][S20]
- **Explicit time stepping → C ≤ 1 is a hard stability limit (CFL condition);** implicit schemes
  are stable at larger C but **accuracy still degrades** as C grows. [S19][S20]
- **Targets:**
  - **LES / DES / transient with resolved unsteadiness: C ≲ 1 (often ≤ 0.5–1)** everywhere in the
    region of interest — this is an *accuracy* requirement, not just stability. [S7]
  - **Implicit URANS / PIMPLE for engineering means: C up to ~5–20+** acceptable if the integrated
    QoI is time-resolved (≥ ~20 time steps per shedding period / per characteristic unsteady cycle).
    [S4]
- **Time-step selection:** set Δt from the *physics* (resolve the smallest unsteady scale you care
  about — e.g. ≥ 20–30 steps per vortex-shedding period at f = St·U/D) **and** the Courant target,
  then take the smaller. Use **adjustable Δt** (target maxCo) where the solver supports it. [S4][S7]
- **Inner iterations:** in implicit transient, drive residuals down **within each time step**
  (PISO/PIMPLE correctors or N outer iterations) — a converged time step is the per-step analogue
  of steady convergence. [S4]
- **Dual time-stepping:** density-based / compressible unsteady solvers wrap an inner
  pseudo-time steady solve inside each physical time step → lets you use implicit physical Δt while
  reusing the steady machinery; converge the inner pseudo-time loop each step. [S1]

---

## 7. Convergence — judge it correctly

Iterative convergence ≠ a correct answer. The defensible convergence checklist: [S1][S10][S17]
1. **Scaled residuals fall and flatten** — typical engineering targets **continuity & momentum
   ~1e-3 to 1e-4; energy ~1e-6; turbulence ~1e-3 to 1e-4.** Residual *level* alone is **not** a
   pass — a coarse/over-diffused case can hit 1e-6 and be wrong. [S1][S10]
2. **Integrated QoI monitors are flat** — **monitor drag, lift, ṁ, ΔP, average Nu/h, a point
   pressure/velocity — and require them to stop changing (e.g. < 0.1–1 % over the last few hundred
   iterations).** This is the *real* convergence test; residuals can stall while forces still drift.
   [S1][S10]
3. **Global imbalances < ~1 %** — net mass, momentum, and **energy imbalance** across all
   boundaries (and domain sources) must close to **< 1 % of throughput** (tighter for CHT/heat).
   A passing imbalance is the strongest single sanity check. [S10][S17]
4. **Oscillating residuals/forces at a fixed frequency** in a "steady" run ⇒ the flow is unsteady
   → switch to transient, don't crank under-relaxation to mask it. [S1][S10]
- **If it won't converge:** reduce under-relaxation (or Courant) → start first-order then switch to
  second → check mesh quality (worst orthogonal-quality/skewness cells) → check BCs (esp. outlet
  backflow) → better initialization (potential-flow / hybrid init / FMG). [S14][S3]

---

## 8. Boundary conditions (where most "garbage in" enters)

- **Inlets:**
  - **Velocity inlet** — incompressible, known velocity (most common). Don't use for
    compressible. [S1]
  - **Mass-flow inlet** — compressible / when ṁ is the spec; fixes ṁ, lets pressure float. [S1]
  - **Pressure inlet** — total pressure known (e.g. driven by reservoir); good for compressible /
    natural-driven flows. [S1]
  - **Turbulence at inlets:** specify **turbulence intensity I and length scale ℓ (or hydraulic
    diameter, or viscosity ratio μ_t/μ).** Defaults matter: internal flows I ≈ 5 % and ℓ ≈ 0.07·D_h;
    clean external flow I ≈ 0.1–1 %. **Wrong inlet turbulence is a top error for k-ω/SST/transition
    (early/late separation, wrong transition).** Place inlets far enough upstream that the BL/wake
    is not clipped. [S6][S12]
- **Outlets:**
  - **Pressure outlet** — set static (gauge) pressure; the safe general outlet. [S1]
  - **Outflow / zero-gradient** — fully-developed assumption; **do not use** with compressible flow
    or where flow is not developed. [S1]
  - **Backflow specification** — if flow reverses at the outlet (recirculation reaching the
    boundary), the solver injects your **backflow turbulence/temperature** values → set them
    sensibly, and better: **move the outlet downstream** so backflow doesn't occur (recirculation
    at a pressure outlet is a top divergence/garbage cause). [S1][S10]
- **Walls:** no-slip (viscous) is default; specify thermal BC (fixed-T, fixed-flux, convective h,
  or coupled for CHT) and roughness if relevant (roughness shifts the log-law E and **requires
  wall functions, not y⁺≈1**). [S13]
- **Symmetry** — zero normal velocity & zero normal gradients; halves/quarters cost. **Never use
  symmetry where the *mean* flow is unsteady/asymmetric** (vortex shedding behind a symmetric
  bluff body is asymmetric — symmetry plane suppresses it and gives a wrong answer). [S1]
- **Periodic / cyclic** — translational (channels) or rotational (single turbomachine passage);
  optionally with a prescribed ṁ or Δp. [S1]
- **Far-field / pressure-far-field** — characteristic (Riemann) BC for external compressible;
  place boundaries **many body-lengths away** (≥ ~10–20 chords) so reflections don't contaminate.
  [S1]

---

## 9. Specialized physics (brief, with the failure mode for each)

### 9.1 Multiphase
Pick the model by topology and volume fraction: [S15][S1]
- **VOF (Volume of Fluid):** **immiscible fluids with a resolved sharp interface** (free surface,
  sloshing, tank filling, slug flow, wave impact). One momentum set + a volume-fraction advection
  per phase; **interface sharpness depends entirely on a compressive/geometric scheme and small
  Courant (≤ ~0.25–0.5 on the interface).** Not for dispersed/mixed flows. [S15]
- **Eulerian (multi-fluid):** separate momentum/continuity per phase + interphase exchange
  (drag, lift, etc.). **Most general & most expensive** — dispersed bubbly/droplet/particle flows,
  fluidized beds, boiling, where phases interpenetrate. [S1]
- **Mixture:** simplified Eulerian (algebraic slip) — cheaper for dispersed flows with low Stokes
  number / homogeneous-ish mixtures (cavitation, sediment). [S1]
- **DPM (Discrete Phase / Lagrangian):** track particles/droplets/bubbles as parcels through a
  continuous phase. **Use for dilute dispersed phase (volume fraction ≲ 10–12 %)** — sprays,
  particle-laden flow, erosion; one-/two-/four-way coupling by loading. [S1]

### 9.2 Compressible & combustion (brief)
- Compressible: density-based or pressure-based-coupled, energy on, ideal-gas/real-gas EOS;
  resolve shocks (grid adaption / 2nd-order + limiter); watch total vs static temperature/pressure
  reporting. [S1]
- Combustion: species transport + reaction (finite-rate / EDM / EDC / flamelet/PDF / FGM); strong
  density/T coupling → usually density-based or tightly-coupled pressure-based; chemistry stiffness
  dominates cost. Validate against canonical flames before trusting. [S1]

### 9.3 Conjugate Heat Transfer (CHT)
Solid + fluid solved together with a **coupled (conservative) interface** that matches temperature
and heat flux across the wall — no assumed h. [S21]
- **Mesh the solid too**, with a conformal (shared) or correctly-mapped non-conformal interface;
  resolve the near-wall fluid to **y⁺ ≈ 1** (heat transfer is wall-gradient-driven — wall functions
  degrade Nu). [S21][S13]
- Watch the **thermal-conductivity / time-scale mismatch** (solids respond ~10²–10⁶× slower) →
  transient CHT may need **different fluid/solid time scales or a steady-solid / transient-fluid
  scheme**; solid thermal inertia dominates transient response. [S21]
- Report **energy imbalance at the interface** and overall; CHT credibility hinges on it. [S10][S21]

### 9.4 Fluid–Structure Interaction (FSI)
Couple the flow solver to a structural (FEM) solver. [S22]
- **One-way:** fluid loads → structure (or thermal → structure); use when structural deformation is
  **small enough not to change the flow** (most stress-from-pressure problems). Cheap, no feedback.
  [S22]
- **Two-way:** structure deforms → mesh moves → flow changes → new loads, iterated to convergence
  each step. Required for **flexible/lightweight structures (flutter, flapping, valves,
  biomechanics/arteries, sails).** [S22]
- **Monolithic vs partitioned:** *monolithic* solves fluid+structure in one system (robust,
  bespoke code); *partitioned* couples separate best-in-class solvers (modular, reusable — the
  industrial norm) but **requires a stable coupling algorithm.** [S22]
- **★ Added-mass instability (the defining FSI pitfall):** when the **structure is light relative
  to the displaced fluid mass** (thin/flexible structures in dense fluid — e.g. arteries in blood,
  light wings in water), **weakly-coupled (explicit/loosely-staggered) partitioned schemes diverge
  no matter how small Δt.** Fix with **strong (implicit) coupling — sub-iterate fluid↔structure
  within each time step to convergence — with under-relaxation (Aitken dynamic relaxation) or
  quasi-Newton (IQN-ILS) acceleration.** Heavy structures in gas (e.g. metal in air) tolerate
  weak coupling. [S22]
- **Mesh motion:** diffusion/Laplacian smoothing or RBF morphing for small deflections; **remeshing
  / overset (Chimera)** for large motion; monitor mesh quality every step (motion → negative cells
  → crash). **Load/displacement mapping** between non-matching fluid & structural meshes must be
  **conservative** (conserve total force/energy across the interface). [S22]

---

## 10. Verification & Validation (CFD-specific)

V&V is the discipline that converts a colorful picture into a defensible result. [S17][S18][S2]
- **Verification = "solving the equations right"** (math/code): grid convergence (GCI), iterative
  convergence, time-step convergence, code-to-code / method-of-manufactured-solutions. **NASA's
  Examining-Spatial-Convergence tutorial and Roache's GCI are the canonical procedure** (see
  meshing brief). [S17][S18][S2]
- **Validation = "solving the right equations"** (physics): compare to **experiment** with quantified
  uncertainty. Use established **validation databases & benchmarks: NASA Turbulence Modeling Resource
  (TMR) / Turbulence Modeling Numerical Analysis (verification cases incl. flat plate, bump, NACA0012,
  backward-facing step), ERCOFTAC Classic Collection & Knowledge Base Wiki Best-Practice Guidelines,
  AIAA Drag Prediction / High-Lift Prediction Workshops.** [S2][S23][S5]
- **ASME V&V 20-2009** — the consensus standard for V&V in CFD & heat transfer; defines the
  validation-uncertainty combination (numerical + input + experimental). [S17]
- **Report, every time:** mesh count + quality, turbulence model + near-wall treatment + achieved
  y⁺, schemes, convergence evidence (residuals **and** QoI monitors **and** imbalances), GCI band,
  and the validation comparison. A result without these is not auditable. [S17][S10]

---

## 11. Headless / batch execution (automation reference)

All four major codes run fully batch/headless — essential for HPC, parameter sweeps, optimization,
and reproducibility. [S24][S25][S26][S27]

### 11.1 Ansys Fluent — journal / TUI, `-g`
- Fluent is driven by a **TUI (text user interface) journal** (Scheme) or **Python (PyConsole/
  PyFluent)**. Headless batch: [S24]
  ```
  fluent 3ddp -g -t<N> -i case.jou > run.log 2>&1        # -g no GUI, -t MPI procs, -i journal
  fluent 3ddp -g -t16 -mpi=intel -cnf=hosts -i solve.jou # cluster
  ```
  Dimensionality/precision token: `2d`/`3d` + `dp` (double precision), e.g. `3ddp`.
- A journal is recorded TUI commands; typical skeleton:
  ```
  /file/read-case-data my.cas.h5
  /solve/initialize/hybrid-initialization
  /solve/iterate 2000
  /file/write-data result.dat.h5
  /exit yes
  ```
- **PyFluent** (`ansys-fluent-core`) launches Fluent headless from Python for scripted
  meshing→solve→post and integration with the wider PyAnsys stack. [S24]

### 11.2 OpenFOAM — text dictionaries + `Allrun` + solver binaries
- A case is **plain-text dictionaries**: `system/{controlDict, fvSchemes, fvSolution,
  blockMeshDict, snappyHexMeshDict, decomposeParDict}`, `constant/{transportProperties,
  turbulenceProperties, polyMesh/}`, and time dirs `0/` (initial & BC fields). Fully
  version-controllable / scriptable. [S25][S26]
  - `controlDict`: application, startTime/endTime, deltaT, writeInterval, `adjustTimeStep`,
    `maxCo`, function objects (forces, residuals, probes). [S25]
  - `fvSchemes`: ddt, grad, **div** (convection — `Gauss linearUpwind`/`limitedLinear`),
    laplacian, **nonOrthogonalCorrectors** via `snGrad`. [S25][S14]
  - `fvSolution`: linear solvers (GAMG/PCG/smoothSolver), **SIMPLE/PIMPLE** dict
    (`nCorrectors`, `nOuterCorrectors`, `nNonOrthogonalCorrectors`, relaxationFactors,
    residualControl). [S25][S4]
- **Solvers:** `simpleFoam` (steady incompressible RANS), `pimpleFoam` (transient incompressible,
  large-Δt), `pisoFoam` (transient, Co<1), `interFoam` (VOF two-phase), `rhoCentralFoam`/
  `rhoPimpleFoam` (compressible), `chtMultiRegionFoam` (CHT), `buoyantSimpleFoam` (natural
  convection). [S26]
- **Run pattern** (the conventional `Allrun` script): `blockMesh` → `snappyHexMesh -overwrite` →
  `decomposePar` → `mpirun -np <N> simpleFoam -parallel` → `reconstructPar` →
  postProcess. `foamLog`/function objects extract residuals & forces. Headless by nature. [S25][S26]

### 11.3 Ansys CFX — `cfx5solve -batch`
- CFX is coupled-solver, set up in CFX-Pre → produces a **.def** (definition) file, then solved
  batch: [S27]
  ```
  cfx5solve -batch -def model.def -par-dist "host*N" -double          # local/parallel
  cfx5solve -def model.def -ini-file prev_results.res                 # restart/initialize
  ```
  - Driven by **CCL (CFX Command Language)** text; `cfx5pre -batch session.pre` builds the .def
    from a session/CCL file; `cfx5post -batch` post-processes; `-par-local`/`-par-dist` for
    partitioning. [S27]

### 11.4 Siemens STAR-CCM+ — Java macro `-batch`
- STAR-CCM+ is automated with **Java macros** and run headless: [S28]
  ```
  starccm+ -batch run.java -np <N> mysim.sim                       # run macro on a sim
  starccm+ -batch run.java -np 64 -mpi openmpi -machinefile hosts  # cluster
  starccm+ -batch step,100 mysim.sim                               # built-in batch commands
  ```
  - Macros are recorded/edited Java (full API: build mesh, set physics, run, export). Also
    scriptable via the **Jython/Python** simulation API. `-power`/`-podkey` for licensing,
    `-rsh`/`-mpi` for parallel transport. [S28]

### 11.5 Cross-cutting batch advice
- **Always log to file and monitor headless** (residuals + force/imbalance reports as text or
  function objects) — you can't watch a GUI on a cluster. [S25]
- **Decompose/partition for MPI**, keep partition count matched to cores, and verify the
  partitioned mesh interface count is small. [S25][S27]
- **Checkpoint/restart** (write data periodically) for long transient/HPC jobs. [S24][S25]

---

## 12. Top CFD mistakes (each with the fix and citation)

1. **Calling it converged because residuals hit 1e-x.** Fix: also require **flat integrated-QoI
   monitors** (drag/lift/ṁ/ΔP/Nu) and **global imbalance < ~1 %.** [S1][S10][S17]
2. **No mesh-independence study.** A single mesh proves nothing. Fix: ≥ 3 grids + GCI on the QoI
   (Roache/ASME V&V 20). [S17][S18]
3. **First cell in the buffer layer (5 < y⁺ < 30), or wrong strategy for the model.** Fix: y⁺≈1
   wall-resolved (heat transfer, separation, transition, SST-accurate) **or** 30–300 with wall
   functions — never in between; verify achieved y⁺ in post. [S13][S9]
4. **Reporting first-order-upwind results as final.** False diffusion. Fix: initialize first-order,
   converge **second-order** (with a limiter on real meshes). [S1][S14]
5. **Defaulting to k-ε for separated/adverse-pressure-gradient/near-wall flow.** Fix: **k-ω SST**;
   RSM for strong swirl/anisotropy. [S5][S11]
6. **Wrong / default inlet turbulence (I, ℓ).** Drives transition & separation for k-ω/SST/γ-Re_θ.
   Fix: set physically (internal I≈5 %, ℓ≈0.07D_h; clean external I≈0.1–1 %); inlet far enough
   upstream. [S6][S12]
7. **Recirculation/backflow at the outlet.** Garbage backflow values + divergence. Fix: move outlet
   downstream; set sensible backflow turbulence/T; use pressure outlet. [S1][S10]
8. **Symmetry plane on a flow whose mean is unsteady/asymmetric** (bluff-body shedding). Fix: model
   the full domain transient. [S1]
9. **Steady solver on inherently unsteady physics** (forces oscillate, won't settle). Fix: go
   transient (URANS/scale-resolving), don't over-relax to fake convergence. [S1][S10]
10. **LES/DES on a RANS-style high-AR mesh, with upwind, at Courant ≫ 1.** Fix: near-isotropic cells
    in the LES region, (bounded) central scheme, **Co ≲ 1**, average over many flow-throughs; prefer
    **DDES/SBES** over original DES to avoid grid-induced separation. [S7][S8]
11. **Wall functions for conjugate heat transfer / Nu.** Under-resolves wall gradient. Fix: y⁺≈1
    wall-resolved, mesh the solid, report interface energy balance. [S21][S13]
12. **Weakly-coupled (explicit) two-way FSI on a light structure in dense fluid.** Diverges
    (added-mass instability) regardless of Δt. Fix: strong/implicit coupling with Aitken/quasi-Newton
    acceleration. [S22]
13. **VOF with a non-compressive scheme / large interface Courant.** Smeared interface. Fix:
    compressive/geometric-reconstruction scheme, small interface Co (≤ ~0.25–0.5). [S15]
14. **Bad cells where the answer lives** (high non-orthogonality/skewness). Fix: target
    non-orthogonality < 70°, skewness < ~0.85; isolate worst cells; add non-orthogonal correctors.
    [S14][S17]
15. **Ignoring compressibility (Ma > 0.3 run incompressible) — or vice-versa.** Fix: choose
    pressure-based-incompressible vs density-based-compressible by Mach number. [S1]

---

## 13. Quick-reference defaults (sane starting points — then verify by convergence & V&V)

- **Solver:** incompressible/low-speed → pressure-based (coupled if memory allows; CFX always
  coupled); compressible-with-shocks → density-based. [S1][S3]
- **Coupling:** steady → SIMPLE/SIMPLEC (relax p≈0.3/U≈0.7, or higher for SIMPLEC); transient →
  PISO or **PIMPLE** (`nOuterCorrectors`>1 to exceed Co=1). [S3][S4]
- **Turbulence:** **k-ω SST + all-y⁺** as default; add **γ-Re_θ** if transition matters; **RSM**
  for swirl/anisotropy; escalate to **DDES/SBES → LES** only for resolved unsteady separation.
  [S5][S11][S8]
- **Near wall:** wall-resolved **y⁺ ≈ 1** (heat transfer / separation / transition), or
  **30 ≲ y⁺ ≲ 300** with wall functions; **never 5–30**; **≥ 10–15 prism layers, growth ≤ 1.2,
  total ≈ δ**, verify achieved y⁺. [S13][S9][S17]
- **Mesh:** hex/poly core + prism layers; **non-orthogonality < 70°, skewness < ~0.85, no
  negative volumes**; ≥ 3 grids for GCI. [S14][S17]
- **Schemes:** **2nd-order upwind + limiter** (steady); **bounded-central** (LES); first-order only
  to initialize; least-squares/Green-Gauss gradients; compressive scheme for VOF. [S1][S14][S7]
- **Transient:** Courant **≲ 1 for LES/DES**, up to ~5–20 for implicit URANS means; ≥ 20–30 steps
  per unsteady period; adjustable Δt to a maxCo target; converge inner iterations each step. [S4][S7]
- **Convergence gate:** residuals flat (cont/mom ~1e-4, energy ~1e-6) **AND** integrated QoI flat
  (< ~0.1–1 %) **AND** mass/energy imbalance < ~1 %. [S1][S10][S17]
- **BCs:** velocity/mass-flow/pressure inlet (+ I & ℓ), pressure outlet (+ backflow), no-slip walls
  (+ thermal/coupled), symmetry only for symmetric *mean* flow, far-field ≥ 10–20 body lengths.
  [S1][S6]
- **Report:** model + near-wall + y⁺ + schemes + mesh + GCI + imbalances + validation vs
  TMR/ERCOFTAC/experiment. [S17][S2]

---

## 14. Multiphase in depth (extends §9.1)

§9.1 gave the one-line model picker; this is the full decision logic, the per-model failure mode,
and the cavitation family. **The first question is always topology: is the interface *resolved*
(a sharp free surface you want to track) or *dispersed* (bubbles/drops/particles distributed in a
carrier)?** That, plus the dispersed-phase volume fraction and Stokes number, picks the model.
[S15][S29][S1]

### 14.1 Interface-capturing: VOF (Volume of Fluid)
- **What it is:** a single shared momentum/energy field for all phases + one **volume-fraction
  (α) advection equation per phase**; the interface is *captured* implicitly wherever 0<α<1. The
  classic **Eulerian, fixed-grid, interface-capturing** method. [S15]
- **Use for:** immiscible fluids with a **resolved sharp interface** — free surface, sloshing, tank
  fill/drain, dam break, wave/slug/film, jet breakup *onset*, mold filling. [S15]
- **The make-or-break numerics:**
  - **Interface sharpness depends entirely on the advection scheme** — use a **compressive /
    geometric-reconstruction** scheme (Geo-Reconstruct/PLIC, **CICSAM**, **HRIC**, OpenFOAM
    `interFoam` **MULES** with `cAlpha`≈1). First-order smears the interface; unlimited high-order
    oscillates and breaks 0≤α≤1 boundedness. (Cross-link §6 "Interface schemes (VOF)".) [S15]
  - **Interface Courant must be small** — explicit/geometric VOF wants **Co ≲ 0.25–0.5 on the
    interface**; this often sets Δt for the whole run. Implicit VOF tolerates larger Co at the cost
    of interface diffusion. [S15][S19]
  - **Surface tension (Brackbill CSF):** sets a capillary time-step limit
    Δt ≲ √(ρ̄ Δx³ / 2π σ); high spurious (parasitic) currents at the interface if σ/curvature is
    under-resolved. [S29]
- **Don't use VOF for:** dispersed/interpenetrating flows (many small bubbles/drops you can't mesh)
  — that is Eulerian/mixture/DPM territory. **VOF is *incompatible with the cavitation mass-transfer
  models below*** (they assume interpenetrating continua, not a tracked interface). [S30][S15]

### 14.2 Interface-resolving research methods (context, not production)
**Level-Set** (smooth signed-distance φ — better curvature/surface-tension than VOF but **not mass-
conservative**) and **Coupled Level-Set/VOF (CLSVOF)** (VOF conserves mass, level-set gives the
normal/curvature) are the accuracy-leaning cousins of VOF; **Front-Tracking** (explicit Lagrangian
marker interface on an Eulerian grid) is the most accurate and least diffusive but topology-change
(merge/breakup) is hard. Mostly research/high-fidelity; production stays on VOF. [S29]

### 14.3 Eulerian–Eulerian (multi-fluid / two-fluid)
- **What it is:** **separate continuity + momentum (+energy) per phase**, each present at a volume
  fraction, coupled by **interphase exchange closures** — drag (Schiller–Naumann, Tomiyama,
  Gidaspow for granular), plus lift, wall-lubrication, turbulent-dispersion, virtual-mass, heat/mass
  transfer. **The most general and most expensive multiphase model.** [S29][S1]
- **Use for:** truly **interpenetrating dispersed flows** where phases have different velocities and
  the dispersed fraction is not dilute — bubble columns, fluidized beds, risers, boiling/condensation
  (with a wall-boiling model), slurry/sediment, gas–solid cyclones. [S29]
- **Granular (Eulerian solids):** **Kinetic Theory of Granular Flow (KTGF)** supplies a granular
  temperature, solids pressure and viscosity so the solid phase behaves as a continuum (fluidized
  beds, risers). [S29]
- **Failure modes:** closure-law sensitivity (drag model choice dominates the answer in dense beds);
  fragile convergence (phase-coupled pressure–velocity); needs phase-pair turbulence treatment;
  far more BCs to get wrong than a single-phase run. [S29]

### 14.4 Mixture model (algebraic-slip Eulerian)
- **What it is:** **one mixture momentum equation** + a volume-fraction equation per secondary phase
  + an **algebraic slip (drift-flux)** relation for relative velocity — a simplified, cheaper
  Eulerian. [S29][S1]
- **Use for:** dispersed flows that are **near-homogeneous / low Stokes number** (small particles or
  bubbles that nearly follow the carrier): sedimentation, hydro-cyclones, mild bubbly flow, and as
  the **carrier framework for cavitation** (below). Cheaper and more robust than full Eulerian; less
  accurate when slip is large or the dispersed phase is dense. [S29][S30]

### 14.5 Lagrangian particle tracking — DPM (Discrete Phase Model)
- **What it is:** the continuous phase is Eulerian; the dispersed phase is **tracked as discrete
  parcels** (each parcel = many physical particles) by integrating Newton's second law per parcel
  (drag, gravity/buoyancy, pressure-gradient, virtual-mass, Saffman lift, Brownian, thermophoresis;
  + heat/mass exchange and evaporation/devolatilization for sprays/coal). [S29][S1]
- **Dilute limit:** valid when the **dispersed-phase volume fraction is low (≲ 10–12 %)** — sprays,
  particle-laden flow, erosion, dust, fuel/atomization, in-cylinder injection. Above that, switch to
  Eulerian/DEM. [S29]
- **Coupling level (set by loading):**
  - **One-way** — flow moves particles, particles don't affect flow (very dilute).
  - **Two-way** — particles exert momentum/heat/mass **source terms** back on the carrier (moderate
    loading).
  - **Four-way** — add **particle–particle collisions** (dense sprays, packed regions) → this is
    where DPM hands off to **DEM**. [S29][S31]
- **Steady vs transient (unsteady/transient particle tracking):** steady DPM injects along a frozen
  field; **transient tracking** advances parcels with the flow each Δt (required for unsteady
  carriers and accurate residence-time/erosion). [S29]

### 14.6 CFD–DEM (Discrete Element Method coupling)
- **DEM** resolves **every particle and every contact** with a contact-force law (**soft-sphere**
  spring-dashpot-friction — Hertz–Mindlin — is the production default; hard-sphere event-driven for
  very dilute rapid granular flow), explicit time-stepping with a **nearest-neighbour search**, at a
  time step set by the contact stiffness (Rayleigh/Hertz time). [S31]
- **CFD–DEM** couples a CFD carrier to DEM particles (fluid drag on particles ↔ particle reaction +
  voidage on fluid) → **dense granular–fluid flows where collisions dominate**: packed/moving beds,
  spouted beds, pneumatic conveying, screw/mixer, hopper discharge. **Most expensive dispersed
  option** (cost scales with particle count); use **coarse-graining/parcel-DEM** to scale up.
  Thermal-DEM adds particle–particle conduction + interstitial-gas conduction/radiation for hot
  granular beds. [S31]

### 14.7 Cavitation (phase change by pressure, on a mixture/Eulerian carrier)
- **Physics:** liquid vaporizes where **local static pressure drops below the saturation (vapor)
  pressure p_v**; the model is a **mass-transfer source between liquid and vapor** added to the
  volume-fraction equation, derived from a simplified **Rayleigh–Plesset** bubble-dynamics balance.
  [S30][S32]
- **The three standard mass-transfer models (all bubble-dynamics based):**
  - **Schnerr–Sauer** — derives the vapor source directly from Rayleigh–Plesset via a **bubble
    number density** (no empirical evaporation/condensation constants → fewest tuning knobs); common
    default. [S30][S32]
  - **Zwart–Gerber–Belamri (ZGB)** — uses a **nucleation-site volume fraction** + evaporation/
    condensation coefficients; **compatible with both mixture and Eulerian** frameworks. [S30]
  - **Singhal et al. ("full cavitation model")** — accounts for non-condensable gas and turbulent
    pressure fluctuations; **mixture-model only** (not Eulerian). [S30]
- **Setup rules (where cavitation runs go wrong):**
  - Run cavitation on a **mixture (or Eulerian) carrier — NOT VOF** (surface-tracking is
    incompatible with the interpenetrating-continua assumption). [S30][S15]
  - Set **p_v correctly for the liquid+temperature**; include **dissolved/non-condensable gas** mass
    fraction if relevant (it shifts inception). [S30]
  - Expect **stiff, oscillatory convergence** — use small time steps / strong under-relaxation;
    cavitation is often inherently **transient** (cloud shedding) even at "steady" operating points.
    [S30]
  - Validate **inception and the σ (cavitation number) breakdown curve** against test data before
    trusting erosion/performance predictions. [S30][S32]

### 14.8 Regime → model selection (the consolidated picker)

| Flow situation | Volume fraction / regime | Recommended model | Why / failure mode |
|---|---|---|---|
| Free surface, sloshing, tank fill, wave, slug, film | Resolved sharp interface | **VOF** (+ compressive scheme, Co≲0.5) | Captures interface; smears without compressive scheme [S15] |
| High-fidelity droplet/curvature (research) | Resolved interface | **Level-Set / CLSVOF / Front-Tracking** | Better curvature/σ; LS not mass-conservative [S29] |
| Bubble column, fluidized/spouted bed, boiling, dense slurry | Dispersed, **not dilute**, strong slip | **Eulerian–Eulerian** (+KTGF if granular) | Most general/expensive; drag-closure sensitive [S29] |
| Near-homogeneous dispersed (small bubbles/particles, low Stokes) | Dispersed, low slip | **Mixture (algebraic slip)** | Cheap; wrong when slip large [S29] |
| Spray, particle-laden, erosion, atomization | **Dilute** dispersed (≲10–12 %) | **DPM (Lagrangian)**, 1-/2-/4-way by loading | Invalid when dense → go DEM/Eulerian [S29][S31] |
| Packed/moving bed, conveying, hopper, mixer (collisions dominate) | Dense granular + fluid | **CFD–DEM** (soft-sphere) | Resolves contacts; cost ∝ particle count [S31] |
| Pumps/propellers/injectors/valves below p_v | Pressure-driven phase change | **Cavitation (Schnerr–Sauer / ZGB / Singhal) on mixture/Eulerian** | NOT VOF; stiff/transient; validate σ curve [S30][S32] |

---

## 15. Compressible / high-speed flow in depth (extends §9.2)

§2.1 picks pressure- vs density-based by Mach; this is the *why*, the flux schemes, shock capturing,
and the BC subtleties that decide whether a high-speed run is right. [S1][S33][S34]

### 15.1 Mach regimes & solver choice (the map)
- **Ma ≲ 0.3 — incompressible:** density change < ~5 %; **pressure-based**. [S1]
- **0.3 ≲ Ma < ~0.8 — subsonic compressible:** density matters, no shocks; **pressure-based-coupled
  or density-based**, energy on, ideal/real-gas EOS. [S1]
- **0.8 ≲ Ma ≲ 1.2 — transonic:** mixed sub/supersonic pockets terminated by **shocks** (airfoils,
  fans, nozzles); **density-based** is the natural choice (pressure-based-coupled works with care).
  [S1][S33]
- **1.2 ≲ Ma ≲ 5 — supersonic;  Ma ≳ 5 — hypersonic:** strong shocks, expansion fans, large
  T-variation, possibly real-gas/chemistry & wall heating; **density-based, robust upwind flux +
  limiter**, fine shock-normal resolution. [S1][S33]

### 15.2 Density-based vs pressure-based (revisited for high speed)
- **Density-based** solves continuity/momentum/energy as a **coupled set**; pressure from the
  **equation of state**. Captures shocks crisply via characteristic (Riemann) flux functions.
  **Poorly conditioned as Ma→0** (acoustic/convective time-scale disparity) → use **low-Mach
  preconditioning** (rescales the eigenvalues) or just use pressure-based below ~0.3. [S1]
- **Pressure-based-coupled** extends to transonic with compressible corrections and is often
  preferred when the same model spans low-and-high-speed regions; **density-based wins for strong
  shocks/hypersonics.** [S1][S3]
- **Time integration:** explicit (with local time-stepping for steady convergence) or **implicit**;
  unsteady compressible uses **dual-time-stepping** (inner pseudo-time steady solve per physical Δt —
  see §6). [S1]

### 15.3 Flux schemes (the heart of a density-based shock solver)
The inviscid (convective) flux at each face is built from a **Riemann-type upwind** function:
- **Roe (flux-difference splitting):** approximate Riemann solver using the **Roe-averaged**
  Jacobian; **sharp shock/contact resolution**, the high-accuracy workhorse. Needs an **entropy fix**
  (Harten) to avoid expansion shocks, and can suffer the **"carbuncle" instability** at strong
  bow shocks (grid-aligned). [S33]
- **AUSM family (Liou — AUSM, AUSM+, AUSM+-up):** **splits the flux into convective (advection-speed)
  and pressure (acoustic-speed) parts** → carbuncle-free, robust for strong shocks/hypersonics, and
  **AUSM+-up adds all-speed (low-Mach) capability.** Excellent general high-speed default. [S34]
- **Van Leer / Steger–Warming (flux-vector splitting):** very robust/diffusive — good for getting a
  hard case started, smears contacts; often used to initialize then switch to Roe/AUSM. [S33][S34]
- **HLLC:** restores the contact/shear wave missing from HLL → robust and reasonably sharp; common
  in modern compressible/SU2-style codes. [S33]
- **Pair with a slope/flux limiter** (Venkatakrishnan/Barth–Jespersen, van Albada, minmod) to keep
  the 2nd-order reconstruction **monotone (TVD) across shocks** — unlimited 2nd-order rings (Gibbs).
  (Cross-link §6.) [S1][S33]

### 15.4 Shock capturing & resolution
- **Capturing (not fitting):** modern CFD *captures* shocks as steep gradients over a few cells;
  resolution needs **fine cells normal to the shock** — use **gradient/Hessian-based mesh adaption**
  on pressure or density to refine on the shock automatically. [S1]
- **Monotonicity:** the limiter must suppress over/undershoot at the shock without killing accuracy
  in smooth regions; verify no negative pressure/temperature. [S1][S33]

### 15.5 Total vs static, and characteristic BCs (a top high-speed error)
- **Stagnation/total conditions** (p₀, T₀) are what you usually *know* at a reservoir/inlet; **static**
  conditions are what exist in the moving stream — they differ by the dynamic head and are related by
  the **isentropic Ma relations** (e.g. T₀/T = 1 + ½(γ−1)Ma²). **Mixing them up (specifying static as
  total or vice-versa) is a classic compressible BC blunder.** [S1]
- **Pressure-far-field / characteristic (Riemann) BC** for external compressible: specify
  free-stream Ma, static p, T, direction; the solver decides inflow/outflow per characteristic.
  **Number of conditions to impose depends on whether the boundary is sub/supersonic inflow/outflow**
  (supersonic inflow: impose everything; supersonic outflow: extrapolate everything). Put far-field
  many body-lengths away to avoid reflection. (Cross-link §8 "far-field".) [S1]
- **Outlets:** at a **supersonic outlet** extrapolate all variables (no downstream pressure imposed);
  at a **subsonic outlet** impose **back static pressure**. Avoid plain "outflow/zero-gradient" for
  compressible. [S1]

---

## 16. Reacting flow / combustion (pointer-depth, honest scope)

Combustion CFD is a specialty; this is enough to choose a model class and know the cost/accuracy
trade — not a substitute for a combustion text or vendor combustion guide. The core is
**turbulence–chemistry interaction (TCI):** reaction rates depend on temperature/species
*exponentially*, so resolving the mean is not enough. [S35][S1]

### 16.1 Building blocks
- **Species transport:** solve a convection–diffusion(–reaction) transport equation per species
  (mass fractions), with thermodynamic/transport property mixing and an energy equation with heat of
  reaction — strong **density/temperature coupling** (use density-based or tightly-coupled
  pressure-based). [S35][S1]
- **Reaction-rate closure (TCI):**
  - **Finite-Rate / Arrhenius** — chemistry from rate constants; accurate only when turbulence
    doesn't limit mixing (laminar/well-resolved); stiff ODE integration. [S35]
  - **Eddy-Dissipation Model (EDM / Eddy-Break-Up):** rate limited by **turbulent mixing** (k/ε
    time-scale), fast irreversible chemistry; cheap and robust for **non-premixed, mixing-limited**
    flames; **over-predicts where kinetics actually matter** (ignition, slow CO/NOx). [S35]
  - **Finite-Rate/Eddy-Dissipation:** takes the **slower of Arrhenius and mixing** rate — a common
    robust compromise. [S35]
  - **Eddy-Dissipation Concept (EDC):** embeds **detailed multi-step chemistry** in fine-scale
    turbulent structures → handles finite-rate kinetics in turbulent flow (pollutants, CO, NOx) at
    **much higher cost** (per-cell stiff chemistry). [S35]
  - **PaSR (Partially Stirred Reactor):** blends EDM-style mixing with finite-rate chemistry
    (popular in OpenFOAM reacting solvers). [S35]
- **Mixture-fraction / flamelet family (non-premixed):** instead of transporting every species,
  transport a conserved **mixture fraction** (+ its variance) and look up species/temperature from
  pre-computed **laminar flamelets** (or chemical equilibrium); **Flamelet-Generated Manifolds (FGM)**
  extend this to premixed/partially-premixed. Very efficient for fast chemistry. [S35]
- **Transported PDF methods:** solve a transport equation for the joint composition PDF →
  **closed chemical source term** (handles arbitrary finite-rate chemistry without a TCI model
  assumption); the most rigorous and the most expensive (Monte-Carlo particle methods). [S35]

### 16.2 Premixed vs non-premixed vs partially premixed
- **Non-premixed (diffusion):** fuel & oxidizer enter separately, burn as they mix → mixture-fraction
  /flamelet/EDM natural fit. [S35]
- **Premixed:** fuel+oxidizer pre-mixed, a **propagating flame front** → progress-variable / turbulent
  flame-speed closures (Zimont, BML), or FGM. [S35]
- **Partially premixed:** real burners/engines → combined mixture-fraction + progress-variable / FGM.
  [S35]

### 16.3 Honest caveats
- Combustion adds **radiation** (P-1/DO/DTRM with WSGG or spectral gas properties) and **pollutant
  post-processing** (NOx/soot), each its own model. [S35]
- **Validate against canonical flames** (Sandia/TNF piloted jet flames, bluff-body, premixed Bunsen)
  before trusting an industrial geometry; chemistry-mechanism choice and TCI model dominate the
  answer. [S35]

---

## 17. Rotating machinery & moving / deforming mesh

Pumps, fans, compressors, turbines, propellers, mixers, wind turbines — the modeling choice is
**how you represent the rotation**, trading steadiness/cost against rotor–stator interaction
fidelity. [S36][S1]

| Method | Steady/transient | What it does | Use when | Cost / limitation |
|---|---|---|---|---|
| **MRF (Multiple Reference Frame) / "frozen rotor"** | **Steady** | Rotating zone solved in a **rotating frame** (adds Coriolis + centrifugal source terms); mesh does **not** move. Interface couples frames at a **frozen relative position**. | Weak rotor–stator interaction; you want a fast **time-averaged** answer; design sweeps, initialization | Cheapest; **no transient interaction**; result depends on the frozen clocking position [S36] |
| **Mixing-plane (stage)** | Steady | Circumferentially **averages** flow at the rotor–stator interface → position-independent stage performance | Turbomachinery stage performance (axial compressors/turbines) with distinct blade rows | Loses circumferential non-uniformity / wake interaction [S36] |
| **Sliding mesh (transient MRF)** | **Transient** | Rotor mesh **physically rotates** each Δt; a non-conformal **sliding interface** re-associates with the stator mesh | **Strong rotor–stator interaction**, blade-passing tones, transient loads, acoustics | Time-accurate, expensive; needs ≥ ~20–40 steps per blade-passing period; conformal pitch matching [S36] |
| **Overset / Chimera (moving body)** | Steady or transient | A body-fitted mesh **overlaps and moves over** a background mesh; solution interpolated in the overlap | **Large relative motion / multiple independent bodies** (store separation, rotor flight, crossing bodies) without remeshing | Interpolation/overlap (orphan-cell) management; conservation care [S36][S37] |
| **Dynamic / morphing (deforming) mesh** | Transient | Mesh **smoothing / layering / remeshing** as boundaries move | Prescribed or solution-coupled deformation: valves, pistons, flapping, **FSI** | Negative-cell risk on large motion → monitor mesh quality every step (cross-link §9.4) [S1] |

**Selection logic:** start **MRF/frozen rotor** (or mixing-plane for a stage) for steady performance
and to initialize; escalate to **sliding mesh** when **rotor–stator interaction, blade-passing
unsteadiness, or tonal acoustics is the QoI**; use **overset** for large/independent body motion and
**dynamic-mesh morphing** for prescribed/coupled deformation (and FSI). A common workflow seeds a
sliding-mesh transient from a converged MRF solution. [S36][S37]

---

## 18. Adjoint methods & shape/topology optimization for fluids

When the objective is a scalar (drag, lift, **pressure drop / total-pressure loss**, uniformity,
heat-transfer rate) and the design has **many parameters**, gradient-based optimization with an
**adjoint** gradient is the efficient tool. [S38][S39]

### 18.1 Why adjoint (the key property)
- A finite-difference or direct-sensitivity gradient costs **one flow solve per design variable.**
  The **adjoint method computes the full gradient (sensitivity to *all* design variables) at the cost
  of ≈ one extra (adjoint) solve, independent of the number of design variables.** This is what makes
  shape/topology optimization with thousands–millions of design DOFs tractable. [S38][S39]
- Output is a **sensitivity field** on the surface (shape) or in the volume (topology): "move this
  surface out / add or remove material here to reduce the objective by this much" — directly
  actionable and a powerful *diagnostic* even without running the optimizer. [S39]

### 18.2 Continuous vs discrete adjoint
- **Continuous adjoint:** derive the adjoint PDE + boundary conditions analytically from the flow
  PDE, then discretize. Cheaper memory, elegant, but the discrete gradient is only *consistent* in
  the limit (can disagree with the actual discrete objective). [S38][S39]
- **Discrete adjoint:** differentiate the **discretized** solver (often by automatic differentiation)
  → gradient is **exactly consistent** with the discrete objective (best for robust optimization),
  at higher memory/implementation cost. [S38][S39]
- **Caveats:** adjoint robustness mirrors the primal — separated/unsteady flows make the adjoint
  stiff/divergent; **"frozen-turbulence" adjoint** (neglecting the turbulence-model linearization) is
  common but introduces gradient error; **unsteady adjoint** must integrate **backward in time** over
  stored states (checkpointing) and is expensive. [S38][S39]

### 18.3 Shape vs topology optimization
- **Shape optimization:** deform an existing surface/parametrization (control points, free-form
  deformation, node normals) along the surface sensitivity → smooth aero/hydro shaping (wing/duct/
  blade drag or loss reduction). [S38][S39]
- **Topology optimization (fluids):** treat every cell's "solidity" as a design variable via a
  **porosity/Brinkman penalization** — a spatially varying momentum sink drives cells to fully-fluid
  or fully-solid, *discovering* channel layout/connectivity (manifolds, cooling channels, low-ΔP
  ducts). The continuous adjoint supplies the porosity sensitivity (e.g. SPAM-type methods). Watch
  **grayscale (intermediate porosity), mesh dependence, and the need to re-mesh/validate the
  extracted geometry** with a body-fitted CFD run. [S39]
- **Objectives & constraints:** minimize drag / total-pressure loss / energy dissipation, or maximize
  heat transfer / flow uniformity, subject to volume, ΔP, or manufacturability constraints; coupled
  thermal-fluid topology optimization trades ΔP against heat transfer. [S39]
- Always **verify the optimized geometry** with an independent, fully-converged, mesh-independent CFD
  solve (GCI per §10) — the optimizer trusts its own (possibly frozen-turbulence) model. [S39][S17]

---

## 19. Turbulence-model uncertainty quantification (RANS model-form error)

**RANS structural model-form error — the deficiency of the turbulence closure itself — is usually the
*dominant* uncertainty in a RANS prediction, larger than discretization or parametric input
uncertainty, yet it is the one most often left unquantified.** Two complementary families bracket it.
[S40][S41][S42]

### 19.1 Parametric (closure-coefficient) UQ — "are my constants right?"
- **Idea:** the turbulence model's **calibration constants** (e.g. k-ε: C_μ, C_1ε, C_2ε, σ_k, σ_ε;
  SST/k-ω: β*, σ, a₁; S-A constants) were fit to canonical flows and carry **epistemic uncertainty**.
  Treat them as uncertain inputs over physically plausible ranges and **propagate to the QoI.** [S42]
- **Method:** **Non-Intrusive Polynomial Chaos (NIPC)** or stochastic collocation is the efficient
  propagator (Monte-Carlo-consistent at a fraction of the cost); **Sobol' (variance-decomposition)
  indices** then **rank which coefficients drive the output** (global sensitivity). [S42]
- **What it tells you:** the *spread of the answer within the chosen model* and which constant to
  pin/measure — coefficient-induced QoI uncertainty intervals can be large (tens of % on drag/skin
  friction in sensitive cases). **It does NOT capture the error of the Boussinesq assumption itself**
  — for that you need structural perturbation. [S42][S40]

### 19.2 Structural UQ — Reynolds-stress **eigenspace perturbation** (Emory–Iaccarino)
- **Idea (the important one):** the deepest RANS error is the **Boussinesq/eddy-viscosity assumption**
  — linear models force the Reynolds-stress anisotropy toward a fixed shape/alignment. The
  **eigenspace perturbation framework** perturbs the **modeled Reynolds-stress tensor** in its
  spectral decomposition to bound the structural (model-form) error **without any high-fidelity
  data.** [S40][S41]
  - **Eigenvalue (amplitude) perturbation:** push the anisotropy toward the **limiting states of
    realizable turbulence on the barycentric (Lumley) map** — **1-component, 2-component, and
    3-component (isotropic) corners** — to bracket how component-wise the turbulence could be. [S40]
  - **Eigenvector (orientation) perturbation:** rotate the principal axes of the Reynolds stress
    (toward alignment that maximizes/minimizes production) to bound **structural misalignment.** [S41]
  - **Realizability is enforced** — perturbed stresses stay positive-semi-definite (physically
    admissible), which is what makes the bracket meaningful rather than arbitrary. [S40][S41]
- **Procedure:** run the baseline RANS, then a small ensemble of perturbed solves (typically the
  three barycentric-corner eigenvalue perturbations × eigenvector variants, scaled by a marker/
  blending factor); the **envelope of the QoI across the ensemble is the estimated model-form
  uncertainty band.** Model-independent; demonstrated on channel flow, square-duct secondary flow,
  and shock/boundary-layer-interaction separation. [S40][S41]
- **Status:** now in vendor/community tooling and increasingly expected in high-consequence RANS
  reporting (turbomachinery, external aero); machine-learning/marker-based variants modulate the
  perturbation strength locally. [S41]

### 19.3 Practical guidance
- **Report a RANS result with a model-form band, not a single line**, whenever the decision is
  sensitive to separation/anisotropy/curvature (exactly where Boussinesq is weakest — cross-link
  §3.1). At minimum, **bracket with eigenspace perturbation**; add closure-coefficient NIPC/Sobol' if
  you need to know *which constant* matters. [S40][S42]
- These quantify **model** uncertainty; combine with **numerical** (GCI, §10) and **input/BC**
  uncertainty under **ASME V&V 20** for a total validation-uncertainty statement — see the
  **meshing/convergence brief (references/meshing-convergence.md)** for GCI and the **V&V/UQ brief
  (references/vv-uq.md)** for the full uncertainty-combination procedure. [S17][S40]

---

## 20. Porous media & heat exchangers

A porous-medium model replaces unresolvable internal geometry (packed beds, filters, catalysts,
perforated plates, tube banks, HX cores) with a **distributed momentum (and heat) sink** — you get
the right pressure drop and bulk heat transfer without meshing every passage. [S43][S1]

### 20.1 Darcy–Forchheimer momentum sink
- The momentum source per unit volume is **S = −(μ/α)·U − (½ C₂ ρ |U|)·U**:
  - **Darcy (viscous) term** μ/α·U — **linear in velocity**, dominates at low Re (laminar/creeping);
    **α = permeability.** [S43]
  - **Forchheimer (inertial) term** ½C₂ρ|U|U — **quadratic in velocity**, dominates at higher Re;
    **C₂ = inertial resistance.** [S43]
- **Calibrate the two coefficients from a ΔP–velocity curve** (experiment or a resolved unit-cell
  CFD): fit ΔP/L = a·U + b·U² → a gives viscous resistance (1/α), b gives inertial (C₂). Specify
  **directional (anisotropic)** resistances for honeycombs/tube banks. [S43]
- **Brinkman / Darcy–Brinkman–Forchheimer** adds a viscous (Laplacian) term so the model recovers
  no-slip at porous–fluid interfaces (needed when wall shear inside/at the medium matters). [S43]

### 20.2 Heat transfer in porous media
- **Local Thermal Equilibrium (LTE):** one temperature for solid+fluid (solid and fluid locally
  equilibrated) — the simplest, valid when solid/fluid exchange is fast relative to transport. [S43]
- **Local Thermal Non-Equilibrium (LTNE / dual-cell energy):** **separate solid and fluid energy
  equations** coupled by an interfacial heat-transfer coefficient + specific area — required when the
  solid and fluid are at meaningfully different temperatures (fast transients, high flux, sparse
  matrices). [S43]

### 20.3 Heat-exchanger macro-models
- **Macro (lumped) HX model:** represents a core as a porous zone with a prescribed **heat-rejection
  vs. flow** characteristic (e.g. NTU/effectiveness or an empirical curve) — fast system-level ΔP and
  duty without resolving fins/tubes. [S43]
- **Dual-cell (two-stream) HX model:** co-located **primary (hot) and auxiliary (cold) cell zones**
  exchanging heat through a UA/effectiveness map → captures both streams' temperature change in one
  CFD domain (radiators, oil coolers, charge-air coolers) without meshing the other side. Calibrate
  the UA / effectiveness and the porous ΔP from rating data. [S43]
- **Honest scope:** macro/dual-cell models give system ΔP and duty, **not** local fin temperatures or
  flow maldistribution detail — resolve a unit cell (or full core with CHT, §9.3) when local fields
  are the QoI. [S43][S21]
- **Cross-link:** conjugate heat transfer, contact resistance, and the thermal-elastic coupling that
  consumes a CHT/HX temperature field are covered in the **thermal-and-coupling brief
  (references/thermal-and-coupling.md)** and §9.3 here. [S21]

---

## 21. Wall-modeled LES (WMLES) & free-surface vs interface-tracking taxonomy

### 21.1 Wall-modeled LES — relieving the near-wall cost (extends §3.3)
- **The problem:** **wall-resolved LES (WRLES)** must resolve the near-wall streak structure
  (Δx⁺≈50–150, Δz⁺≈15–40, y⁺≈1) → near-wall cost scales ~**Re^1.8** and dominates the whole run at
  high Re. (See §3.3.) [S44]
- **WMLES:** resolve only the **outer boundary layer** with LES and supply the wall shear stress from
  a **wall model** instead of resolving the inner layer:
  - **Wall-stress (approximate-boundary-condition) models:** an algebraic **log-law / equilibrium-
    stress** model (or a thin **wall-model RANS** — a TBLE/zonal solve) returns τ_w from the LES
    velocity at a matching height. [S44]
  - **Hybrid / DES-as-WMLES (IDDES):** RANS treats the inner layer, LES the outer — a practical WMLES
    route (cross-link §3.3 DDES/IDDES/SBES). [S44]
- **Payoff:** WMLES cost scales much more weakly with Re (≈ outer-layer LES, ~Re-mild) → the only way
  LES reaches high-Re external/industrial walls. **Trade-off:** accuracy of the wall model in
  non-equilibrium (separation/APG/roughness) regions; the matching-location and log-layer-mismatch
  must be handled. Still **transient, Co≲1, near-isotropic outer cells, average over flow-throughs.**
  [S44]

### 21.2 Interface-capturing vs interface-tracking (free-surface taxonomy)
Two philosophies for a multi-fluid interface (cross-link §14): [S29][S15]
- **Interface-capturing (Eulerian, fixed grid):** the interface is a *field* on a fixed mesh —
  **VOF** (volume fraction), **Level-Set** (signed distance), **CLSVOF**. Handles **arbitrary topology
  change (merge/breakup) automatically**; interface is smeared over cells and its sharpness depends on
  the scheme. **The production choice.** [S15][S29]
- **Interface-tracking (Lagrangian/ALE, moving grid):** the mesh **conforms to and moves with** the
  interface — **front-tracking** (marker points on a background grid) or **boundary-fitted/ALE
  moving-mesh**. **Sharpest, least numerical diffusion**, exact interface BCs — but **topology change
  is hard** (re-gridding at merge/breakup) and large deformation needs remeshing. Research / very
  high fidelity. [S29]
- **Rule:** topology changes or violent free surface → **capturing (VOF)**; a single, modestly
  deforming interface where sharpness/surface-tension fidelity is paramount → **tracking/ALE**. [S29]

---

## 22. Aeroacoustics (pointer — see the dynamics-NVH-acoustics brief)

Flow-generated noise (jets, fans, cavities, trailing edges, HVAC) is usually computed in two stages
and is treated in depth in the **companion dynamics-NVH-acoustics brief
(references/dynamics-nvh-acoustics.md)** — this is the CFD-side pointer. [S45]

- **Source from CFD:** a scale-resolving unsteady solve (**LES/DES/DDES/SBES**, §3.3) provides the
  unsteady pressure/velocity field that is the acoustic source — RANS/URANS generally **cannot**
  supply broadband acoustic sources. [S45]
- **Acoustic analogy propagation:** **Lighthill's analogy** recasts Navier–Stokes into a wave
  equation with an aerodynamic source; **Ffowcs Williams–Hawkings (FW-H)** extends it to moving solid
  surfaces (rotors/fans) → integrate the surface/volume sources to far-field observers cheaply,
  avoiding a fully resolved acoustic mesh out to the observer. [S45]
- **Direct (DNC) computation** (resolving acoustic propagation in the CFD domain) needs
  **low-dissipation/low-dispersion schemes, non-reflecting BCs, and acoustic-CFL resolution** — costly,
  reserved for near-field/short-range. [S45]
- **Mesh/scheme note:** acoustic energy is tiny vs. hydrodynamic → upwind dissipation destroys it;
  use the **(bounded) central, fine-isotropic, Co≲1** LES practice of §3.3/§6. **Cross-link:** modal/
  structural-acoustic response, FRFs and FE/BE acoustics are in the **dynamics-NVH-acoustics brief.**
  [S45]

---

## SOURCES

- **[S1] Versteeg & Malalasekera, *An Introduction to Computational Fluid Dynamics: The Finite
  Volume Method*, 2nd ed. (Pearson)** — Highest reliability: the standard CFD textbook covering FVM,
  pressure-based vs density-based, SIMPLE/SIMPLEC/PISO, discretization schemes (upwind/central/TVD),
  boundary conditions, multiphase, compressible. (Canonical reference; corroborated by the indexed
  vendor/wiki sources below.)
- **[S2] CFD overview — primary: Versteeg & Malalasekera [S1] and Ferziger, Perić & Street,
  *Computational Methods for Fluid Dynamics*, 4th ed. (Springer). Orientation:** Wikipedia,
  "Computational Fluid Dynamics" — https://en.wikipedia.org/wiki/Computational_fluid_dynamics
  — overview of FVM, the RANS/LES/DES/DNS hierarchy and relative cost, governing-equation
  discretization, V&V context.
- **[S3] CFD-Online Wiki + Versteeg, pressure–velocity coupling** —
  https://en.wikipedia.org/wiki/SIMPLE_algorithm (and CFD-Online turbulence/numerics wiki) — Reliable:
  SIMPLE derivation, under-relaxation necessity, segregated vs coupled.
- **[S4] OpenFOAMWiki, "The PIMPLE algorithm in OpenFOAM" (Holzmann)** —
  https://openfoamwiki.net/index.php/OpenFOAM_guide/The_PIMPLE_algorithm_in_OpenFOAM — Reliable
  practitioner reference: PISO vs SIMPLE vs PIMPLE, nCorrectors/nOuterCorrectors, why PIMPLE allows
  Co>1, under-relaxation in steady vs transient.
- **[S5] Turbulence modeling — primary: Pope, *Turbulent Flows* (Cambridge, 2000) and Wilcox,
  *Turbulence Modeling for CFD*, 3rd ed. (DCW); NASA Turbulence Modeling Resource [S23] for the
  verified model forms. Orientation:** idealsimulations, "Turbulence models in CFD — RANS, DES,
  LES and DNS" https://www.idealsimulations.com/resources/turbulence-models-in-cfd/ ; Wikipedia
  "Turbulence modeling" https://en.wikipedia.org/wiki/Turbulence_modeling — S-A, k-ε, k-ω, SST,
  RSM strengths/weaknesses; energy cascade & Kolmogorov scale; model-selection guidance.
- **[S6] CFD-Online Wiki, "Turbulence modeling" & "Two equation models"** —
  https://www.cfd-online.com/Wiki/Turbulence_modeling ; https://www.cfd-online.com/Wiki/Two_equation_models
  — High reliability: Boussinesq eddy-viscosity assumption, RANS model taxonomy, near-wall LRN vs HRN
  treatments, wall-function law (E=9.8), k-ε round-jet/adverse-gradient defects.
- **[S7] CFD-Online Wiki, "Large eddy simulation (LES)"** —
  https://www.cfd-online.com/Wiki/Large_eddy_simulation_(LES) — High reliability: SGS models
  (Smagorinsky, Dynamic, WALE), filtering, central-scheme/low-dissipation requirement, cost scaling.
- **[S8] CFD-Online Wiki, "Detached eddy simulation (DES)"; Wikipedia CFD §DES** —
  https://www.cfd-online.com/Wiki/Detached_eddy_simulation_(DES) ;
  https://en.wikipedia.org/wiki/Computational_fluid_dynamics — High reliability: DES RANS↔LES
  length-scale switch, reduced cost vs LES, grid-induced separation / modeled-stress depletion and
  the DDES shielding fix, non-zonal single field, URANS-vs-DDES comparison.
- **[S9] CFD-Online Wiki, "Dimensionless wall distance (y plus)"** —
  https://www.cfd-online.com/Wiki/Dimensionless_wall_distance_(y_plus) — High reliability: y⁺
  definition (u_τ·y/ν), friction velocity, first-cell-height estimation via C_f correlation,
  pre-solve estimate-then-verify workflow.
- **[S10] ideaMetrics, "Convergence in FEA Analysis / Validation Guide" (imbalance & QoI gates,
  general to CFD)** — https://ideametricsglobalengineering.com/convergence-in-fea-analysis-validation-guide/
  — Reliable: imbalance ≤ 1 %, monitor integrated quantities not just residuals, ≥3-grid mesh
  convergence, residual non-oscillation. (FEA-framed but the equilibrium/imbalance/monitor logic is
  identical for CFD.)
- **[S11] SimScale Docs, "K-Omega Turbulence Models"** —
  https://www.simscale.com/docs/simulation-setup/global-settings/k-omega-sst/ — Reliable vendor docs:
  k-ω freestream sensitivity, k-ε freestream-region vs k-ω wall-region, SST blending function F₁ +
  viscosity limiter, all-y⁺ robustness, adverse-pressure-gradient/separation performance.
- **[S12] Menter (1994) SST k-ω; Langtry–Menter γ-Re_θ Transition SST; CFD-Online "SST k-omega
  model"** — https://www.cfd-online.com/Wiki/SST_k-omega_model — High reliability: SST formulation &
  blending, stagnation production limiter, correlation-based local transition model and its
  mesh/y⁺≈1 + inlet-Tu requirements. (Original Menter AIAA J. 32(8):1598 and Langtry-Menter AIAA
  J. 47(12):2894 are the primary papers.)
- **[S13] CFD-Online "Two equation models — Near-wall treatments"; law of the wall** —
  https://www.cfd-online.com/Wiki/Two_equation_models — High reliability: viscous sublayer (y⁺<5),
  buffer layer (5–30), log layer (30–300+), κ≈0.41/E≈9.8, LRN (y⁺~1, integrate to wall) vs HRN
  (wall functions) strategies.
- **[S14] SimScale Docs, "Mesh Quality"** —
  https://www.simscale.com/docs/simulation-setup/meshing/mesh-quality/ — Reliable vendor docs: CFD
  divergence thresholds (non-orthogonality 88, skewness, aspect ratio), and the explicit scheme
  guidance (non-orth 75–80 → 2nd-order bounded Gauss linearUpwind/limitedLinear; >80 → bounded
  first-order Gauss upwind).
- **[S15] VOF — primary: Hirt & Nichols (1981) "Volume of fluid (VOF) method for the dynamics
  of free boundaries," J. Comput. Phys. 39:201. Orientation:** Wikipedia, "Volume of fluid method"
  — https://en.wikipedia.org/wiki/Volume_of_fluid_method — VOF volume-fraction advection,
  why first-order smears & higher-order oscillates → need for compressive/geometric-reconstruction
  schemes to keep the interface sharp and bounded.
- **[S16] CFD-Online Wiki, "Reynolds stress model (RSM)"** —
  https://www.cfd-online.com/Wiki/Reynolds_stress_model_(RSM) — High reliability: RSM transports
  individual Reynolds stresses (drops Boussinesq), captures anisotropy/swirl/secondary flow, cost
  & convergence trade-offs.
- **[S17] Companion brief "Meshing, Element Technology, and Mesh Convergence" (this skill,
  research/meshing-convergence.md), drawing on Roache (1994/1997), ASME V&V 20-2009, SimScale,
  curiosityFluids** — High reliability: full GCI procedure (observed order p, Richardson
  extrapolation, F_s=1.25 3-grid, asymptotic-range check, r≥1.3), prism/inflation-layer guidance,
  CFD quality metrics. See that file's SOURCES for primaries.
- **[S18] curiosityFluids, "Establishing Grid Convergence" (OpenFOAM cavity worked example)** —
  https://curiosityfluids.com/2016/09/09/establishing-grid-convergence/ — Reliable: worked GCI/
  Richardson-extrapolation on an OpenFOAM case; cites the NASA Examining-Spatial-Convergence
  tutorial (https://www.grc.nasa.gov/WWW/wind/valid/tutorial/spatconv.html) and Roache.
- **[S19] CFL condition — primary: Courant, Friedrichs & Lewy (1928) Math. Ann. 100:32; LeVeque,
  *Finite Volume Methods for Hyperbolic Problems* (Cambridge). Orientation:** Wikipedia,
  "Courant–Friedrichs–Lewy condition" —
  https://en.wikipedia.org/wiki/Courant%E2%80%93Friedrichs%E2%80%93Lewy_condition —
  C = uΔt/Δx, C_max=1 for explicit, larger for implicit.
- **[S20] CFD-Online Wiki, "Courant–Friedrichs–Lewy condition"** —
  https://www.cfd-online.com/Wiki/Courant%E2%80%93Friedrichs%E2%80%93Lewy_condition — Reliable:
  CFD-framed CFL, explicit vs implicit C_max sensitivity.
- **[S21] Conjugate heat transfer — primary: Patankar, *Numerical Heat Transfer and Fluid Flow*
  (Hemisphere, 1980); Versteeg & Malalasekera [S1]. Orientation:** Wikipedia, "Conjugate
  (convective) heat transfer" — https://en.wikipedia.org/wiki/Conjugate_convective_heat_transfer
  — coupled fluid-solid interface (matched T & flux), no assumed h, solid/fluid time-scale
  disparity in transient CHT.
- **[S22] FSI — primary: Förster, Wall & Ramm (2007) Comput. Methods Appl. Mech. Engrg. 196:1278
  (added-mass instability of partitioned schemes); Bazilevs, Takizawa & Tezduyar, *Computational
  Fluid–Structure Interaction* (Wiley). Orientation:** Wikipedia, "Fluid–structure interaction" —
  https://en.wikipedia.org/wiki/Fluid%E2%80%93structure_interaction — one-way vs two-way,
  monolithic vs partitioned, and the **added-mass instability** for light structures in dense fluid
  (weak coupling diverges regardless of Δt → need strong/implicit coupling). Mapping/mesh-motion
  context.
- **[S23] ERCOFTAC Best Practice Guidelines & Classic Database; NASA Turbulence Modeling Resource
  (TMR); AIAA Drag/High-Lift Prediction Workshops** — https://www.ercoftac.org/ ;
  https://turbmodels.larc.nasa.gov/ — Highest reliability: the canonical CFD validation/benchmark
  collections and turbulence-model verification cases (flat plate, NACA0012, bump, backward-facing
  step). (Authoritative; cited from standard CFD practice — direct fetch of NASA TMR/grc was network-
  blocked in this session.)
- **[S24] Ansys Fluent User's Guide & PyFluent docs (TUI/journal batch, `-g`/`-t`)** —
  https://fluent.docs.pyansys.com/ (PyFluent) and Fluent Users/Text-Command-List manuals — High
  reliability vendor docs: `fluent 3ddp -g -t<N> -i journal`, TUI journal commands, PyFluent
  headless launch. (Command syntax is stable, documented vendor CLI.)
- **[S25] OpenFOAM User Guide — case file structure & system dictionaries** —
  https://www.openfoam.com/documentation/user-guide/2-openfoam-cases/2.1-file-structure-of-openfoam-cases
  ; https://www.openfoam.com/documentation/user-guide — High reliability vendor docs: 0/constant/system
  layout, controlDict/fvSchemes/fvSolution, decomposePar/reconstructPar, Allrun pattern, function
  objects.
- **[S26] OpenFOAM Tutorial Guide & solver applications** —
  https://www.openfoam.com/documentation/tutorial-guide — High reliability vendor docs: solver
  binaries simpleFoam/pimpleFoam/pisoFoam/interFoam/rhoPimpleFoam/chtMultiRegionFoam and their
  intended flow regimes.
- **[S27] Ansys CFX Solver Manager / `cfx5solve` documentation** — Ansys CFX Reference Guide
  (cfx5solve, cfx5pre, cfx5post batch; CCL) — High reliability vendor docs:
  `cfx5solve -batch -def model.def -par-dist`, .def workflow, CCL automation. (Stable documented CLI.)
- **[S28] Siemens Simcenter STAR-CCM+ User Guide — running in batch, Java macros** — Simcenter
  STAR-CCM+ documentation (`starccm+ -batch macro.java -np N sim`) — High reliability vendor docs:
  Java-macro automation, `-batch`/`-np`/`-mpi` headless cluster execution, JythonPython API.
  (Stable documented CLI.)

### Advanced-topic sources (sections 14–22)

- **[S29] Multiphase flow — primary: Brennen, *Fundamentals of Multiphase Flow* (Cambridge, 2005);
  Ishii & Hibiki, *Thermo-Fluid Dynamics of Two-Phase Flow* (Springer); CFD-Online & Ansys/STAR-CCM+
  multiphase theory. Orientation:** Wikipedia, "Multiphase flow" —
  https://en.wikipedia.org/wiki/Multiphase_flow — overview of multiphase regimes
  (dispersed vs separated/interface), Eulerian–Eulerian two-fluid closures (drag/lift/virtual-mass),
  mixture/algebraic-slip, KTGF granular, and interface-capturing vs interface-tracking taxonomy
  (VOF/level-set/CLSVOF/front-tracking). Corroborated by vendor multiphase guides [S30] and the VOF
  primary [S15].
- **[S30] Ansys Fluent Theory Guide §"Cavitation Models" & "Multiphase Flows"; Ansys Knowledge
  forum** — https://ansyshelp.ansys.com/ (Fluent Theory, Multiphase & Cavitation) ;
  https://www.afs.enea.it/project/neptunius/docs/fluent/html/th/node343.htm (mirrored Fluent Theory,
  cavitation models) ; https://innovationspace.ansys.com/knowledge/ — High reliability vendor theory:
  Schnerr–Sauer / Zwart-Gerber-Belamri / Singhal cavitation models and their framework
  compatibility (mixture vs Eulerian; **VOF incompatible** with cavitation interpenetrating-continua
  assumption), non-condensable-gas handling, DPM dilute-limit and coupling levels.
- **[S31] DEM — primary: Cundall & Strack (1979) "A discrete numerical model for granular
  assemblies," Géotechnique 29:47; CFD-DEM coupling literature. Orientation:** Wikipedia,
  "Discrete element method" — https://en.wikipedia.org/wiki/Discrete_element_method —
  soft-sphere (Hertz–Mindlin) vs
  hard-sphere contact models, explicit time-stepping + neighbour search + contact-stiffness time
  step, four-way (collisional) coupling, thermal-DEM (particle conduction + interstitial gas),
  coarse-graining; the DPM→DEM hand-off at dense loading.
- **[S32] CFD-Online Wiki, "Cavitation modeling"** —
  https://www.cfd-online.com/Wiki/Cavitation_modeling — Reliable: cavitation as pressure-driven phase
  change below vapor pressure p_v, Rayleigh–Plesset bubble-dynamics basis of the mass-transfer source
  terms, homogeneous-mixture modeling, σ (cavitation number) validation.
- **[S33] Primary: Toro, *Riemann Solvers and Numerical Methods for Fluid Dynamics*, 3rd ed.
  (Springer); Roe (1981) J. Comput. Phys. 43(2):357. Orientation: Wikipedia, "Roe solver"** —
  https://en.wikipedia.org/wiki/Roe_solver — High
  reliability: Roe approximate Riemann solver / flux-difference splitting, Roe averaging, Harten
  entropy fix, carbuncle instability; flux-vector splitting (van Leer/Steger–Warming), HLLC,
  TVD limiters; Mach-regime solver selection and low-Mach preconditioning. (Roe 1981, J. Comput.
  Phys. 43(2):357 is the primary.)
- **[S34] Primary: Liou & Steffen (1993) J. Comput. Phys. 107:23; Liou (1996/2006) AUSM+ / AUSM+-up.
  Orientation: Wikipedia, "Advection upstream splitting method (AUSM)"** —
  https://en.wikipedia.org/wiki/AUSM — High reliability: AUSM / AUSM+ / AUSM+-up convective–pressure
  flux splitting, carbuncle-free robustness for strong shocks/hypersonics, AUSM+-up all-speed (low-
  Mach) capability. (Liou & Steffen 1993; Liou 1996/2006 are the primaries.)
- **[S35] CFDLAND/CFD Flow Engineering combustion guides; Ansys Fluent & OpenFOAM combustion theory;
  Poinsot & Veynante, *Theoretical and Numerical Combustion*** —
  https://cfdland.com/a-guide-to-combustion-simulation-in-ansys-fluent-from-theory-to-practice/ ;
  https://cfdflowengineering.com/combustion-modeling-in-openfoam/ — Reliable practitioner+vendor:
  species transport, turbulence–chemistry interaction, finite-rate/EDM/finite-rate-EDM/EDC/PaSR,
  mixture-fraction & laminar-flamelet/FGM, transported-PDF, premixed vs non-premixed vs partially
  premixed; canonical-flame (Sandia/TNF) validation. (Pointer-depth; combustion-text/vendor-guide for
  full detail.)
- **[S36] Ansys Fluent Theory §"The Multiple Reference Frame Model" & sliding-mesh; cfdyna,
  "CFD simulation of rotating devices (MRF/SMM)"; mixing-solution "MRF versus Sliding Mesh"** —
  https://www.afs.enea.it/project/neptunius/docs/fluent/html/th/node33.htm ;
  https://www.cfdyna.com/CFDHT/rotatingDevices.html — High reliability: MRF/frozen-rotor (rotating-
  frame Coriolis+centrifugal source terms, steady, frozen interface), mixing-plane (circumferential
  averaging), sliding mesh (transient, physically rotating mesh, blade-passing interaction), and the
  MRF→sliding-mesh workflow.
- **[S37] Overset/Chimera grid method (STAR-CCM+ / Fluent overset docs; Steger–Benek Chimera
  literature)** — overset/Chimera background-mesh overlap, body motion without remeshing, orphan-cell/
  interpolation/conservation handling; used for large relative motion and multiple independent bodies.
  High reliability (standard moving-mesh method; vendor-documented).
- **[S38] Primary: Jameson (1988) "Aerodynamic design via control theory," J. Sci. Comput. 3:233;
  Giles & Pierce (2000) Flow Turbul. Combust. 65:393. Orientation: Wikipedia, "Adjoint state method"** —
  https://en.wikipedia.org/wiki/Adjoint_state_method — High reliability: adjoint/dual formulation,
  the key property that **gradient cost is independent of the number of design parameters**;
  continuous vs discrete adjoint, frozen-turbulence and unsteady (backward-in-time/checkpointing)
  caveats. (Jameson 1988, J. Sci. Comput. 3:233 is a foundational aero-adjoint primary.)
- **[S39] Fluid topology-optimization reviews (PMC "A Mini Review on Fluid Topology Optimization";
  SPAM, Springer "Low-friction fluid flow surface design using topology optimization")** —
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10647552/ ;
  https://arxiv.org/pdf/1512.08445 (Sensitive Porosity Adjoint Method) — Reliable: continuous-adjoint
  surface sensitivity fields, porosity/Brinkman-penalization topology optimization, drag/total-
  pressure-loss/dissipation objectives, grayscale/mesh-dependence pitfalls, coupled thermal-fluid
  topology optimization, need to re-mesh/validate the extracted geometry.
- **[S40] Emory, Pecnik & Iaccarino (2011) "Modeling structural uncertainties in Reynolds-averaged
  computations of shock/boundary-layer interactions," AIAA 2011-479; Emory, Larsson & Iaccarino
  (2013) Phys. Fluids 25:110822 — eigenvalue/barycentric Reynolds-stress perturbation** — Highest
  reliability primaries: data-free, realizability-constrained perturbation of Reynolds-stress
  anisotropy toward the 1C/2C/3C limiting states (Lumley/barycentric map) to bound RANS structural
  model-form error; the dominant RANS uncertainty; demonstrated on channel/square-duct/SBLI.
- **[S41] Iaccarino, Mishra & Ghili (2017) "Eigenspace perturbations for uncertainty estimation of
  single-point turbulence closures," Phys. Rev. Fluids 2:024605; physically-constrained eigenspace
  perturbation (Phys. Fluids 36:025153, 2024); MDPI Fluids 4(2):113 (OpenFOAM implementation)** —
  https://www.mdpi.com/2311-5521/4/2/113 ;
  https://pubs.aip.org/aip/pof/article/36/2/025153/3267202/ — High reliability: combined eigenvalue +
  **eigenvector (orientation)** perturbation = full eigenspace perturbation, realizability
  enforcement, perturbation-strength markers/ML modulation, ensemble-envelope as the model-form UQ
  band; OpenFOAM/community tooling.
- **[S42] Schaefer/Cary et al. (2016) "Uncertainty Quantification of Turbulence Model Closure
  Coefficients for Transonic Wall-Bounded Flows," AIAA J. (NASA NTRS 20160005982); k-ε closure-
  coefficient UQ via NIPC (Tandfonline 2024)** — https://ntrs.nasa.gov/citations/20160005982 ;
  https://arc.aiaa.org/doi/10.2514/1.J054902 ;
  https://www.tandfonline.com/doi/full/10.1080/19942060.2024.2430658 — High reliability: parametric
  (closure-coefficient) epistemic UQ via Non-Intrusive Polynomial Chaos, Sobol'/variance-
  decomposition ranking of coefficients (S-A, Wilcox k-ω, Menter SST, standard k-ε); large QoI
  uncertainty intervals; explicitly distinct from (and not a substitute for) structural eigenspace UQ.
- **[S43] CFD Flow Engineering, "CFD modelling of flow through porous media"; Ansys/STAR-CCM+ porous-
  media & heat-exchanger (dual-cell) theory; Darcy–Brinkman–Forchheimer literature** —
  https://cfdflowengineering.com/cfd-modeling-of-flow-through-porous-media-with-governing-equations/ —
  Reliable practitioner+vendor: Darcy (viscous, μ/α) + Forchheimer (inertial, ½C₂ρ|U|U) momentum sink,
  coefficient calibration from a ΔP–U curve, anisotropic/directional resistance, Brinkman term;
  LTE vs LTNE (dual-cell energy) heat transfer; macro and **dual-cell** heat-exchanger models
  (UA/effectiveness), with their lumped-scope limitation.
- **[S44] Larsson, Kawai, Bodart & Bermejo-Moreno (2016) "Large eddy simulation with modeled wall
  stress: recent progress and future directions," Mech. Eng. Rev. 3:15-00418; Bose & Park (2018)
  Annu. Rev. Fluid Mech. 50:535 "Wall-Modeled LES for Complex Turbulent Flows"** — High reliability
  reviews: WRLES near-wall cost ~Re^1.8, wall-stress (equilibrium log-law / TBLE / zonal-RANS) wall
  models, hybrid/IDDES-as-WMLES, matching-location & log-layer-mismatch issues, the much weaker
  Re-scaling of WMLES that makes high-Re wall-bounded LES feasible. (Corroborates §3.3 cost scaling.)
- **[S45] Companion brief "Dynamics, NVH & Acoustics" (this skill, references/dynamics-nvh-
  acoustics.md); Lighthill (1952) Proc. R. Soc. A 211:564; Ffowcs Williams & Hawkings (1969) Phil.
  Trans. R. Soc. A 264:321** — High reliability: two-stage aeroacoustics (scale-resolving CFD source +
  acoustic-analogy propagation), Lighthill analogy, FW-H for moving surfaces (rotors/fans), direct
  computation requirements (low-dissipation schemes, non-reflecting BCs, acoustic CFL); see that brief
  for structural/modal-acoustic, FRF and FE/BE acoustics depth.

*Cross-verification note: turbulence-model selection and the Boussinesq-limitation rationale are
corroborated across CFD-Online [S6][S16], idealsimulations/Wikipedia [S5], and SimScale [S11];
the SST blending + freestream-sensitivity story across [S11][S12][S6]. Near-wall y⁺ bands (sublayer
<5 / buffer 5–30 / log 30–300) and the LRN-y⁺≈1 vs HRN-wall-function split are corroborated across
[S13][S6][S9]. CFL/Courant limits across [S19][S20]. DES grid-induced-separation→DDES across [S8].
GCI/mesh-independence across [S17][S18] (and the meshing brief's primaries Roache/ASME V&V 20).
FSI added-mass instability per [S22]. Batch-execution syntax is stable documented vendor CLI usage
[S24][S25][S26][S27][S28]. Where NASA TMR/grc.nasa.gov and several vendor blog hosts were
network-blocked during this session, the corresponding facts (GCI tutorial, y⁺ first-cell estimate,
SST/transition papers) are independently corroborated by the indexed CFD-Online/Wikipedia/SimScale/
OpenFOAM sources and the canonical textbooks Versteeg & Malalasekera [S1] and Pope, "Turbulent
Flows" (Cambridge, 2000).*

*Advanced sections (14–22): multiphase model selection corroborated across Wikipedia multiphase
[S29], Ansys cavitation/multiphase theory [S30] and the VOF primary [S15]; cavitation Rayleigh–
Plesset/p_v basis and VOF-incompatibility across [S30][S32]. Compressible flux schemes corroborated
across [S33] (Roe) and [S34] (AUSM) with Toro/Roe primaries. MRF-vs-sliding-vs-overset across Fluent
theory and cfdyna/mixing-solution [S36][S37]. The adjoint "gradient cost independent of #design-vars"
property [S38] and porosity-based fluid topology optimization [S39] are mutually consistent. The
turbulence-UQ split is the load-bearing one and is cross-checked deliberately: **parametric closure-
coefficient UQ (NIPC/Sobol')** [S42, incl. NASA NTRS] is shown to be distinct from and complementary
to **structural eigenspace perturbation** [S40 Emory–Iaccarino, S41 eigenvector/eigenspace] — both
agree that RANS structural model-form error is the dominant, most-often-unquantified uncertainty.
Darcy–Forchheimer (viscous+inertial) and LTE/LTNE dual-cell HX models per [S43]. WMLES Re-scaling
relief per the Larsson/Bose-Park reviews [S44], consistent with the WRLES ~Re^1.8 cost in §3.3 [S7].
Aeroacoustics (Lighthill/FW-H two-stage) per [S45] and the dynamics-NVH-acoustics companion brief.
Several primaries (NASA NTRS closure-coefficient UQ, AIAA/PRF eigenspace-perturbation papers, AIAA
journal hosts, MDPI) were paywalled or access-restricted in this session; the corresponding facts are
corroborated by the open abstracts/preprints and the indexed Wikipedia/CFD-Online/vendor sources, and
keyed to the canonical primaries by author/year/venue above.*
