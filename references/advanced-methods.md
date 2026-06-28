# Advanced FEM/CAE Methods — Practitioner Best-Practices Brief

Scope: substructuring / superelements / Component Mode Synthesis (CMS); model order reduction (MOR); multibody dynamics (rigid + flexible) and co-simulation; optimization (topology / shape / sizing / parameter) and model updating / inverse parameter ID; submodeling; and a loads & boundary-conditions catalog. Vendor-neutral where possible; vendor specifics flagged (Nastran/MSC & NX, Ansys/MAPDL/Workbench, Simcenter 3D, Adams). Numbers and rules are sourced; see SOURCES. Conventions stated in the platform's units; verify against your solver's manual.

---

## 1. Substructuring / Superelements / Component Mode Synthesis (CMS)

**What it is.** Replace a large FE part by a small set of generalized DOF (boundary/interface DOF + a truncated set of component modes). The reduced stiffness/mass (and optionally damping) matrices form a *superelement* that is assembled with other parts. Two passes: a **generation pass** (reduce one component, output reduced matrices) and a **use/assembly pass** (couple superelements + residual structure, solve, then recover internal results by **data recovery / expansion** back to physical DOF).

### 1.1 Method families (pick by interface treatment)

- **Hurty / Craig–Bampton (fixed-interface CMS)** — the workhorse. Basis = **constraint modes** (one per retained boundary/interface DOF: a unit static displacement imposed on that DOF with all other boundary DOF fixed, interior free) **+ fixed-interface normal modes** (interior eigenmodes with the boundary fully clamped, truncated above a frequency cutoff). Exact at the static limit; converges from below as you add modes. Default in Nastran (`SEBULK`/external SE), Ansys (CMS, `CMSOPT,FIX`), Simcenter, and Adams flex bodies. Best when interfaces are well-defined and you want robust, monotone convergence.
- **Free-interface methods (MacNeal, Rubin, Craig–Chang)** — basis = **free-interface normal modes + rigid-body modes + (residual) attachment/inertia-relief modes**. Craig & Chang (1976) added **residual flexibility** to the free-interface coupling, which markedly improves accuracy vs. truncated free modes alone. Advantage: free-free component modes can be obtained directly from modal **test** data (good for test–analysis hybrid models); interface DOF can be eliminated during assembly. Use when components are tested free-free or when the assembled interface is soft. (Ansys `CMSOPT,FREE`.)
- **Dual Craig–Bampton / enhanced CB** — research-grade hybrids that improve interface convergence; relevant for very large jointed/contact assemblies.

### 1.2 How many modes / what cutoff (the number that matters most)

- **Frequency cutoff rule of thumb:** retain fixed-interface normal modes up to **1.5×–2× the highest frequency of interest** (f_max). Below ~1.5×f_max accuracy of the top retained modes degrades because of modal truncation. Many production decks cite explicit bands (e.g., retain modes 0–4000 Hz when interested to ~2000–3000 Hz). For rotordynamics, a common cutoff is **5× max rotor speed**.
- **Constraint modes are always kept in full** (one per retained interface DOF) — they carry the static/load-path accuracy and are not truncated. Therefore *interface DOF count* drives superelement size more than interior modes do.
- **Convergence check (mandatory):** re-run with a higher cutoff (add the next band of modes) and confirm target frequencies/responses change by less than your tolerance (commonly <1–2% on retained natural frequencies). CB converges monotonically from above on frequencies, so a stable result is trustworthy.
- **Residual/attachment modes** (free-interface methods) restore the static flexibility lost by truncation — omit them and force/stress recovery near interfaces is poor.

### 1.3 Interface (boundary) DOF reduction

Large mating surfaces (e.g., bolted flanges, glued faces) generate too many retained DOF and bloat the superelement. **Interface reduction** (a secondary CMS/characteristic-constraint-mode reduction on the boundary set, "Enhanced Craig–Bampton") keeps only the dominant interface shapes. Use when interface DOF dominate the reduced-model size.

### 1.4 DMIG / matrix exchange and vendor coupling

- Nastran exchanges reduced matrices as **DMIG** (Direct Matrix Input at Grid points). Generate external superelements with `EXTSEOUT`; output format via `PARAM,EXTOUT` → `DMIGPCH` (.pch), `DMIGOP2` (.op2), `DMIGOP4` (.op4), `DMIGBIN`. Place DMIG inside a `BEGIN SUPER` block or in the residual structure block (handled differently — they are ultimately added to the element matrices).
- **Reduced load vectors:** an external SE created with a load (e.g., `GRAV`) and `DMIGPCH` emits an extra reduced-load matrix (`PAX`). With **multiple SUBCASEs**, the residual (assembly) run must carry as many SUBCASEs as needed to sequence the reduced loads correctly — a classic mistake is mismatched subcase counts.
- Reduced matrices flow into other tools: e.g., Adams imports a **Modal Neutral File (MNF)** generated by CB reduction containing generalized M/K, eigenvalues, mode shapes, **stress/strain modes**, modal loads, nodal coords, attachment nodes, and inertia invariants.

### 1.5 When to use CMS

Large **repeated** assemblies (model one sector/bracket once, instantiate many); dynamic reduction for large models where only a frequency band matters; coupling subsystems from different teams/vendors via matrix exchange; test–analysis substructuring; enabling flexible bodies in multibody (§3); and design loops where only a sub-part changes (regenerate one superelement, keep the rest).

### 1.6 Top mistakes

- Cutoff set at f_max instead of ~1.5–2×f_max → truncation error in the band of interest.
- Forgetting residual/attachment modes in free-interface methods → bad interface force/stress recovery.
- Too many retained interface DOF (full mating face) → superelement no smaller than the original; fix with interface reduction.
- Subcase / reduced-load mismatch between generation and assembly runs.
- Skipping the **expansion/data-recovery** verification (reduced model gives global response but you must expand to get physical stresses).

---

## 2. Model Order Reduction (MOR) beyond CMS

- **Guyan / static condensation (Guyan reduction):** partition DOF into masters (a-set) and slaves (o-set); slaves condensed assuming **no inertia in the slave set**. Exact for statics; **introduces mass error** in dynamics that grows with frequency — only valid well below the first slave-set mode. Choose masters where mass is concentrated / where you want response. It is the static (zero-mode) limit of Craig–Bampton.
- **Modal truncation / IRS / dynamic condensation:** keep low modes; **Improved Reduced System (IRS)** and dynamic reduction add a pseudo-static inertia correction to Guyan to recover dynamic accuracy.
- **Krylov-subspace / moment-matching MOR:** projection-based reduction that matches the first *r* (one-sided) or *2r* (two-sided) **moments** of the transfer function about chosen expansion frequencies. Preserves second-order structure and SPD of M/K when done with structure-preserving variants. Cheaper than full eigen-extraction for input/output (frequency-response) accuracy over a band; good for forced-response and **frequency-domain** fidelity where modal truncation is weak.
- **State-space ROM for controls / digital twins:** export reduced M/K/C (and B/C input–output maps) as a **state-space (LTI) system** for control design, hardware-in-the-loop, real-time, and digital-twin use. CB/Krylov ROMs are the usual bridge from FE to Simulink/state-space and to **FMU** export (§3). Match the band to the controller bandwidth; verify against the full model's FRF.
- **Certified / a-posteriori-bounded ROM (reduced basis):** for models re-evaluated across a **parameter space** (geometry, material, BC, load — the many-query / real-time / digital-twin case), the rigorous approach is the **certified reduced-basis (RB) method** (Patera, Rozza, Hesthaven–Stamm): an **offline greedy** builds the basis by repeatedly adding the parameter point where a **cheap, rigorous a-posteriori error bound** Δ_N(μ) ≥ ‖u(μ) − u_N(μ)‖ is largest, so the basis is **provably near-optimal**; the **online** stage returns both the reduced output *and* its certified error bar in cost **independent of the full-model size** (offline–online split), with a separate (often tighter) bound on the output QoI. POD-based ROMs admit analogous residual-based error indicators. **Takeaway for any ROM (CMS, Krylov, POD included): a reduced model should carry a *computable error estimate*, not just a validity band asserted by one FRF overlay.** When the tool exposes it (pyMOR, RBniCS, certified-ROM / digital-twin features), drive basis construction and trust by the bound; when it doesn't, treat the FRF/transient verification as the (weaker) substitute and **state that explicitly**.

**Rule:** every reduced model is an approximation **over a band**. Always state the validity band and verify (FRF overlay, frequency error, or a representative transient) against the full FE before trusting it.

> **Data-driven / ML reduction & surrogates.** The classical, structure-preserving reduction above (CMS, Guyan, Krylov, intrusive POD-Galerkin) has a **data-driven counterpart** — snapshot POD/PODI, DMD, non-intrusive operator inference, **hyper-reduction** (DEIM / ECSW / gappy-POD) for nonlinear ROM, ML surrogates (GP/Kriging, neural operators, PINNs, GNN simulators), and **digital twins** (executable/hybrid, FMI/FMU, calibration-to-sensor). See **`ml-surrogates-and-rom.md`** for that layer; it is not duplicated here.

---

## 3. Multibody Dynamics (MBD) — rigid + flexible bodies

### 3.1 Rigid vs. flexible

Start rigid for mechanism kinematics/gross dynamics; add flexibility where compliance affects loads, modes, or where you need component stress. **Flexible bodies** are introduced via **modal / CMS reduction** (floating-frame-of-reference formulation): the FE part is reduced (typically **Craig–Bampton**) to a modal body. In Adams, the first 6 orthonormalized CB modes are the rigid-body modes (deactivated during MBD because the floating frame already carries gross motion); the elastic CB modes capture deformation.

### 3.2 Joints, constraints, drivers, contact

- **Joints/constraints** remove relative DOF (revolute, translational, spherical, universal, cylindrical, fixed); **count DOF** (Gruebler/Kutzbach) to avoid **redundant constraints** (over-constraint → indeterminate reaction loads, solver warnings). Use **bushings/compliant connectors** instead of redundant rigid joints to remove redundancy and get physical reactions.
- **Drivers/motions** prescribe joint coordinates vs. time; ensure they are consistent (no driving a removed DOF).
- **Contact** (rigid–rigid, rigid–flex, flex–flex) needs careful stiffness/penetration/friction and small integration steps; it is the usual cause of non-convergence and runtime blow-up.

### 3.3 Co-simulation (FMI / FMU)

- **FMI (Functional Mock-up Interface)** is the open standard; a model is shipped as an **FMU** (zip with `modelDescription.xml` + compiled binaries/source).
  - **Model Exchange:** FMU exposes equations; the importing tool's solver integrates.
  - **Co-Simulation:** FMU **contains its own solver**; a **master algorithm** commands "advance by Δt" (the *communication/macro* step) and exchanges I/O only at those points.
- **Communication step size is the key knob.** Inputs/outputs update only at communication points, so too large a Δt loses accuracy/can destabilize the coupling; too small slows the run. **Practice:** start at the output interval; if inaccurate, **reduce the communication step (not the output interval)**; use variable-step / higher-order input extrapolation if the FMU supports it. FMI 3.0 adds **clocks** for discrete/multi-rate hybrid co-sim. Watch for **algebraic-loop / coupling instability** at the interface (Gauss–Seidel vs. Jacobi master schemes, signal extrapolation order).

### 3.4 Loads recovery back to FE (the deliverable of flexible MBD)

Two standard routes from an MBD run to component stress:
- **Modal stress recovery (MSR):** during reduction, **stress modes** are exported (in the MNF); MBD modal coordinates × stress modes → stress time histories directly, cheaply, for the whole event. Best for fatigue/durability over long load cases.
- **Quasi-static load superposition / inertia-relief recovery:** export joint/interface forces (and inertial loads) from MBD at critical instants and re-apply them to the full FE (often with inertia relief, §6.7) for a detailed static stress solve at peak events.

### 3.5 Top mistakes

- Redundant constraints → meaningless or oscillating reaction loads (use bushings).
- Too few flexible modes → missing compliance; wrong CB cutoff → wrong dynamics (same §1.2 rules apply to the reduction).
- Co-sim Δt too coarse → coupling error/instability mistaken for physics.
- Recovering stress from a too-truncated modal basis (residual stresses near interfaces lost).

---

## 4. Optimization

### 4.1 Types

- **Topology optimization** — find material layout in a design space (SIMP: Solid Isotropic Material with Penalization; or level-set). Output is a concept, not a final part.
- **Shape optimization** — move boundaries/control points (mesh morphing / CAD-parameter or free-form deformation) to improve an existing topology, **distinct from topology** (which decides where material *is*) and **from sizing** (which scales discrete dimensions). The canonical structural use is **stress-concentration relief**: reshape a **fillet, notch, hole, or re-entrant corner** so the peak stress drops at fixed envelope/mass — flatten the stress along the boundary (a "fully-stressed"/uniform-tangential-stress contour is the optimum signature). Keep a **minimum-radius / manufacturability constraint** (a true sharp corner is a singularity — see `meshing-convergence.md`); drive the objective by a **mesh-converged** peak/fatigue quantity, not a single-mesh hotspot; and **re-mesh and re-verify** the morphed geometry on full FE. Often the cheapest high-payoff optimization when the load path is already sound and only the local detail concentrates stress.
- **Sizing/parameter optimization** — thicknesses, beam sections, material/stiffness/damping parameters as continuous variables.

### 4.2 Topology — numerical-instability controls (must-haves)

- **Checkerboarding:** alternating solid/void from FE discretization error (worst with low-order/first-order elements). Cure with **filtering** (sensitivity or density filter) or higher-order elements.
- **Mesh dependence:** without a length scale, finer meshes invent finer members (non-converging topology). A **filter radius** imposes a **minimum member size**, making the topology mesh-independent (same topology across mesh sizes).
- **Intermediate (gray) densities:** SIMP penalty (typ. **p = 3**) pushes densities to 0/1; projection (Heaviside) sharpens edges.
- **Robust formulation** (eroded/dilated/intermediate designs) imposes min-size on **both** solid and void and accounts for manufacturing over/under-etch — the most reliable way to get a manufacturable, length-scale-controlled result.
- **Always re-interpret and re-solve:** rebuild a clean CAD/mesh from the topology result and **re-verify on full FE** (the SIMP field is not a validated stress model).

### 4.3 DOE → surrogate → optimize (metamodel-based design optimization, MBDO)

Standard efficient workflow when each FE solve is expensive:
1. **DOE / sampling** of the design space — **Latin Hypercube Sampling (LHS)** / optimal LHS is the default space-filling design (vs. full-factorial/central-composite for low dimensions).
2. **Fit a surrogate / metamodel** — **Kriging/Gaussian process** (typically needs fewer points and is more accurate than quadratic response surfaces — often ~2× accuracy for the same sample budget), RBF, polynomial RSM, or MLS.
3. **Optimize on the cheap surrogate** (global/gradient search), optionally with adaptive infill (EGO/expected improvement) to add FE points where it matters.
4. **Re-solve the optimum on the full FE** and confirm the surrogate prediction (never ship a surrogate-predicted optimum unverified).

Tooling: Ansys **optiSLang** / DesignXplorer; Siemens **HEEDS (SHERPA)**; Nastran **SOL 200** (gradient-based design opt with analytic sensitivities); PyMAPDL/PyAnsys + SciPy for custom loops.

### 4.4 Model updating / inverse parameter ID (calibration)

Adjust model parameters so the model matches **measured** data (modal frequencies/shapes, FRFs, **transient curves T(t) or strain(t)**).
- **Sensitivity-based (deterministic) updating:** compute response sensitivities to parameters (analytically in **Nastran SOL 200**, or by finite difference in tools like FEMtools / Simcenter 3D Correlation), then minimize a weighted **objective = Σ (model − test)²** (with regularization) via gradient optimizer; iterate. Run a **parameter sensitivity screen first** to select the few influential parameters — updating too many ill-conditioned parameters over-fits.
- **Transient-curve calibration:** objective is the residual between simulated and measured **time series** (e.g., thermal T(t), displacement(t)); use curve-distance metrics; beware non-identifiability (multiple parameter sets fit equally — check parameter covariance / FIM rank).
- **Adjoint / all-at-once** methods give cheap gradients for many parameters in constitutive-model discovery.
- **Inverse-ID hygiene:** hold out validation data; report identifiability (which parameters are pinned vs. degenerate); prefer the fewest physically meaningful parameters; verify the updated model on an independent load case.

### 4.5 Top mistakes

- Topology without a filter/length scale → mesh-dependent, checkerboarded, non-manufacturable result; not re-verified on full FE.
- Surrogate optimum trusted without a confirming full-FE solve.
- Updating too many correlated parameters (over-fit / non-unique); no held-out validation.
- DOE too small for the surrogate dimension (under-sampled metamodel).

---

## 5. Submodeling (cut-boundary displacement method)

**What it is.** Solve a coarse global model, then build a **fine** model of a small region (notch, fillet, weld, hole) and drive its **cut boundaries** with displacements **interpolated from the global solution** ("cut-boundary displacement" / "specified boundary displacement" method). Captures local stress concentration without globally fine mesh.

**Saint-Venant basis & the distance rule.** Justified by **Saint-Venant's principle**: local disturbances die out away from their source, so if the cut boundary is **far enough from the region of interest** the interpolated (slightly wrong) boundary displacements don't corrupt the local result. **Practice:** place cut boundaries away from any stress concentration; a good check is to split the submodel a short distance inboard of the cut so the zone of interest is buffered.

**Verification (mandatory):** compare a field that both models share on the cut boundary — typically **von Mises stress** at the cut-boundary nodes of the submodel vs. the same locations in the global model. **Agreement there proves the cut is remote enough** (St-Venant satisfied); disagreement means move the boundary outward. Also confirm the submodel result is mesh-converged in the region of interest.

**Variants:** 2D→3D and shell→solid submodeling (drive solid cut faces from shell DOF, mapping rotations to through-thickness displacement). Loads/temperatures applied inside the submodel region must be re-applied (cut-boundary displacements alone don't carry body loads in the interior).

**Top mistakes:** cut boundary too close to the concentration (St-Venant violated → wrong peak stress); forgetting to re-apply pressures/body loads/thermal in the submodel; not verifying cut-boundary stress agreement; expecting submodeling to fix a globally wrong load path (it only refines local detail of a correct global solution).

---

## 6. Loads & Boundary-Conditions Catalog

General laws first, then each load type.

**The 6-DOF rule (every static model must be fully restrained).** A static FE model must have **all 6 rigid-body DOF removed** or the stiffness matrix is singular (no solution / garbage). When the hardware itself isn't fully grounded, use a **statically determinate 3-2-1 (minimum-constraint) scheme** (3 DOF at one point, 2 at a second, 1 at a third) so you suppress rigid-body motion **without adding artificial stiffness or reactions**, or use **inertia relief** (§6.7).

**Constrain only what the hardware constrains (avoid over-constraint).** A default "Fixed Support" clamps all 6 DOF on an edge/face and is the most common artifact source: it **over-stiffens**, **inflates stress near the support**, and creates **fixed-edge stress singularities** that don't converge with mesh refinement. Prefer: realistic **elastic supports** (springs with physical stiffness), **remote displacement** via interpolation elements, or model enough of the surrounding structure to get the real compliance.

**Saint-Venant for loads/BCs:** point loads and idealized restraints create local singularities; results are only trustworthy **away** from them. Read stresses at a Saint-Venant distance from any point load, rigid tie, or sharp re-entrant corner.

### 6.1 Pressure
Distributed normal traction on faces; follows the surface (and, for "follower" pressure in large deflection, rotates with it). Mesh fine enough to resolve pressure gradients; for shells confirm pressure side/sign.

### 6.2 Bearing load
Compressive load over the **contact half** of a hole, distributed (cosine/parabolic over the loaded 180°, zero on the unloaded half) rather than a point or uniform full-circle load — represents a pin/shaft pushing on a bore. Use the solver's bearing-load feature or a cosine-weighted traction.

### 6.3 Remote force / moment via RBE3 (distributing) vs. RBE2 (kinematic)
- **RBE3 (distributing coupling / interpolation element):** transfers a force/moment/mass from a reference (independent) point to a set of (dependent) nodes as a **weighted average** — **adds NO stiffness**. Correct choice for applying a **remote load**, distributing a bolt/pin reaction, lumped-mass attachment, or pressure-to-point mapping while **preserving local flexibility**. Set up dependent/independent and **weights** correctly (geometry/area-based weights for non-uniform patches).
- **RBE2 (kinematic coupling):** all dependent nodes rigidly follow the independent node — **adds infinite stiffness**, rigidizing that region. Use for genuinely rigid connections/fixtures; **never** to apply a load over a flexible face (it will over-stiffen and distort local stress) and avoid across thermally-expanding faces (it suppresses expansion).
- **Bolted/jointed connections:** combine **RBE3 + CBUSH (or spring) + RBE3** to connect with a realistic, finite joint stiffness and avoid both the rigidity of RBE2 and rigid-body motion (preferred over bare CELAS for 6-DOF spring behavior with proper coordinate handling).

### 6.4 Bolt pretension / preload
Preload is an **internal pre-stress**, not an external force — model it correctly:
- Solid bolts: split the shank and apply a **pretension (clamp) load** on the cut faces; **two load steps** — (1) apply preload, (2) **"lock" the preload** and apply service loads (the bolt then carries only its share of the external load). This is the standard Ansys/Abaqus/Nastran-Femap procedure.
- Choice of fidelity: **solid bolt + contact** (with thread or bonded-thread contact) for bolt stress / contact status; **beam (CBEAM/BEAM188) connector** (RBE3-tied to hole edges) when only the assembly behavior matters — far smaller model; for beam connectors, preload is applied via initial strain/APDL since a direct pretension load may not be available.

### 6.5 Gravity / acceleration (body load)
Apply as a uniform acceleration field (g) over the whole model; direction in the global frame. For "g-loads"/quasi-static maneuver loads, scale acceleration. Requires a consistent **mass** model (density correct, lumped vs. consistent mass per solver).

### 6.6 Rotational / centrifugal (and spin softening / stress stiffening)
Apply **angular velocity** (and angular acceleration if spinning up) about an axis → centrifugal body force ∝ ρ ω² r. For high-speed rotors include **stress stiffening** (geometric stiffness from centrifugal pre-stress raises bending/whirl frequencies) and **spin softening** (apparent stiffness reduction); both matter for Campbell/critical-speed work.

### 6.7 Inertia relief (unconstrained models)
For a structure in free flight / on soft mounts (rocket under thrust, vehicle on a track, dropped part at the instant of balance): the static problem is singular, so the solver computes **rigid-body accelerations** that **exactly balance** the applied loads, then solves the **self-equilibrated** static problem for relative displacements/stresses.
- **Nastran:** supply a **`SUPORT`** entry listing a statically determinate set of rigid-body DOF (a point where "holding" removes all rigid-body motion), and **`PARAM,GRDPNT`** for the reference; **automatic inertia relief** picks the SUPORT for you (uses the basic origin). The **net reaction at the SUPORT should be ~0** (it only removes rigid-body motion; it carries no real load) — a non-zero SUPORT reaction means loads aren't balanced (modeling error).
- **Ansys:** Inertia Relief option in static structural; the solver balances applied loads with body-force accelerations.
- Requires a consistent mass model; only valid for loads that are (nearly) in quasi-static equilibrium with inertia (steady or slowly-varying acceleration).

### 6.8 Enforced displacement / enforced motion
Prescribe nonzero displacement (or velocity/acceleration in dynamics) at DOF — e.g., a press-fit, a measured deflection, or a settlement. In modal/transient base-excitation, enforced motion is applied via the **large-mass method** or the solver's enforced-motion (SPCD / `D` set) feature.

### 6.9 Base excitation / random & shock
For equipment on a moving base: **base excitation** (single-point or multi-point), driven by acceleration PSD (random vibration), shock response spectrum (SRS), or enforced acceleration. Use the **large-mass / large-stiffness** trick or native enforced-acceleration. Recover **relative** vs. absolute responses appropriately; for random, recover RMS / 3-sigma stresses (Miles' equation as a sanity check for SDOF-like response).

### 6.10 Imported / mapped loads (CFD, thermal, electromagnetic)
1-way coupling: map a **CFD pressure/temperature field** or **thermal solution** onto the structural mesh (node/element interpolation; conservative vs. profile-preserving mapping). Check **load summation is conserved** after mapping (total force/heat preserved), and that source and target meshes overlap the same surface. Thermal stress: import the temperature field as the thermal load with a stress-free reference temperature set correctly.

### 6.11 Symmetry / antisymmetry / cyclic symmetry
Powerful size reducers — but with strict validity limits.
- **Symmetry plane:** geometry **and** loading mirror-symmetric. On the plane, constrain the **translation normal to the plane and the two in-plane rotations** (e.g., YZ/X-normal plane: fix UX, ROTY, ROTZ). Reaction and stress on the plane are recovered correctly.
- **Antisymmetry plane:** symmetric geometry, **equal-and-opposite** loading. Constrain the **two in-plane translations and the normal rotation** (the complementary set: fix UY, UZ, ROTX for an X-normal plane).
- **Modal / buckling caveat (critical):** a single symmetric half with symmetry BCs captures **only the symmetric modes** and **misses all antisymmetric modes** (and vice-versa). **Do not use symmetry for a complete modal/buckling extraction** unless you run the half-model **twice** (once with symmetric, once with antisymmetric plane conditions) and merge the mode sets — or just model the full structure. Same trap for nonlinear/buckling where the failure mode is antisymmetric (e.g., column buckling, shear).
- **Cyclic (rotational) symmetry:** model one **sector**; couple the **low/high cyclic-edge** DOF with cyclic boundary conditions. Modal cyclic symmetry solves **per harmonic index (nodal diameter)** as separate load steps over Hermitian sector matrices; you must run **enough harmonic indices** (0…N/2) to fill the frequency band of interest, or modes are missed. Standard for bladed disks, fans, flanged rings.

### 6.12 Top BC mistakes (high-frequency in review)
- **Over-constraint / "Fixed Support" everywhere** → artificial stiffness, suppressed deflection, fixed-edge stress singularities that never converge.
- Applying loads as **point forces on single nodes** or via **RBE2** over flexible faces → local singularity / artificial stiffening (use distributed traction or RBE3).
- **Symmetry used for modal/buckling** → missed antisymmetric modes; cyclic with too few harmonic indices → missed modes.
- **Bolt preload as an external force** instead of a locked pretension → wrong load sharing.
- **Inertia relief with a non-zero SUPORT reaction** (loads not balanced) or inconsistent mass → invalid.
- Reading peak stress **at** a singular constraint/point load rather than at a Saint-Venant distance.
- Mapped CFD/thermal loads not **conservation-checked** (total force/heat not preserved) or mesh mismatch.

---

## SOURCES

CMS / superelements / DMIG
- T. Irvine, "Component Mode Synthesis, Fixed-Interface Model" (Vibrationdata tutorial). http://www.vibrationdata.com/tutorials2/component_mode_synthesis.pdf ; https://vibrationdata.wordpress.com/2013/04/30/craig-bampton-method/
- Sandia/OSTI, "Methods for Component Mode Synthesis Model Generation for Uncertainty Quantification." https://www.osti.gov/servlets/purl/1408346
- MIT (K.J. Bathe group), "Component mode synthesis with subspace iterations for controlled accuracy of frequency and mode shape solutions." https://web.mit.edu/kjb/www/Principal_Publications/Component_mode_synthesis_with_subspace_iterations_for_controlled_accuracy_of_frequency_and_mode_shape_solutions.pdf
- "Interface reduction technique for Enhanced Craig–Bampton method" (MSSP). https://www.sciencedirect.com/science/article/pii/S0888327023009822
- Craig & Chang, free-interface method of substructure coupling for dynamic analysis — *AIAA J.* 14(11):1633–1635 (1976): https://doi.org/10.2514/3.7264
- "Optimal Craig–Bampton Mode Selection for Nonlinear Flexible Multibody Analysis" (MDPI Vibration). https://www.mdpi.com/2571-631X/8/4/81
- MSC, "The New External Superelements in MSC/NASTRAN and a DMAP Alter." https://web.mscsoftware.com/support/library/conf/auc99/p02499.pdf
- Eng-Tips, External superelements / EXTSEOUT / DMIGPCH / PAX & multi-subcase. https://www.eng-tips.com/threads/external-superelements-model-reduction-questions.443388/

MOR (Guyan / Krylov / state-space)
- Krylov-subspace / moment-matching MOR (TUM, Salimbahrami & Lohmann). https://www.epc.ed.tum.de/fileadmin/w00cgc/rt/publikationen/forschungsberichte/FB_2002_Salimbahrami_Invariance.pdf
- "Order reduction of large scale second-order systems using Krylov subspace methods" — Salimbahrami & Lohmann, *Linear Algebra Appl.* 415:385–405 (2006): https://doi.org/10.1016/j.laa.2004.12.013

Multibody dynamics & co-simulation
- Hexagon/MSC, "Flex body dynamics and modal stress recovery using Adams" (MNF, CB reduction, stress modes). https://hexagon.com/support-success/manufacturing-intelligence/design-engineering-support/training/flex-body-dynamics-and-modal-stress-recovery-using-adams
- "Modal reduction procedures for flexible multibody dynamics" (Multibody Syst. Dyn.). https://link.springer.com/article/10.1007/s11044-020-09770-w
- "Friction Models and Stress Recovery Methods in Vehicle Dynamics Modelling." https://link.springer.com/article/10.1007/s11044-005-4183-2
- FMI standard — Co-Simulation & Model Exchange specs. https://fmi-standard.org/assets/releases/FMI_for_ModelExchange_and_CoSimulation_v2.0.pdf ; https://fmi-standard.org/assets/releases/FMI_for_CoSimulation_v1.0.pdf
- Claytex, "FMI basics: Co-simulation vs. Model Exchange." https://www.claytex.com/tech-blog/fmi-basics-co-simulation-vs-model-exchange/
- FMI 3.0 & FMPy cheatsheet (communication step / clocks). https://dr-clementcoic.github.io/fmi-cheat-sheet/

Optimization & model updating
- Sigmund & Petersson, "Numerical instabilities in topology optimization (checkerboards, mesh-dependencies, local minima)" — *Struct. Optim.* 16(1):68–75 (1998): https://doi.org/10.1007/BF01214002
- "Checkerboard and minimum member size control in topology optimization" (Struct. Multidisc. Optim.). https://link.springer.com/article/10.1007/s001580050179
- "Analytical relationships for imposing minimum length scale in the robust Topology Optimization formulation." https://arxiv.org/pdf/2101.08605
- "Kriging model combined with Latin hypercube sampling for surrogate modeling" — *ISQED* 2009:554–558 (IEEE): https://doi.org/10.1109/ISQED.2009.4810354
- "A tutorial on Latin hypercube design of experiments" — Viana, *Qual. Reliab. Eng. Int.* 32:1975–1985 (2016): https://doi.org/10.1002/qre.1924
- FEMtools / Nastran SOL 200 sensitivity-based model updating. https://www.invicom.com/solutions/cae-software/model-updating.html
- NASA/TM-20220016410, "Structural Model Tuning Tool: User's Reference Manual." https://ntrs.nasa.gov/api/citations/20220016410/downloads/20220016410%20FINAL.pdf
- "Reduced and All-at-Once Approaches for Model Calibration and Discovery in Computational Solid Mechanics." https://arxiv.org/pdf/2404.16980

Submodeling
- Ansys Innovation Courses, "Performing Submodeling in Ansys Mechanical — Lesson 6." https://innovationspace.ansys.com/courses/courses/numerically-accurate-results/lessons/performing-submodeling-in-ansys-mechanical-lesson-6/
- PADT, "Submodeling in ANSYS Mechanical: Easy, Efficient, and Accurate." https://www.padtinc.com/2013/08/14/submodeling_ansys_mechanical/
- SimuTech, "Step by Step Guide for 2D to 3D Submodeling in Ansys Mechanical." https://simutechgroup.com/step-by-step-guide-for-2d-to-3d-submodeling/
- BETA CAE, "Using submodeling technique…" (cut-boundary stress agreement check). https://www.beta-cae.com/events/c2pdf/H2-6-2.pdf

Loads & boundary conditions
- Predictive Engineering, "NX Nastran Connection Elements (RBE2, RBE3 and CBUSH)" white paper. https://www.predictiveengineering.com/sites/default/files/predictive_engineering_white_paper_on_nx_nastran_connection_elements_rbe2_rbe3_and_cbush_rev-1.pdf
- Fidelis FEA, "Kinematic (RBE2) vs Distributing (RBE3) Coupling." https://www.fidelisfea.com/post/what-is-the-difference-between-a-kinematic-rbe2-and-a-distributing-rbe3-coupling-in-fea
- EnDuraSim, "Nastran RBE2 vs RBE3 Rigid Elements." http://www.endurasim.com.au/wp-content/uploads/2015/02/EnDuraSim-Rigid-Elements.pdf
- Gantovnik, "Nastran Tips #115: When to Use RBE2 vs. RBE3." https://gantovnik.com/bio-tips/2020/09/115-rbe3-vs-rbe2/
- LEAP Australia, "An Overview of Methods for Modelling Bolts in ANSYS." https://www.leapaust.com.au/blog/fea/an-overview-of-methods-for-modelling-bolts-in-ansys/
- Krolo et al., "Guidelines for Modelling the Preloading Bolts… (FEM)." https://onlinelibrary.wiley.com/doi/10.1155/2016/4724312 ; Ansys, "Bolt Pretension Object." https://innovationspace.ansys.com/courses/wp-content/uploads/sites/5/2020/10/2.2.3_Bolt-Pretension-Object_new_brand.pdf
- ESA Corp, "NASTRAN Inertia Relief" (SUPORT, GRDPNT, automatic IR). https://www.esacorp.com/nastran_hints_toc/nastran-inertia-relief/
- "A study of inertia relief analysis" — Liao, AIAA 2011-2002, 52nd AIAA/ASME/ASCE/AHS/ASC SDM Conf. (2011): https://doi.org/10.2514/6.2011-2002
- Fidelis FEA, "Symmetry In FEA — Sym-plify Your Models!" (sym/antisym DOF table, modal caveat). https://www.fidelisfea.com/post/symmetry-in-fea-sym-plify-your-models
- Ansys, "Modal Cyclic Symmetry Analysis" / "Cyclic Symmetry Analysis Guide." https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/ans_cycsym/advcycmodalans.html ; https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/pdf/Ansys_Mechanical_APDL_Cyclic_Symmetry_Analysis_Guide.pdf
- Engineering.com, "Avoiding singularities in FEA boundary conditions"; Eng-Tips, "3-2-1 Constraints approach in FEA." https://www.engineering.com/avoiding-singularities-in-fea-boundary-conditions/ ; https://www.eng-tips.com/threads/3-2-1-constraints-approach-in-fea-analysis.239491/
- Siemens Community, "How to constrain structural models effectively while avoiding artificial stiffness in Simcenter 3D." https://community.sw.siemens.com/s/article/How-to-constrain-structural-models-effectively-while-avoiding-artificial-stiffness
