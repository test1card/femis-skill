# Electromagnetics (EM) FEM/CAE — Practitioner Brief

Scope: the methodology of **computational electromagnetics (CEM)** as it touches the FEM/CAE
practitioner — formulation choice by frequency regime, when FEM is the wrong tool (MoM/FDTD),
edge vs nodal elements, boundary/port/radiation conditions, electric-machine and antenna/RF
workflows, EM-driven multiphysics (thermal, structural, NVH, piezo/MEMS), and the
mesh/verification/automation specifics. Generalizable across **Ansys Maxwell** (low-frequency)
and **HFSS** (high-frequency), **COMSOL AC/DC & RF** modules, **CST Studio Suite**, and the
open-source stack (**getDP/ONELAB, Elmer, FEniCSx**). Cross-verified against Jin's *The Finite
Element Method in Electromagnetics*, vendor theory docs, and the IEEE/CEM literature. Numbers
are defaults / rules-of-thumb; confirm against your installed version and the physics. Citations
`[n]` → SOURCES. Confidence tags: **[VERIFIED-web]** = corroborated across ≥2 independent
sources; **[DOCS-ONLY]** = single-vendor doc / standard canon.

The governing rule for the whole topic: **the frequency regime picks the formulation, and the
formulation picks the element type.** Get those two wrong and no amount of mesh refinement
saves you — the classic failure (nodal elements for a vector field) produces *non-physical
spurious modes that do not vanish as the mesh shrinks*.

---

## Contents

- [1. The regime map — pick the formulation from the frequency](#1-the-regime-map-pick-the-formulation-from-the-frequency)
- [2. Electrostatics & magnetostatics (the scalar/low-end)](#2-electrostatics-magnetostatics-the-scalarlow-end)
- [3. Low-frequency eddy-current / transient magnetics (the A-V / T-Ω world)](#3-low-frequency-eddy-current-transient-magnetics-the-a-v-t-ω-world)
- [4. High-frequency full-wave — edge elements, ports, and absorbing boundaries](#4-high-frequency-full-wave-edge-elements-ports-and-absorbing-boundaries)
- [5. Method selection — FEM is not always the right CEM tool](#5-method-selection-fem-is-not-always-the-right-cem-tool)
- [6. Applications](#6-applications)
- [7. EM-driven multiphysics coupling](#7-em-driven-multiphysics-coupling)
- [8. Meshing, gauges & verification specifics](#8-meshing-gauges-verification-specifics)
- [9. Headless / automation](#9-headless-automation)
- [10. Top mistakes (quick-reference)](#10-top-mistakes-quick-reference)
- [See also](#see-also)
- [SOURCES](#sources)

## 1. The regime map — pick the formulation from the frequency

Maxwell's equations are one set, but the dominant terms — and therefore the right unknown,
element, and solver — change drastically with frequency. **Decide the regime first.** [VERIFIED-web]

| Regime | Dominant physics | Governing reduction | Primary unknown(s) | Element | Solver flavor |
|---|---|---|---|---|---|
| **Electrostatics** | Coulomb; no time variation | `∇·(ε∇V) = −ρ` (Poisson/Laplace) | scalar potential **V** | **nodal** (V is scalar) | SPD, like steady thermal |
| **Magnetostatics** | DC currents, magnets; `∂/∂t=0` | `∇×(ν∇×A) = J` or scalar `Ω` | **A** (3-D edge) or **Ω** scalar | edge (A) / nodal (Ω) | nonlinear if iron (B-H) |
| **Low-frequency / magneto-quasi-static (MQS)** | eddy currents, induction; displacement current **negligible** | `∇×(ν∇×A) + σ∂A/∂t = Js` | **A-V** or **T-Ω** | **edge** (A) | complex (harmonic) or transient |
| **High-frequency / full-wave** | wave propagation, radiation; **all terms retained** | vector Helmholtz `∇×(ν∇×E) − ω²εE = −jωJ` | **E** or **H** field | **edge (Nédélec)** mandatory | complex symmetric, indefinite |

**The displacement-current test (the regime boundary).** The neglect of `∂D/∂t` is valid when
the object is **electrically small** — dimension ≪ wavelength, equivalently when conduction
current `σE` ≫ displacement current `ωεE`. Rule of thumb: **quasi-static below ~λ/10–λ/20** of
the feature size; above that you are in full-wave territory and *must* retain the wave term or
you will miss resonance, radiation, and propagation entirely. [VERIFIED-web]

**Why this matters more than in mechanics:** a structural analyst can usually run a "more
complete" element and be safe. In EM, using the **full-wave solver at DC** is ill-conditioned
(the `ω²` term → 0, system becomes singular / "low-frequency breakdown"), and using a
**static/quasi-static solver above λ/10** silently discards the physics. There is no universally
safe over-modeling choice — match the regime.

---

## 2. Electrostatics & magnetostatics (the scalar/low-end)

- **Electrostatics** is numerically the twin of steady-state conduction heat transfer: SPD
  `∇·(ε∇V)=−ρ`, **nodal** elements, Dirichlet (fixed V / electrodes) and Neumann (symmetry /
  zero normal D) BCs. QoIs: capacitance matrix, field/`E` for **dielectric breakdown**, force
  by virtual work. Watch field **singularities at sharp electrode corners** (mesh-refine or
  apply a fillet — the true field is finite, the ideal-corner field is not). [DOCS-ONLY]
- **Magnetostatics** splits by region:
  - **Magnetic scalar potential Ω** (`H = −∇Ω`) in **current-free** regions — scalar, nodal,
    cheap (far fewer DOF, less memory). Comes in **total** and **reduced** (source-field
    subtracted) flavors; the **reduced scalar potential suffers cancellation error in high-μ
    iron** (large `H_source` minus large `∇Ω`), so use **total Ω in iron / reduced Ω in air**,
    or switch those regions to **A**. [VERIFIED-web]
  - **Magnetic vector potential A** (`B = ∇×A`) wherever **currents/conductivity live** —
    requires **3-D edge elements** and a **gauge** (§7). [VERIFIED-web]
  - **Nonlinear B-H** (ferromagnetic saturation) makes the solve **nonlinear → Newton-Raphson**
    with line search; supply the full single-valued B-H (or `ν(B²)`) curve and watch for the
    knee. Permanent magnets enter as a remanent `B_r` / coercivity `H_c` (demagnetization
    curve); check the **operating point stays above the knee** (irreversible demag risk).

---

## 3. Low-frequency eddy-current / transient magnetics (the A-V / T-Ω world)

The workhorse regime for **motors, transformers, inductors, induction heating, NDT, MRI, bus
bars** — anything where time-varying flux drives **eddy currents** but the device is electrically
small.

### Skin depth — the length scale that controls everything

> **δ = √(2 / (ω·μ·σ)) = 1/√(π·f·μ·σ)**, with ω = 2πf, μ = μ_r·μ₀, σ = conductivity.
> [VERIFIED-web]

Current crowds into a surface layer of thickness ~δ and decays exponentially; **fields
penetrate only ~4–5 skin depths**. [VERIFIED-web] δ **shrinks with √f** and is **tiny in
ferromagnetic conductors** (high μ_r). At 50/60 Hz, δ ≈ 9–10 mm in copper but sub-mm in steel.

### The mesh-the-skin-depth rule (the #1 LF-EM accuracy gate)

> **Put ≥ 2 element layers within one skin depth** (≥ 1 is the bare minimum; 2–3 is robust),
> using a **boundary/inflation layer** biased to the conductor surface. [VERIFIED-web]

If the skin depth is **not** resolved, an **A-formulation FE solve over-estimates the
losses** (the exponential current profile is under-integrated). [VERIFIED-web] This is the
EM analog of the boundary-layer-mesh rule in CFD. Practical recipe: compute δ at the **highest
frequency** of interest, set a surface layer ≈ δ/2–δ/3, and grow into the bulk. **High f +
high μ ⇒ punishing mesh** — at high frequency many solvers switch to a **surface-impedance
boundary condition (SIBC / impedance BC)** that imposes the analytic skin-effect relation on
the surface *instead of* meshing the layer (valid when δ ≪ part thickness). [VERIFIED-web]

### A-V vs T-Ω — the two LF formulations

| | **A-V (magnetic vector potential + electric scalar)** | **T-Ω (current vector potential + magnetic scalar)** |
|---|---|---|
| Unknown | **A** everywhere (+ V in conductors) | **T** in conductors, **Ω** in non-conductors |
| Element | edge for A, nodal for V | edge for T, nodal for Ω |
| DOF count | higher (vector everywhere) | **lower** (scalar Ω fills the big air region) |
| Best when | general; conductors fill much of domain; default in most commercial LF tools | large non-conducting/air regions; thin conductors |
| Catch | needs gauge in non-conducting regions (§7) | **multiply-connected conductors need cuts/cohomology** (loop currents) |

Both are standard; **A-V is the common commercial default** (Maxwell Eddy Current, COMSOL
Magnetic Fields), **T-Ω** is favored when the air volume dwarfs the conductors. [VERIFIED-web]

### Harmonic (frequency-domain) vs transient

- **Time-harmonic / AC** (complex phasors at one ω): linear, fast, gives loss/impedance at a
  single frequency. **Cannot represent nonlinear B-H exactly** — uses an *effective/equivalent
  permeability* linearization; for saturating iron this introduces error (mitigated by
  homogenized/harmonic-balance schemes). [VERIFIED-web]
- **Transient** (step in time): mandatory for **motion (rotor rotation), nonlinear saturation,
  PWM/non-sinusoidal excitation, inrush, and hysteresis**. Time step bounded like transient
  thermal — resolve the electrical period (and PWM carrier) with enough steps (≥ ~20/period,
  far more for PWM); for rotating machines tie Δt to **mechanical step per element of air-gap
  arc** so the rotor advances ≤ ~1 element/step.

---

## 4. High-frequency full-wave — edge elements, ports, and absorbing boundaries

The regime for **antennas, RF/microwave components, waveguides, filters, resonators, signal
integrity above ~GHz, radar/scattering (RCS), EMC above the quasi-static limit.**

### Why nodal elements FAIL for vector fields (the spurious-mode problem)

Nodal (Lagrange) elements enforce **full continuity of all components** across element faces.
But the physical E/H field is only **tangentially continuous** — its **normal component jumps**
at material interfaces, and the curl-curl operator has a huge null space (any gradient field).
Forcing nodal continuity:

1. wrongly constrains the field at dielectric/conductor interfaces and at re-entrant corners;
2. **fails to represent the null space of ∇×**, so the discrete spectrum is polluted by
   **spurious / non-physical modes** with no physical frequency, which **do not converge away
   under mesh refinement.** [VERIFIED-web]

### Nédélec edge (vector) elements — the fix

**Edge elements (Nédélec / Whitney H(curl) elements)** assign DOF to **element edges (tangential
field circulation)** rather than nodes. They:

- enforce **tangential continuity, allow the normal jump** — physically correct at material
  interfaces; [VERIFIED-web]
- **correctly span the gradient null space** → **no spurious modes** in eigen/driven solves;
  [VERIFIED-web]
- naturally handle **conductor edges/corners** (field singularities) and PEC tangential-E=0.

This is **not optional** — vector edge elements are *the* discretization for full-wave FEM
(HFSS, COMSOL RF, CST's FEM solver all use them). A common **mixed** trick for waveguide-mode
solvers: **edge elements for the transverse field + nodal for the longitudinal component** to
capture hybrid modes while staying spurious-free. [VERIFIED-web] High-order **hierarchical
Nédélec** elements (p-refinement) buy accuracy without remeshing.

### Ports & S-parameters

- **Wave ports** — solve the **2-D modal eigenproblem on the port face** to get the propagating
  mode(s)/impedance, then use them as the field excitation; the proper choice for **enclosed
  waveguides/transmission lines** and the basis for accurate, de-embeddable S-parameters.
  [VERIFIED-web]
- **Lumped ports** — an internal impedance sheet for **planar/PCB feeds** where a 2-D modal
  solution is impractical; simpler but less rigorous than a wave port.
- **S-parameters** (`S₁₁` reflection / `S₂₁` transmission) are the headline RF QoI; **S₁₁ in dB**
  drives antenna **return loss / bandwidth** (e.g. resonance where `|S₁₁| < −10 dB`). Always
  **de-embed** the port reference plane and run a **frequency sweep** (interpolating/fast sweep
  for smooth bands; discrete for sharp resonances). [VERIFIED-web]
- **Modes vs terminals** — for multi-conductor lines convert modal to **terminal** S-parameters
  for circuit hand-off.

### Radiation / open-domain truncation (the "where does space end" problem)

An antenna radiates to infinity; the mesh cannot. Truncate with one of: [VERIFIED-web]

| Truncation | What it is | Use / caveat |
|---|---|---|
| **ABC (absorbing boundary condition)** | 1st/2nd-order local operator that absorbs outgoing waves | cheap; needs **≥ ~λ/4 (often ~λ/8 min, λ/4 safe) standoff** from the radiator; reflects at oblique incidence |
| **PML (perfectly matched layer)** | a few layers of fictitious anisotropic lossy material; **near-zero reflection at all angles** | **best accuracy, box-size-independent far field**; costs extra FE elements; must be placed/meshed correctly (place in the radiating near field, not touching the structure) [VERIFIED-web] |
| **FE-BI (finite-element boundary integral)** | terminate the FE mesh with an exact MoM integral equation | **exact radiation condition, tightest air box**; conformal; more expensive per-unknown but smallest domain (§5 hybrid) [VERIFIED-web] |

**Air-box rule of thumb:** with an ABC keep ~**λ/4** from the antenna; with PML you can hug the
structure tighter (a few cells past the near field). Always **verify the result is invariant to
box size** — if S₁₁/gain move when you grow the box, the truncation is too close. [VERIFIED-web]

- **Far-field** (gain, directivity, radiation pattern, beamwidth, polarization) is computed by a
  **near-field-to-far-field transformation** over a closed surface around the antenna; near-field
  for coupling/SAR.

---

## 5. Method selection — FEM is not always the right CEM tool

The single most consequential EM-CAE decision: **FEM vs MoM/BEM vs FDTD.** Each discretizes a
different thing. [VERIFIED-web]

| Method | Discretizes | Domain | Native domain | Strengths | Weaknesses / when to avoid |
|---|---|---|---|---|---|
| **FEM** | **volume** (the whole 3-D region incl. air) | bounded (needs ABC/PML for open) | **frequency** (also transient) | **inhomogeneous/anisotropic materials, complex closed 3-D geometry, near-resonance, cavities/waveguides, fine detail**; unstructured mesh conforms to curves | meshes empty space; open-region radiation needs truncation; not ideal for electrically huge open problems |
| **MoM / BEM** | **surfaces/wires only** (boundary integral) | **inherently open** (Green's function = exact radiation) | frequency | **antennas, scattering/RCS, planar PCB/interconnect, wire structures**; **only surfaces meshed** → few unknowns for open radiators; no numerical dispersion | **dense matrix** (O(N²) memory, O(N³) solve) — needs fast solvers (MLFMM/ACA) to scale; **homogeneous/piecewise materials** preferred; hard with arbitrary inhomogeneity |
| **FDTD** | **volume on a structured (Yee) grid** | bounded (needs ABC/PML) | **time** (→ broadband in one run via FFT) | **broadband/UWB, transient, nonlinear/dispersive media, pulses, large simple-material problems, bio-EM/SAR**; trivially parallel | **staircases curved/oblique geometry** (structured grid); CFL-limited Δt; one run = one excitation; resonant/high-Q needs long runs |

**Selection heuristics** [VERIFIED-web]:

- **Closed, materially complex, 3-D, single/narrow band** (connectors, packages, cavities,
  waveguides, filters, 3-D antennas in housings, electric machines) → **FEM**.
- **Open radiation / antennas / RCS / planar PCB & on-chip passives** (mostly metal in air) →
  **MoM/BEM**.
- **Broadband/UWB, transient, pulses, large electrically-big with simple materials, SAR** →
  **FDTD**.
- **Hybrid FE-BI / FEBI**: FEM for the inhomogeneous interior (e.g. a dielectric-loaded antenna
  or a radome) + MoM boundary integral for the exact open-region condition — **best of both**
  for antennas with complex material loading; tightest air box, exact radiation. Open-source
  FEM-BEM coupling exists (e.g. FEniCS + Bempp). [VERIFIED-web]
- **Domain-decomposition / hybrid FE-FDTD / MoM-PO** for multi-scale problems (a small detailed
  antenna on a large platform).

---

## 6. Applications

### 6.1 Electric machines & actuators (the LF-EM flagship)

- **Torque computation — three methods, cross-check them:** [VERIFIED-web]
  - **Maxwell stress tensor (MST)** — integrate `T = (1/μ₀)[(B·n)B − ½B²n]` on a contour/surface
    **in the air gap**. Simplest (needs only local B on the path) but **sensitive to air-gap
    mesh and contour placement** — use a path mid-gap, with a fine, regular air-gap mesh.
  - **Virtual work / co-energy** — `T = ∂W'/∂θ` at constant current (co-energy) or `−∂W/∂θ` at
    constant flux; robust, energy-based.
  - **Arkkio's method** — MST averaged over an annular air-gap *volume* → far less
    mesh-sensitive than a single contour; the practical default in machine tools.
  - **Acceptance:** the three should agree within a few %; large disagreement = bad air-gap mesh.
- **Cogging torque** (PM machines, no current) is a **small difference of large numbers** →
  demands a **very fine, periodic air-gap mesh** and fine rotor-position stepping; under-resolved
  meshes give garbage cogging.
- **Rotation — sliding mesh / moving band:** the rotor moves relative to the stator each step.
  Standard schemes: a **moving band / sliding interface** (a thin air-gap layer remeshed or
  re-connected each step) with **edge-element continuity** across the interface; harmonic/mortar
  coupling at the sliding interface avoids per-step remeshing. **Keep the air gap ≥ ~2 element
  layers** and the rotor advancing ≤ ~1 element/step. [VERIFIED-web]
- **Losses — separate the mechanisms:** [VERIFIED-web]
  - **Copper / I²R (DC + AC):** AC copper loss (skin + proximity) needs the conductor skin depth
    meshed (§3) or it is under-predicted.
  - **Core / iron loss — Bertotti loss separation:** `P_fe = k_h·f·B^α (hysteresis) + k_e·f²·B²
    (classical eddy) + k_exc·f^1.5·B^1.5 (excess/anomalous)`. Coefficients fitted to
    manufacturer Epstein-frame data; apply post-processing on the FE B(t) waveform per element.
    Beware **minor loops / rotational fields / PWM harmonics** — sinusoidal Bertotti
    under-predicts there (use loss-surface or hysteresis models).
  - **Magnet eddy-current loss:** segment magnets to cut it; resolve magnet skin depth.
- **Co-simulation:** machines are usually run **FE-in-the-loop with a circuit/drive** (external
  PWM inverter, control) and coupled to **thermal** (loss → temperature → resistivity/remanence
  feedback) and **structural/NVH** (§7).

### 6.2 Power electronics, inductors, transformers, bus bars

- Extract **frequency-dependent R(f), L, parasitics** (PEEC/Q3D-style or FE eddy-current).
  **AC resistance ≠ DC resistance** once skin/proximity matter — mesh the skin depth. [VERIFIED-web]
- **Transformers:** leakage inductance, **winding eddy/proximity loss**, core loss (Bertotti),
  inrush (nonlinear transient), hot-spot for insulation life (→ thermal coupling).
- **Litz / stranded** conductors: homogenize rather than mesh every strand.

### 6.3 Antennas & RF (the full-wave flagship)

- **QoIs:** **S₁₁ / return loss / bandwidth, input impedance/VSWR, gain & directivity, radiation
  pattern, beamwidth, efficiency, polarization/axial ratio, isolation/coupling (S₂₁).**
- **Tooling:** **FEM (HFSS / COMSOL RF / CST-FEM)** for 3-D detailed/loaded antennas; **MoM**
  for wire/planar; **FE-BI** for dielectric-loaded radiators (§5).
- **Verify against box size and mesh** (S₁₁ and gain must be stable); **de-embed ports**;
  resolve the resonance with a discrete sweep.

### 6.4 EMI / EMC

- **Coupling, shielding effectiveness, crosstalk, radiated/conducted emissions, ESD.** Spans
  regimes: **low-frequency shielding/coupling → quasi-static FEM**; **high-frequency
  radiated/cavity resonance → full-wave (FEM/FDTD)**; **PCB/interconnect emissions → MoM/FDTD**.
- **Shielding effectiveness** needs the shield **skin depth meshed** (often an impedance BC) and
  a wide dynamic range; aperture/seam leakage dominates real enclosures.

### 6.5 Sensors & actuators

- **Inductive/eddy-current NDT & position sensors, LVDTs, solenoids, voice coils, magnetic
  bearings, Hall/fluxgate** — LF eddy-current or magnetostatic FEM; force by MST/virtual work;
  often coupled to a circuit and to motion.

### 6.6 Superconductors / HTS (note) [VERIFIED-web]

- HTS modeling uses dedicated formulations because of the **strongly nonlinear E-J power law**
  (`E ∝ (J/J_c)^n`, n large): the **H-formulation** (solve for **H** directly, edge elements)
  is the versatile standard for **AC loss, trapped field, flux pumps**; **H-Φ** and **coupled
  A-H** / **T-A** reduce cost by using a scalar/A potential outside the tapes. Strongly coupled
  to **thermal** (quench) and **mechanical** (Lorentz stress in magnets). Specialist territory —
  flag for a dedicated HTS workflow.

---

## 7. EM-driven multiphysics coupling

EM is rarely the end goal — it feeds **heat, force, and motion.** Decide **one-way (sequential)
vs two-way (strong)** the same way as thermo-mechanical (`references/thermal-and-coupling.md`):
one-way is valid when the EM solution **does not depend** on the field it produces. [VERIFIED-web]

### EM → thermal (the most common chain)

| Mechanism | Heat source | Where |
|---|---|---|
| **Resistive / Joule (I²R)** | `Q = J·E = σ\|E\|²` | conductors carrying current |
| **Induction heating** | eddy-current Joule from external coil | workpiece (skin-depth-localized) |
| **Core / iron loss** | hysteresis + eddy + excess (Bertotti) | magnetic steel |
| **Dielectric / microwave heating** | `Q = ½ω·ε₀·ε″·\|E\|²` (loss tangent) | lossy dielectrics |

- **One-way:** EM loss map → thermal body load (when material properties barely move with T).
- **Two-way (strong):** when **σ(T), μ(T), ε(T)** change enough to alter the EM solution — e.g.
  **induction heating of ferromagnetic steel** (σ drops, and crossing the **Curie point** kills
  μ → δ jumps), microwave heating with strongly T-dependent loss. Iterate EM↔thermal (often with
  **sub-cycling** — many fast EM cycles per thermal step, since the EM period ≪ thermal time
  constant). [VERIFIED-web]
- Hand-off mirrors `references/thermal-and-coupling.md`: loss density → thermal solve →
  temperature; **energy balance must close.**

### EM → structural / NVH

| Mechanism | Force/strain source | Application |
|---|---|---|
| **Lorentz / J×B body force** | `F = J×B` | bus bars, coils, rail/coil systems, MHD |
| **Maxwell stress (magnetic pressure)** | surface stress on iron/air boundary | motor stator-tooth radial forces |
| **Magnetostriction** | field-induced strain in magnetic material | transformer hum, motor acoustics |
| **Electrostatic / Coulomb force** | `F` on charged/dielectric surfaces | MEMS, capacitive actuators |

- **Motor NVH chain (one-way, standard):** transient EM → **radial air-gap force harmonics on
  the stator teeth** → structural **modal + harmonic/forced response** → **radiated acoustic
  noise** (vibro-acoustics). The EM force spectrum (spatial + temporal harmonics) is the
  excitation; **align EM time-step harmonics with the structural mode frequencies** or you miss
  the resonant orders. See `references/dynamics-nvh-acoustics.md` for the structural→acoustic
  half. [VERIFIED-web]
- **Two-way** only when deformation changes the gap/field appreciably (large coil deflection,
  MEMS pull-in).

### Piezoelectric & MEMS (intrinsically two-way electro-mechanical)

- **Piezoelectricity** is a **strongly coupled constitutive law** (strain ↔ electric field via
  the `d`/`e` matrices) — solved with **coupled-field elements** carrying **both displacement and
  voltage DOF**; not separable into one-way steps. Used for transducers, ultrasonic, energy
  harvesters, SAW/BAW resonators. [VERIFIED-web]
- **MEMS / electrostatic actuators:** electrostatic force ↔ structural deflection ↔ changing gap
  ↔ changing field — **two-way**, with the famous **pull-in instability** (snap-through when
  electrostatic force outruns mechanical restoring stiffness; needs arc-length/continuation like
  structural buckling, see `references/solver-numerics.md` §3).
- **Electro-thermal-stress chains** (e.g. Joule heating → thermal expansion → stress in a fuse,
  MEMS thermal actuator, or busbar) stack the §7 EM→thermal and the thermo-mechanical chain.

---

## 8. Meshing, gauges & verification specifics

### Meshing

- **Skin depth:** ≥ 2 element layers within δ (§3); inflation/boundary layer biased to the
  conductor surface; or impedance BC when δ ≪ thickness. [VERIFIED-web]
- **Air gap (machines):** ≥ ~2 layers, regular/periodic, finer than the iron — torque/cogging
  accuracy lives here.
- **Wavelength (full-wave):** resolve λ in the *material* (`λ = λ₀/√(ε_r·μ_r)`) — high-ε
  substrates shrink λ → finer mesh. HFSS-style **adaptive refinement** drives mesh until the
  **ΔS between passes < target** (e.g. 0.02); always check the convergence curve, not one pass.
- **Edge elements for H(curl):** non-negotiable for A/E/H vector unknowns (§4).
- **Air-box / radiation standoff:** ABC ≥ ~λ/4; PML hugging tighter — verify box-size
  invariance (§4). [VERIFIED-web]
- **Curvature & corners:** conformal mesh for curved metal; refine (or fillet) sharp
  electrode/conductor edges where the field is singular.

### Gauge conditions (the LF/edge-element pitfall) [VERIFIED-web]

The vector potential **A** is non-unique (`A` and `A+∇φ` give the same `B`) → the magnetostatic
/ non-conducting curl-curl system is **singular** unless **gauged**:

- **Tree-cotree (spanning-tree) gauging** — fix the edge DOF on a spanning tree of the mesh
  graph; classic, removes the null space.
- **Coulomb gauge** `∇·A = 0` — penalty/Lagrange enforcement.
- **In COMSOL/commercial terms:** *"Gauge Fixing for A-field"* is **required for the stationary
  (DC/magnetostatic) study and in non-conducting regions**, but is **not required in the
  time-dependent study where σ ≠ 0** (the `σ∂A/∂t` term regularizes the system). [VERIFIED-web]
- **T-Ω caveat:** **multiply-connected conductors** (a conductor with a hole / closed loop)
  need **homology cuts / loop (cohomology) currents** so net current can circulate — omitting
  them gives wrong currents.

### Verification (the EM sanity gates)

- **Energy / flux balance** — input power = ohmic loss + radiated + stored rate; flux continuity
  `∮B·dA = 0`. Closes < ~1 % like thermal energy balance. [DOCS-ONLY]
- **Force/torque method cross-check** — MST vs virtual-work vs Arkkio agree within a few %; if
  not, refine the air gap (§6.1). [VERIFIED-web]
- **S-parameter convergence & passivity** — S must converge under adaptive mesh; a **passive**
  device needs `|S| ≤ 1` (eigenvalues of `SᴴS ≤ 1`) and **reciprocal** `S = Sᵀ` (no
  ferrites/active) — non-passive/non-reciprocal results flag a port or mesh error. [VERIFIED-web]
- **Spurious-mode check (eigen)** — with edge elements physical modes are clean; a cluster of
  near-zero "DC modes" is the gradient null space (expected, filtered), *not* spurious — true
  spurious modes appear only with nodal elements (§4). [VERIFIED-web]
- **Box-size / truncation invariance** — grow the air box; S₁₁/gain must not move (§4).
- **Mesh independence / GCI** — same discipline as the rest of CAE (`references/vv-uq.md`).
- **Analytic anchors** — coax/parallel-plate capacitance, infinite-solenoid inductance, skin
  depth in a slab, dipole input impedance: sanity-check the solver on a closed-form case first.

---

## 9. Headless / automation

EM solvers are increasingly script-first; batch sweeps (frequency, geometry, drive state) are
the norm. Cross-link `references/agent-automation-boundary.md` for the general GUI-vs-batch
discipline.

- **PyAEDT (Ansys Electronics Desktop — HFSS, Maxwell, Q3D, Icepak, etc.)** [VERIFIED-web]
  - `pip install pyaedt`; **`import ansys.aedt.core`** (the modern namespace; the older
    `import pyaedt` still aliases). Needs a **licensed local AEDT (2022 R1+)**.
  - **Non-graphical/batch:** launch with `non_graphical=True` (default is GUI/False) — e.g.
    `Hfss(non_graphical=True, new_desktop=True)`, `Maxwell3d(...)`. One Python script can build
    geometry, assign materials/boundaries/ports/excitations, mesh, solve, sweep, and extract
    S-params/fields/loss — enabling **far higher simulation volume than manual GUI work.** [VERIFIED-web]
  - Also drives **parametric/optimization** loops and multiphysics hand-off (HFSS→Icepak,
    Maxwell→Mechanical).
- **COMSOL AC/DC & RF** — batch via **`comsol batch -inputfile model.mph`**, **COMSOL
  Compiler / Application Builder**, **Java API**, or **LiveLink for MATLAB**; parameter sweeps
  and cluster runs headless.
- **CST Studio Suite** — VBA macros and a **Python library (`cst`)** for headless project
  control and post-processing.
- **Open-source stack** [VERIFIED-web]:
  - **getDP + ONELAB/Gmsh** — purpose-built FEM EM (electro/magneto-statics, eddy-current,
    full-wave), PETSc solvers, fully scriptable `.pro` problem files; the strongest open EM-FEM.
  - **Elmer (CSC)** — multiphysics FEM with magnetostatic/electrostatic/eddy-current and
    wave-equation solvers; SIF text input, MPI; couples to OpenFOAM (EOF-Library) for MHD.
  - **FEniCSx** — general PDE/FEM in Python; H(curl) (Nédélec) elements available, good for
    custom/research EM formulations; couples to **Bempp** for FEM-BEM.
  - **MoM/FDTD open-source:** **openEMS** (FDTD), **NEC2 / necpp** (wire MoM), **Meep** (FDTD,
    photonics), **scuff-em** (BEM) — pick by method/regime per §5.

---

## 10. Top mistakes (quick-reference)

1. **Wrong regime:** quasi-static solver above ~λ/10 (misses radiation/resonance), or full-wave
   at DC (low-frequency breakdown, singular system). Pick the regime first (§1).
2. **Nodal elements for a vector field** → spurious modes that don't converge away. Use **edge
   (Nédélec)** elements (§4).
3. **Skin depth not meshed** (< 2 layers in δ) → **over-predicted eddy/AC losses** and wrong
   AC R/L (§3).
4. **No gauge** on a magnetostatic / non-conducting A-formulation → singular matrix; or omitting
   **cuts** for multiply-connected T-Ω conductors (§8).
5. **Reduced scalar potential in high-μ iron** → cancellation error; use total Ω (or A) there (§2).
6. **Air box too small / wrong truncation** — ABC < λ/4 or PML touching the structure → reflected
   waves corrupt S₁₁/gain; verify box-size invariance (§4, §8).
7. **Wrong port** (lumped where a wave port is needed) or un-de-embedded reference plane →
   wrong S-parameters (§4).
8. **Torque from a single MST contour on a coarse air-gap mesh** (especially cogging) → noisy;
   use Arkkio/virtual-work and refine the gap; cross-check methods (§6.1, §8).
9. **Sinusoidal Bertotti for PWM / rotational / minor-loop fields** → under-predicted core loss
   (§6.1).
10. **Harmonic (effective-μ) solve for a saturating nonlinear machine** where a transient is
    required (§3).
11. **One-way EM→thermal when σ(T)/μ(T) matter** (induction heating across Curie, microwave) →
    needs two-way iteration with sub-cycling (§7).
12. **Wrong CEM method for the problem** — FEM volume-meshing a huge open radiator (use MoM), or
    MoM on an arbitrarily inhomogeneous body (use FEM) (§5).
13. **Trusting one adaptive pass** — not checking the ΔS / mesh-convergence curve (§8).

---

## See also

- `references/thermal-and-coupling.md` — the EM→thermal hand-off (Joule/induction/dielectric
  heating as a thermal body load; energy balance; T-dependent properties).
- `references/dynamics-nvh-acoustics.md` — the structural→acoustic half of motor NVH (modal /
  forced response, vibro-acoustics) excited by EM air-gap forces (§7).
- `references/solver-numerics.md` — linear/eigen/nonlinear solvers, conditioning, time
  integration; pull-in/snap-through (arc-length) for MEMS; eigen spurious-mode discipline.
- `references/software-landscape.md` — HFSS / Maxwell / CST / COMSOL positioning and the
  open-source stack.
- `references/agent-automation-boundary.md` — general GUI-vs-batch / headless discipline that
  PyAEDT/COMSOL-batch/getDP fall under (§9).
- `references/vv-uq.md` — mesh-independence / GCI and credibility scaling applied to EM QoIs.

---

## SOURCES

Reliability key: **H** = primary vendor theory/user manual, textbook, or peer-reviewed/standards
body (highest); **M** = vendor knowledge-base / reputable practitioner / encyclopedic reference
cross-checked; **L** = forum/secondary (corroborative only).

1. Jin, *The Finite Element Method in Electromagnetics* (3rd ed., Wiley/IEEE) — canonical text:
   formulation by regime, edge/Nédélec elements, spurious modes, ports, ABC/PML, FE-BI. **H**
   (standard reference; topic canon).
2. F. Kikuchi, "Numerical Analysis of Nédélec's Edge Elements" (RIMS Kôkyûroku 1145) — edge
   elements eliminate spurious modes; tangential continuity / null-space representation.
   https://www.kurims.kyoto-u.ac.jp/~kyodo/kokyuroku/contents/pdf/1145-1.pdf — **H**.
3. "Comparative Performance of Novel Nodal-to-Edge finite elements over Conventional Nodal
   element for Electromagnetic Analysis," arXiv:2203.14522 — why nodal fails (spurious,
   non-converging); edge allows normal jump. https://arxiv.org/pdf/2203.14522 — **M**.
4. "And Yet Another FEM-Based Mode Solver for Dielectric Waveguides," arXiv:2604.12014 — mixed
   edge(transverse)+nodal(longitudinal) waveguide mode solver, spurious suppression.
   https://arxiv.org/abs/2604.12014 — **M** (arXiv ID verified live, Apr 2026).
5. "High-Order Hierarchical Nédélec Edge Elements" — p-refinement vector elements.
   https://doi.org/10.1109/8.791939 — **M** (canonical p-refinement H(curl) basis: Webb, *IEEE TAP* 47(8):1244–1253, 1999).
6. Ansys Maxwell Help, "Skin Depth for an Eddy Current T-Ω Solution" — δ = √(2/ωμσ); fields
   penetrate ~4–5 skin depths; eddy/skin effects must be explicitly requested; impedance
   handling.
   https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v242/en/Subsystems/Maxwell/Content/SkinDepthforanEddyCurrentSolution.htm
   — **H** (vendor doc).
7. "Skin Depth Considerations in Eddy Current NDT" (Springer) — δ = √(1/πfμσ); resolution of
   the skin layer. https://link.springer.com/chapter/10.1007/978-1-4615-3344-3_37 — **H/M**.
8. CEA, "FEM technique for modeling eddy-current testing of ferromagnetic media with small skin
   depth" — under-resolved δ → A-formulation **over-estimates losses**; refinement need.
   https://cea.hal.science/cea-01845468v1/document — **H**.
9. "T-Ω formulation for eddy-current problems in multiply connected regions" — T-Ω vs A-V,
   cuts/multiply-connected. https://doi.org/10.1063/1.338583 — **H/M** (canonical cuts reference: Kotiuga, *J. Appl. Phys.* 61(8):3916–3918, 1987).
10. "Homogenized harmonic balance FEM for nonlinear eddy current… ," arXiv:2503.19657 — harmonic
    vs transient for nonlinear/saturating iron; effective-permeability limits.
    https://arxiv.org/pdf/2503.19657 — **M**.
11. SimuTech / Ozen, "Antenna Design using Ansys HFSS" — HFSS = full-wave frequency-domain FEM;
    wave vs lumped ports, S-parameters, radiation boundary, PML, FE-BI; near/far field.
    https://simutechgroup.com/resources/blog/designing-antennas-using-ansys-hfss/ ·
    https://blog.ozeninc.com/resources/designing-antennas-using-ansys-hfss — **M** (vendor
    channel).
12. EDABoard / HFSS boundary-condition thread + Ozen HFSS setup lecture — ABC standoff ~λ/4, PML
    near-zero reflection / box-size-independent far field, radiation-boundary "balloon."
    https://www.edaboard.com/threads/hfss-antenna-boundary-conditions.196521/ ·
    https://www.ozeninc.com/wp-content/uploads/2021/03/ANSYS_HFSS_L03_1_HFSS_3D_DesignSetup.pdf
    — **M/L**.
13. Cadence System Analysis, "FDTD vs FEM vs MoM: What Are They and How Are They Different" —
    method strengths/weaknesses and selection.
    https://resources.system-analysis.cadence.com/blog/msa2021-fdtd-vs-fem-vs-mom-what-are-they-and-how-are-they-different
    — **M**.
14. EMWorks, "When to Use FEM, CFD, MoM, and More" + AN-SOF "Navigating the Numerical
    Landscape" — practical method-selection by problem (planar/MoM, 3-D closed/FEM, broadband/FDTD).
    https://www.emworks.com/blog/when-to-use-fem-cfd-mom-and-more-a-practical-look-at-computational-methods-for-engineers
    · https://antennasimulator.com/index.php/knowledge-base/navigating-the-numerical-landscape-choosing-the-right-antenna-simulation-method/
    — **M**.
15. Morris (ARMMS), "Which Electromagnetic Simulator Should I Use?" — MoM only meshes surfaces
    (open-region advantage), FEM/FDTD for true 3-D; narrow- vs broad-band.
    https://www.armms.org/media/uploads/09_armms_nov11_dmorris.pdf — **M**.
16. EpsilonForge, "Open-Source Electromagnetic Simulation: FDTD, FEM, MoM" — getDP/ONELAB,
    Elmer, FEniCS, openEMS, Bempp FEM-BEM coupling. https://www.epsilonforge.com/post/open-source-electromagnetics/
    — **M**.
17. Silwal/Rasilo (TUT), "Computation of Torque of an Electrical Machine With Different Types of
    FE Mesh in the Air Gap" — MST contour sensitivity, air-gap mesh, Arkkio.
    https://homepages.tuni.fi/paavo.rasilo/pubs/Silwal2014.pdf — **H**.
18. "Comparison of Different FE Calculation Methods for the Electromagnetic Torque of PM
    Machines" — MST vs co-energy vs virtual work cross-check. (Cited by official title;
    consult via the publisher / a reputable academic index, not a re-hosted copy.) — **M**.
19. "On torque computation in electric machine simulation by harmonic mortar methods,"
    arXiv:2112.05572 — sliding interface / moving band / mortar coupling for rotation.
    https://arxiv.org/pdf/2112.05572 — **H/M**.
20. "Mitigation of cogging torque… shape & topology optimization" + correlation-of-cutting
    study (PMC8622082) — cogging mesh sensitivity, Bertotti/iron-loss factors and degradation.
    https://doi.org/10.1108/EC-01-2015-0007 · https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8622082/
    — **M/H**.
21. COMSOL AC/DC Module User's Guide (6.0) + "Comparison of magnetic vector and total scalar
    potential," arXiv:2107.01957 — A-formulation needs edge elements + gauge; scalar potential
    fewer DOF; gauge-fixing required for stationary / not for transient σ≠0; total vs reduced Ω;
    reduced-scalar cancellation in high-μ iron.
    https://doc.comsol.com/6.0/doc/com.comsol.help.acdc/ACDCModuleUsersGuide.pdf ·
    https://arxiv.org/pdf/2107.01957 — **H**.
22. COMSOL AC/DC Module product page + "A reduced scalar potential approach for magnetostatics,"
    arXiv:2405.01082 + "Efficient Reduced Magnetic Vector Potential…," arXiv:2309.02004 —
    magnetomechanics/electromechanics/Joule+expansion/induction couplings; reduced formulations.
    https://www.comsol.com/acdc-module · https://arxiv.org/pdf/2405.01082 · https://arxiv.org/pdf/2309.02004
    — **H/M**.
23. "Coupled electromagnetic-thermal solution strategy for induction heating of ferromagnetic
    materials," *Applied Math Modelling* — two-way EM↔thermal, σ(T)/μ(T), Curie, sub-cycling.
    https://www.sciencedirect.com/science/article/pii/S0307904X22003298 — **H**.
24. "A combined electromagnetic and thermal analysis of induction motors" + induction-heating
    thermal studies — Joule/eddy heat source, sequential vs fully coupled.
    https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/elps.202400216
    — **M/H**.
25. "Overview of H-Formulation: A Versatile Tool for Modeling Electromagnetics in HTS
    Applications" (+ H-Φ COMSOL impl. arXiv:2006.13784, coupled A-H arXiv:1909.03312,
    H-formulation AC-loss review arXiv:1908.02176) — HTS E-J power law, H/H-Φ/A-H/T-A, EM-thermal
    & EM-mechanical coupling. https://doi.org/10.1109/ACCESS.2020.2996177 ·
    https://arxiv.org/pdf/2006.13784 · https://arxiv.org/pdf/1909.03312 · https://arxiv.org/pdf/1908.02176
    — **H/M**.
26. "FEM analysis of electro-mechanical coupling effect of piezoelectric materials," *Comp. Mat.
    Sci.* — coupled displacement+voltage DOF (intrinsically two-way).
    https://www.sciencedirect.com/science/article/abs/pii/S0927025697000414 — **H**.
27. PyAEDT (PyAnsys) — GitHub/PyPI/docs: `pip install pyaedt`, `import ansys.aedt.core`,
    `non_graphical` launch (default GUI), AEDT 2022 R1+, batch/high-volume simulation across
    HFSS/Maxwell/Q3D/Icepak. https://github.com/ansys/pyaedt · https://pypi.org/project/pyaedt/ ·
    https://aedt.docs.pyansys.com/version/stable/Getting_started/index.html ·
    https://aedt.docs.pyansys.com/version/stable/API/_autosummary/ansys.aedt.core.hfss.Hfss.html
    — **H** (vendor/PyAnsys docs).
28. getDP/ONELAB & Elmer & FEniCSx — open-source EM-FEM solvers (getDP eddy-current/full-wave +
    PETSc; Elmer magnetostatic/electrostatic/wave + EOF-Library OpenFOAM coupling; FEniCSx PDE/FEM
    Python). https://www.epsilonforge.com/post/open-source-electromagnetics/ ·
    https://www.sciencedirect.com/science/article/pii/S2352711018302164 · https://learnemc.com/free-cem-codes
    — **M**.
