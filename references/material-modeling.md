# Material Modeling, Constitutive Models & Calibration — Practitioner Brief

Dense, web-sourced best-practices reference for an FEM/CAE Agent Skill. Authoritative, generalizable across Ansys / Abaqus / LS-DYNA / Simcenter / COMSOL. Numbers and top mistakes included. Citations at the end.

> **Governing rule:** Use the simplest constitutive model the physics allows. Every additional parameter must be *earned* by test data and *validated* against a deformation mode you did **not** fit. A complex model fit to one test curve is less trustworthy than a simple model fit to several.

---

## 0. Units consistency (the silent killer)

There is no unit system inside an FE solver — it trusts your numbers. Mixing unit systems is one of the most common sources of wrong-by-orders-of-magnitude results, and it usually does **not** error out.

- Pick **one** consistent set and convert *every* material constant into it. The classic FE consistent set is **[mm, t (tonne), s, N, MPa]**: length mm, mass tonne (10³ kg), force N, stress **MPa**, density **t/mm³** (e.g. steel 7.85e-9, aluminum 2.7e-9), energy mJ. The SI set **[m, kg, s, N, Pa]** uses density in kg/m³ (steel 7850) and stress in Pa.
- **Density is the most-corrupted constant.** A wrong-unit density silently corrupts every dynamic (modal frequency ∝ √(k/m)), explicit (wave speed, time step), and transient-thermal (ρ·cp) result while statics looks fine — so the error hides until a modal or drop test.
- Thermal: be explicit about W/m·K vs W/mm·K, J/kg·K vs mJ/t·K, and absolute vs relative temperature for radiation (radiation needs **absolute** K).
- Record the unit system in the run manifest and state E, ρ, k, cp with units next to them. Sanity-check one natural frequency or wave speed against a hand calc after any unit conversion.

---

## 1. Elasticity

### Isotropic / orthotropic / anisotropic
- **Isotropic** — 2 independent constants (E, ν; G = E/[2(1+ν)]). Default for metals and most bulk materials.
- **Orthotropic** — **9 independent constants**: E₁,E₂,E₃, ν₁₂,ν₁₃,ν₂₃, G₁₂,G₁₃,G₂₃. Composite laminae (UD ply), wood, rolled/textured sheet, single crystals, 3D-printed parts. The off-diagonal Poisson ratios must satisfy reciprocity νᵢⱼ/Eᵢ = νⱼᵢ/Eⱼ — solvers expect the **major** Poisson ratios; entering minor ones (or violating reciprocity) gives a non-symmetric, non-positive-definite compliance matrix and a solver error or garbage.
- **Transversely isotropic** (5 constants) is the usual reduction for a UD lamina (fiber direction + isotropic transverse plane) — fewer tests, common default for CFRP plies.
- **Fully anisotropic** — 21 independent terms; rare, reserved for some crystals/auxetics.
- **Stability gate:** the elastic stiffness/compliance matrix must be positive-definite. For orthotropic materials this constrains the Poisson ratios (e.g. 1 − ν₁₂ν₂₁ − ν₂₃ν₃₂ − ν₃₁ν₁₃ − 2ν₂₁ν₃₂ν₁₃ > 0). Many "mystery" orthotropic solver failures are violated stability from inconsistent handbook constants.

### Temperature-dependent E, ν, α
- Make **E(T), ν(T), and α(T)** temperature-dependent for *any* thermal-stress, cryogenic, or high-temperature problem. E of metals typically drops ~5–30% from RT to a few hundred °C; cryo-stiffening is the opposite.
- Supply tables spanning the **full** temperature range of the analysis. **Do not flat-extrapolate** past the last data point — at cryogenic temperatures α and cp fall steeply toward zero (Debye T³ for cp; α → 0 as T → 0 by the third law), and a constant-property extrapolation grossly over-predicts cryo strains/heat capacity.
- The reference (strain-free) temperature must match how the property table is anchored (typically 293 K / 20 °C). A mismatch injects a spurious uniform pre-strain.

---

## 2. Metal plasticity

### Yield criteria
- **von Mises (J2)** — isotropic ductile metals. The default; pressure-independent.
- **Hill (1948)** — anisotropic yield (rolled sheet, textured/extruded metals). Needs yield-ratio parameters Rᵢⱼ (or Lankford r-values) from tests in multiple directions; for sheet forming the r-values (r₀, r₄₅, r₉₀) drive earing/thinning. More advanced anisotropic yield: Barlat Yld2000/Yld2004 (sheet forming).
- **Drucker-Prager / Mohr-Coulomb** — pressure-dependent yield for soils, rock, concrete, foams, some polymers; tension/compression asymmetry. See **§2b (geomechanics)** for the full menu (Mohr-Coulomb, Drucker-Prager + cap, Modified Cam-Clay) and effective-stress basics.

### Hardening rules — match to load history
- **Isotropic hardening** — yield surface grows uniformly. Correct for **monotonic** loading only. Using it for cyclic/reversed loading wrongly over-stiffens reversal and **misses the Bauschinger effect**.
- **Kinematic hardening** — surface translates (back-stress); captures Bauschinger and reversed yielding. Linear (Prager/Ziegler) is crude; use for one or few reversals.
- **Combined / Chaboche** — superposition of several Armstrong-Frederick nonlinear kinematic back-stresses (+ optional isotropic Voce term). The standard for **cyclic plasticity, ratcheting, shakedown, low-cycle fatigue**.
- **Curve shape:** bilinear (tangent modulus) is fine only to ~5–10% strain; use **multilinear** or a **Voce/power-law** saturation form for large strain or to capture the knee accurately.

### TRUE vs engineering stress–strain — get this right or everything downstream is wrong
- **Input true stress / true (log) plastic strain**, never engineering values. Conversions valid only up to necking (uniform deformation):
  - σ_true = σ_eng·(1 + ε_eng)
  - ε_true = ln(1 + ε_eng)
  - plastic strain: ε_pl = ε_true − σ_true/E
- Solvers expect a **plastic** strain table starting at (0, σ_yield).
- **Past necking the simple conversion is invalid** — stress/strain are no longer uniform across the section. By the **Considère criterion**, diffuse necking begins when dσ_true/dε_true = σ_true (hardening rate equals current true stress), which is at the engineering UTS. Beyond that, extend the true curve by (a) an inverse/iterative FE fit of a notched or round-bar tensile test, or (b) a fitted hardening law (Hollomon σ=Kεⁿ, Swift, Voce) — **do not** just plot raw post-UTS data.
- The engineering curve *falls* after UTS only because area shrinks; the true curve keeps **rising**. Feeding a falling curve into a plasticity model creates spurious softening/instability.

### Rate-dependent plasticity (impact, forming, blast, high strain rate)
- **Johnson-Cook** — the workhorse for metals at high rate/temperature:
  σ = (A + B·εⁿ)·(1 + C·ln(ε̇*))·(1 − T*ᵐ), with ε̇* = ε̇/ε̇₀ and T* = (T−T_room)/(T_melt−T_room).
  - **A** = yield stress, **B** = hardening modulus, **n** = hardening exponent, **C** = strain-rate sensitivity, **m** = thermal-softening exponent. (Example, a mild steel: A≈220 MPa, B≈620 MPa, n≈0.12, C≈0.010, m≈1.0.)
  - Calibrate A,B,n from a quasi-static true curve; C from tests at several strain rates (e.g. split-Hopkinson bar); m from elevated-temperature tests; ε̇₀ is the reference rate you fitted at.
- **Cowper-Symonds** — simpler rate scaling σ_dyn/σ_static = 1 + (ε̇/D)^(1/q); common in crash (steel D≈40 s⁻¹, q≈5 are textbook starting values — *verify per alloy*).
- **Perzyna / Peric** — overstress viscoplasticity in implicit codes.

---

## 2b. Geomechanics — soils, rock, concrete (pressure-dependent constitutive models)

Geomaterials differ from metals in three structural ways that drive model choice: yield is **pressure-dependent** (strength rises with confinement), they are **frictional/dilatant** (shearing causes volume change), and they are **weak in tension** with a large **tension/compression asymmetry**. The load is carried partly by the solid skeleton and partly by **pore fluid**, so geomechanics is governed by **effective stress**, not total stress. These models also appear in soil/rock/foam/concrete contexts in `plasticity-inelastic-assessment.md` and in the geotechnical/civil tools in `specialized-analyses.md` and `software-landscape.md` (§geomechanics tools).

### Yield criteria — when to use which

| Criterion | Shape (π/meridian plane) | Inputs | When to use |
|---|---|---|---|
| **Mohr-Coulomb** | irregular **hexagon** in the deviatoric plane; linear τ–σ envelope | cohesion **c**, friction angle **φ** (+ dilation ψ, tension cutoff) | The classic **soil & rock** strength criterion (τ = c + σ′·tanφ). Physically intuitive, matches triaxial data well; the **sharp corners/apex** hurt FE convergence — use a rounded/smoothed version or Drucker-Prager as a numerical stand-in. Tension cutoff needed (it over-predicts tensile strength). |
| **Drucker-Prager** | smooth **cone** (circle in deviatoric plane) | friction-like **β** and cohesion-like **d** (matched to c, φ) | Smooth (corner-free) **DP** approximation of Mohr-Coulomb — far better **convergence**, the practical default for soil/rock/foam/some polymers in FE. **Match the cone to MC** at the relevant condition (triaxial compression vs. extension vs. plane strain — they give *different* β), or it will be unconservative. Linear, hyperbolic, and exponential DP variants exist. |
| **Drucker-Prager Cap (modified DP)** | DP shear cone **+ an elliptical "cap"** closing the high-pressure end | DP params + cap eccentricity + **hardening law p_b(ε_vol^pl)** | DP alone has no yield under pure hydrostatic compression, so dense soils/powders/foams **can't compact**. The **cap** adds a pressure-dependent yield surface that captures **plastic volumetric compaction** (consolidation, powder pressing). Use whenever hydrostatic crush / densification matters. |
| **Modified Cam-Clay (MCC)** | single **ellipse** in (p′, q) space; **critical-state** framework | λ (virgin compression slope), κ (swelling slope), **M** (critical-state line slope, ↔ φ), e₀, p_c (preconsolidation) | The **critical-state** model for **soft/normally-consolidated clays** (Roscoe-Schofield-Wroth). Couples **shear and volumetric** response: predicts hardening/softening, contraction vs. dilation, and that all states drift to a **critical state** (shearing at constant volume). The right tool for **consolidation, embankment, foundation settlement** on clay; less suited to sands/dilatant or heavily over-consolidated soils. |

- **Dilatancy / non-associated flow:** for frictional materials the **dilation angle ψ < φ** (associated flow, ψ = φ, badly over-predicts volume expansion and shear strength). Use a **non-associated** flow rule (separate plastic potential) for Mohr-Coulomb / Drucker-Prager. Note non-associated plasticity gives a **non-symmetric** stiffness matrix (solver cost) and can lead to non-uniqueness/localization.
- **Concrete** straddles this section and §5: pressure-dependent yield (DP-like) **plus** tensile cracking/damage → see **Concrete Damaged Plasticity (CDP)** in §5.

### Effective stress & consolidation (the pore-pressure coupling)

- **Terzaghi effective stress:** σ′ = σ − u (pore pressure u). **Strength and stiffness of soil depend on effective stress σ′, not total stress σ** — this is the single most important idea in geomechanics. Run constitutive models (MC, DP, Cam-Clay) on **effective** stress; for partially saturated soils use **Bishop's** χ-weighted form.
- **Drained vs. undrained:** *drained* = load slow enough that pore water escapes and u stays at hydrostatic (long-term); *undrained* = load fast, water trapped, **excess pore pressure** carries the load (short-term, end-of-construction). They give different strengths — pick the analysis type to match the loading rate and drainage, or run a **coupled** transient.
- **Consolidation (Biot / Terzaghi):** the time-dependent dissipation of excess pore pressure as water drains, with the load **transferring from fluid to skeleton** → settlement over time. Solved as a **coupled pore-fluid-diffusion / stress** ("u-p") analysis (Biot poroelasticity); the **coefficient of consolidation c_v** sets the timescale. Required for settlement-vs-time, staged embankment construction, and excavation heave. (Poroelasticity also appears under porous/Biot media in §8.)

---

## 3. Hyperelasticity (rubber, elastomers, soft tissue — large strain)

Hyperelastic models derive stress from a **strain-energy density function W** (so the material is path-independent and energy-conserving). W is written in terms of either the **invariants** of the right Cauchy-Green tensor (I₁, I₂, I₃ — or the **deviatoric/isochoric** Ī₁, Ī₂ plus the volume ratio J for the near-incompressible split) or the **principal stretches** (λ₁, λ₂, λ₃, as in Ogden). The whole game is choosing a W with the **fewest parameters** that reproduces *all* the deformation modes your part actually sees, and confirming the fit is **stable** over the operating stretch range. Holzapfel's continuum-mechanics treatment is the standard reference for the invariant/stretch formulations and the volumetric–isochoric split.

### 3.1 Model-selection table

| Model | Params | Form / basis | Good to (uniaxial strain, guide) | Data needed | Strengths / limitations |
|---|---|---|---|---|---|
| **Neo-Hookean** | 1 (C₁₀, +D₁) | Ī₁-linear; statistical Gaussian chain | ~**30–100%** | 1 mode (a single modulus) | Simplest, always stable, no upturn — **misses** the large-strain stiffening (S-shape); only a small-strain / first-cut model. |
| **Mooney-Rivlin (2-param)** | 2 (C₁₀, C₀₁) | linear in Ī₁, Ī₂ | ~**100%** (tension); shear larger | ≥2 modes | Captures mild I₂ dependence; **no upturn**, can go unstable in compression if C₀₁ chosen badly. |
| **Mooney-Rivlin (3-param)** | 3 | adds C₁₁ | ~**150%** | ≥2–3 modes | More curvature; risk of over-fit / wavy extrapolation outside data. |
| **Mooney-Rivlin (5-param)** | 5 | quadratic in (Ī₁−3),(Ī₂−3) | ~**150–200%** | ≥3 modes | Flexible mid-range; **easily unstable** and oscillatory beyond the data — needs all modes to pin it. |
| **Yeoh** | 3 (C₁₀,C₂₀,C₃₀) | cubic in Ī₁ only (no I₂) | ~**200%+** | **1 mode can suffice** (uniaxial), but verify others | "Reduced-polynomial"; good **large-strain extrapolation** and recovers the upturn from limited data; popular for **carbon-black-filled** rubber. Weak where I₂ matters (equibiaxial can be off). |
| **Ogden (N=1)** | 2 (µ₁,α₁) | principal stretches λ^α | ~**100–200%** | ≥1–2 modes | Non-integer exponent fits real rubber well even at N=1; basis for the others. |
| **Ogden (N=2)** | 4 | sum of 2 stretch terms | ~**300%** | ≥2–3 modes | Good balance of fidelity vs. stability. |
| **Ogden (N=3)** | 6 (µᵢ,αᵢ) | sum of 3 stretch terms | **full range to failure** | **≥3 modes (all of UT+EB+PS)** | Most flexible; captures the full S-curve and upturn; **most data-hungry** and most prone to instability if under-constrained — do not use N=3 with one test. |
| **Arruda-Boyce (8-chain)** | 2 (µ, λ_lock) | physically-based chain network; **limiting stretch λ_lock** | up to **λ_lock** (set by network) | 1 mode often enough | Physically meaningful, **robust extrapolation** across modes from one test, built-in lock-up; can't tune I₂ independently. |
| **Gent** | 2 (µ, J_m) | limiting first-invariant **I₁−3 → J_m** | up to lock limit | 1–2 modes | Simple closed-form strain stiffening (asymptote at J_m); excellent for capturing **abrupt lock-up**; phenomenological. |
| **(soft tissue) Holzapfel-Gasser-Ogden, Fung** | many | anisotropic, fiber-reinforced exponential | tissue-specific | multi-axial + fiber data | For arteries/biological tissue — anisotropic, **not** for filled rubber; listed so it isn't reached for by mistake. |

**Reading the table:** start at the **top** and go down only as the data and the deformation modes demand. For most engineering rubber, **Yeoh** (one-to-few modes, large strain) or **Ogden N=2–3** (all modes, best fidelity) or **Arruda-Boyce/Gent** (physical, robust extrapolation) cover the field; Neo-Hookean and 2-param Mooney-Rivlin are first-cut / small-strain only.

### 3.2 Test-data requirements — the #1 hyperelastic mistake

- **Fit to multiple deformation modes, not one.** The classic error is fitting from **uniaxial tension alone**: it constrains W poorly and **extrapolates badly** to the biaxial and shear states a real part experiences (a seal is multiaxial, a diaphragm is biaxial). A single-mode fit can match its own curve perfectly and still be wrong everywhere else.
- Provide the three standard homogeneous modes — **uniaxial tension (UT) + equibiaxial tension (EB) + planar/pure-shear (PS)** — which between them span the (I₁, I₂) space; add a **volumetric (confined-compression) test** for compressible/foam materials or to pin the bulk modulus. Note equibiaxial tension is **kinematically equivalent to uniaxial compression**, so an EB test substitutes for the hard-to-run compression test.
- Rough rule: Mooney-Rivlin (2-param) needs **≥2 modes**, Ogden **N=3 needs all 3 modes**. More parameters demand more independent modes or the fit is under-constrained and the extra terms just fit noise.
- Fit over the **stretch range the part sees** (don't fit to 500% if it works at 50%), and **weight** the modes by relevance. Report the residual per mode, not one lumped error.

### 3.3 Mullins effect (stress softening on cyclic loading)

- **Mullins effect** = the **stress-softening** of filled rubber on the **second and later loading cycles**: after a first loading to some maximum stretch, reloading to a stretch below that maximum follows a **softer** path; the virgin (primary) curve is only recovered by exceeding the previous maximum. It is a **damage-like, history-dependent** phenomenon (often modeled with a damage variable that depends on the **maximum strain energy** previously attained), usually accompanied by **permanent set / hysteresis** and some recovery over time.
- **Why it matters for FE:** a plain hyperelastic fit to the *first* loading curve will **over-predict stiffness** on subsequent cycles. For components that are **pre-conditioned** in service (most seals, mounts, bushings), fit the constitutive model to the **stabilized (shaken-down) cyclic** response, not the virgin curve; for a single monotonic event, the virgin curve is right.
- Capture it with a dedicated **Mullins (Ogden-Roxburgh) damage** add-on layered on a base hyperelastic model (available in Abaqus, Ansys, etc.), calibrated from **cyclic load-unload tests at several maximum stretches**. Don't try to fake softening with a lower modulus — that loses the stretch-dependence.

### 3.4 Near-incompressibility & volumetric locking

- Rubber is **nearly incompressible** (ν → 0.5; bulk modulus K ≫ shear modulus µ). With **pure-displacement** elements this drives **volumetric locking** — the incompressibility constraint over-constrains the element, stiffening it spuriously and producing pressure checkerboarding. Remedies, in rough order of preference:
  - **Mixed displacement–pressure (u–P) / "hybrid" elements** — pressure carried as an independent field (a Herrmann/mixed formulation). The standard, robust choice for ν → 0.5; **default to hybrid elements for any near-incompressible material.**
  - **F-bar / B-bar (mean-dilatation)** — the volumetric part of the deformation gradient is averaged over the element to relax the constraint; common for first-order solids/large strain.
  - **Selective-reduced integration (SRI)** — full integration of the deviatoric (shear) part, reduced integration of the volumetric (bulk) part; cheap and effective but watch for hourglassing on under-integrated terms.
  - Avoid fully-integrated **first-order pure-displacement** elements for incompressible rubber; if you must use reduced integration, enable **hourglass control**.
- **Bulk-modulus / penalty choice (D₁, where K = 2/D₁):** set it **deliberately**. Too incompressible (K/µ too high) wrecks **conditioning** and slows/stops convergence; too compressible is **unphysical** (the part dilates under load). A typical **initial bulk/shear ratio K/µ ≈ 10³–10⁴** (equivalently ν ≈ 0.499–0.4999) is the usual compromise for filled rubber — use a measured volumetric test if dilation actually matters. **D₁ = 0 (fully incompressible)** is only valid with hybrid/mixed elements; specifying it without them will fail.

### 3.5 Drucker (material) stability — always check the fit

- A curve fit can look excellent yet be **unstable**: for a physically admissible material the incremental work must be positive, **dσ : dε > 0** (Drucker stability), which requires the tangent stiffness to stay **positive-definite**. An unstable fit makes the analysis **diverge or give nonsense** once any element enters the unstable stretch range.
- Good solvers **automatically report the stability range**: Abaqus checks the **six canonical states — uniaxial, equibiaxial, and planar, each in tension and compression** — and prints the stretch interval over which the fit is stable. **Read that report.** A fit "stable from 0.7 to 4.0" is fine only if your part never leaves that band.
- Instability usually comes from **over-parameterizing** (5-param Mooney-Rivlin / Ogden N=3) fit to **too few modes**, so the unconstrained terms wander. Remedies: **lower the model order**, **weight the fit toward your operating range**, **add the missing deformation mode**, or switch to an inherently better-behaved form (**Yeoh, Arruda-Boyce, Gent**), which are far less prone to unstable wiggles.

---

## 4. Time-dependent behavior

### Viscoelasticity (polymers, adhesives, damping)
- **Prony series** (generalized Maxwell): G(t) = G_∞ + Σ gᵢ·e^(−t/τᵢ) (and/or bulk K(t)). Pick relaxation times τᵢ **roughly equally spaced on a log-time decade** grid spanning your loading times, then fit the moduli gᵢ.
- **Source data:** stress-relaxation or **DMA** (storage/loss modulus vs frequency & temperature). Build a **master curve** via **time–temperature superposition (TTS)**.
- **Shift function:** **WLF** above Tg (C₁, C₂ constants; "universal" C₁≈17.4, C₂≈51.6 K only as a fallback — fit your own), **Arrhenius** below Tg / for shift over wide T. The Prony series is the *time-domain* model; WLF/Arrhenius supplies the *temperature* dependence.
- Pitfalls: too few terms can't span the decades of relevant time; instantaneous modulus G₀ = G_∞ + Σgᵢ must match the measured glassy modulus; the normalized gᵢ must sum < 1 (leaving G_∞ > 0) for a solid.

### Creep (high T or long duration)
- **Norton-Bailey (Bailey-Norton)** captures **primary + secondary** in one law:
  ε_cr = A·σⁿ·tᵐ (time-hardening) or the strain-hardening form ε̇_cr = f(σ, ε_cr).
  - **A, n, m** are temperature-dependent constants (n = stress exponent, m < 1 gives decaying primary rate; m = 1 / its rate form ⇒ pure secondary Norton creep). Fit by **power-law (log-log) regression** of strain-vs-time at several stresses and temperatures.
  - **Strain-hardening** form usually predicts variable-stress histories better than time-hardening; prefer it when stress redistributes (e.g. relaxation, bolt preload).
- **Tertiary creep / rupture** is damage-driven (Kachanov-Rabotnov, Omega/MPC) and usually *not* solved directly — instead check against **ASME-style** creep-rupture / Larson-Miller limits.
- Always state the valid stress and temperature window; extrapolating Norton-Bailey beyond the calibrated range is unreliable, with errors growing at high T.

---

## 5. Damage & failure

### Ductile metals
- **Johnson-Cook damage** — fracture strain ε_f = [D₁ + D₂·exp(D₃·η)]·(1 + D₄·ln ε̇*)·(1 + D₅·T*), η = stress triaxiality; damage accumulates D = Σ Δε_p/ε_f, element deletes at D=1. Simple, widely available.
- **GISSMO** (LS-DYNA) — generalized incremental stress-state-dependent model; couples onto a base plasticity model (von Mises, Barlat). Inputs: **LCSDG** = failure strain vs triaxiality (and Lode angle), **ECRIT** = instability curve, **FADEXP** = stress-fade exponent, **LCREGD** = **mesh-size regularization** curve. State-of-practice for crash/forming fracture.
- **Gurson / GTN** — porous-metal (void nucleation-growth-coalescence) for high-triaxiality ductile tearing.
- **Critical practice — mesh regularization:** softening/damage localizes into one element band, so dissipated energy is **mesh-dependent**. Regularize by element size (GISSMO LCREGD) or by a **fracture-energy (Gf)**-based softening, and **report mesh sensitivity**. Calibrate fracture strain across **multiple triaxialities** (smooth + notched + shear + plane-strain specimens), not from a single tensile test.

### Composites (intralaminar)
- **Tsai-Wu / max-stress / max-strain** — quick *index* (does it fail?), no failure mode.
- **Hashin / Puck / LaRC** — **mode-distinguishing** (fiber tension/compression, matrix tension/compression) → drive **progressive damage** to ultimate. **Puck** (action-plane) is generally more accurate for matrix/inter-fiber failure and is favored in aerospace; Hashin is the common default.
- Needs lamina strengths Xt, Xc, Yt, Yc, S (and fracture-plane angle / inclination params for Puck).

### Delamination / interlaminar (composites, adhesives)
- **Cohesive Zone Model (CZM)** — traction-separation law with **strength (peak traction)** + **fracture toughness G_c** (areas G_Ic mode-I, G_IIc mode-II) + **penalty stiffness**; mixed-mode via B-K or power law. **Preferred** because it needs **no pre-crack** and no remeshing; can model both initiation and growth.
- **VCCT** — energy-release-rate at a crack tip vs G_c; accurate for **propagation of an existing crack** but needs a **pre-crack, a very fine tip mesh**, and (for advancing fronts) remeshing.
- **CZM convergence tips:** the cohesive zone must be resolved by **several elements** (≥3–5) across its length, or G_c is under-integrated and results are mesh-sensitive; lower penalty stiffness, viscous regularization, or arc-length/explicit solving tame the snap-back instability. Calibrate strength and G_c from **DCB (mode-I), ENF (mode-II), MMB (mixed)** coupon tests.

### Concrete / quasi-brittle
- **Concrete Damaged Plasticity (CDP)** — yield/flow + tensile & compressive damage. Key inputs: **dilation angle ψ** (≈30–40° normal concrete; ~55° reported for UHPC), **eccentricity** (≈0.1), biaxial/uniaxial strength ratio **σ_b0/σ_c0** (≈1.16; ~3.0 UHPC), Kc (≈0.667), plus σ–ε curves and damage vars for tension and compression.
- Define **tension stiffening** by a fracture-energy (Gf) criterion to reduce mesh sensitivity; add small **viscoplastic regularization** (viscosity µ) for convergence — but keep µ small (it artificially adds strength). Check mesh and dilation sensitivity.

---

## 6. Composites / Classical Lamination Theory (CLT)

- A laminate is built from lamina engineering constants (transversely-isotropic ply) + **ply thickness + orientation (stacking sequence)** → **ABD matrices**: **A** (extensional), **B** (extension-bending **coupling**), **D** (bending).
- **B ≠ 0 means extension-bending coupling** — an in-plane load warps the part. **Symmetric** layups give B = 0; **balanced** layups remove extension-shear coupling. Unsymmetric layups also warp from cure/thermal mismatch.
- Model as **layered shell** (one element through thickness, section = ply stack) for thin parts, or **layered/stacked solids** when interlaminar (through-thickness) stresses matter (free edges, joints, thick laminates). Check **ply-by-ply**, watch **free-edge interlaminar stresses, delamination, and buckling/wrinkling**.
- Sandwich = composite **skins (shell)** + orthotropic **core (solid or homogenized)**; core shear and face wrinkling govern.
- **Effective laminate CTE** is directional and can even be slightly negative along fibers — compute from CLT, do not assume isotropic α.

---

## 7. Thermal properties (heat transfer & thermal stress)

- Required fields: **k(T)** (conductivity), **cp(T)** (specific heat), **ρ** (density), and **α(T)** (CTE). All should be tabulated vs temperature for cryo/high-T work.
- **Phase change / latent heat:** model with an **enthalpy** (H = ∫ρ·cp dT + latent heat) method or a steeply-varying effective cp over the mushy range — do **not** approximate a melt/freeze with constant cp; you lose the latent heat and badly mis-predict transient times.
- **Thermal expansion — use ∫α(T) dT, not α·ΔT.** Two distinct quantities exist and are routinely confused:
  - **Instantaneous CTE** α(T) = (1/L)·dL/dT.
  - **Total thermal strain** ε_th = ∫_{T_ref}^{T} α(T′) dT′ (often tabulated directly as integrated expansion ΔL/L from a reference like 293 K).
  - Over a wide range α(T) varies strongly (toward 0 at cryo), so the linear ε ≈ α·ΔT is wrong; many solvers expect a **secant** (mean) CTE referenced to the *same* T_ref used for the strain-free state — if you mix instantaneous-α data into a secant-α field (or change T_ref) you get a large spurious strain. Either feed integrated strain directly or convert instantaneous → secant about your reference: ᾱ(T) = [∫_{T_ref}^{T} α dT′]/(T − T_ref).
- **Radiation:** solar absorptivity **α_s** and infrared emissivity **ε** are **different** properties (different wavelength bands) — do not reuse one number for both; both can be temperature/surface dependent. Radiation needs **absolute temperature** and the Stefan-Boltzmann constant in consistent units.
- **Contact heat transfer** (thermal contact conductance / resistance across joints) is separate — see thermal-contact-resistance reference.

---

## 8. Other constitutive models (know they exist)

Crushable/anisotropic **foam** (energy absorption), **gaskets** (pressure-closure curve, not a continuum modulus), **shape-memory alloys** (superelastic/transformation), **piezoelectric** (coupled electromechanical), **porous/poroelastic** (Biot, soils), **magnetostrictive**, swelling/hygroscopic. Each needs its own characterization test — don't fake them with elasticity + a fudge factor.

---

## 9. Data sources

| Source | Scope | Pedigree / use |
|---|---|---|
| **MMPDS** (Battelle/FAA, ex-MIL-HDBK-5) | Aerospace metallic alloys & fasteners | The "bible" of **statistically-based design allowables**: **A-basis** (99% exceed at 95% confidence — fail-safe-critical/single-load-path) and **B-basis** (90%/95% — redundant structure). Includes temperature-knockdown curves. FAA/regulator-accepted. |
| **CMH-17** (Composite Materials Handbook) | Polymer/metal/ceramic-matrix composites | Composite analog of MMPDS; statistical allowables + test methods. |
| **NIST cryogenic database** | Materials 4 K–300 K | Curve-fitted **k, cp, linear thermal expansion (integrated ΔL/L), Young's modulus** as **log-polynomial** fits (coefficients a…i) over ranges <4 K, 4–77 K, 77–300 K, 300 K–melt. Fits good to ~1–2% (single dataset), up to ~5% across datasets. Covers OFHC Cu, 6061-T6/5083 Al, 304/316 SS, Invar, Inconel 718, G-10, Kevlar, Teflon, etc. The standard for cryo CAE. |
| **MatWeb / Total Materia** | Huge breadth, all classes | Convenient *typical/nominal* datasheet values — **not** design allowables, often single-temperature, mixed pedigree. Use for early sizing; verify before certification. |
| **Ansys Granta MI / GRANTA Selector** | Curated multi-class DB + traceability | Pedigreed values with units/temperature ranges; integrates into Ansys. Good provenance. |
| **ESDU** | Aerospace data items & methods | Validated engineering methods + some property data. |
| **Vendor datasheets / mill certs** | Specific grade/heat | Real, but check whether typical vs minimum, and the test temperature/condition. |

**Always record source + temperature range + basis (typical vs A/B-basis)** in the run manifest for every material card.

### Callable open property libraries (for hand-calc sanity numbers)

For the **independent cross-checks** that feed the unit-consistency, energy-balance, and hand-calc sanity gates, several open Python libraries return engineering property values **programmatically** — useful for a quick second opinion without opening a solver or a datasheet. Treat them as **sanity-check sources, not a solver dependency**, and never substitute a library call for the qualified vendor material card in a SIGNOFF run; state the library, version, and valid T/P range alongside any number used.

- **CoolProp** — fluid and thermophysical properties (density, cp, viscosity, k, enthalpy, vapor pressure) for ~120 fluids via a REFPROP-like equation-of-state backend. Use to sanity-check a coolant ρ·cp, a vapor pressure, or a heat-balance enthalpy. (open-source, C++ with Python bindings.)
- **fluids** and **ht** (Caleb Bell) — fluid-dynamics (`fluids`: friction factors, loss coefficients, two-phase, pump/valve relations) and heat-transfer (`ht`: convection/conduction/radiation correlations, Nusselt numbers, fouling) correlation libraries. Use to independently reproduce a convective `h`, a pressure drop, or a Nusselt-number hand calc before trusting a CFD/thermal boundary condition.
- **thermo** (Caleb Bell) — phase equilibria and mixture/chemical thermodynamics (VLE, activity coefficients, mixture properties) for energy-balance and phase-behavior cross-checks.
- **pint** — unit handling / dimensional analysis; carries units through a hand calc and **catches unit-system mistakes** (the §0 silent killer) by raising on incompatible dimensions. The natural companion when converting a material constant into the chosen consistent set.

(Solids breadth — matminer / Materials Project — exists too but is database-backed rather than correlation-based; verify pedigree before any use beyond early sizing.)

---

## 10. Calibration — which tests for which model, and validate on held-out data

- **Elastic constants:** tension/compression (E, ν via strain gauges/DIC), torsion (G); for orthotropic, tests along each material axis + off-axis.
- **Plasticity (monotonic):** uniaxial true stress–plastic-strain curve; extend past necking by inverse FE of a notched/round-bar test (Bridgman correction) or a fitted hardening law.
- **Anisotropic yield (Hill/Barlat):** tension at 0/45/90° (r-values) + biaxial/bulge for sheet.
- **Cyclic / Chaboche:** **strain-controlled symmetric** loops (isotropic + kinematic parts) for stabilized hysteresis; **stress-controlled asymmetric** (mean-stress) tests for **ratcheting**. Identify back-stresses by fitting the loop; **2–3 back-stresses** usually suffice (large strain may want 4–5). Don't over-parameterize — many parameter sets fit one loop equally; ratcheting is *very* sensitive to them, so validate on a ratcheting test the fit did not see.
- **Rate-dependent (J-C / Cowper-Symonds):** quasi-static + multiple strain rates (drop-weight, **split-Hopkinson bar**) + elevated-T for thermal softening.
- **Hyperelastic:** uniaxial + equibiaxial + planar (+ volumetric) — multi-mode is mandatory; for filled rubber used cyclically, calibrate the **Mullins** softening from **load-unload cycles at several maximum stretches** and fit the base model to the **stabilized** curve. **Read the solver's Drucker-stability range** for the fit.
- **Geomechanics (MC / DP / Cam-Clay):** **triaxial** tests (drained and undrained, at several confining pressures) for c, φ, M and the critical-state/cap parameters; **oedometer / consolidation** test for λ, κ, c_v and preconsolidation p_c; report results on **effective stress**.
- **Viscoelastic:** DMA frequency/temperature sweep or stress-relaxation → master curve → Prony + WLF/Arrhenius.
- **Creep:** strain-vs-time at several (σ, T) → power-law regression for A, n, m.
- **Damage/fracture:** multiple triaxialities (smooth/notched/shear/plane-strain) for ductile; DCB/ENF/MMB for delamination Gc; uniaxial tension+compression (+ biaxial) for concrete CDP.
- **Validation discipline:** fit on one set of modes, **predict a held-out mode/test and compare** (e.g. fit uniaxial+planar, predict biaxial; fit one cyclic loop, predict ratcheting). A fit that only reproduces its own training curve is unverified. Use least-squares / Levenberg-Marquardt or an optimizer (DOE/optiSLang, HEEDS, PyMAPDL+SciPy) and **bound parameters to physically meaningful ranges**.

---

## 11. Top pitfalls (the ones that bite repeatedly)

1. **Inconsistent units** — esp. density (corrupts dynamics/explicit/thermal silently). Sanity-check a frequency or wave speed.
2. **Engineering vs true stress–strain mix-up**, and using raw **post-necking** data instead of an inverse/law-based extension.
3. **Missing temperature dependence** of E/α/k/cp; **flat-extrapolating** properties at cryo or high T (α, cp → 0 at cryo by the third law/Debye).
4. **α·ΔT instead of ∫α dT**, or mixing instantaneous vs secant CTE / changing the reference temperature.
5. **Wrong hardening rule for the load history** — isotropic for cyclic loading misses Bauschinger; monotonic curve reused for fatigue/ratcheting.
6. **Single-mode hyperelastic fit** — uniaxial-only extrapolates badly to biaxial/planar; ignoring the **Drucker-stability** warning → divergence; fitting the **virgin** curve for a part that is cyclically pre-conditioned (**Mullins** softening) → over-stiff.
7. **ν = 0.5 (or near) without hybrid/mixed u–P elements** — volumetric locking.
8. **Over-parameterized constitutive models** fit to too little data — non-unique parameters, false confidence; not validated on a held-out mode.
9. **Mesh-dependent softening/damage** — no fracture-energy or size regularization; no reported mesh-sensitivity study. CZM with too few elements in the cohesive zone.
10. **Orthotropic constant inconsistencies** — violated Poisson reciprocity/stability → non-positive-definite stiffness, solver failure or nonsense.
11. **Treating MatWeb "typical" values as design allowables**, or ignoring A/B-basis distinctions for certified structure.
12. **Phase change with constant cp** — latent heat lost, transient timing wrong.
13. **Solar absorptivity = IR emissivity** assumption in radiation; relative instead of absolute temperature.
14. **Geomechanics on total instead of effective stress**, or **associated flow (ψ = φ)** for a frictional soil (over-predicts dilation/strength); Drucker-Prager cone not matched to Mohr-Coulomb at the right condition (triaxial-compression vs. extension vs. plane-strain) → unconservative.

---

## SOURCES

True/engineering stress–strain, necking, Considère criterion:
- CAEflow — Stress-Strain Conversion for FEA: https://caeflow.com/fea/stress-strain-conversion/
- LSTC FAQ — Stress vs strain for plasticity models: https://ftp.lstc.com/anonymous/outgoing/support/FAQ/stress_vs_strain_for_plasticity_models
- ASME J. Eng. Mater. Technol. — Extracting equivalent stress/plastic-strain of necking material: https://asmedigitalcollection.asme.org/materialstechnology/article/146/2/021007/1193777/
- Plastometrex — Necking & Ultimate Tensile Strength: https://www.plastometrex.com/blogs/necking-the-ultimate-tensile-strength

Chaboche / combined hardening / ratcheting:
- On the calibration of the Chaboche hardening model & a modified rule (Int. J. Solids Struct.): https://www.sciencedirect.com/science/article/pii/S0020768309001644
- Determination of Chaboche dual-backstress parameters for ratcheting (AISI 52100): https://www.sciencedirect.com/science/article/abs/pii/S0142112319300155
- Sensitivity & calibration of Chaboche kinematic hardening for ratcheting (MDPI Appl. Sci.): https://www.mdpi.com/2076-3417/9/12/2578
- Identification of Chaboche-Lemaitre combined hardening parameters (Acta Mechanica): https://link.springer.com/article/10.1007/s00707-020-02851-z

Hyperelasticity / model selection / Mullins / Drucker stability / multi-mode data:
- Ogden, R.W. — Large deformation isotropic elasticity (Proc. R. Soc. Lond. A, 1972), the Ogden strain-energy form: https://royalsocietypublishing.org/doi/10.1098/rspa.1972.0026
- Ogden — *Non-Linear Elastic Deformations* (Dover, 1997) — standard text for stretch-based hyperelastic formulations.
- Holzapfel, G.A. — *Nonlinear Solid Mechanics: A Continuum Approach for Engineering* (Wiley, 2000) — invariant/stretch forms, volumetric–isochoric split, near-incompressibility.
- Mullins, L. — Softening of rubber by deformation (Rubber Chem. Technol., 1969) — the Mullins stress-softening effect: https://meridian.allenpress.com/rct/article/42/1/339/89034
- Ogden & Roxburgh — A pseudo-elastic model for the Mullins effect in filled rubber (Proc. R. Soc. A, 1999): https://royalsocietypublishing.org/doi/10.1098/rspa.1999.0431
- Abaqus Analysis User's Manual — Hyperelastic behavior of rubberlike materials: http://abaqusdocs.eait.uq.edu.au/v6.11/books/usb/pt05ch21s05abm07.html
- Abaqus — Fitting of hyperelastic and hyperfoam constants (Drucker stability checks): https://classes.engineering.wustl.edu/2009/spring/mase5513/abaqus/docs/v6.6/books/stm/ch04s06ath124.html
- Abaqus — Mullins effect / Ogden-Roxburgh damage in rubberlike materials: http://abaqusdocs.eait.uq.edu.au/v6.11/books/usb/pt05ch21s06abm04.html
- SimScale — How to choose a hyperelastic material model: https://www.simscale.com/blog/how-to-choose-hyperelastic-material/
- COMSOL — Fitting measured data to different hyperelastic models: https://www.comsol.com/blogs/fitting-measured-data-to-different-hyperelastic-material-models
- MDPI Designs — Comparative analysis of hyperelastic models & element types: https://www.mdpi.com/2411-9660/7/6/135

Geomechanics yield criteria / critical-state / effective stress:
- Roscoe, Schofield & Wroth — On the yielding of soils (Géotechnique, 1958) — origin of critical-state soil mechanics: https://www.icevirtuallibrary.com/doi/10.1680/geot.1958.8.1.22
- Schofield & Wroth — *Critical State Soil Mechanics* (McGraw-Hill, 1968) — Modified Cam-Clay framework.
- Roscoe & Burland — On the generalised stress-strain behaviour of wet clay (1968) — the Modified Cam-Clay ellipse.
- Drucker & Prager — Soil mechanics and plastic analysis or limit design (Q. Appl. Math., 1952) — the Drucker-Prager criterion: https://www.ams.org/journals/qam/1952-10-02/S0033-569X-1952-48291-2/
- Terzaghi — *Theoretical Soil Mechanics* (Wiley, 1943) — effective stress, consolidation.
- Biot — General theory of three-dimensional consolidation (J. Appl. Phys., 1941) — poroelastic consolidation: https://doi.org/10.1063/1.1712886
- Abaqus — Mohr-Coulomb, Drucker-Prager (+ cap), Modified Cam-Clay, and coupled pore-fluid/consolidation (geotechnical) material & analysis docs: http://abaqusdocs.eait.uq.edu.au/v6.11/books/usb/pt05ch23abm.html

Johnson-Cook flow stress & damage:
- ScienceDirect topic — (Johnson-)Cook Model overview: https://www.sciencedirect.com/topics/engineering/cook-model
- Johnson-Cook plasticity & damage for AISI-1045 (PMC): https://pmc.ncbi.nlm.nih.gov/articles/PMC6416717/
- J-C flow stress & damage for polycarbonate impact (Int. J. Impact Eng.): https://www.sciencedirect.com/science/article/abs/pii/S0734743X23001859

Viscoelastic Prony / WLF / DMA master curve:
- Prony series from DMA data for structural adhesives (ScienceGate / Ingeniería Investigación y Tecnología): https://www.sciencegate.app/document/10.22201/fi.25940732e.2020.21n2.014
- Frequency/temperature viscoelastic characterization via Prony series (MDPI): https://www.mdpi.com/2673-3161/5/4/44
- Viscoelastic relaxation modulus characterization using Prony series — Pacheco et al., *Lat. Am. J. Solids Struct.* 12 (2015): https://doi.org/10.1590/1679-78251412

Creep / Norton-Bailey:
- May, Segletes & Gordon — Application of the Norton-Bailey Law for creep prediction via power-law regression (UCF): https://momrg.cecs.ucf.edu/wp-content/uploads/2019/05/May-D.-Segletes-D.-and-Gordon-A.-P.-2013-The-Application-of-the-Norton-Bailey-Law-for-Creep-Prediction-through-Power-Law-Regression.pdf
- COMSOL — Creep and viscoplasticity theory (Norton-Bailey, time/strain hardening): https://doc.comsol.com/5.5/doc/com.comsol.help.sme/sme_ug_theory.06.32.html
- Kachanov-Rabotnov / Norton-Bailey curve fitting for SS-316 (PMC): https://pmc.ncbi.nlm.nih.gov/articles/PMC8509217/

Composite failure / cohesive / VCCT:
- VCCT vs CZM for delamination propagation — Liu et al., *Aerospace Systems* 6:621–632 (2023): https://doi.org/10.1007/s42401-023-00231-8
- Cohesive models for damage evolution in laminated composites — Camanho, Dávila & de Moura, *Int. J. Fracture* (2005): https://doi.org/10.1007/s10704-005-4729-6
- Composite failure criteria practical guide (Hashin/Puck/Cuntze): https://engineeringdownloads.com/composite-failure-criteria-engineering-guide/
- Overcoming CZM convergence difficulty (arXiv): https://arxiv.org/pdf/1911.12311

Concrete Damaged Plasticity:
- Recommended CDP parameters & constitutive models for UHPC in Abaqus (Eng. Structures): https://www.sciencedirect.com/science/article/abs/pii/S0141029625005450
- Generalised calibration & optimization of CDP for cracked RC (ScienceDirect): https://www.sciencedirect.com/science/article/pii/S2590123024021480
- Lee & Fenves, *Plastic-Damage Model for Cyclic Loading of Concrete Structures* (J. Eng. Mech. 1998) — foundational CDP formulation: https://doi.org/10.1061/(ASCE)0733-9399(1998)124:8(892)

GISSMO ductile damage / regularization:
- On parameter identification for the GISSMO damage model (LS-DYNA / DYNAlook): https://lsdyna.ansys.com/wp-content/uploads/attachments/metalforming25-a.pdf
- Parameters calibration of the GISSMO failure model for SUS301L-MT (Chin. J. Mech. Eng.): https://link.springer.com/article/10.1186/s10033-023-00844-2
- Calibration of GISSMO for fracture prediction of AHSS (LS-DYNA): https://lsdyna.ansys.com/wp-content/uploads/2022/11/calibration-of-gissmo-model-for-fracture-prediction-of-a-super-high-formable-advanced-high-strength-steel.pdf

Thermal / cryogenic data & data sources:
- NIST — Properties of Selected Materials at Cryogenic Temperatures (pub overview): https://www.nist.gov/publications/properties-selected-materials-cryogenic-temperatures
- NIST Cryogenics — Material Properties index (curve fits, materials list): https://trc.nist.gov/cryogenics/materials/materialproperties.htm
- NIST Cryogenic Material Properties Database (full report PDF): https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=913059
- MMPDS — Definition of design allowables (A/B-basis) (mmpds.org): https://www.mmpds.org/about-us/definition-of-design/
- Battelle — MMPDS press / scope (A- and B-basis entries): https://www.battelle.org/insights/newsroom/press-release-details/battelle-publishes-new-volume-of-mmpds--the--bible--of-aerospace-metallic-material-properties
- MMPDS 2015 statistical property analysis overview: https://www.mmpds.org/wp-content/uploads/2015/03/mmpds_2015_statistical_property_analysis_overview.pdf
