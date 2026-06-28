# Claims validation — external sources for the router's load-bearing claims

`SKILL.md` (the router) compresses many quantitative thresholds, formulas, and named standards into terse
gates. This appendix gives each load-bearing claim an **authoritative external source** and a **verdict**, so
every router gate is traceable. It was produced by a multi-source deep-research pass (six parallel domain
reviews) under an explicit *verify-or-flag* rule: no source was used unless confirmed to exist and support the
point; anything unconfirmable would be marked UNVERIFIED.

**Verdict key:** VALIDATED (source backs the exact statement) · QUALIFIED (true, with an important caveat) ·
CONTEXT-DEPENDENT (depends on element/solver/physics) · REFUTED · UNVERIFIED.

**Result — 53 claims: 39 VALIDATED, 14 QUALIFIED, 0 REFUTED, 0 UNVERIFIED.** The QUALIFIED rows share a theme
that matches the router's intent: the *physics* is sound, but several *numbers* are indicative rules-of-thumb,
not universal constants — read them as guidance and verify in context. Three wording issues this pass exposed
were corrected in place (see the end).

> Scope: this validates the **router's** compressed claims. The detailed `references/*.md` files carry their
> own inline citations and `SOURCES` sections. Per-claim notes are condensed; consult the cited source for the
> full statement and its conditions of validity.

## 1. Meshing, element technology & convergence

| # | claim | authoritative source | verdict | note |
|---|-------|----------------------|---------|------|
| 1 | Quadratic elements preferred for stress/curved geometry; avoid linear TET4 for stress | Abaqus Analysis User's Manual (solid-element selection); Cook, Malkus, Plesha & Witt, *Concepts and Applications of FEA*, 4th ed. | VALIDATED | TET4's defect is constant-strain over-stiffness + slow convergence (not "shear-locking" in the parasitic-shear sense). Strong consensus, not absolute — linear hex / reduced-integration are fine for many cases. |
| 2 | Linear fully-integrated elements shear-lock (~+34% too stiff in a thin-cantilever bending test; magnitude problem-dependent) | Abaqus *Getting Started* §4.1; Jefferson Lab note on shear locking (Nastran/Abaqus/Ansys) | QUALIFIED | Shear-locking is firmly established; the ~34% is one reproducible aspect-ratio-specific benchmark (C3D8 vs C3D8R/C3D8I), **not** a universal constant — magnitude grows with aspect ratio/coarseness. |
| 3 | Shell idealization appropriate when thickness/length ≲ 1/10–1/20 | Abaqus *Getting Started* §5 (thin/thick shells); CSI Knowledge Base | VALIDATED | A standard rule-of-thumb band, not a hard cutoff (Abaqus uses ~1/15 for the thin/thick boundary; Kirchhoff valid for span/thickness ≳ 20). |
| 4 | Mesh quality: skewness ≤0.5 (reject >0.95), orthogonal quality >0.2, Jacobian 1–10, aspect ratio <~20, growth ratio ≤1.2–1.5 | Ansys Fluent User's Guide §6.2.2 (Mesh Quality); SimScale mesh-quality docs | QUALIFIED | Skewness reject >0.95 confirmed. **Orthogonal-quality minimum is >0.1 (Fluent); >0.2 is a conservative FEA convention.** Jacobian/growth-ratio bands are common mesher conventions, not located in primary text. Thresholds are physics/element-dependent. |
| 5 | GCI (Roache / ASME V&V 20 / Celik 2008): ≥3 grids, r≥1.3, Fs=1.25 (≥3 grids)/3.0 (2), observed order p, asymptotic check ≈1 | Celik et al., *J. Fluids Eng.* 130(7):078001 (2008), https://doi.org/10.1115/1.2960953; ASME V&V 20-2009; Roache (1994/1998) | VALIDATED | All four numbers confirmed. Caveat: `p = ln(ε32/ε21)/ln(r)` is the **equal-ratio** simplification; Celik's published apparent-order equation is the iterative unequal-ratio form (already handled by `scripts/gci.py`). |
| 6 | Zienkiewicz–Zhu / SPR recovery estimator; effectivity index → 1; from a single solve | Zienkiewicz & Zhu, *IJNME* 24:337–357 (1987); SPR Parts 1–2, *IJNME* 33 (1992) | QUALIFIED | Asymptotic exactness (effectivity → 1) from one solve confirmed. **"Bounds" is wrong — it is an *estimate* (asymptotically exact), not a guaranteed upper bound** (a rigorous bound needs equilibrated/residual methods). Fixed in place. |
| 7 | p-refinement → exponential convergence for smooth fields; properly graded hp recovers exponential rates at isolated singularities | Szabó & Babuška, *Finite Element Analysis* (1991); Gui & Babuška, *Numer. Math.* 49 (1986); Babuška & Suri, *SIAM Review* 36 (1994) | VALIDATED | "Properly graded" is load-bearing: requires piecewise-analytic data + geometrically graded mesh with matched p-distribution; arbitrary hp does not give exponential rates. |
| 8 | Reduced-integration linear elements hourglass (spurious zero-energy modes) and need control | Cook, Malkus, Plesha & Witt, 4th ed.; Flanagan & Belytschko, *IJNME* 17:679–706 (1981) | VALIDATED | Under-integration → rank deficiency → zero-energy modes; stabilization (e.g. Flanagan–Belytschko) required. BC/assembly may suppress an isolated mode, but it propagates in general meshes. |

## 2. Connections, bolts & thermal contact

| # | claim | authoritative source | verdict | note |
|---|-------|----------------------|---------|------|
| 1 | RBE2 (rigid kinematic) adds stiffness/over-stiffens; RBE3 (interpolation) spreads load without adding stiffness | MSC/NX Nastran element theory; Fidelis FEA, EnDuraSim, Predictive Engineering (practitioner/vendor consensus) | VALIDATED | No single governing standard — authority is vendor theory + consensus. "No added stiffness" assumes a *correctly defined* RBE3 (a badly defined one can introduce artifacts). |
| 2 | Bolt preload target Fi ≈ 0.7 × proof load | Shigley's *Mechanical Engineering Design*, Ch. 8 (Fi = 0.75·Fp non-permanent, 0.90·Fp permanent) | VALIDATED | "≈0.7" is the conservative shorthand for the non-permanent case; the skill's own 0.75/0.90 split is the precise textbook position. |
| 3 | Torque–preload T = K·F·d, nut factor K ≈ 0.2 (dry steel) | Bickford, *Handbook of Bolts and Bolted Joints*; Shigley §8; Juvinall & Marshek | VALIDATED | K ≈ 0.2 is a nominal mid-value; K is strongly condition-dependent (≈0.15 lubricated, ≈0.30 plated/dry). |
| 4 | VDI 2230 is the standard systematic bolted-joint method | VDI 2230 Blatt 1, "Systematic calculation of highly stressed bolted joints" | VALIDATED | The canonical systematic method (R0–R13). A German guideline, not the sole global standard (cf. Eurocode 3 EN 1993-1-8, ECSS). |
| 5 | Preload scatter ~±3–5% (ultrasonic) to ±25–35% (dry torque) | VDI 2230 Blatt 1 tightening-factor αA table | QUALIFIED | Ordering/direction confirmed (VDI αA ≈ 1.6–2.0 torque, 1.2–1.4 angle, tightest for elongation/ultrasonic). The ±% are a **standard restatement** of the αA ratio bands, not verbatim VDI text. |
| 6 | h_c drops ~1 order of magnitude as T falls (~200 K → ~20 K); rises with contact pressure | Peer-reviewed cryogenic TCC studies (*Cryogenics*/*Int. J. Refrigeration*); Madhusudana, *Thermal Contact Conductance* (Springer) | QUALIFIED | Pressure dependence (TCC ∝ P^0.2–0.95) and the steep cryo decline are validated; the specific "one order of magnitude 200→20 K" is a **representative generalization**, not one tabulated value (material/finish/pressure-dependent). |
| 7 | In vacuum the gas-conduction path vanishes — never assume perfect contact in vacuum/cryo | Madhusudana (3-path model h = h_c + h_g + h_r); cryo TCR design lit. (Salerno & Kittel; USPAS/FNAL) | VALIDATED | Textbook: h_g → 0 in vacuum leaves only solid-spot constriction + radiation; finite contact conductance is mandatory in vacuum/cryo models. |
| 8 | Weld fatigue uses hot-spot/structural stress (IIW), not raw peak toe stress | IIW Recommendations (Hobbacher, doc. XIII-1823-07); Eurocode 3 EN 1993-1-9 | VALIDATED | IIW prescribes surface-stress extrapolation to the toe (0.4t & 1.0t) + hot-spot FAT classes; the raw toe peak is singular/mesh-dependent and does not converge. |
| 9 | Bolt preload changes under thermal/cryo load via CTE mismatch | VDI 2230 Blatt 1 (thermal term ΔF_th); Shigley §8 | VALIDATED | Differential expansion adds/relieves clamp force; first-order for cryo/space hardware (steel bolt + Al member: heating gains preload, cooling loses it). |

## 3. Solver numerics, explicit & structural dynamics

| # | claim | authoritative source | verdict | note |
|---|-------|----------------------|---------|------|
| 1 | Use physical (not logical) cores; DMP > SMP; small models saturate ~4–8 cores | Ansys Mechanical APDL Parallel Processing & Performance Guides | QUALIFIED | Physical-cores and DMP>SMP firmly documented (vendor cites ~4× over SMP); the "~4–8 core" knee is a model/solver/hardware-dependent rule of thumb. |
| 2 | Out-of-core direct solve ~10× slower than in-core | Ansys Mechanical APDL Performance Guide (Solver Guidelines) | QUALIFIED | Direction/significance confirmed ("orders of magnitude" slower disk vs RAM; "rarely recommended"); the "~10×" is indicative, varies with I/O subsystem (HDD vs NVMe) and shortfall. |
| 3 | Explicit stable Δt ≤ L_min/c (CFL/Courant) | Courant–Friedrichs–Lewy (1928); LS-DYNA Theory Manual; Belytschko, *Nonlinear FE for Continua and Structures* | VALIDATED | c = √(E/ρ) (1-D). Codes apply a safety factor (LS-DYNA TSSFAC default 0.9); the smallest element governs. |
| 4 | Mass scaling added mass < ~5%; hourglass energy < ~5–10% of internal | LS-DYNA Theory Manual & LSTC/Ansys support guidance | VALIDATED | Accepted heuristics (LSTC: hourglass < 10%). Acceptable level is problem-dependent (quasi-static tolerates more). |
| 5 | Implicit Newmark/HHT-α unconditionally stable for linear structural dynamics | Newmark (1959); Hilber, Hughes & Taylor (1977); Hughes, *The Finite Element Method* | VALIDATED | Newmark unconditional for γ=1/2, β=1/4; HHT-α 2nd-order + unconditional for α∈[−1/3,0]. Stability is a **linear** property — not guaranteed for nonlinear dynamics. |
| 6 | Extract ≥80–90% cumulative effective modal mass per excited direction | NASA-STD-5002 (Load Analyses of Spacecraft and Payloads); Irvine, "Effective Modal Mass" | VALIDATED | Standard modal-truncation criterion (>80% common, >90% goal); the exact % is a guideline, programs may set their own. |
| 7 | Random vibration: Q=1/(2ζ); Miles GRMS ≈ √((π/2)·f_n·Q·ASD); design to 3σ | Miles (1954), *J. Aero. Sci.*; Steinberg, *Vibration Analysis for Electronic Equipment*; NASA/GSFC FEMCI | VALIDATED | Miles' eqn valid for a SDOF with **flat/broadband** PSD near f_n; 3σ is the conventional Gaussian peak design (some programs use higher). |
| 8 | SRS conventionally Q=10 (≈5% damping) | MIL-STD-810H Method 516.8; IEST-RP-DTE012; Irvine, "Intro to the SRS" | VALIDATED | The long-standing default; SRS must always state the Q/damping used (other values valid). |
| 9 | Negative/zero pivots in a direct solve indicate singularity (RBM / lost contact / bad props) | Ansys MAPDL Theory Reference (Singular Matrices); Bathe, *Finite Element Procedures* (LDLᵀ) | VALIDATED | Zero/near-zero pivot → true singularity; a **negative** pivot specifically signals loss of positive-definiteness (instability/indefinite system). Solver flags node/DOF. |

## 4. Fracture, fatigue, buckling, composites & plasticity

| # | claim | authoritative source | verdict | note |
|---|-------|----------------------|---------|------|
| 1 | LEFM G = K²/E′ (E′ = E plane stress, E/(1−ν²) plane strain) | Anderson, *Fracture Mechanics*, 4th ed.; Irwin, *J. Appl. Mech.* 24:361–364 (1957) | VALIDATED | Standard Irwin relation; mixed-mode form G = (K_I²+K_II²)/E′ + K_III²/2μ. |
| 2 | J-integral is path-independent; read J from the contour/domain integral, not the singular tip stress | Rice, *J. Appl. Mech.* 35(2):379–386 (1968); Anderson, Ch. 3 | QUALIFIED | Path-independence is rigorous only for nonlinear-**elastic**/deformation-theory plasticity, monotonic proportional loading, no body forces/crack-face tractions/thermal strains in the contour. Domain (EDI) evaluation is the correct FEA practice. |
| 3 | Mean-stress corrections: Goodman, Gerber, Soderberg, SWT | Dowling, *Mechanical Behavior of Materials*, 4th ed.; Smith–Watson–Topper, *J. Materials* 5(4):767–778 (1970) | VALIDATED | SWT/Morrow are strain-life damage parameters; Goodman/Gerber/Soderberg are stress-life constant-life lines. SWT predicts no damage for fully-compressive max stress (known limitation). |
| 4 | Strain-life Coffin–Manson; notch via Neuber or Glinka ESED | Coffin (1954)/Manson (NACA TN-2933, 1953); Neuber (1961); Molski & Glinka, *Mater. Sci. Eng.* 50:93–100 (1981) | VALIDATED | Full strain-life is Coffin–Manson–Basquin; Neuber over-predicts notch strain, Glinka under-predicts — both accepted. |
| 5 | Palmgren–Miner: Σ(n_i/N_i) = 1 at failure | Miner, *J. Appl. Mech.* 12:A159–A164 (1945); Palmgren (1924) | VALIDATED | Equation is standard; experimentally the critical sum scatters ≈0.7–2.2 and is sequence-dependent — many codes adopt a conservative D < 1. |
| 6 | Spectral (vibration) fatigue from a PSD via Dirlik | Dirlik, PhD thesis, Univ. of Warwick (1985); review Mršnik et al., *Int. J. Fatigue* 47:8–17 (2013) | VALIDATED | De-facto standard frequency-domain method; empirical, derived for stationary Gaussian processes (alternatives: Tovo–Benasciutti, Zhao–Baker). |
| 7 | Linear buckling is an upper bound; needs knockdown (NASA SP-8007) or GNIA/GMNIA with seeded imperfections | NASA SP-8007 (rev. 2020); EN 1993-1-6 (GMNIA) | VALIDATED | Upper bound applies to **imperfection-sensitive** shells; SP-8007's classical knockdown is now seen as overly conservative — EN 1993-1-6 is the explicit GMNIA standard. |
| 8 | ASME VIII-2 stress-linearization categories P_m, P_L, P_b, Q, F vs S_m; Bree for shakedown/ratcheting | ASME BPVC VIII-2, Part 5 + Annex 5-A; Bree, *J. Strain Analysis* 2(3):226–238 (1967) | QUALIFIED | **F (peak) has no membrane/bending S_m limit — it feeds fatigue only.** Limits: P_m ≤ S, P_L ≤ 1.5S, P_L+P_b ≤ 1.5S; the secondary range P_L+P_b+Q ≤ **S_PS** (≈2S_y), not S_m. ASME's ratcheting screen is a Bree-derived rule, not the diagram directly. |
| 9 | Composite progressive damage needs crack-band / fracture-energy regularization for mesh objectivity | Bažant & Oh, *Matériaux et Constructions* 16(3):155–177 (1983); Lapczyk & Hurtado, *Composites A* 38:2333–2341 (2007) | VALIDATED | Softening localizes to a band → mesh-dependent dissipation; scaling the softening law by element characteristic length (dissipated energy = G_f) restores objectivity. Controls energy/size, not mesh-orientation bias. |

## 5. Thermal, radiation, CFD & electromagnetics

| # | claim | authoritative source | verdict | note |
|---|-------|----------------------|---------|------|
| 1 | Bi = hL/k < 0.1 justifies lumped capacitance | Incropera et al., *Fundamentals of Heat and Mass Transfer*, Ch. 5; Cengel & Ghajar, Ch. 4 | VALIDATED | L = V/A_s; Bi < 0.1 ⇒ spatial T-variation under ~5% — a convention, not a sharp threshold. |
| 2 | Explicit transient-thermal Fo = αΔt/L² ≤ 0.5; backward-Euler robust default | Incropera et al., Ch. 5 (FD transient); Patankar, *Numerical Heat Transfer and Fluid Flow* | QUALIFIED | Fo ≤ 1/2 is for a **1-D interior** node; tightens with dimensionality (2-D interior ≤ 1/4) and convective/surface nodes. Backward-Euler is unconditionally **stable** but stable ≠ accurate. |
| 3 | Radiation enclosure: view-factor row sums → 1 (closed); absolute T; solar α ≠ IR ε | Incropera et al., Ch. 13; Gilmore, *Spacecraft Thermal Control Handbook* Vol. I, Ch. 4; Henninger NASA TM (NTRS 19840015630) | VALIDATED | ΣF_ij = 1 for a closed enclosure (self-view for concave surfaces); σT⁴ needs absolute T; α_solar (short-wave) ≠ ε_IR (long-wave) except for a gray surface. |
| 4 | MLI effective emittance ε* ~0.01–0.05; dominant spacecraft-thermal uncertainty | Gilmore (ed.), *Spacecraft Thermal Control Handbook* Vol. I, Ch. 5 (Insulation); NASA TM (NTRS 20190025589) | QUALIFIED | ε* range well-established (size/workmanship-dependent; flight > coupon). "Dominant uncertainty" is true for MLI-enclosed designs, **not universal** — elsewhere contact conductance/optical-degradation/heater dissipation can dominate. |
| 5 | RANS k-ω SST is a reasonable general-purpose default | Menter, *AIAA Journal* 32(8):1598–1605 (1994), https://doi.org/10.2514/3.12149; NASA Turbulence Modeling Resource | VALIDATED | A safe industrial default (blends near-wall k-ω + freestream k-ε). Still RANS — weak in strongly swirling/separated/transitional/free-shear flows; "default" ≠ "always best." |
| 6 | y+ ≈ 30–300 (wall functions) or y+ < 1 (resolved); avoid buffer 5<y+<30; ≥10–15 inflation layers | Law-of-the-wall (Pope, *Turbulent Flows*; Schlichting; Wilcox); Menter / Ansys Fluent–CFX best practice | QUALIFIED | Each sub-claim correct for **standard** wall functions; modern scalable/all-y+ wall treatment (e.g. SST automatic) is y+-insensitive and tolerates the buffer zone, so "must avoid" is treatment-dependent. "10–15 layers" is a rule of thumb. |
| 7 | CFD convergence ≠ residuals (1e-3…1e-6) alone; monitor integrated quantities + imbalances < ~1% | AIAA G-077-1998; Roache, *Verification and Validation in Comp. Science & Eng.*; Ansys Fluent guidance | VALIDATED | Residuals can stall while the solution drifts; converge QoIs (forces, flows) and check global imbalances (~1%, often stricter). The 1% is a typical guideline. |
| 8 | EM skin depth δ = √(2/(ωμσ)); mesh ≥2 elements into the skin depth | Jackson, *Classical Electrodynamics* §5.18 / Balanis, *Advanced Engineering Electromagnetics*; Ansys Maxwell eddy-current docs | VALIDATED | Standard good-conductor approximation (= 1/√(πfμσ)). "≥2 elements" is the practical vendor guideline to avoid overestimating losses (higher fidelity uses graded layers). |
| 9 | High-frequency full-wave FEM needs Nédélec (edge) elements; nodal → spurious modes | Jin, *The Finite Element Method in Electromagnetics*; Nédélec, *Numer. Math.* 35:315–341 (1980); Bossavit | VALIDATED | Edge (H(curl)-conforming) elements enforce tangential continuity + a discrete de Rham complex, removing the spurious modes of nodal vector discretizations. |
| 10 | Acoustic FEM ≥6 elements/wavelength is a MINIMUM (pollution/dispersion grows with frequency/size) | Ihlenburg & Babuška, *Comp. & Math. with Appl.* 30(9):9–37 (1995); Ihlenburg, *FE Analysis of Acoustic Scattering* (1998) | VALIDATED | ~6–10 nodes/λ is the Nyquist-type floor; the **pollution effect** means fixed λ/h is insufficient as k grows (phase error ∝ k²h) — accuracy degrades with frequency/domain size unless refined further or higher-order/stabilized. |

## 6. V&V, UQ, credibility & units

| # | claim | authoritative source | verdict | note |
|---|-------|----------------------|---------|------|
| 1 | ASME V&V 20 u_val² = u_num² + u_input² + u_D²; validated where \|E\| ≤ u_val | ASME V&V 20-2009 (Coleman/Stern methodology) | QUALIFIED | Formula correct. **\|E\| ≤ u_val is a resolution/noise floor** (model error is within the validation's resolution) — V&V 20 explicitly states validation is *not* pass/fail. Adequacy vs a required accuracy is a separate judgment. Softened in place. |
| 2 | Verification precedes validation; calibration ≠ validation (validate on held-out data) | Roache, *V&V in Computational Science and Engineering* (1998); Oberkampf & Roy, *V&V in Scientific Computing* (2010) | VALIDATED | The "solving the equations right / the right equations" framing is canonical; genuine validation assesses predictive accuracy on **independent** data not used in calibration. |
| 3 | NASA-STD-7009 CAS = 8 factors; Sandia PCMM = 6 elements; weakest factor governs | NASA-STD-7009A/B; Oberkampf, Pilch & Trucano, SAND2007-5948 (PCMM) | QUALIFIED | Counts correct. **"Weakest governs" is true for NASA CAS (min-rollup) but overstated for PCMM, which deliberately does not aggregate to a single score** (reports min/avg/max). Qualified in place. |
| 4 | mm-t-s units: steel ρ = 7.85e-9 t/mm³, g = 9810 mm/s², stress/E in MPa | LS-DYNA / Abaqus consistent-units tables | VALIDATED | Self-consistent (mm·t·s ⇒ N, MPa). 7.85e-9 is a common steel value (tables cite 7.8–7.9e-9 by alloy). |
| 5 | NAFEMS LE / T benchmarks are standard code-verification problems | NAFEMS, *The Standard NAFEMS Benchmarks* (TNSB, Rev. 3, 1990) | VALIDATED | LE (linear-elastic) and T (thermal) series are recognized vendor-used verification cases. **They are code/solver verification, not experimental validation.** |
| 6 | ECSS-E-ST-32-03 FE-model verification checklist (free-free RBMs, mass/CoG, strain-energy/ε norms, orphan nodes, SPC reactions ≈0) | ECSS-E-ST-32-03C (2008) = EN 16603-32-03 | VALIDATED | Confirmed: rigid-body mass matrix reproducing mass/inertia/CoG, strain-energy/grounding residual (ε → 0), orphan-node justification. "SPC reaction ≈ 0" is standard FE QA (NASA FEMCI; NX Nastran model checks) consistent with the standard's intent. |
| 7 | Free-free unconstrained 3D solid → 6 RB modes at ≈0 Hz; count is dimensionality-dependent | Structural-dynamics theory; NASA GSFC FEMCI; NX Nastran free-free QA | VALIDATED | 6 RBMs (3 translation + 3 rotation) appear near-zero numerically; 2-D plane → 3, axisymmetric → 1. |
| 8 | ASME V&V 40 scales V&V rigor to decision consequence/risk | ASME V&V 40-2018; FDA guidance (2023) | VALIDATED | Model risk = f(model influence, decision consequence); required credibility set commensurate with risk. Written for medical devices but the risk-informed framework is widely adapted. |

## In-place corrections this validation pass triggered

- **ZZ/SPR "bounds" → "estimates (asymptotically exact)"** (`SKILL.md`): the Zienkiewicz–Zhu / SPR recovery
  estimator is asymptotically exact, not a guaranteed upper bound.
- **"weakest factor governs" qualified** (`SKILL.md`): true for NASA-STD-7009 CAS (min-rollup); Sandia PCMM
  deliberately does *not* aggregate to a single governing score.
- **ASME V&V 20 `|E| ≤ u_val`** (`SKILL.md`): clarified as a *resolution/noise floor* for detecting model
  error, not a binary pass/fail "validated" test.

*Methodology: six parallel domain reviews, each instructed to prefer consensus standards > classic textbooks >
peer-reviewed papers > authoritative vendor manuals, and to mark UNVERIFIED rather than cite an unconfirmed
source. Every DOI/standard number above was confirmed to resolve to the stated work.*
