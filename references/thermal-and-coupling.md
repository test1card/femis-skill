# Thermal & Coupled Thermo-Mechanical Analysis — Practitioner Brief

Best-practices reference for a public FEM/CAE Agent Skill. Generalizable across Ansys
Mechanical/MAPDL, Simcenter 3D / Simcenter Nastran (TMG), and Thermal Desktop
(SINDA/FLUINT). Numbers are defaults/rules-of-thumb; always confirm against the actual
solver version and the physics of the model. Sources at end.

---

## 1. Steady vs transient — and when lumping is legitimate

- **Steady-state** when only the end equilibrium matters and all BCs are time-invariant.
  MAPDL `ANTYPE,STATIC`; Simcenter/NX Nastran SOL 153; Thermal Desktop STEADY. No `[C]`
  capacitance matrix is assembled; the result is path-independent.
- **Transient** when BCs vary in time, when thermal mass / time-to-equilibrium matters, or
  when the *deformation-driving signal* is a moving spatial gradient (see §9). MAPDL
  `ANTYPE,TRANS` + `TIMINT,ON`; SOL 159; TD transient. Requires a capacitance matrix
  (ρ·cp) and an initial condition.
- **Lumped-capacitance test — Biot number.** `Bi = h·L_c / k`, with characteristic length
  `L_c = V/A_s`. **`Bi < 0.1` → internal gradients < ~5%; a single lumped node is valid**
  (temperature is a function of time only, not position). `Bi ≥ 0.1` → you must mesh and
  resolve the spatial gradient. This is the classic Incropera criterion and the dividing
  line between a SINDA-style network node and a meshed FE region.
- **Lumped-parameter caution (network/SINDA practice):** a lumped node averages out
  intra-region gradients. A multi-node region with internal conductors is required where
  `Bi ≥ 0.1` or where you need the gradient for downstream thermo-elastic distortion.

---

## 2. Transient time-stepping — bounded on BOTH sides

The single most common transient-thermal error is mis-set Δt. It is bounded above *and*
below, which is counter-intuitive.

- **Upper bound — Fourier number.** `Fo = α·Δt / L²` with α = k/(ρ·cp), L the smallest
  element dimension in the heat-flow direction. **Target `Fo ≤ 0.5` at the
  steepest-gradient element** for accuracy. (For *explicit* schemes `Fo ≤ 0.5` is a hard
  stability limit; for the implicit schemes below it is an accuracy/oscillation guideline,
  not a stability requirement.) Practical recipe: take a small, correct **initial step**,
  then let automatic time-stepping grow it.
- **Lower bound — the too-small-Δt oscillation (counter-intuitive).** For a *given mesh*, a
  Δt that is too **small** produces spurious spatial **temperature oscillations / unphysical
  dips** (e.g. nodes dipping below the initial or ambient temperature) at sharp fronts. The
  governing relation is between element size and time step: roughly `Δt_min ∝ ρ·cp·Δx² / k`
  (i.e. `Fo` must not fall too low locally). **The fix is to refine the mesh in the
  high-gradient zone, not to keep shrinking Δt** — "using a smaller time step for the same
  mesh will often give worse results." Higher-order (quadratic) thermal elements overshoot
  more at sharp gradients than linear elements.
  - In MAPDL this is governed by the **oscillation limit** in automatic time stepping
    (`TINTP` `OSLM`/`TOL`), default oscillation factor **f = 1/2**; the per-step oscillation
    magnitude should stay below ~0.5.
- **Time integration scheme.**
  - **Backward Euler (θ = 1, fully implicit)** — unconditionally stable, no oscillation,
    1st-order accurate in time. This is the robust default for stiff/nonlinear thermal
    (radiation, phase change). MAPDL `TINTP` THETA → 1.0.
  - **Crank–Nicolson (θ = 0.5, trapezoidal)** — 2nd-order accurate, but **only A-stable, not
    L-stable**: it admits *decaying spurious oscillations* when `α·Δt/Δx²` is large
    (> ~0.5, Von Neumann). Use it for smooth problems where accuracy matters; back off to
    backward Euler (or refine) if you see ringing.
- **Initial condition.** Always set a physically correct initial temperature field (`IC`, or
  a `TIMINT,OFF` static step to establish T₀ then switch `TIMINT,ON`). A wrong/uniform IC
  contaminates the early transient — which is exactly the part that drives distortion.

---

## 3. Boundary conditions: conduction / convection / radiation

- **Conduction** — interior physics; the conductivity matrix. Across joints use a **thermal
  contact conductance** (§6), not perfect bonding, unless verified.
- **Convection** — `q'' = h·(T − T∞)`. Supply h (often T- and orientation-dependent);
  in vacuum/space, **convection ≈ 0** — radiation dominates.
- **Radiation** — see §4. The nonlinear, error-prone BC.
- **Applied flux / sources** — solar, internal dissipation, heater power. Distinguish
  **absorbed solar (α·G)** from re-emitted IR.

---

## 4. Radiation — the T⁴ nonlinearity

Radiation makes the system nonlinear (`q ∝ σ·ε·T⁴`), so it **requires an iterative
solution** and converges slowly. Get the bookkeeping right first, then help convergence.

**Setup correctness (most "non-convergence" is really a setup bug):**
- **Absolute temperature.** Stefan–Boltzmann `σ = 5.67×10⁻⁸ W/m²K⁴` acts on *absolute*
  temperature. If the model is in °C, set the offset (MAPDL `TOFFST`/`STEF`,
  Nastran `PARAM,TABS` + `PARAM,SIGMA`). A missing offset is a silent, large error.
- **Distinct solar α vs IR ε.** Surfaces are spectrally selective: **solar absorptance α
  (short-wave) ≠ infrared emittance ε (long-wave)**. Using one value for both is a classic
  mistake — e.g. white paint / OSRs have low α, high ε by design.
- **Enclosure view factors must satisfy the laws:** **summation (row-sum) rule
  Σⱼ Fᵢⱼ = 1** for every surface i in a closed enclosure (include self-view Fᵢᵢ for concave
  surfaces), and **reciprocity Aᵢ·Fᵢⱼ = Aⱼ·Fⱼᵢ**. **Check row-sums → 1.0** and confirm ΔF
  between successive ray-count/resolution settings is below tolerance before trusting RADKs.
- **Radiosity** = total energy leaving a gray-diffuse surface (emission + reflection); the
  net-exchange equations are solved for radiosity J, then coupled to conduction.

**View-factor / exchange-factor computation:**
- **Monte-Carlo ray tracing** — fires many random rays per surface; handles specularity,
  transmission, and articulated geometry; statistically respects the summation property;
  accurate but slower and noisy (error ∝ 1/√N rays). Thermal Desktop / RadCAD writes
  exchange factors (RADKs) consumed by SINDA.
- **Progressive radiosity** — faster, deterministic, gray-diffuse; good first pass.
- **Hemicube / analytic** (Ansys Mechanical) — raise hemicube/ray resolution until row-sums
  and ΔF converge.

**Convergence aids (in priority order):**
1. **Ramp loads** and use small increments / substeps (radiation is nonlinear — default
   ramping helps).
2. **Start from an initial T near the expected final T** (cuts the T⁴ swing the solver must
   chase).
3. **Under-/over-relax the radiative flux.** MAPDL `RADOPT` `FLUXRELX` default **0.1** for
   stability; raise it (toward ~0.5) for non-radiation-dominant problems to speed up.
4. Tighten the radiosity/temperature tolerance only after the above.
5. **Check for missing or wrong radiation surfaces/contact pairs** — the usual real culprit,
   especially on thin parts where front/back faces get confused.
- **Recompute exchange factors (RADKs / view factors) when geometry articulates or when
  optical properties (α, ε) are temperature-dependent** — they are *not* automatically
  refreshed inside a thermal solve.

---

## 5. Steep cp(T) and phase change — use enthalpy, not cp·ΔT

- **Enthalpy method.** Where cp varies steeply or latent heat L is released over a
  temperature range (melt/freeze, sharp cryogenic cp features), specify total **enthalpy
  H(T) = ∫ρ·cp dT (+ latent heat)** rather than a pointwise cp. The enthalpy formulation is
  the stable/robust way to capture latent heat and steep cp without the energy error and
  oscillation that a differentiated-cp approach produces. **If a supplier gives *relative*
  enthalpy, add the reference Href** so the absolute curve is correct.
- **Nonlinear formulation: Full vs Quasi (critical trap).** In Ansys transient thermal the
  default **"Quasi" nonlinear formulation can ignore the enthalpy curve / a steeply varying
  cp(T)**, silently giving wrong stored energy. **Set Nonlinear Formulation = Full**
  (`THOPT,FULL`, or Analysis Settings ▸ Nonlinear Controls) for any phase change or sharp
  cryogenic cp(T). Phase-change/enthalpy solves are nonlinear → full **Newton–Raphson**;
  keep line search `LNSRCH,ON`; choosing a good tangent matrix matters when L is large.

---

## 6. Thermal contact conductance (vacuum / cryo)

- Across a real (bolted/pressed) joint, heat crosses only through micro-asperity contacts +
  any interstitial medium. Model it as a **contact conductance h_c (W/m²K)** or a joint
  resistance, **never as perfectly bonded**, unless verified.
- **In vacuum the gas-conduction path vanishes** → conductance drops; **at cryo it drops
  steeply further** as contact spots and material conductivity shrink.
- **Drivers:** contact pressure (↑ pressure → ↑ conductance), surface roughness
  (↓ roughness → ↑ conductance), interface temperature, and interstitial/filler material.
- **Uncertainty is large and a primary risk.** Predictions are typically **±25% for
  isotropically rough surfaces, ±50% for strongly anisotropic** ones; pressed contacts show
  inherent non-repeatability from work-hardening, plastic deformation, and non-uniform
  pressure. **Treat h_c as a tunable calibration parameter** bounded by literature/test, and
  correlate it against measured ΔT across the joint. (Cryogenic contact-conductance data,
  e.g. Al and stainless 1.6–6 K under bolt load, exist for bounding.)

---

## 7. Energy-balance closure — the universal sanity gate

For any thermal solve, **in − out − stored ≈ 0** must close to **< ~1%**. Steady: Σ inputs =
Σ outputs (radiated + convected + conducted away). Transient: net flux = rate of change of
stored energy. **Verify closure before trusting any temperature or downstream stress
result** — a large imbalance flags a missing sink/source, a bad BC, or unconverged
radiation.

---

## 8. Spacecraft / vacuum / cryogenic specifics

**MLI (multi-layer insulation):**
- Modeled by a single lumped **effective emittance ε\*** rather than layer-by-layer.
- ε\* is **dominated by workmanship** — seams, penetrations, edges, compression — and is
  **hard to predict.** Reported values: ~**0.01–0.05** for large well-made blankets, but
  **0.05–0.30 for small/complex blankets** (e.g. propellant lines). It is the **dominant
  thermal-model uncertainty** and a **non-tunable-from-analysis parameter**: the only
  reliable way to get the as-built ε\* is **system-level thermal-vacuum test**, ideally with
  extra non-flight thermocouples. **Bound ε\*** (carry a hot and a cold value).

**Thermal margins (uncertainty + design margin):**
- Carry **thermal uncertainty margins**, conventionally on the order of **±10–20 K** (plus a
  separate design margin) on top of worst-case predictions.
- Representative **GEVS-style** numbers: **+10 °C of worst-case predictions + 5 °C modeling
  margin**, with a **minimum +15 °C qualification margin** over worst-case predicts.
- **Correlation buys margin back:** once the model is correlated to test, allowable cycling
  ranges/margins can be **reduced** (e.g. operational predictions to +10 °C, survival to
  +0 °C). But a residual correlation error matters: a 10 °C uncertainty margin with a 5 °C
  correlation error can drop the probability of staying within limits from ~93% → ~64%.

**TVAC correlation (mandatory before flight predictions are trusted):**
- Correlate the model to a **thermal-vacuum / thermal-balance test of at least one hot–cold
  cycle.** Tune **ε\*, contact conductances, and heater powers** until predicted vs measured
  agree within the margin (typical correlation goal: a few K mean / RMS).
- **Verify radiative couplings independently of conductive ones** — they trade off and can
  compensate each other, hiding two offsetting errors. **Recompute RADKs** after any
  geometry or optical-property change.
- Governed by standards: **ECSS-E-ST-31** (thermal control) and the **ECSS-E-HB-31-03A**
  thermal-analysis handbook; **NASA-STD-7002 / GEVS** and **ECSS-Q-ST-70-02C** for test.

**ECSS-E-ST-31C thermal margin & correlation discipline (apply the governing standard's
numbers — don't invent margins):**
- **Carry a thermal uncertainty margin on every prediction.** Per **ECSS-E-ST-31C**, design
  to worst-case predicts plus an **uncertainty margin commonly on the order of ±10 K**
  (mission- and phase-specific — the actual number comes from the project's thermal
  requirement, not a default). This is the analysis-side allowance for everything the model
  cannot know exactly (optical properties, ε\*, contact conductance, environment).
- **Budget the model-correlation error to ≤ ~½ the uncertainty margin** — i.e. **≈ ±5 K
  typical** when the margin is ±10 K. The correlation error eats into the same allowance, so
  if the model disagrees with test by more than about half the margin, the remaining margin
  is no longer trustworthy (a ±10 K margin riding on a 5 K correlation error already erodes
  the probability of staying within limits — see the margin/correlation trade-off above).
- **Correlate to thermal-balance / TVAC test in BOTH steady-state AND transient before
  crediting predictions.** A steady-state-only correlation can match end temperatures while
  the time constants (capacitance × resistance) are wrong, so the *transient* gradients — the
  ones that drive thermo-elastic distortion (§9) — stay uncorrelated. Tune ε\*, contact
  conductances, and heater powers against measured steady **and** transient data.
- **Bottom line: an uncorrelated thermal model does not earn its margin.** Until correlated,
  predictions carry only the unverified uncertainty allowance and cannot be credited for
  flight. This is the thermal-domain instance of the model-credibility discipline in
  `references/vv-uq.md` (scale rigor to consequence; a result is only as credible as its
  weakest factor — here, validation/correlation). Do the correlation **per-sensor (local),
  not by tier/region mean** (§9): a region-averaged match can hide the intra-region gradient
  that both bends the structure and signals an uncorrelated conduction/radiation split.

**Cryogenic modeling:**
- **CTE for thermal strain: use `ε_th = ∫ α(T) dT`, NOT `α·ΔT`.** α(T) drops toward zero as
  T→0; a constant-α (or α·ΔT from room temperature) overstates contraction badly. Use the
  integrated contraction (e.g. NIST cryogenic CTE integrals).
- Supply **T-dependent k(T) and cp(T) over the full range; do not flat-extrapolate.** For
  metals k(T) often rises then falls (peak well below 100 K, RRR-dependent — e.g. OFHC
  copper); **cp collapses toward T→0** (Debye T³ for the lattice + linear electronic term).
  A wrong low-T k or cp wrecks both steady gradients and transient time constants.
- Joint conductance drops steeply at cryo (§6); radiation `∝ T⁴` becomes very weak, so small
  parasitic conduction paths dominate the heat leak.
- NIST cryogenic material-property fits (4–300 K) are the standard source; quoted
  uncertainties up to ~5% (sub-0.2% for well-characterized materials).
- **Thermal Desktop / SINDA:** Monte-Carlo ray trace (accurate, slower) vs progressive
  radiosity (fast); recompute exchange factors when optical properties are T-dependent or
  geometry articulates.

---

## 9. Thermo-mechanical coupling

**One-way sequential (the standard 95% case).** Valid when the temperature field can be
solved *without* knowing the stress/deformation (it almost always can).
- **MAPDL:** solve thermal → write `.rth`; in the structural model
  `LDREAD,TEMP,,,<time>,,'<job>','rth'` imports nodal temperatures as a body load. Requires
  a **reference (strain-free) temperature `TREF`** and a CTE **`MP,ALPX`** (use the
  *secant/integrated* α consistent with §8). The thermoelastic load is `{F} ∝ α·(T − TREF)`.
- **Simcenter / NX Nastran:** SOL 153 temps → **`TEMPERATURE(LOAD)`** in a SOL 101/106 run;
  material CTE on `MAT1` field `A`; `PARAM,TABS`. **SOL 401 / 402** do multi-step / direct
  thermo-mechanical coupling when needed. For thermal expansion of RBE1/RBE2/RBE3 set the
  relevant option to **LAGRAN**.
- **Abaqus** analog: `*TEMPERATURE` read from the heat-transfer `.odb` (predefined field) in
  a sequentially coupled stress step.

**Mesh mapping.** **Thermal and structural meshes need NOT match** — temperatures are
**interpolated** onto the structural mesh (e.g. 1st-order thermal field → 2nd-order
structural elements is fine). Easiest/safest is to **reuse the same mesh**; if not,
verify the interpolation didn't smear sharp gradients.

**Direct / strong coupling — use only when justified.** Use coupled-field elements
(MAPDL `SOLID226/227`, Abaqus coupled temp-displacement, SOL 401/402) only when there is
genuine **two-way feedback**: deformation changes the thermal problem (contact
opening/closing alters conductance, gap radiation, frictional/plastic heating, large
geometry change). It is more expensive and harder to converge. On coupled-field elements
you must define **both** thermal and mechanical material properties.

**Transient-gradient caveat (the subtle, high-value point).** The *settled/soaked* field is
often near-isothermal → small, uniform expansion → little distortion. **The distortion-
driving signal lives in the transient spatial gradient** (∇T during cool-down/warm-up).
Therefore:
- Run the structural import at the **worst-gradient time slice(s)**, not just steady state.
- **Validate the spatial temperature field per-sensor (local), not by tier/region mean** — a
  region-averaged fit can match the mean while hiding the intra-region gradient that
  actually bends the structure.

---

## 10. Top mistakes (quick-reference)

1. Lumping a region with **Bi ≥ 0.1** (hides the internal gradient that drives distortion).
2. **Too-small Δt** on a coarse mesh → unphysical temperature oscillation/dips; shrinking Δt
   makes it *worse* — **refine the mesh** instead. (And too-large Δt → `Fo > 0.5` inaccuracy.)
3. Radiation in °C with **no absolute-temperature offset** → silent gross error.
4. **One value for solar α and IR ε.**
5. Not checking **view-factor row-sums → 1** / not recomputing RADKs after geometry/optics
   change.
6. Phase change / steep cp(T) left on **Quasi** formulation → enthalpy/cp ignored; use
   **Full** + enthalpy.
7. Treating bolted/pressed joints as **perfectly bonded**; ignoring the ±25–50% h_c
   uncertainty and the vacuum/cryo conductance drop.
8. Skipping the **energy-balance < 1%** check.
9. Cryo CTE via **α·ΔT instead of ∫α dT**; flat-extrapolating k(T)/cp(T) below the data.
10. Flying an **un-correlated** spacecraft model / no TVAC tuning of ε\*, h_c, heater power;
    no thermal margin.
11. Thermo-mechanical import at **steady state only**, missing the worst transient gradient;
    validating temperature on **region-mean instead of per-sensor**.
12. Wrong/missing **TREF**, or CTE inconsistent with the temperature units / reference.

---

## SOURCES

Heat-transfer fundamentals (Biot, lumped capacitance, Fourier, view-factor laws):
- Incropera & DeWitt, *Fundamentals of Heat and Mass Transfer* (lumped-capacitance `Bi < 0.1`
  criterion). Summary: https://www.numberanalytics.com/blog/mastering-lumped-capacitance-heat-transfer
- U. Waterloo ECE309, *Conduction Heat Transfer* notes (Bi, lumped analysis):
  https://www.mhtlab.uwaterloo.ca/courses/ece309/lectures/notes/S16_chap5_web.pdf
- View factors — summation & reciprocity rules: Incropera & DeWitt, *Fundamentals of Heat
  and Mass Transfer* (radiation-exchange chapter), and Modest, *Radiative Heat Transfer*
  (Academic Press) for the view-factor algebra; Martinez (UPM) radiation view-factor notes
  http://imartinez.etsiae.upm.es/~isidoro/tc3/Radiation%20View%20factors.pdf . Orientation:
  https://fiveable.me/heat-mass-transfer/unit-4/view-factors-radiation-exchange-surfaces/study-guide/ysU8UG7xckoFrVHN ·
  Wikipedia — View factor, https://en.wikipedia.org/wiki/View_factor

Transient time-stepping, oscillation, Crank–Nicolson vs backward Euler:
- "Convergency and Stability of Explicit and Implicit Schemes in the Simulation of the Heat
  Equation," *Applied Sciences* 11(10):4468 (Fo/Δx² ratio, oscillation):
  https://doi.org/10.3390/app11104468
- "Spurious oscillations reduction in transient diffusion… FEM," *Scientific Reports* (2022):
  https://www.nature.com/articles/s41598-022-23185-x
- Crank–Nicolson method (2nd-order, A-stable, oscillation when α·Δt/Δx² large) — Crank &
  Nicolson (1947) *Proc. Camb. Phil. Soc.* 43:50 (primary); LeVeque, *Finite Difference
  Methods for Ordinary and Partial Differential Equations* (SIAM, 2007). Orientation:
  Wikipedia — Crank–Nicolson method, https://en.wikipedia.org/wiki/Crank%E2%80%93Nicolson_method
- Ansys MAPDL Theory — Automatic Time Stepping / oscillation limit (`TINTP` OSLM, f=1/2):
  https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_thry/thy_tool6.html
- SimuTech, *Thermal Time-Transient Loading and Solution in Ansys* (element-size vs min Δt;
  smaller Δt on same mesh gives worse results):
  https://simutechgroup.com/thermal-time-transient-loading-and-solution-in-ansys/
- LinkedIn (E. Stamper), *Calculating Solution Settings for a Transient Thermal Analysis*:
  https://www.linkedin.com/pulse/calculating-solution-settings-transient-thermal-analysis-eric-stamper

Radiation / radiosity / view-factor convergence:
- Ansys MAPDL Thermal Analysis Guide 2025 R1 (radiosity solver, ramping, RADOPT):
  https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/pdf/ANSYS_Mechanical_APDL_Thermal_Analysis_Guide.pdf
- Ansys Theory — Radiosity Solution Method (FLUXRELX default 0.1, segregated solve):
  https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_thry/thy_heat5.html
- Sheldon Imaoka (Ansys), *ANSYS Tips & Tricks: Radiosity Solver in WB* — vendor memo, no
  canonical URL; see the Ansys MAPDL Thermal Analysis Guide and Ansys Theory radiosity refs above
  for the authoritative treatment.
- NASA TM, *Development and Verification of Enclosure Radiation Capabilities* (row-sum,
  reciprocity, MC vs progressive): https://ntrs.nasa.gov/api/citations/20160006076/downloads/20160006076.pdf
- C&R Technologies RadCAD (Monte-Carlo vs progressive radiosity; SINDA RADK output):
  https://www.crtech.com/products/radcad
- Verification of 2-D Monte-Carlo ray-trace for radiation (error ∝ 1/√N):
  https://arxiv.org/pdf/1810.05204

Phase change / enthalpy / nonlinear formulation:
- "An enthalpy-based finite element method for nonlinear heat problems involving phase
  change," *Computers & Structures* (2002):
  https://www.sciencedirect.com/science/article/abs/pii/S0045794901001651
- "An implicit mixed enthalpy–temperature method for phase-change problems":
  https://doi.org/10.1007/s00231-006-0090-1

Thermal contact conductance (vacuum / cryo):
- "Measurement of thermal contact resistance and the design of thermal contacts at cryogenic
  temperatures," *Cryogenics* (2024):
  https://www.sciencedirect.com/science/article/abs/pii/S0011227524001425
- "Experimental characterization of cryogenic contact resistance," *Cryogenics* (2022):
  https://www.sciencedirect.com/science/article/abs/pii/S0011227522001692
- Hasselström, *Thermal Contact Conductance in Bolted Joints* (Chalmers MSc; ±25%/±50%
  prediction bands): https://publications.lib.chalmers.se/records/fulltext/159027.pdf
- "Empirical Evaluation of TCR of Bolted Joint Configurations under Vacuum" — Esfahani, Sedghi & Karimian,
  64th Int. Astronautical Congress, Beijing (2013) *[background — no primary DOI registered]*.
- FNAL/USPAS, *A review of thermal contact resistance* (cryo):
  https://uspas.fnal.gov/materials/21onlineSBU/Background/Further%20reading%20-%20Contact%20resistance%20at%20cryo%20temperature.pdf

Spacecraft thermal — MLI, margins, TVAC correlation, standards:
- ECSS-E-ST-31C, *Thermal control – general*:
  https://ecss.nl/standard/ecss-e-st-31c-thermal-control/ ·
  http://everyspec.com/ESA/download.php?spec=ECSS-E-ST-31C.048170.pdf
- ECSS-E-HB-31-03A, *Thermal analysis handbook* (Nov 2016):
  https://ecss.nl/wp-content/uploads/2016/11/ECSS-E-HB-31-03A15November2016.pdf
- NASA, *MLI Blanket Effective Emittance Variance…* (ε\* 0.05–0.30, workmanship-driven):
  https://ntrs.nasa.gov/citations/20190025589 ·
  https://ttu-ir.tdl.org/server/api/core/bitstreams/abb4bcbd-bf48-4f09-8a63-70a8dd3fb144/content
- NASA, *Test-Derived Effective Emittance for Cassini MLI Blankets*:
  https://ntrs.nasa.gov/citations/20210004177
- NASA, *Defining and Applying Limits for Test and Flight* (GEVS +10/+5/+15 °C; correlated
  reduction): https://ntrs.nasa.gov/api/citations/20150018333/downloads/20150018333.pdf
- *Assessment of Thermal Balance Test Criteria* (ICES 2016) — correlation error vs margin:
  https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/ICES_2016_6.pdf
- "Uncertainty calculation for spacecraft thermal models (generalized SEA)," *Acta
  Astronautica*: https://www.sciencedirect.com/science/article/abs/pii/S0094576518303084
- MDPI *Aerospace* 11(3):231, space-telescope thermal uncertainty / critical parameters:
  https://www.mdpi.com/2226-4310/11/3/231

Cryogenic material properties:
- NIST Cryogenics — Material Properties database (4–300 K fits; ≤5% / <0.2% uncertainty):
  https://trc.nist.gov/cryogenics/materials/OFHC%20Copper/OFHC_Copper_rev1.htm ·
  https://www.nist.gov/mml/acmd/cryogenic-materials-properties-reference-list
- NIST SP, *Properties of Selected Materials at Cryogenic Temperatures* (CTE integrals,
  k(T), cp(T)): https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=913059

Thermo-mechanical coupling:
- Ansys, *Example Thermal-Stress Analysis* (LDREAD, TREF, one-way coupling):
  https://ansyshelp.ansys.com/public//Views/Secured/corp/v251/en/ans_cou/Hlp_G_COU2_7.html
- Abaqus, *Sequentially coupled thermal-stress analysis* (one-way validity criterion):
  https://abaqus-docs.mit.edu/2017/English/SIMACAEANLRefMap/simaanl-c-thermstressanal.htm
- Applied CAx, *Thermal-Stress Analysis — Femap & NX Nastran* (TEMPERATURE(LOAD), mesh
  reuse): https://www.appliedcax.com/resources/simcenter-femap-nastran/thermal-stress-analysis/
