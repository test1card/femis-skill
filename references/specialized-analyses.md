# Specialized analyses (overview + router, plus the misc methods that live here)

Depth for the one-liners in SKILL.md, **and the router to the dedicated failure-discipline files**. Each failure
discipline (buckling, fatigue, composites, plasticity, fracture, explicit/crash) now has its own deep reference —
this file links to it so there is a **single source of truth** — and keeps full content for the analyses that
have no dedicated file (submodeling, hyperelastic, cyclic symmetry, creep, topology/DOE). Each entry is a pointer
to the right method + the trap that bites most.

## Dynamics

- **Modal:** extract enough modes that **cumulative effective mass ≥ 80–90%** in each excitation direction; include any mode >1–2% effective mass; cover to ~1.5× max excitation frequency. A free-free run must give **6 rigid-body modes ≈ 0 Hz** first (under/over-constraint check).
- **Prestressed (preloaded) modal:** solve the static load first, carry the stress field into the modal (stress stiffening) — **tension raises, compression lowers** natural frequencies; mode shapes unchanged. Essential for tensioned/membrane/cable/thin and **spinning** structures (add **spin softening**).
- **Damping:** define realistically (modal / Rayleigh α,β); results are sensitive near resonance.
- **Harmonic / frequency response:** cluster frequency points near each resonance; mode-superposition (fast, linear) vs full method.
- **Random vibration (PSD):** GRMS from the input ASD/PSD; **design to 3σ = 3×GRMS** (Gaussian, conservative). **Miles' equation** `GRMS ≈ √(π/2·f_n·Q·ASD)` (Q = 1/(2ζ)) for a quick SDOF estimate; full FE random response for multi-mode. Report 1σ then apply 3σ for margins.
- **Implicit vs explicit:** implicit (unconditionally stable, large steps) for static/quasi-static/slow dynamics; explicit for short (<~1 s) high-rate events (impact/drop/crash) — conditionally stable, **Δt ≈ L_min/c**, so keep the smallest element reasonable. Watch artificial/hourglass energy < ~5–10% of internal. → full setup (contact, erosion, hourglass, mass-scaling, SPH/ALE/CEL, blast/drop/ballistic) in **`explicit-dynamics-impact.md`**.
- **Rotordynamics:** solve the **speed-dependent** eigenproblem with **gyroscopic** effects (modes split forward/backward whirl); build a **Campbell diagram** (intersect 1×/2× lines = critical speeds); include bearing/foundation flexibility. A zero-speed modal is **not** the critical speeds.

## Failure-discipline files (single source of truth)

These five topics each have a **dedicated deep reference** — go there for method selection, setup, and acceptance
gates. (Explicit dynamics / crash → see the Dynamics "implicit vs explicit" bullet above and
**`explicit-dynamics-impact.md`**.)

- **Buckling / stability** → **`buckling-stability.md`** — linear eigenvalue buckling over-predicts (LBA upper bound); LBA vs GNA-GNIA vs GMNIA, knockdown factors, imperfection seeding from the 1st mode, post-buckling path-following, stiffened panels. (Symmetry BCs filter antisymmetric modes — invalid for buckling.)
- **Fatigue / durability** → **`fatigue-durability.md`** — S–N / ε–N, rainflow + Miner, mean-stress (Goodman/Gerber/Soderberg), notch correction, multiaxial critical-plane, spectral (Dirlik), TMF, FKM; welds via hot-spot structural stress.
- **Composites / laminates** → **`composites-analysis.md`** — Tsai–Wu vs Hashin/Puck/LaRC, progressive damage with crack-band regularization, delamination/VCCT/CZM, sandwich/honeycomb modes, draping, environmental knockdowns. (Constitutive ABD/criteria live in `material-modeling.md §5–6`.)
- **Plasticity / inelastic assessment** → **`plasticity-inelastic-assessment.md`** — true stress–strain, isotropic/kinematic/Chaboche hardening, shakedown/ratcheting/Bree, limit-load, ASME VIII-2 elastic-plastic route, stress linearization, springback. (Constitutive side in `material-modeling.md §2`.)
- **Fracture (LEFM / EPFM)** → **`fracture-mechanics.md`** — K / J extraction, contour/domain-integral path-independence gate, contour-integral vs VCCT vs XFEM vs CZM vs SMART remesh growth, crack-tip meshing, fatigue crack growth, mixed-mode direction.

## Submodeling (cut-boundary displacement method)

Resolve a local stress concentration without re-solving the whole model: run coarse global, map the global
**displacement field onto the submodel's cut boundaries** (MAPDL `CBDOF`/`SUBMODELING`). **Cut boundary must be
≥1 characteristic dimension from the detail** (Saint-Venant); **verify** by checking cut-face stresses match the
global model.

## Hyperelastic (rubber/elastomer)

Fit from **multi-mode test data** (uniaxial+biaxial+shear; ≥2 curves for Mooney-Rivlin, ≥3 for Ogden) —
uniaxial-only fits extrapolate badly. Mooney-Rivlin ≤~200% strain, Ogden/Yeoh for large strain. Near-incompressible
(ν≈0.5) → mixed u–P / hybrid elements; check Drucker stability.

## Cyclic symmetry

Model one sector of a rotationally periodic part (rotor, ring, bladed disk) — master↔slave face mapping through
the sector angle; large runtime/RAM savings (`CYCLIC`). Still constrain rigid-body motion. **Modal must sweep
harmonic indices** to capture all modes in range.

## Creep (high-temp, time-dependent)

Model **primary + secondary** with **Norton-Bailey** (time- or strain-hardening); tertiary = impending rupture,
not usually solved. Use when T/T_melt high or for long-duration loads; needs temperature-dependent creep
constants; check against ASME-style limits (e.g. 1% creep strain in 100,000 h).

## Topology / DOE / optimization

DOE → response surface → sensitivity → optimize (far cheaper than brute force); **topology optimization** for
min-mass layout. **Always re-solve the optimum on a full FE model** (the surrogate is an approximation); verify
each sampled design converged. Full optimizer/calibration tool map → `optimization-calibration.md`.
