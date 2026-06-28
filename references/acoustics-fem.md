# Acoustics FEM: Ducts/Mufflers, Absorption, Exterior Truncation (IE/PML), Poroelastic Trim, Aeroacoustics, SEA & Hybrid FE-SEA, Transmission Loss, Structural-Acoustic Coupling, and Mistakes

Vendor-neutral reference for CAE/FEM acoustics practitioners. Each section gives concrete methodology, key formulas with numbers, and source URLs. Primary authority is textbooks, standards, peer-reviewed papers, and official solver documentation; practitioner pages and encyclopedia-style pages are orientation/corroboration only, not load-bearing authority. Items that could not be cross-verified against at least two authoritative sources are flagged [UNVERIFIED] or [SINGLE-SOURCE].

Sources prioritized: COMSOL Acoustics Module official documentation, Actran/Hexagon documentation, peer-reviewed papers (Acta Acustica, JASA, JCP), Altair OptiStruct/Acoustic documentation, and canonical acoustics texts (Pierce, Munjal, Fahy/Gardonio, Lyon/DeJong, Allard/Atalla). CFDyna, HandWiki, Engineering.com, vendor blogs, and ScienceDirect topic pages are retained only as orientation links where a primary source is also named.

---

## Contents

- [1. Duct Acoustics and Muffler Analysis: 4-Pole (Transfer Matrix) Method](#1-duct-acoustics-and-muffler-analysis-4-pole-transfer-matrix-method)
- [2. Cut-On Frequency for Higher-Order Modes in Ducts](#2-cut-on-frequency-for-higher-order-modes-in-ducts)
- [3. Absorption: Impedance Boundary Condition and Room Acoustics](#3-absorption-impedance-boundary-condition-and-room-acoustics)
- [4. Infinite Elements vs PML for Exterior Acoustics](#4-infinite-elements-vs-pml-for-exterior-acoustics)
- [5. Aeolian / Flow Noise Basics (Vortex Shedding)](#5-aeolian-flow-noise-basics-vortex-shedding)
- [6. Top Acoustics Mistakes in FEM/CAE](#6-top-acoustics-mistakes-in-femcae)
- [7. Poroelastic & Sound-Package (Trim) Materials: Biot / JCA / Delany-Bazley](#7-poroelastic-sound-package-trim-materials-biot-jca-delany-bazley)
- [8. Aeroacoustics: Lighthill / Curle / FW-H and the Hybrid-CAA Workflow](#8-aeroacoustics-lighthill-curle-fw-h-and-the-hybrid-caa-workflow)
- [9. Statistical Energy Analysis (SEA) and Hybrid FE-SEA](#9-statistical-energy-analysis-sea-and-hybrid-fe-sea)
- [10. Airborne Transmission Loss of Panels and Partitions](#10-airborne-transmission-loss-of-panels-and-partitions)
- [11. Structural-Acoustic Coupling (Depth): the Unsymmetric {u, p} System](#11-structural-acoustic-coupling-depth-the-unsymmetric-u-p-system)
- [12. Quick-Reference Numbers](#12-quick-reference-numbers)
- [Sources Summary (all topics)](#sources-summary-all-topics)
- [See also](#see-also)

## 1. Duct Acoustics and Muffler Analysis: 4-Pole (Transfer Matrix) Method

### Conceptual framework

The Transfer Matrix Method (TMM) — also called the four-pole or transmission matrix method — is the standard 1-D analytical tool for muffler and silencer design. It treats each duct element as a two-port network that maps the state vector [p, U] (acoustic pressure p, acoustic volume velocity U = v_n · A) at its inlet to its outlet:

```
[p₁]   [T₁₁  T₁₂] [p₂]
[U₁] = [T₂₁  T₂₂] [U₂]
```

**Cascading property:** When multiple elements are in series (straight duct + expansion chamber + perforated tube + …), the overall system matrix is the ordered product of the individual matrices:

```
[T_system] = [T₁] · [T₂] · [T₃] · …
```

This is why TMM is so efficient — complicated systems reduce to a 2×2 product. It is analogous to a thermal or electrical network of lumped elements.

**Reciprocity / passive network constraint:** For a passive, linear, reciprocal system the determinant must satisfy:

```
T₁₁ · T₂₂ − T₁₂ · T₂₁ = 1
```

Verify this as a sanity check when deriving or importing matrices numerically.

**Validity limit:** TMM assumes 1-D **plane-wave propagation** only. It is accurate **below the cut-on frequency** (see Section 2) where only the plane wave mode propagates. Above cut-on, higher-order 3-D modes appear and TMM breaks down — switch to FEM/BEM.

Authority: Pierce, *Acoustics – An Introduction to its Physical Principles and Applications*, and Munjal, *Acoustics of Ducts and Mufflers*. Orientation link only: CFDyna aeroacoustics reference — https://www.cfdyna.com/Home/AeroAcoustics.html

### Transfer matrices for standard elements

**Uniform straight duct, length L, cross-sectional area A:**
```
T₁₁ = T₂₂ = cos(kL)
T₁₂ = −j · (ρc/A) · sin(kL)      [Pa·s/m³]
T₂₁ = −j · (A/ρc) · sin(kL)      [m³/(Pa·s)]
```
where k = ω/c = 2πf/c is the wave number, ρ is fluid density, c is speed of sound.

**Simple expansion chamber, chamber area A₂, inlet/outlet area A₁, chamber length L:**

The expansion section and contraction section each contribute their own matrices. For the complete chamber (assuming inlet and outlet ducts are the same area A₁ and the chamber has area A₂):

```
T₁₁ = T₂₂ = cos(kL)
T₁₂ = −j · (ρc/A₂) · sin(kL)
T₂₁ = −j · (A₂/ρc) · sin(kL)
```

**Transmission Loss of simple expansion chamber** (with anechoic termination at outlet, area ratio m = A₂/A₁):

```
TL = 10 · log₁₀ [ 1 + ((m − 1/m)/2)² · sin²(kL) ]
```

- TL peaks occur when kL = π/2, 3π/2, … (i.e., f = c/(4L), 3c/(4L), …)
- TL passes through zero (pass bands) when kL = 0, π, 2π, … (i.e., f = 0, c/(2L), c/L, …)
- Larger area ratio m increases peak TL but does not shift the frequency of maxima/zeros

**General TL formula from the full 4-pole matrix** (for anechoic downstream termination, source impedance Z_s = ρc/A₁):

```
TL = 20 · log₁₀ [ |T₁₁ + T₁₂/Z_t + Z_s·T₂₁ + Z_s·T₂₂/Z_t| / 2 ]
```
where Z_t = ρc/A_t (termination impedance). For equal inlet/outlet area and anechoic termination Z_t = Z_s = ρc/A₁ this simplifies to:

```
TL = 20 · log₁₀ [ |T₁₁ + T₁₂·A₁/(ρc) + ρc·T₂₁/A₁ + T₂₂| / 2 ]
```

Sources:
- Munjal, *Acoustics of Ducts and Mufflers*, and Pierce, *Acoustics*. Orientation link: CFDyna practitioner reference: https://www.cfdyna.com/Home/AeroAcoustics.html
- Muffler transmission loss by the transfer-matrix method — Gerges et al., *J. Braz. Soc. Mech. Sci. Eng.* 27:132–140 (2005): https://doi.org/10.1590/S1678-58782005000200005
- Wiley Online Library, "Theoretical and Experimental Study on the Transmission Loss of a Side Outlet Muffler": https://onlinelibrary.wiley.com/doi/10.1155/2020/6927574

### When to use FEM vs TMM

| Criterion | Use TMM | Use FEM/BEM |
|---|---|---|
| Frequency range | Below cut-on (plane wave only) | Above cut-on (higher-order modes) |
| Geometry | Simple 1-D series elements | Complex 3-D shapes, curved walls, non-circular |
| Speed | Fast (seconds), ideal for parameter sweeps | Slow (minutes to hours), but accurate in 3-D |
| Flow effects | Included via Mach-number corrections to k | Full convection via linearized Euler/CAA |
| Perforated tubes, baffles | Available in extended TMM formulations | Naturally handled by FEM with impedance BCs |

**Perforated tubes/resonators:** Extended TMM adds transfer impedance across the perforated wall as an additional term coupling the inner and outer channels — commonly used for catalytic converters and diesel particulate filter mufflers. See Munjal (1987) for formulations; FEM becomes the preferred tool when the perforation geometry is irregular.

Authority: Munjal, *Acoustics of Ducts and Mufflers*. Orientation link only: https://www.cfdyna.com/Home/AeroAcoustics.html

---

## 2. Cut-On Frequency for Higher-Order Modes in Ducts

The cut-on (cut-off) frequency is the frequency above which a given higher-order acoustic mode begins to propagate without exponential decay along the duct axis. Below this frequency only the plane wave (0,0) mode propagates, making the duct 1-D. Above it, 3-D analysis is required.

### Circular duct (diameter D = 2R)

The (m,n) mode has cut-on wavenumber k_{mn} = χ'_{mn} / R where χ'_{mn} is the n-th root of the derivative of the Bessel function J'_m = 0.

**First higher-order mode cut-on (m=1, n=1):**
```
χ'₁₁ = 1.8412   →   f_c1 = 1.8412 · c / (π · D)
```
Numerically at 20°C (c = 343 m/s):
```
f_c1 [Hz] ≈ 1.8412 × 343 / (π × D) = 201 / D [m]
```
Example: D = 0.1 m (100 mm) → f_c1 ≈ 2010 Hz.

**Second cut-on (m=2, n=1):** χ'₂₁ = 3.054 → f_c = 3.054 · c / (π · D)

**First axisymmetric (m=0, n=1):** χ'₀₁ = 3.832 → f_c = 3.832 · c / (π · D) — even higher.

Source (A.D. Pierce, cited in CFDyna): f_CUT-ON = 1.8412 × c / (πD) — https://www.cfdyna.com/Home/AeroAcoustics.html; cross-verified by Acta Acustica (Ford et al., 2023): https://acta-acustica.edpsciences.org/articles/aacus/full_html/2023/01/aacus220052/aacus220052.html

### Rectangular duct (width a, height b, a ≥ b)

Mode (m,n) cut-on:
```
f_{mn} = (c/2) · sqrt( (m/a)² + (n/b)² )
```

**First higher-order mode (m=1, n=0):**
```
f_c = c / (2a)
```
Example: a = 0.2 m, c = 343 m/s → f_c = 857 Hz.

Source: MDPI Applied Sciences, "Three-Dimensional Acoustic Analysis of a Rectangular Duct with Gradient Cross-Sections": https://www.mdpi.com/2076-3417/12/11/5307

### Elliptical duct (major half-axis a, minor half-axis b)

```
f_c = β · c / (2πa)
```
where β is a function of eccentricity e = sqrt(1 − b²/a²), determined from Mathieu function roots.

Source: CFDyna reference: https://www.cfdyna.com/Home/AeroAcoustics.html

### Practical implication

- **Below f_c:** Use TMM (1-D, plane wave). Plane wave assumption is valid. Muffler design in the low-frequency exhaust range typically falls in this regime.
- **Above f_c:** Cross-modes propagate. TMM gives wrong results. Use 3-D FEM or BEM. FEM muffler models for broadband performance must include the frequency range well above f_c.
- **Quick check:** For a circular exhaust pipe of 80 mm diameter, f_c ≈ 201/0.08 ≈ 2,500 Hz — this is well within the audible / NVH-relevant range for automotive exhausts.

---

## 3. Absorption: Impedance Boundary Condition and Room Acoustics

### Sabine absorption and reverberation

**Absorption area (sabins):**
```
A = Σ (αᵢ · Sᵢ)    [m² or sabins]
```
where αᵢ = absorption coefficient of surface i (dimensionless, 0 to 1), Sᵢ = area of that surface [m²].

**Sabine reverberation time** (time for sound to decay 60 dB):
```
T₆₀ = 0.161 · V / A    [seconds]
```
where V = room volume [m³], A = total absorption area [m²].

**Limitation:** Sabine's formula assumes a **diffuse field** (uniform energy density). It is invalid for highly absorptive spaces (α > ~0.2) where the Eyring formula is more accurate:
```
T₆₀ = 0.161 · V / (−S · ln(1 − ᾱ))
```
where ᾱ is the average absorption coefficient and S is total surface area.

Sources:
- ScienceDirect, "Sabine Equation — an overview": https://www.sciencedirect.com/topics/engineering/sabine-equation
- Acousticlab reverberation time reference: https://www.acousticlab.com/en/reverberation-time-and-sabines-formula/

### Impedance boundary condition in FEM

The **specific normal acoustic impedance** at a boundary surface is:
```
Z_n = p / v_n    [Pa·s/m = Rayl]
```
where p is the acoustic pressure and v_n is the normal particle velocity at the surface.

**Relationship to absorption coefficient α and reflection coefficient Γ:**
```
Γ = (Z_n − ρc) / (Z_n + ρc)          [reflection coefficient, complex]
α = 1 − |Γ|²                           [power absorption coefficient]
```
Conversely, given a measured α, the corresponding impedance (for normal incidence) is:
```
Z_n = ρc · (1 + sqrt(1−α)) / (1 − sqrt(1−α))    [real, lossless estimate]
```
Note: measured random-incidence α (Sabine) ≠ normal-incidence α. Use the appropriate conversion when populating FEM BCs.

**Implementation in COMSOL:** In Pressure Acoustics, apply an "Impedance" boundary node and specify Z_n = p/v_n directly, or specify the impedance in terms of absorption coefficient. Frequency-dependent Z(f) can be tabulated.

**Implementation in Actran:** Apply an impedance condition as a frequency table or material model on the surface panels.

**Implementation in Nastran (Simcenter):** PACINF bulk data card defines the acoustic impedance for a surface; CACINF elements reference it.

### Locally reacting vs extended reacting

| Type | Definition | Applicability |
|---|---|---|
| **Locally reacting** | The surface impedance Z_n depends only on the local pressure/velocity at that point — no wave propagation within the absorber | Thin panels, liners where in-plane propagation is negligible; standard impedance BC |
| **Extended reacting** | Waves propagate within the absorber material; the response at one point depends on the entire absorber field | Thick porous blankets, bulk-reacting liners; requires modeling the absorber domain explicitly (e.g., Biot model) |

**Practical rule:** Use locally reacting (simple impedance BC) for thin treatments and when the absorber thickness ≪ λ. Switch to extended reacting (model the porous layer explicitly) for thick insulation or when oblique-incidence behavior matters.

Sources:
- NASA NTRS, "Examination of the Measurement of Absorption": https://ntrs.nasa.gov/api/citations/20150023091/downloads/20150023091.pdf
- ScienceDirect, "Efficiency of room acoustic simulations with time-domain FEM including frequency-dependent absorbing boundary conditions": https://www.sciencedirect.com/science/article/abs/pii/S0003682X21003066

---

## 4. Infinite Elements vs PML for Exterior Acoustics

Both methods truncate the FEM computational domain so that an acoustic model can simulate open, anechoic, free-field radiation without a physical boundary that reflects waves back.

### Infinite Elements (IE / IFEM)

**Origin and formulation:** Developed by Burnett (1994) and Astley et al. (1994, 1998). The key references for Actran's implementation are:
- Astley, Macaulay, Coyette (1994), *J. Sound Vibration* 170(1):97–118
- Astley, Macaulay, Coyette, Cremers (1998), *JASA* 103(1):49–63

The idea is to attach semi-infinite elements to the outer surface of the FEM mesh that extend to r → ∞. Inside each element, the solution is represented as a **wave-envelope × polynomial decay**:

```
p(r,θ,φ) = (e^{ikr} / r) × Σ a_n · P_n(cos θ) × 1/rⁿ    [schematically]
```

The mapped coordinate η ∈ [−1, +1) maps to physical r ∈ [R, ∞) via:

```
r = R · (1 + η) / (1 − η)    →    η = 1 is r = ∞
```

**Key properties:**
- The element matrices are **frequency-dependent** (contain k = ω/c) — a different matrix must be assembled for each frequency
- Works best for **convex outer boundaries** (sphere or ellipsoid enclosing all sources and scatterers) — accuracy degrades for concave boundaries
- IE elements must be **centered on the source region** (the origin of the wave envelope expansion)
- **Same mesh** is used across all frequencies in the analysis (mesh is frequency-independent; the matrix depends on k)
- For frequency sweeps with a fixed mesh, IE is straightforward — just reassemble with the new k

**Availability:** Actran (conjugated IE, Astley formulation — historically the primary method), COMSOL Acoustics Module (IE available alongside PML), Abaqus Acoustics.

**Actran note:** Actran was built from the ground up using IE as the primary non-reflecting BC, replacing BEM for exterior radiation. It uses *conjugated* infinite elements (Coyette & Van den Nieuwenhof, 2000, *JASA* 108(4):1464–1473).

Sources:
- Coyette & Van den Nieuwenhof (2000), *JASA* 108(4):1464-1473, and Actran/Hexagon documentation for infinite-element implementation.
- Orientation only: HandWiki Software:Actran (reference list with DOIs): https://handwiki.org/wiki/Software:Actran
- Orientation only: Engineering.com Actran overview: https://www.engineering.com/actran-for-acoustic-radiation-designs/

### Perfectly Matched Layer (PML)

**Origin and formulation:** Introduced by Bérenger (1994) for electromagnetics, adapted to acoustics by Collino & Tsogka (2001) and many others. The PML introduces a **complex-valued coordinate stretching** into the PML domain:

```
x̃ = x + (σ(x) / iω) · x̂    (frequency domain)
```

Equivalently, in the PML region the wave equation is modified so that waves entering from the physical domain **decay exponentially without reflection at the interface**, for any angle of incidence and any frequency — this is the key property.

**Key properties:**
- In the **frequency domain**, the PML imposes a complex-valued coordinate transformation; the thickness of the PML does not need to correspond to a specific number of physical wavelengths (COMSOL documentation: "The physical thickness of the layers is not important in frequency domain models. Here a real stretching is applied to mathematically scale the thickness relative to the wavelength.")
- In the **time domain**, the PML geometry and thickness DO matter — additional equations are solved for the inverse-Laplace-transformed fields. Use at least 8 mesh layers; set thickness L to contain the relevant frequency content of the transient signal.
- Works for **arbitrary geometry** (any convex or non-convex domain shape) — not restricted to spherical or ellipsoidal outer boundaries
- The PML is **frequency-by-frequency** in the sense that the complex stretching depends on ω — for broadband frequency sweeps, the matrices change with each frequency step

**Meshing guidelines (COMSOL 6.3 official documentation):**
- Use **structured mesh** (mapped in 2D, swept in 3D) inside the PML domain
- Frequency domain: use at least **5–6 mesh layers** (rational stretching) or **8 mesh layers** (polynomial stretching) through the PML thickness
- Time domain: use at least **8 mesh layers** of the same element size as the adjacent physical domain
- Ensure element size inside PML resolves the wavelength consistently with the physical domain

**Performance note (Altair APML):** The Altair OptiStruct Adaptive PML (APML) method divides the frequency range into **frequency bands** (adaptive factor 1.2 by default) and assembles the PML for each band — this is the key reason APML achieves improved performance over IE for broadband sweeps, while maintaining accuracy "similar to the Infinite Elements (IE) method."

Sources (all verified):
- COMSOL 6.3 official documentation, Perfectly Matched Layers (PMLs): https://doc.comsol.com/6.3/doc/com.comsol.help.aco/aco_ug_pressure.05.139.html
- Altair OptiStruct 2025, APML documentation: https://2025.help.altair.com/2025.1/hwsolvers/os/topics/solvers/os/analysis_acoustic_apml_c.htm
- Wiley NME, Bériot & Modave (2021), "An automatic perfectly matched layer for acoustic finite element simulations in convex domains of general shape": https://onlinelibrary.wiley.com/doi/full/10.1002/nme.6560
- JCP (2019), "A perfectly matched layer formulation adapted for fast frequency sweeps of exterior acoustics finite element models": https://dl.acm.org/doi/10.1016/j.jcp.2019.108878

### Sommerfeld absorbing BC (first-order radiation condition)

The simplest non-reflecting BC is the **Sommerfeld radiation condition** applied as a first-order absorbing boundary:
```
∂p/∂n + p/(c·Δt) = 0    (time domain)
∂p/∂r = −ik·p            (frequency domain, plane wave approximation)
```
This is exact only for **plane waves** hitting the boundary **perpendicularly**. For oblique angles, it generates spurious reflections that grow with angle. Use it only when:
- The boundary is far from all sources and scatterers (many wavelengths away)
- The geometry is such that nearly all radiation hits the boundary normally
- Accuracy requirements are low

In most serious FEM radiation analyses, PML or IE is preferred over a first-order Sommerfeld BC.

### Decision table: IE vs PML vs Sommerfeld

| Criterion | Infinite Elements | PML | Sommerfeld (1st order) |
|---|---|---|---|
| **Geometry of outer boundary** | Best for convex (sphere/ellipsoid) | Any shape (convex or not) | Any, but far-field only |
| **Accuracy at oblique angles** | High (captures all angles via wave expansion) | High (by construction, angle-independent) | Low (reflects oblique waves) |
| **Mesh changes between frequencies?** | No — same mesh, matrix reassembled with new k | No — same mesh, same formulation, just different k | No |
| **Frequency domain behavior** | Matrices depend on k; straightforward sweep | Physical thickness irrelevant; structured mesh required | Simple algebraic BC |
| **Time domain** | Difficult (history-dependent convolutions) | PML domain equations modified; 8+ mesh layers | Simple but reflective |
| **Non-convex outer boundaries** | Loses accuracy | Works correctly | Works (but reflects) |
| **Distance from sources / scatterers** | IE must enclose all sources; centering matters | PML must enclose all sources; can be thin shells | Must be many λ away |
| **Available in** | Actran (primary), COMSOL, Abaqus | COMSOL, Actran (APML), Altair (APML), Simcenter | Almost all codes |

**Rule of thumb for distance from sources:** Place the inner face of the IE or PML region at least **λ/2 to one full wavelength** from the nearest source or scatterer at the lowest frequency of interest. Too close → evanescent near-field contamination; the IE/PML is designed for propagating waves, not reactive near-fields.

Sources:
- COMSOL 6.3 documentation: https://doc.comsol.com/6.3/doc/com.comsol.help.aco/aco_ug_pressure.05.139.html
- Altair 2025 APML documentation: https://2025.help.altair.com/2025.1/hwsolvers/os/topics/solvers/os/analysis_acoustic_apml_c.htm
- Actran/HandWiki history with Astley citation: https://handwiki.org/wiki/Software:Actran
- Acta Acustica, "Partition of Unity FEM with PML" (2020): https://acta-acustica.edpsciences.org/articles/aacus/full_html/2020/04/aacus200026/aacus200026.html

---

## 5. Aeolian / Flow Noise Basics (Vortex Shedding)

### Physical mechanism

When a bluff body (e.g., a circular cylinder) is placed in a crossflow, **Kármán vortices** are shed periodically from alternate sides. These vortices produce periodic **lift force fluctuations** on the body. Because the force oscillates, it acts as a **dipole acoustic source** (force per unit volume). The resulting tonal noise is the **aeolian tone**.

### Strouhal number

The dimensionless shedding frequency is characterized by the **Strouhal number**:
```
St = f · d / U
```
where f = shedding frequency [Hz], d = cylinder diameter [m], U = freestream velocity [m/s].

**For a smooth circular cylinder** at Reynolds numbers 10³–10⁵ (where periodic vortex shedding is well-established):
```
St ≈ 0.2    (range ~0.18–0.22 depending on Re)
```

**Aeolian tone frequency:**
```
f_aeolian = St · U / d ≈ 0.2 · U / d
```

Example: U = 10 m/s, d = 0.05 m → f = 0.2 × 10 / 0.05 = 40 Hz.

Sources:
- Bohrium / Feynman aeolian tones reference: https://www.bohrium.com/en/sciencepedia/feynman/keyword/aeolian_tones
- Springer Experiments in Fluids (2020), cylinder vortex shedding: https://link.springer.com/article/10.1007/s00348-020-02972-0
- MDPI Aerospace (2025), D-shaped cylinder aeolian tone: https://www.mdpi.com/2226-4310/13/4/321

### Dipole source character and aeroacoustic scaling

The aeolian tone is a **dipole** — power radiated scales as U⁶ (in the compact-source, low-Mach limit via Lighthill's analogy applied to a dipole source). This contrasts with monopole (volume change) scaling U⁴ and quadrupole (turbulence-in-free-field) scaling U⁸.

For cylinders in a crossflow, the dominant radiation direction is **perpendicular to the flow** (the lift direction), consistent with a lateral dipole.

**Aeroacoustic source models:** Lighthill's analogy and the Ffowcs Williams–Hawkings (FW-H) extension are the foundation for all flow-noise prediction. They are developed in full — with the scaling laws, surface-vs-permeable FW-H surface choice, hybrid-CAA workflow, and RANS broadband screening — in **§8 (Aeroacoustics) below**, which is the authoritative home for the acoustic-propagation side. (The unsteady CFD that supplies the source data is described in `cfd.md`.)

Authority: Lighthill (1952), Curle (1955), and Ffowcs Williams-Hawkings (1969). Orientation link only: CFDyna aeroacoustics page (Lighthill section): https://www.cfdyna.com/Home/AeroAcoustics.html

---

## 6. Top Acoustics Mistakes in FEM/CAE

### Mistake 1: Too few elements per wavelength — the 6-EPW rule

**Rule:** Use at least **6 linear elements per wavelength** (h ≤ λ/6) at the highest frequency of interest. For quadratic (second-order) elements, 5–6 quadratic elements per wavelength suffice, since they resolve the wave shape more accurately per DOF.

```
λ = c / f_max     (c ≈ 343 m/s in air at 20°C)
h_max = λ / 6 = c / (6 · f_max)
```

Example: f_max = 4000 Hz → λ = 343/4000 = 0.0858 m → h_max = 0.0143 m (14.3 mm) for linear elements.

**Where does the "6" come from?** It is the empirical minimum needed to keep **dispersion error** (phase velocity error) acceptably small. FEM introduces a numerical wave number k_h that differs from the analytical k = ω/c:

```
k_h ≈ k · [1 + (kh)²/24 + ...]    (for linear elements)
```

With 6 elements/λ, kh = 2π/6 ≈ 1.047, giving a phase error of about 1–2% per wavelength. Over many wavelengths this **accumulates** — this is the **pollution error** (Ihlenburg & Babuška, 1995). The rule is a minimum, not a guarantee: for large domains (many wavelengths across), use more.

**COMSOL best practice (official blog):** For FEM, "a good mesh resolves the acoustic waves… the default physics-controlled mesh in COMSOL ensures about 5–6 elements per wavelength at the highest frequency." For large frequency sweeps, automate remeshing per frequency band.

**Pollution / dispersion error at high frequency:** Even satisfying 6-EPW, the error grows with k²h² per wavelength traveled. For long-range propagation or high-frequency acoustics, use **higher-order elements** (quadratic or spectral), **hp-FEM**, or switch to ray-tracing / SEA.

Sources:
- COMSOL Blog, "How to Automate Meshing in Frequency Bands for Acoustic Simulations": https://www.comsol.com/blogs/how-to-automate-meshing-in-frequency-bands-for-acoustic-simulations
- "More Than Six Elements Per Wavelength" — Langer, Maeder et al., *J. Comput. Acoust.* 25(4):1750025 (2017): https://doi.org/10.1142/S0218396X17500254
- Marburg, "Six boundary elements per wavelength: Is that enough?" — *J. Comput. Acoust.* 10(1):25–51 (2002): https://doi.org/10.1142/S0218396X02001401

### Mistake 2: Mesh sized for the lowest frequency, then used at higher frequencies

**Symptom:** The model gives good results at low frequency (mesh was designed for that range) but diverges or blows up at higher frequencies.

**Fix:** Size the mesh for **f_max**, not f_min. If the analysis covers 0–4000 Hz, mesh for 4000 Hz throughout. If memory is limiting, use frequency-band remeshing (COMSOL: parametric remesh per frequency band; Actran 2024.2: AUTOMATIC mode for exterior acoustics sets mesh size per frequency band automatically).

Source: COMSOL Blog: https://www.comsol.com/blogs/how-to-automate-meshing-in-frequency-bands-for-acoustic-simulations

### Mistake 3: Wrong element type — using structural (solid) elements for acoustic fluid

**What goes wrong:** Standard structural solid elements (SOLID185, SOLID186 in Ansys; CHEXA in Nastran) solve the **displacement** field and use the **stiffness matrix** formulation. Acoustic fluid requires solving the **pressure** field via the **Helmholtz equation** (or its weighted-residual FEM form), using **acoustic pressure elements** with a fluid mass matrix and stiffness based on compressibility.

**Correct element types:**
- Ansys MAPDL: FLUID30 (3-D acoustic fluid), FLUID38 (2-D), FLUID220/221 (higher-order, quadratic tet/hex)
- Simcenter Nastran: CHEXA/CTETRA with PSOLID referencing an acoustic material (MID → MAT10 card, which specifies bulk modulus K and density ρ)
- COMSOL: Pressure Acoustics interface automatically uses correct element formulation

**Coupled structural-acoustic:** Structural elements for the solid domain, pressure elements for the fluid domain, with a **fluid-structure interface** condition (FSI coupling: σ·n = −p·n on solid, and the solid normal acceleration drives the fluid). Getting the coupling condition wrong (wrong sign, wrong DOF mapping, or omitting it entirely) is a frequent error in hand-built models.

Source: Ansys Elements Reference (FLUID220/221): https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_elem/elem_acouselems.html

### Mistake 4: Forgetting structural-acoustic coupling when it matters

**When it matters:** Whenever the acoustic loading significantly changes structural vibration (mass-loaded by fluid) or the structural motion significantly changes the acoustic field. Key cases:
- **Thin panels in contact with heavy fluid** (water, dense gas): added acoustic mass lowers structural natural frequencies by up to tens of percent — "dry" (in vacuo) frequencies are wrong.
- **Vehicle interior cavity** + body panels: panel vibration is the noise source; the acoustic cavity feeds back through the coupling.
- **Loudspeaker / transducer design:** radiation impedance from the acoustic field changes the moving mass and damping of the diaphragm.

**When 1-way coupling is acceptable:** When fluid is air and the structure is stiff and heavy (large impedance mismatch) — structural motion drives acoustics, acoustic pressure back-reaction on the structure is negligible. Use 1-way: solve structural first → apply surface velocities as acoustic source.

Source: ScienceDirect structural-acoustic coupling: https://www.sciencedirect.com/article/abs/pii/S0022460X00934783

### Mistake 5: Using symmetry planes incorrectly for acoustic modes

**The error:** Applying a symmetry BC (p = 0 on the plane, which implies a pressure-release / antisymmetric condition; or ∂p/∂n = 0, which implies a rigid-wall / symmetric condition) to exploit geometric symmetry in a modal analysis — but then only capturing half the modes.

**What is filtered:** A rigid-wall symmetry plane (∂p/∂n = 0) passes **symmetric** modes and blocks **antisymmetric** modes. A pressure-release plane (p = 0) passes antisymmetric modes and blocks symmetric ones. If only one symmetry plane is used, half the mode family is invisible. If antisymmetric modes happen to be the dominant noise contributors, the model will completely miss them.

**Fix:** For acoustic eigenfrequency / modal analyses, run the **full model** unless you are explicitly and intentionally extracting only symmetric or only antisymmetric modes (e.g., for a coupled structural-acoustic problem where you know the excitation is symmetric). Even then, report both families and combine.

This is the same trap as in structural modal analysis (antisymmetric buckling / bending modes missed on a half-model).

### Mistake 6: Wrong boundary conditions — rigid wall vs impedance BC

**Rigid wall (default in FEM):** ∂p/∂n = 0 (zero normal velocity). Physically correct for a perfectly reflective, infinitely stiff, infinitely massive wall. **Overestimates** sound pressure levels in a room or cavity if any absorption is present.

**Common error:** Leaving all walls as rigid in a room acoustics model → predicted T₆₀ is infinite (no absorption), SPL at resonance is unphysically high. Every real wall has some absorption; at minimum, assign typical values (α_concrete ≈ 0.02–0.05, α_carpet ≈ 0.3–0.5, α_acoustic tile ≈ 0.5–0.9).

**Impedance BC:** Use Zn = ρc × (1 + Γ)/(1 − Γ) for a given target absorption coefficient α. Make it frequency-dependent if the absorber has known frequency-dependent properties.

**Pressure-release BC** (p = 0): Physically represents a free surface (water-air interface) or an open end of a duct. Do not confuse with the rigid-wall BC — they are the two extremes.

### Mistake 7: Forgetting radiation damping in coupled problems

**What radiation damping is:** When a vibrating structure radiates into an unbounded medium, the radiated sound carries energy away from the structure. This appears in the coupled equations as an **additional complex term** in the structural impedance — "radiation damping." It is the mechanism by which a loudspeaker diaphragm or a vibrating pipe is damped by the acoustic field.

**Error:** Solving a structural-acoustic model where the acoustic domain is truncated with a rigid wall (instead of a proper IE or PML) → acoustic energy reflects back → no net energy loss → structural resonance peaks are predicted far too sharply → predicted SPL at resonance is non-physical.

**Fix:** Always use a proper non-reflecting termination (IE, PML, or anechoic BC) at the boundary of an acoustic radiation problem. If the problem is purely interior (a sealed cavity), radiation damping is absent by definition and the model is correct without it — but then include material absorption.

### Mistake 8: Using normal modes without enough modes for harmonic response

**Error:** Mode-superposition frequency response with too few modes in the modal basis → missing response contributions from truncated modes → incorrect (non-conservative) amplitude predictions, especially at anti-resonances and for forces/stresses.

**Fix:** Include modes up to 1.5–2× f_max; verify ≥ 80–90% effective mass; add **residual vectors** (acoustic mode-acceleration correction) to capture static contribution of truncated high-frequency modes. This is equally important for acoustic and structural modes in coupled systems.

### Mistake 9: Wrong or frequency-constant absorption coefficient assignment

**Error:** Assigning a single absorption coefficient α at one frequency (e.g., the standard 500 Hz test value) for all frequencies in the analysis. Absorption coefficients are strongly frequency-dependent — a carpet may have α ≈ 0.1 at 125 Hz but α ≈ 0.6 at 2000 Hz.

**Fix:** Use **frequency-dependent impedance tables** derived from measured data (ISO 354 measurements in reverberation chambers). In COMSOL, Actran, and Simcenter 3D Acoustics, you can import a Z(f) table as the boundary condition.

### Mistake 10: Applying SEA at too-low frequency (insufficient modal density)

**When SEA is valid:** Statistical Energy Analysis assumes a **high modal density** in each subsystem — roughly ≥ 5–10 modes per octave band in each subsystem. Below this threshold, deterministic mode shapes dominate and the statistical averaging assumption breaks down.

**Modal density for a 3-D acoustic cavity:**
```
n(f) ≈ 4πV·f² / c³   [modes per Hz]
```
For a small room (V = 50 m³, c = 343 m/s): n(1000 Hz) ≈ 4π × 50 × 10⁶ / 4.04×10⁷ ≈ 15.5 modes/Hz — adequate. At 100 Hz: n ≈ 0.155 modes/Hz — completely inadequate for SEA.

**Rule of thumb crossover frequency:** FEM/BEM for f < f_SEA; SEA for f > f_SEA. Hybrid FE-SEA covers the mid-frequency gap. The SEA crossover is typically **500–2000 Hz** for room acoustics, and scales downward for larger structures.

Source: Lyon & DeJong, *Theory and Application of Statistical Energy Analysis*, 2nd ed. (Butterworth-Heinemann, 1995) — the canonical SEA text (modal-density n(f), coupling-loss factors, modal-overlap / FEM↔SEA crossover). Orientation: Wikipedia — Statistical energy analysis, https://en.wikipedia.org/wiki/Statistical_energy_analysis

### Mistake 11: Not validating the acoustic FEM model against known analytical solutions

**Mandatory validation checks before trusting any acoustic FEM result:**

1. **Closed-form plane wave in a duct:** 1D tube, rigid walls, analytically known resonant frequencies f_n = nc/(2L). FEM should match to < 1%.
2. **Simple expansion chamber TL vs. TMM:** Compute TL by FEM (two-port BCs) and compare with the analytical formula above. Discrepancy > 3–5% → mesh too coarse at the highest frequency or wrong BCs.
3. **Radiation from a baffled piston (Rayleigh integral):** Compare FEM far-field directivity against the analytical Rayleigh integral result for a circular piston.
4. **Free-field Green's function:** Point source in unbounded domain; check that the FEM+PML result decays as 1/r.

### Mistake 12: PML / Infinite Element placed too close to sources or scatterers

**The error:** Placing the IE or PML inner boundary in the acoustic **near-field** of the source or scatterer. IE and PML are formulated for **propagating waves** — they cannot correctly absorb the evanescent near-field that decays exponentially from the source.

**Fix:** Place the IE/PML at least **λ/2 at the lowest frequency** (preferably one full wavelength) from the nearest source or scatterer surface. For acoustic radiation problems, the near-field extends roughly ~1/(2π) × λ ≈ λ/6 from a compact source, so at least λ/4 clearance is a practical minimum.

**COMSOL / Altair APML guidance:** The APML mesh must "fully enclose the vibrating structure." The COMSOL documentation warns: "When a PML is present in the model do not apply an Incident Pressure Field on its outer boundaries. The PML is applied to absorb waves that move out of the computational domain."

Sources:
- COMSOL 6.3 PML doc: https://doc.comsol.com/6.3/doc/com.comsol.help.aco/aco_ug_pressure.05.139.html
- Altair APML modeling guidelines: https://2025.help.altair.com/2025.1/hwsolvers/os/topics/solvers/os/analysis_acoustic_apml_c.htm

### Mistake 13: Forgetting temperature effects on speed of sound

**Formula:**
```
c = 331.3 · sqrt(T / 273.15)    [m/s]
```
where T is absolute temperature in Kelvin.

At key temperatures:
- 0°C (273.15 K): c = 331.3 m/s
- 20°C (293.15 K): c = 343.1 m/s
- 100°C (373.15 K): c = 386.9 m/s
- −40°C (233.15 K): c = 306.2 m/s (cold-soak engine)

**Errors this causes:**
- **Resonant frequencies:** f = c/(2L) — a 4% error in c gives a 4% error in all predicted frequencies
- **Cut-on frequencies:** f_c = 1.84·c/(πD) shifts linearly with c
- **TMM results:** All four-pole matrices contain k = ω/c — wrong c shifts TL curves in frequency
- **Muffler design:** Hot exhaust gas (c ≈ 450–500 m/s at 500°C exhaust temp) has dramatically different acoustics than cold air — a muffler tuned at cold conditions will not perform as designed at hot operation.

For air with humidity correction (more precise):
```
c ≈ 331.3 · sqrt(1 + T_C/273.15) · sqrt(1 + 0.0016·RH·P_sat/P_atm)
```
where RH is relative humidity and P_sat is saturation vapor pressure. Typically a 0.1–0.3% correction, negligible for most CAE purposes.

### Mistake 14: Not including mean flow effects in duct acoustics

For ducts carrying flow at Mach number M:
- The effective wave number becomes k⁺ = k/(1+M) downstream and k⁻ = k/(1−M) upstream (convection effect)
- The TMM matrices are modified (Munjal convective TMM)
- FEM: Use linearized Euler equations or the background flow in COMSOL's Aeroacoustics interface

**Rule of thumb:** For M < 0.05 (duct velocity < ~17 m/s in air at 20°C), flow effects on acoustics are < 5% and can usually be neglected. For automotive exhaust (M ~ 0.1–0.3) or HVAC at high velocity, flow corrections are important.

Source: CFDyna aeroacoustics page (citing Munjal): https://www.cfdyna.com/Home/AeroAcoustics.html

---

## 7. Poroelastic & Sound-Package (Trim) Materials: Biot / JCA / Delany-Bazley

Foams, fibrous blankets, felts, seat cushions, headliners, and acoustic liners ("sound package" / "trim") cannot be captured by a single rigid-wall or simple impedance BC when the treatment is thick or load-bearing. They are **porous media**: a solid frame (skeleton) saturated by air, with energy dissipated by viscous friction in the pores and by heat exchange between the air and the frame. The modelling choice is a ladder of increasing fidelity and cost. This section extends the locally-vs-extended-reacting distinction in §3 (the impedance BC is the *cheapest* rung; full Biot is the *most expensive*).

### Biot poroelastic theory — three waves

In a poroelastic medium the solid frame and the saturating fluid both carry stress and can move independently, so Biot theory predicts **three** propagating waves (vs one in a fluid):

| Wave | Character | Notes |
|---|---|---|
| **Fast compressional (P1)** | Frame-borne dilatation; frame and fluid roughly in phase | Dominates the structure-borne path |
| **Slow compressional (P2)** | Fluid-borne (Biot "slow wave"); frame and fluid out of phase | Highly attenuated, important near coupling surfaces |
| **Shear (S)** | Carried by the elastic frame only | Absent in equivalent-fluid models |

Use **full Biot** only when the **frame itself is elastic and vibrates** — i.e. the structure-borne path *through* the trim matters (low frequency, stiff or resonant frame, decoupled double walls, seats on rails). It is the most expensive model: FEM implementations use a **{u, U}** (solid + fluid displacement) or, more commonly, the reduced **{u, p}** (Atalla mixed) formulation, coupled to the surrounding acoustic cavity and structure.

### Equivalent-fluid (rigid-frame / limp-frame) reduction

When the frame either does not move (effectively rigid) or carries no stiffness (limp), the two compressional waves collapse and Biot reduces to a single **equivalent fluid** with complex, frequency-dependent effective density ρ_eq(ω) and bulk modulus K_eq(ω). This is the workhorse for most trim:

- **Rigid-frame:** frame much stiffer/heavier than the air load (most stiff/dense foams, high frequency, frame clamped). Only the in-pore air moves.
- **Limp-frame:** frame light and unsupported (light fibrous blankets, hanging felts) — adds the frame *mass* but not its stiffness to the effective density; gives a few-dB-accurate low-frequency correction over rigid-frame.

**Johnson–Champoux–Allard (JCA)** — the standard equivalent-fluid model, **5 macroscopic (non-acoustic) parameters**:

| Symbol | Parameter | Units | Typical range / role |
|---|---|---|---|
| σ | (static airflow) flow resistivity | Pa·s/m² (= N·s/m⁴, "rayl/m") | dominant; foams ≈ 5,000–50,000; light fiber 5,000–20,000; dense fiber up to ~100,000 |
| φ | open porosity | – | 0.90–0.99 for foams/fibers |
| α∞ | tortuosity (high-frequency limit) | – | 1.0–3.0 (1 = straight pores) |
| Λ | viscous characteristic length | m | ~10–250 µm; governs viscous (mid/high-f) loss |
| Λ′ | thermal characteristic length | m | Λ′ ≳ Λ (often ~2Λ); governs thermal loss |

JCA captures **both viscous and thermal dissipation** across the full audio band and is the default for foams and fibrous materials when the 5 parameters are characterized (impedance-tube + non-acoustic measurements, or inverse fitting). **JCAL** (6-param, adds static thermal permeability k₀′) and **JCAPL** (7-param, adds static viscous permeability) improve the low-frequency fit; use them when low-frequency accuracy is critical and the extra parameters are available.

**Delany–Bazley** and the **Miki** correction — **single-parameter** (flow resistivity σ only) *empirical* power-law fits of characteristic impedance and wavenumber for **fibrous** materials:

- Valid band: **0.01 < f/σ < 1.0** (f in Hz, σ in Pa·s/m²) — i.e. neither too low nor too high in the dimensionless frequency.
- **Delany–Bazley** is non-physical at low frequency (predicts negative real surface impedance). **Miki (1990)** re-fits the exponents to fix this and extend validity — prefer Miki over raw Delany–Bazley for any low-frequency work.
- Single-parameter convenience trades away accuracy vs JCA; use for quick estimates, fibrous-only, when only σ is known.

### Modelling-decision summary

| Situation | Model | Why |
|---|---|---|
| Frame stiff/heavy vs air load; high frequency | **Rigid-frame equivalent fluid (JCA)** | Frame motion negligible; cheapest accurate |
| Light, unsupported frame | **Limp-frame equivalent fluid (JCA + frame mass)** | Frame mass matters, stiffness does not |
| Frame elastic/resonant; structure-borne path through trim | **Full Biot** | Need the frame (P1) and shear waves and their coupling |
| Quick fibrous estimate, only σ known | **Miki (≻ Delany–Bazley)** | Single-parameter empirical, fibrous, mind 0.01<f/σ<1.0 |
| Thin treatment, absorber thickness ≪ λ | **Locally-reacting impedance BC (§3)** | No internal propagation to resolve |

### FEM practice

- **Coupled poroelastic FE:** Biot (u-U or u-p) elements meshed for the *frame* wave (often the slow wave is the resolution-limiting one), coupled to the acoustic cavity (porous↔fluid continuity of pressure and normal displacement) and to the structure (porous↔solid). Most expensive; reserve for the structure-borne cases above.
- **Equivalent-fluid domain:** mesh the trim as a lossy acoustic fluid with ρ_eq(ω), K_eq(ω) from JCA — far cheaper, couples to the cavity as an ordinary (complex) acoustic region.
- **Transfer-Matrix Method (TMM) layer:** for a locally-reacting *layered* trim (porous + air gap + septum + facing), compute the multilayer surface impedance Z(f) analytically (1-D plane-wave TMM through the layers, à la §1 but for normal/oblique incidence through porous layers) and apply it as a frequency-dependent impedance BC — the cheapest way to represent a known stack-up, valid when the trim is locally reacting and the panel is large vs wavelength. Cross-link to the impedance BC in §3 and the absorption-coefficient table in Mistake 6.

**Confidence: HIGH** (Allard & Atalla; Johnson-Koplik-Dashen 1987; Champoux-Allard 1991; Delany-Bazley 1970; Miki 1990; COMSOL Poroelastic Waves; Matelys APMR).

Sources:
- Allard & Atalla, *Propagation of Sound in Porous Media: Modelling Sound Absorbing Materials*, 2nd ed., Wiley (2009).
- Biot, "Theory of propagation of elastic waves in a fluid-saturated porous solid," *JASA* 28 (1956).
- Johnson, Koplik & Dashen, *J. Fluid Mech.* 176 (1987); Champoux & Allard, *J. Appl. Phys.* 70 (1991).
- Delany & Bazley, *Applied Acoustics* 3 (1970); Miki, *J. Acoust. Soc. Jpn (E)* 11 (1990).
- Matelys "Acoustical Porous Material Recipes" (APMR): https://apmr.matelys.com/
- COMSOL Poroelastic Waves / Acoustics Module documentation.

---

## 8. Aeroacoustics: Lighthill / Curle / FW-H and the Hybrid-CAA Workflow

Flow-induced (aerodynamic) noise — jets, fans, HVAC ducts, side mirrors, landing gear, cavity tones — is generated by the unsteady flow and then propagates as sound. **This section is the authoritative home for the acoustic-propagation side; `cfd.md` owns the unsteady, turbulence-resolving CFD that supplies the source data.** The aeolian-tone / vortex-shedding mechanism in §5 is the simplest special case (a compact dipole); here is the general framework.

### Lighthill's acoustic analogy

Lighthill (1952) rearranged the exact Navier–Stokes equations — with no approximation — into an inhomogeneous wave equation for the density perturbation ρ′ propagating in a quiescent medium at c₀:

```
∂²ρ′/∂t² − c₀²∇²ρ′ = ∂²T_ij/∂x_i∂x_j          (Lighthill's equation)
T_ij = ρ u_i u_j + (p′ − c₀²ρ′) δ_ij − τ_ij     (Lighthill stress tensor)
```

The three source contributions in T_ij:
- **ρ u_i u_j** — Reynolds-stress **quadrupole**; dominant in free turbulence at low Mach.
- **(p′ − c₀²ρ′)** — entropy / non-isentropic (compressibility, heat release) term.
- **τ_ij** — viscous stress; negligible at high Reynolds number.

For free turbulence (no solid surfaces, M ≲ 0.3–1), the quadrupole gives Lighthill's celebrated **jet-noise eighth-power law**:

```
P_acoustic ∝ ρ₀ U⁸ / c₀⁵          (free-field quadrupole)
```

### Curle — stationary solid surfaces add dipoles

Curle (1955) extended Lighthill to include **stationary** rigid surfaces. The surface integral introduces a **dipole** source — the fluctuating pressure (loading) on the body. At low Mach number the dipole **dominates the volume quadrupole**:

```
dipole  P ∝ U⁶   ≫   quadrupole  P ∝ U⁸          (low Mach)
```

This is why bluff-body / surface-loading noise (the aeolian tone of §5, cylinder/strut noise, trailing-edge noise) is a dipole and far louder per unit flow energy than free-jet quadrupole noise at the same low speed.

### Ffowcs Williams–Hawkings (FW-H) — arbitrarily moving surfaces

FW-H (1969) generalizes Curle to surfaces in **arbitrary motion** (rotating blades, propellers, fans) and is the industrial standard. It yields three source types:

| Source | Physical origin | Velocity scaling |
|---|---|---|
| **Monopole (thickness)** | volume displacement of the moving body | U⁴ |
| **Dipole (loading)** | unsteady surface pressure / force | U⁶ |
| **Quadrupole (volume)** | the Lighthill T_ij in the volume off the surface | U⁸ |

**Industrial far-field workflow:** run unsteady **scale-resolving CFD (LES / DES / DDES)** → store p′ and velocity on an **FW-H integration surface** → evaluate the **Farassat 1A retarded-time integral** to propagate to far-field microphone (observer) locations. Cheap relative to resolving the whole acoustic field, and the observers can be arbitrarily far without meshing the intervening space.

- **Permeable (porous) FW-H surface** — placed in the *irrotational near-field* surrounding the body; it **captures the volume quadrupole** as well as monopole+dipole, because the enclosed volume sources radiate through it. It **must enclose all significant sources** and **must not be crossed by the turbulent wake** (see mistake below).
- **Solid (on-body) FW-H surface** — coincides with the wall; captures **only monopole + dipole**. Correct (and simpler) when the volume quadrupole is negligible (low Mach, compact bodies).

### Hybrid vs direct CAA

- **Hybrid CAA (the standard):** decouple source and propagation — CFD computes the unsteady sources, then either (a) the **FW-H integral** propagates to the far field, or (b) a **Lighthill-source FEM/BEM wave solve** propagates through a complex acoustic domain (ducts, cabins). Efficient; the two physics use different meshes and time steps.
- **Direct CAA:** resolve the acoustics *within* the CFD itself. Requires very-low-dissipation schemes, non-reflecting BCs, and the mesh/Δt to **resolve the acoustic wavelength** (which is much longer than the flow scales but demands accuracy over long distances). Very expensive — reserve for **feedback-loop problems** (whistles, cavity tones, screech, edge tones) where source and field are two-way coupled.

### RANS broadband screening (cheap, approximate, NOT predictive)

Steady-RANS post-processing models **rank** noise sources but must not be reported as absolute levels:

- **Proudman** acoustic power for isotropic turbulence: `P_A = α_ε · ρ · ε · Ma_t⁵` (ε = turbulent dissipation, Ma_t = turbulent Mach number).
- **Curle surface acoustic power** and broadband boundary-layer-noise models — for surface-source ranking.

Use these only to *locate and rank* sources for design iteration; for absolute spectra you need scale-resolving CFD + FW-H.

### Aeroacoustics mistake to add

- **Permeable FW-H surface crossed by the turbulent wake** → large **spurious broadband noise** (vortical structures convecting across the porous surface are mis-interpreted as acoustic sources). **Fix:** extend the surface downstream past the wake, use multiple end-cap surfaces with averaging, or fall back to a solid on-body surface if the quadrupole is negligible.

**Confidence: HIGH** (Lighthill 1952; Curle 1955; FW-H 1969; Farassat 1A; Ansys Fluent / COMSOL Aeroacoustics; NASA NTRS FW-H notes).

Sources:
- Lighthill, "On sound generated aerodynamically. I," *Proc. Roy. Soc. A* 211 (1952).
- Curle, "The influence of solid boundaries upon aerodynamic sound," *Proc. Roy. Soc. A* 231 (1955).
- Ffowcs Williams & Hawkings, "Sound generation by turbulence and surfaces in arbitrary motion," *Phil. Trans. Roy. Soc. A* 264 (1969).
- Proudman, "The generation of noise by isotropic turbulence," *Proc. Roy. Soc. A* 214 (1952).
- Ansys Fluent Acoustics (FW-H) and COMSOL Aeroacoustics module documentation; NASA NTRS FW-H spurious-noise notes.
- See `cfd.md` for the unsteady source-generation (LES/DES) side; §5 above for the aeolian special case.

---

## 9. Statistical Energy Analysis (SEA) and Hybrid FE-SEA

FEM/BEM resolves individual modes and is exact at low frequency, but the cost and mesh density explode with frequency, and at high frequency the response becomes **sensitive to small manufacturing variation** so a single deterministic answer is meaningless. **Statistical Energy Analysis (SEA)** is the high-frequency method: it abandons individual modes and solves a **power balance** between subsystems, each described by *statistically averaged* energy. (Mistake 10 above flags the low-frequency-validity trap; this section is the methodology.)

### Power balance between subsystems

Each subsystem i stores vibrational/acoustic energy E_i and is driven by input power Π_in,i. At steady state, input power = power dissipated internally + net power coupled to neighbours:

```
Π_in,i = ω · η_i · E_i  +  Σ_j  ω · η_ij · ( E_i − E_j · n_i/n_j )
```

The **energies E_i are the unknowns**; the loss factors and modal densities are the inputs:

| Quantity | Symbol | Meaning |
|---|---|---|
| **Modal density** | n_i(ω) | modes per unit frequency (modes/Hz or modes/rad·s⁻¹) in subsystem i |
| **Damping loss factor (DLF)** | η_i | fraction of energy dissipated per radian; internal losses |
| **Coupling loss factor (CLF)** | η_ij | fraction of energy transferred i→j per radian across the junction |

**Consistency (reciprocity) relation** — the keystone that lets CLFs be measured/derived consistently:

```
n_i · η_ij = n_j · η_ji
```

### Modal density and the modal overlap factor

Closed-form modal densities for canonical subsystems:

```
Flat plate (bending):   n(f) = (A/2) · √(ρ_s h / D)     ≈ constant in frequency
                        (A = area, ρ_s = density, h = thickness, D = bending stiffness)
Acoustic room (3-D):    n(f) = 4π V f² / c³              (rises as f²; matches §3 / Mistake 10)
```

The **modal overlap factor** decides whether SEA is even applicable:

```
M = η · ω · n(ω)              (= DLF × angular freq × modal density)
```

- **M ≳ 1** *and* **≳ 5–10 modes per band** → SEA assumptions (diffuse field, equipartition, high overlap) hold.
- **M ≪ 1** (well-separated resonances) → deterministic FEM/BEM is required.

### Coupling loss factors

CLFs are obtained from:
- **Wave-transmission coefficients** at line junctions (plate–plate) or area junctions (plate–cavity) — analytical for canonical joints.
- **Radiation efficiency** σ_rad for structure↔cavity coupling (how well a panel radiates into / is driven by an acoustic space).
- **Experimental power-injection method (PIM)** — shake one subsystem, measure energy ratios, invert for the CLF matrix; the standard experimental route when geometry is too complex for analytical CLFs.

### Hybrid FE-SEA — the mid-frequency method

The **mid-frequency** band (some subsystems have few modes, others many) defeats both pure FEM (too expensive / variance-sensitive) and pure SEA (too few modes). **Hybrid FE-SEA (Shorter & Langley, 2005)** partitions the model:

- **Deterministic (FE) subsystems** — stiff, low-mode-count parts (a frame, a bracket) modelled with ordinary FEM.
- **Statistical (SEA) subsystems** — diffuse, high-mode-count parts (panels, cavities) modelled as SEA.
- The two are coupled through the **diffuse-field reciprocity relationship**, which expresses the random subsystem's effect on the deterministic one as an equivalent "direct-field" dynamic stiffness plus a reciprocal random loading. This **resolves the mid-frequency problem** and is the modern production approach (VA One, Simcenter 3D / SEA).

### Frequency-regime map

| Regime | Modal overlap | Method |
|---|---|---|
| **Low** | M ≪ 1, few modes/band | Deterministic **FEM / BEM** (coupled "wet" modes — see §10 and `dynamics-nvh-acoustics.md`) |
| **Mid** | mixed (some subsystems sparse, some dense) | **Hybrid FE-SEA** |
| **High** | M ≳ 1, ≥ 5–10 modes/band, diffuse | **SEA** |

**Confidence: HIGH** (Lyon & DeJong; Shorter-Langley 2005; VA One / Simcenter SEA; NAFEMS).

Sources:
- Lyon & DeJong, *Theory and Application of Statistical Energy Analysis*, 2nd ed., Butterworth-Heinemann (1995).
- Shorter & Langley, "Vibro-acoustic analysis of complex systems," *J. Sound Vib.* 288 (2005) — the hybrid FE-SEA formulation.
- ESI VA One and Siemens Simcenter SEA documentation; NAFEMS SEA primers.
- See Mistake 10 (validity threshold) and `dynamics-nvh-acoustics.md` (the deterministic modal/vibro-acoustic basis at low frequency).

---

## 10. Airborne Transmission Loss of Panels and Partitions

Transmission Loss (TL = 10·log₁₀(1/τ), τ = transmitted/incident power) of a single panel or double wall follows a characteristic curve with three named regions — **mass-law**, the **coincidence dip**, and (for double walls) the **mass-air-mass** behaviour. dynamics-nvh-acoustics.md names TL as an output of a coupled solve; here are the governing curves that any FEM result should reproduce.

### Mass law (the stiffness-free, damping-free region)

In the frequency band below coincidence the panel behaves as a limp mass; the field-incidence transmission loss is:

```
TL ≈ 20·log₁₀( m″ · f ) − 47   [dB]      (field incidence; m″ in kg/m², f in Hz)
```

- **+6 dB per doubling of surface mass m″** and **+6 dB per doubling of frequency** (i.e. +6 dB/octave).
- **Normal incidence** is ~+5 dB higher than field (diffuse) incidence: the constant becomes ≈ −42 instead of −47, so **TL_field ≈ TL_normal − 5 dB**. Report which incidence you mean — measured (ISO 10140 reverberation-room) TL is field incidence.

### Coincidence / critical frequency dip

At the **critical (coincidence) frequency** the bending wavelength in the panel matches the trace wavelength of the incident sound, the panel couples efficiently to the field, and TL **collapses** into a deep dip:

```
f_c = (c² / 2π) · √( m″ / D )      (D = bending stiffness per unit width)
```

- **Above f_c** TL recovers and rises steeply (~7–9 dB/octave) — much faster than the 6 dB/octave mass law.
- **Stiff / thick panels have a *low* f_c** (in-band, bad — the dip lands in the frequency range of interest). **Limp / thin panels push f_c up** out of the band of interest. This is why adding stiffening ribs can *worsen* airborne TL by dragging f_c down into the band — a common counter-intuitive result.

### Double-wall mass-air-mass (MAM) resonance

Two leaves separated by an air (or porous-filled) cavity outperform a single wall of the same total mass *above* the mass-air-mass resonance:

```
f_mam = (1 / 2π) · √[ ρ₀ c² ( 1/m₁″ + 1/m₂″ ) / d ]      (d = cavity depth)
```

- **Below f_mam** the double wall acts as one combined mass (TL ≈ single-wall mass law of m₁″+m₂″).
- **At f_mam** there is a TL dip (the two masses resonate on the air spring).
- **Above f_mam** TL rises at **~18 dB/octave** — far exceeding mass law; this is the basis of partitions, aircraft fuselage trim, and insulated glazing units (IGUs).
- **Decisive details:** cavity **absorption** (porous fill — see §7) damps cavity resonances and standing waves; **mechanical decoupling** (no rigid stud/bridge connecting the leaves) is essential — any rigid bridging creates a structure-borne short-circuit that destroys the double-wall benefit.

### Summary

| Region | Slope | Driver |
|---|---|---|
| Mass law (below f_c) | +6 dB/oct (and +6 dB/doubling mass) | surface mass m″ |
| Coincidence dip (at f_c) | sharp drop | bending stiffness ↔ trace match |
| Above f_c (single panel) | ~7–9 dB/oct | stiffness-controlled |
| Below f_mam (double wall) | mass law of total mass | combined mass |
| Above f_mam (double wall) | ~18 dB/oct | decoupled leaves + air spring |

**Confidence: HIGH** (Fahy & Gardonio; ISO 717 / ISO 10140; standard architectural-acoustics texts).

Sources:
- Fahy & Gardonio, *Sound and Structural Vibration: Radiation, Transmission and Response*, 2nd ed., Academic Press (2007).
- ISO 717 (single-number ratings) and ISO 10140 (laboratory TL measurement).
- COMSOL transmission-loss tutorials; standard architectural-/building-acoustics references.

---

## 11. Structural-Acoustic Coupling (Depth): the Unsymmetric {u, p} System

When a structure and an acoustic fluid share a wetted interface, the displacement field u of the solid and the pressure field p of the fluid are coupled. This deepens Mistakes 4 and 7 (when coupling and radiation damping matter) and the FSI bullet in Mistake 3, and is the low-frequency deterministic regime referenced by §9. The modal/vibro-acoustic machinery (ATV, panel contribution, modal basis) lives in `dynamics-nvh-acoustics.md`; here is the coupled-equation structure and the heavy-vs-light-fluid decision.

### The coupled system is unsymmetric

The standard pressure-formulation coupled equations have an **unsymmetric** form:

```
[ K_s   −C  ] { u }   [ M_s    0  ] { ü }   { F_s }
[  0    K_f ] { p } + [ ρ₀Cᵀ  M_f ] { p̈ } = { F_f }
```

- C is the **fluid-structure coupling matrix** (couples interface pressure to structural load and structural acceleration to fluid excitation); it appears off-diagonal and **asymmetrically** (−C above, ρ₀Cᵀ below).
- Consequences: the coupled eigenproblem needs an **unsymmetric eigensolver** (or one of the symmetrization schemes — {u, p, φ} velocity-potential, or pressure/displacement-potential forms) and the modes are in general complex.

### Dry vs wet modes

- **Dry (in-vacuo) modes:** structural modes computed with **no fluid** (C = 0). Correct when the fluid back-reaction is negligible.
- **Wet modes:** modes of the **fully coupled** system; the fluid adds mass (and, with radiation, damping). In heavy fluid these shift natural frequencies **by tens of percent** below the dry values, so dry modes are simply wrong.

### Heavy-fluid vs light-fluid loading — the decision rule

| Loading | Examples | Coupling | Modes |
|---|---|---|---|
| **Light fluid** (air on a stiff/heavy structure) | car body panels, building partitions, most aerospace structures in air | **One-way (weak)** is usually OK: solve in-vacuo (dry) modes, then radiate (apply surface velocities as the acoustic source) | dry ≈ wet |
| **Heavy fluid** (water, oil, fuel) | ship/submarine hulls, fuel tanks, pumps/pipes full of liquid, biomedical/underwater, sloshing | **Two-way (strong)** mandatory: fluid mass-loading and radiation reaction change the structure → solve **wet** modes | wet ≪ dry |

**Rule of thumb:** fluid loading is significant when the **fluid added-mass / radiation-reaction term is comparable to the structural modal mass** — i.e. when ρ₀c·(radiation term)·area is of the same order as the modal mass. Air on a thin lightweight panel can *still* be non-negligible (the impedance mismatch is large but the panel mass is tiny), so check the ratio rather than assuming "air ⇒ one-way."

### Solution strategy and radiation damping

- **Modal-based** coupled response (project onto dry modes + **residual vectors** to recover truncated static contribution — see Mistake 8) is efficient for **light fluid**.
- **Direct** (fully-coupled physical-DOF) solution is used for **heavy fluid / strong coupling** where a dry-mode basis is inadequate.
- **Radiation damping:** energy radiated to an unbounded fluid removes energy from the structure (it appears as a complex term in the structural impedance). It is **often the dominant damping under water** and must not be dropped — and it only exists if the exterior is terminated by a proper non-reflecting BC (IE / PML / anechoic, per §4 and Mistake 7); truncating with a rigid wall reflects the energy back and predicts unphysically sharp resonances.

**Confidence: HIGH** (Fahy; Everstine; Ansys/Nastran coupled-acoustic SOL 108/111 + ACMODL; COMSOL Acoustic-Structure Interaction).

Sources:
- Fahy & Gardonio, *Sound and Structural Vibration*, 2nd ed. (2007).
- Everstine, "Finite element formulations of structural acoustics problems," *Computers & Structures* 65 (1997).
- Ansys / Simcenter Nastran coupled-acoustic (SOL 108/111, acoustic cavity, ACMODL) and COMSOL Acoustic-Structure Interaction documentation.
- Cross-link: `dynamics-nvh-acoustics.md` (modal basis, ATV, panel-contribution, coupled "wet" modes); §9 (where this deterministic regime sits in the frequency map); Mistakes 3, 4, 7, 8.

---

## 12. Quick-Reference Numbers

| Quantity | Formula / Value |
|---|---|
| Speed of sound in air at 20°C | 343 m/s |
| Speed of sound vs temperature | c = 331.3·√(T/273.15) m/s |
| First cut-on, circular duct | f_c = 1.8412·c/(π·D) |
| First cut-on, rectangular duct | f_c = c/(2a) [a = wider dimension] |
| Expansion chamber TL peak | kL = π/2, i.e., L = λ/4 |
| Expansion chamber TL zero | kL = π, i.e., L = λ/2 |
| Sabine T₆₀ | 0.161·V/A [V in m³, A in m²] |
| Impedance ↔ reflection coeff. | Γ = (Zn − ρc)/(Zn + ρc) |
| Absorption coefficient | α = 1 − |Γ|² |
| Strouhal number, cylinder | St ≈ 0.2 |
| Aeolian tone frequency | f = 0.2·U/d |
| Acoustic mesh minimum | h ≤ λ/6 (linear), λ/5 (quadratic) |
| PML layers (freq. domain) | 5–6 (rational) or 8 (polynomial) |
| PML layers (time domain) | ≥ 8 same size as physical domain |
| IE/PML clearance from source | ≥ λ/2 at lowest frequency |
| SEA validity (min. modal density) | ≥ 5–10 modes per octave band |
| 4-pole reciprocity check | T₁₁·T₂₂ − T₁₂·T₂₁ = 1 |
| JCA parameter count | 5 (σ, φ, α∞, Λ, Λ′); JCAL = 6, JCAPL = 7 |
| Delany–Bazley / Miki valid band | 0.01 < f/σ < 1.0 (single-param, fibrous) |
| Typical foam flow resistivity σ | ≈ 5,000–50,000 Pa·s/m²; porosity φ ≈ 0.90–0.99 |
| Lighthill free-jet quadrupole | P ∝ ρ₀U⁸/c₀⁵ (U⁸); Curle dipole U⁶; thickness monopole U⁴ |
| Proudman acoustic power | P_A = α_ε·ρ·ε·Ma_t⁵ (RANS screening only) |
| SEA modal overlap factor | M = η·ω·n(ω); SEA valid M ≳ 1 |
| SEA reciprocity | n_i·η_ij = n_j·η_ji |
| Mass law (field incidence) | TL ≈ 20·log₁₀(m″·f) − 47 dB; +6 dB/oct, +6 dB/doubling mass |
| Mass law normal incidence | ≈ field + 5 dB (constant ≈ −42) |
| Coincidence/critical frequency | f_c = (c²/2π)·√(m″/D); above f_c ~7–9 dB/oct |
| Double-wall mass-air-mass | f_mam = (1/2π)·√[ρ₀c²(1/m₁″+1/m₂″)/d]; above f_mam ~18 dB/oct |

---

## Sources Summary (all topics)

**Duct acoustics / TMM / muffler:**
- Pierce, *Acoustics*, and Munjal, *Acoustics of Ducts and Mufflers*. Orientation link: CFDyna aeroacoustics reference: https://www.cfdyna.com/Home/AeroAcoustics.html
- Wiley Shock and Vibration, side-outlet muffler TL (2020): https://onlinelibrary.wiley.com/doi/10.1155/2020/6927574
- Single-chamber muffler transfer-matrix modeling — Gerges et al., *J. Braz. Soc. Mech. Sci. Eng.* 27:132–140 (2005): https://doi.org/10.1590/S1678-58782005000200005
- IJERA, single expansion chamber TMM: https://www.ijera.com/papers/Vol2_issue1/DA21651658.pdf

**Cut-on frequencies:**
- Pierce, *Acoustics*. Orientation link: CFDyna: https://www.cfdyna.com/Home/AeroAcoustics.html
- Acta Acustica, Ford et al. (2023): https://acta-acustica.edpsciences.org/articles/aacus/full_html/2023/01/aacus220052/aacus220052.html
- MDPI Applied Sciences, rectangular duct: https://www.mdpi.com/2076-3417/12/11/5307

**PML / Infinite Elements:**
- COMSOL 6.3 official PML documentation: https://doc.comsol.com/6.3/doc/com.comsol.help.aco/aco_ug_pressure.05.139.html
- Altair OptiStruct 2025 APML documentation: https://2025.help.altair.com/2025.1/hwsolvers/os/topics/solvers/os/analysis_acoustic_apml_c.htm
- Actran/Hexagon documentation and Astley/Coyette infinite-element literature.
- Orientation only: Actran history / Astley IE references (HandWiki): https://handwiki.org/wiki/Software:Actran
- Orientation only: Actran capabilities overview (Engineering.com): https://www.engineering.com/actran-for-acoustic-radiation-designs/
- Orientation only: Actran GSAS blog: https://gsasindia.com/blog/hexagon-actran-acoustic-simulation-india
- Wiley NME, automatic PML (Bériot & Modave 2021): https://onlinelibrary.wiley.com/doi/full/10.1002/nme.6560
- JCP, PML for fast frequency sweeps (2019): https://dl.acm.org/doi/10.1016/j.jcp.2019.108878
- Acta Acustica, PU-FEM with PML (2020): https://acta-acustica.edpsciences.org/articles/aacus/full_html/2020/04/aacus200026/aacus200026.html

**Absorption / room acoustics:**
- Sabine / room-acoustics textbook treatments. Orientation only: ScienceDirect Sabine equation overview: https://www.sciencedirect.com/topics/engineering/sabine-equation
- Acousticlab, reverberation time: https://www.acousticlab.com/en/reverberation-time-and-sabines-formula/
- ScienceDirect, time-domain FEM with absorbing BCs: https://www.sciencedirect.com/science/article/abs/pii/S0003682X21003066
- NASA NTRS, impedance tube measurement: https://ntrs.nasa.gov/api/citations/20150023091/downloads/20150023091.pdf

**Aeolian tones / aeroacoustics:**
- Springer Experiments in Fluids (2020): https://link.springer.com/article/10.1007/s00348-020-02972-0
- MDPI Aerospace (2025): https://www.mdpi.com/2226-4310/13/4/321
- Lighthill (1952), Curle (1955), Ffowcs Williams-Hawkings (1969). Orientation link: CFDyna aeroacoustics / Lighthill: https://www.cfdyna.com/Home/AeroAcoustics.html

**Poroelastic / sound-package (trim):**
- Allard & Atalla, *Propagation of Sound in Porous Media*, 2nd ed., Wiley (2009).
- Biot, *JASA* 28 (1956); Johnson-Koplik-Dashen, *J. Fluid Mech.* 176 (1987); Champoux & Allard, *J. Appl. Phys.* 70 (1991).
- Delany & Bazley, *Applied Acoustics* 3 (1970); Miki, *J. Acoust. Soc. Jpn (E)* 11 (1990).
- Matelys APMR (acoustical porous material recipes): https://apmr.matelys.com/
- COMSOL Poroelastic Waves / Acoustics Module documentation.

**Aeroacoustics (Lighthill / Curle / FW-H / hybrid CAA):**
- Lighthill, *Proc. Roy. Soc. A* 211 (1952); Curle, *Proc. Roy. Soc. A* 231 (1955).
- Ffowcs Williams & Hawkings, *Phil. Trans. Roy. Soc. A* 264 (1969); Proudman, *Proc. Roy. Soc. A* 214 (1952).
- Ansys Fluent Acoustics (FW-H), COMSOL Aeroacoustics, NASA NTRS FW-H spurious-noise notes.

**SEA / hybrid FE-SEA:**
- Lyon & DeJong, *Theory and Application of Statistical Energy Analysis*, 2nd ed. (1995).
- Shorter & Langley, *J. Sound Vib.* 288 (2005) — hybrid FE-SEA.
- ESI VA One, Siemens Simcenter SEA documentation; NAFEMS SEA primers.

**Transmission loss / structural-acoustic coupling:**
- Fahy & Gardonio, *Sound and Structural Vibration*, 2nd ed., Academic Press (2007).
- Everstine, *Computers & Structures* 65 (1997); ISO 717 / ISO 10140.
- Ansys / Simcenter Nastran coupled-acoustic (SOL 108/111, ACMODL); COMSOL Acoustic-Structure Interaction & TL tutorials.

**Acoustics FEM best practices / mesh / mistakes:**
- COMSOL Acoustics documentation and COMSOL Blog, automate meshing for acoustics: https://www.comsol.com/blogs/how-to-automate-meshing-in-frequency-bands-for-acoustic-simulations
- "More Than Six Elements Per Wavelength" — Langer, Maeder et al., *J. Comput. Acoust.* 25(4):1750025 (2017): https://doi.org/10.1142/S0218396X17500254
- Marburg, "Six boundary elements per wavelength: Is that enough?" — *J. Comput. Acoust.* 10(1):25–51 (2002): https://doi.org/10.1142/S0218396X02001401
- Ansys FLUID elements reference: https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_elem/elem_acouselems.html
- Lyon & DeJong, *Theory and Application of Statistical Energy Analysis*, 2nd ed. (Butterworth-Heinemann, 1995) — primary SEA reference. Orientation: Wikipedia — Statistical energy analysis, https://en.wikipedia.org/wiki/Statistical_energy_analysis

---

## See also

- `dynamics-nvh-acoustics.md` — structural dynamics, NVH, and vibro-acoustics: modal/harmonic/random/transient analysis, coupled ("wet") modes, acoustic mesh density, ATV / panel-contribution analysis, transmission loss, and the modal-basis chain that feeds any coupled structural-acoustic solve.
- `cfd.md` — computational fluid dynamics. It **generates the unsteady flow sources** (scale-resolving LES/DES surface pressure and velocity histories) that the aeroacoustic propagation methods in §8 of *this* file consume. The acoustic-propagation side (Lighthill / Curle / FW-H integrals, hybrid-CAA workflow) is owned **here**; `cfd.md` owns the turbulence-resolving source computation only.
- `meshing-convergence.md` — general mesh sizing, element-quality, and mesh-independence / convergence methodology underpinning the elements-per-wavelength rules used throughout this reference.
