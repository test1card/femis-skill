# Buckling & structural stability — practitioner-grade best-practices brief

Scope: **why linear buckling over-predicts, the three analysis levels (LBA / GNA-GNIA / GMNIA), knockdown factors, imperfection seeding, post-buckling path-following, and the buckling modes of built-up structures** — eigenvalue extraction, imperfection-sensitive shells, snap-through/snap-back, stiffened panels, stress-stiffening/preload, thermal and lateral-torsional buckling, and the acceptance gates that make a stability result defensible. Cross-verified against EN 1993-1-6 (shell buckling), NASA SP-8007 Rev 2 (2020), the NESC Shell Buckling Knockdown Factor (SBKF) program, Ansys/Abaqus/Nastran solver docs, and stability-theory references. Numbers are code lower-bounds / industry rules of thumb; always confirm against the governing design code and your installed solver version. Citations are bracketed `[n]` → SOURCES at end.

The governing rule for the whole topic: **the linear eigenvalue buckling load is an upper bound that real structures almost never reach.** Thin shells in particular buckle at a *fraction* of the classical load because of geometric imperfections, and the entire discipline exists to quantify that gap — by an empirical knockdown factor, or by a nonlinear analysis with realistic imperfections seeded in. A linear buckling number reported as the strength is the single most common — and most dangerous — stability mistake.

The numerical machinery (eigensolvers for `Kφ = −λK_gφ`, arc-length/Riks for the post-limit path, `STABILIZE` for local instabilities, negative-pivot interpretation) lives in **`solver-numerics.md` §2–§3 and §6** — this brief is the *application* discipline and cross-links there rather than repeating it.

---

## 1. The three analysis levels (EN 1993-1-6 nomenclature)

EN 1993-1-6 (shell buckling) gives the cleanest naming for the ladder of fidelity. The same hierarchy applies in every code and solver; the letters (G = geometric, M = material, N = nonlinear, I = imperfections, A = analysis) compose:

| Level | Name | What it captures | Gives | Cost |
|---|---|---|---|---|
| **LA / LBA** | Linear (bifurcation) buckling | Eigenvalue of `Kφ = −λK_gφ`; small-deflection, elastic, perfect geometry | Buckling load factor λ (× the applied load) + mode shapes; **upper bound** | One static + one eigen solve — cheap |
| **GNA** | Geometrically Nonlinear, perfect | Large-deflection equilibrium path of the *perfect* structure | Limit load of the perfect shell (still optimistic for imperfection-sensitive shells) | Nonlinear static |
| **GNIA** | Geometrically Nonlinear + Imperfections | GNA with a seeded geometric imperfection; trace past the limit point with arc-length | Realistic elastic collapse load | Nonlinear static + imperfection |
| **MNA** | Materially Nonlinear, perfect geometry | Plastic limit / collapse load, small-deflection | Plastic reference resistance (used in the EN capacity-curve interaction) | Nonlinear static |
| **GMNA / GMNIA** | Geometrically + Materially Nonlinear (+ Imperfections) | Everything: large deflection, plasticity, residual stress, imperfections | The design collapse load — the **most realistic** analysis | Most expensive; the reference for thin metal shells |

**How to use the ladder.** Run **LBA first, always** — it is cheap, gives the mode shapes you need to seed imperfections, and tells you whether buckling even competes with strength. Then either (a) apply a **code knockdown factor** to the LBA load (the SP-8007 / EN "stress-design" route), or (b) run **GNIA/GMNIA** with realistic imperfections to demonstrate the margin directly (the "numerically determined" route, EN 1993-1-6 Annex). For slender thin shells the two routes should agree to within the knockdown scatter; if GMNIA gives *more* than the knocked-down LBA, your imperfections are too small. [1][2]

> **LBA is for mode extraction and a first screen — never for the reported strength of a thin shell.** It ignores imperfections, pre-buckling nonlinearity (the membrane stress field that develops before buckling), load redistribution, and plasticity. It is the *only* level that is one cheap solve, which is exactly why it is over-reported.

The eigenvalue solve itself: `Kφ = −λK_gφ`, where `K_g` is the geometric (stress) stiffness from a reference static load. Use **Block Lanczos** (robust, handles the indefinite buckling pencil) — see `solver-numerics.md` §2; iterative Lanczos (LANPCG) is **not** for buckling. Extract several modes, not one (§6 gate). Linear buckling needs the pre-stress carried from a static substep (Ansys `PSTRES`/`STATSUB`, Abaqus `*BUCKLE` after a `*STATIC` step, Nastran SOL 105). [solver-numerics §2]

---

## 2. Knockdown factors — the heart of shell buckling

Real thin shells buckle at a *fraction* of the classical/LBA load. The ratio is the **knockdown factor (KDF)**:

> **ρ = N_cr,design / N_cr,classical** (or `λ_design / λ_LBA`), with **0 < ρ ≤ 1**.

The reason is **imperfection sensitivity**: a shell in axial compression stores enormous membrane strain energy and has many closely-spaced buckling modes with nearly the same critical load. A tiny geometric deviation lets the structure find a lower-energy buckled state, so the realized load collapses far below the perfect-shell eigenvalue. Axial compression of a thin cylinder is the **most imperfection-sensitive case in all of structural mechanics**; external pressure and torsion are less sensitive; a flat plate in compression is *insensitive* (it has stable post-buckling, see §4). [3][4]

**NASA SP-8007 — the launch-vehicle standard.** The original 1968 monograph "Buckling of Thin-Walled Circular Cylinders" gave a deterministic empirical lower-bound KDF as a function of R/t, fitted to the lower envelope of decades of test scatter. It was **revised to Rev 2 in 2020** after ~50 years — the revision incorporates modern high-fidelity analysis and the SBKF test data, and explicitly frames the 1968 curve as a *very conservative* lower bound that newer methods can beat with justification. [3]

> Historically the SP-8007 lower-bound ρ falls as the shell gets thinner: **as low as ~0.2 for very thin cylinders** (high R/t) in axial compression, rising toward ~0.5–0.7 for thicker shells. Treat the exact value as R/t-dependent from the current curve — **never** assume a single fixed number, and always cite the edition. [3]

**SBKF / NESC — earning a higher KDF.** The NASA Engineering & Safety Center **Shell Buckling Knockdown Factor** program (and its composite-cylinder companion) showed that the 1968 lower bound is *overly* conservative for modern, well-controlled hardware. With **measured (as-built) imperfections, manufacturing quality control, and high-fidelity GMNIA**, test cylinders reach **~0.7–0.9 of classical** — a large mass saving on a launch vehicle. The lesson: a low KDF is the price of *not* characterizing your imperfections; measuring them and analyzing with them buys the margin back. [4][5]

**Two legitimate routes to the design load:**
1. **Stress design (KDF route):** N_design = ρ · N_LBA, with ρ from SP-8007 / EN 1993-1-6 capacity curves (the α imperfection-reduction factor and the χ buckling-reduction curve). Fast, code-blessed, conservative.
2. **Numerically determined (GMNIA route):** demonstrate the collapse load directly with realistic imperfections (§3), then apply only the code's calibration/partial factor. Needs imperfection justification and a calibration check against a known case (EN 1993-1-6 requires the GMNIA procedure be validated against a configuration with a known answer). [1][3][4]

For non-shell members (columns, beams) the analogous "knockdown" is built into the **column/buckling curves** (Euler reduced by Perry-Robertson / EN 1993-1-1 χ curves a–d for residual stress + out-of-straightness) — same idea, different empirical packaging (§5, §8).

---

## 3. Imperfection seeding — the menu

If you go the GNIA/GMNIA route, the geometric imperfection *is* the analysis — its **shape** and **amplitude** set the answer. Pick the method deliberately and justify it:

| Method | What you do | Best for | Watch-outs |
|---|---|---|---|
| **1st eigen-mode (eigen-affine)** | Scale the LBA mode-1 shape and add it to the nodal geometry | Default screening; the EN/most-codes baseline | **Not always the worst** mode; for cylinders the lowest eigenvalue is one of many near-equal modes |
| **Worst multiple-mode combination** | Superpose several low modes, search amplitudes/phases for the lowest collapse | Closely-spaced spectra (cylinders, spheres) where mode-1 alone is unconservative | Combinatorial search; can be costly — optimization or DOE over a few modes |
| **Measured / as-built geometry** | 3-D scan the real part, map the deviation field onto the mesh | Highest fidelity (SBKF); flight hardware; ties to the as-built / metrology workflow | Needs the scan; result is part-specific, not a design envelope |
| **Single Perturbation Load (SPLA / DLP)** | Apply a single inward lateral "dimple" load, increase axial load, find the **plateau** of collapse-load-vs-dimple-magnitude | Deterministic, **mesh-robust lower bound** for axially-compressed cylinders; design-friendly | The plateau (not the minimum) is the design value; verify the dimple is local and the plateau is reached |
| **Manufacturing signature** | Impose the known fabrication pattern (weld shrinkage land, mid-surface traveling wave, roll-forming periodicity) | Welded tanks, rolled/seamed shells | Requires process knowledge; combine with eigen-mode for robustness |

**Amplitude discipline (decisive).** The imperfection amplitude is *the* sensitivity knob:
- **Too small** → the GNIA collapse load creeps back up toward the (unconservative) LBA value.
- **Too large** → the seeded shape "corrugates" / pre-stiffens the shell and can give a *false higher* load or the wrong mode.
- **Tie the amplitude to the tolerance spec.** Common bases: a fraction of the wall thickness (e.g. **0.1–1·t**, often ~t for general work), the **fabrication tolerance class** (EN 1993-1-6 gives Class A/B/C imperfection amplitudes Δw₀ = (1/Q)·√(r/t)·t tied to a fabrication-quality parameter Q), or the **measured deviation envelope**. State which, and report a **sensitivity sweep over amplitude** — the collapse load vs amplitude curve is the real deliverable, not a single number. [1][6]

**Sign and direction matter.** For cylinders, *inward* dimples are usually worst; for a single eigen-mode the sign that reduces the load is the one to use. SPLA's inward perturbation is chosen for exactly this reason. [6]

---

## 4. Bifurcation vs limit point vs snap-through / snap-back

Stability "failure" is not one phenomenon. The load–displacement topology decides which solver control you need (cross-ref `solver-numerics.md` §3):

| Behavior | Path topology | Post-critical | Solver control |
|---|---|---|---|
| **Stable-symmetric bifurcation** | Path branches; post-buckling stiffens (rising) | **Benign** — plates carry load past buckling (post-buckling reserve, effective width) | Load or displacement control fine; the structure is imperfection-*insensitive* |
| **Unstable-symmetric / asymmetric bifurcation** | Path branches; post-buckling **drops** sharply | **Dangerous** — shells; sharp load shedding, **highly imperfection-sensitive** (this is what drives the KDF) | Arc-length; small imperfection collapses it near the bifurcation |
| **Limit point (snap-through)** | Single path with a smooth peak (no branch); load rises, peaks, then drops with continued displacement | Shallow arches, domes, shallow shells "snap" to an inverted shape | **Displacement or arc-length control** — load control *diverges* at the peak |
| **Snap-back** | Path turns back in **both** load *and* displacement (S/Z shaped) | Sharp local instabilities, some composite/delamination, some shells | **Arc-length specifically** — neither load nor displacement control can trace it |
| **Mode-jumping** | Sudden jump to a different buckled pattern (secondary bifurcation) on the post-buckling path | Stiffened panels, long plates changing half-wave count | May need **dynamic** (implicit-dynamic or explicit) relaxation; static arc-length can stall at the jump |

**Why control type is not optional.** Load control imposes the load and solves for displacement — it cannot pass a limit point (the load it is told to apply does not exist on the higher branch) and **diverges** with a negative-pivot. Displacement control imposes displacement and solves for load — it passes a simple limit point but **fails at snap-back** (displacement also reverses). **Arc-length (Riks/Crisfield)** treats the load factor as an extra unknown and steps along the path in (u, λ) space, so it traces past both — this is fully covered in `solver-numerics.md` §3 (Riks defaults, `ARCLEN`, SOL 106/400, the contact-loss caveat). For mode-jumping and dynamic snap, switch to implicit-dynamic with a little numerical damping, or explicit. [solver-numerics §3]

**Bifurcation vs limit point — a practical tell.** A *perfect* structure with a bifurcation shows the eigenvalue (LBA) clearly; adding any imperfection converts the sharp bifurcation into a smooth limit point (the imperfect path "rounds the corner" and peaks below the eigenvalue). That conversion *is* the imperfection-sensitivity story — the more it drops, the more sensitive the shell.

---

## 5. Built-up / stiffened structures — local vs global vs element

A real panel, frame, or stiffened shell does not have *one* buckling load — it has a **hierarchy of competing modes**, and the design must check all of them plus their interaction:

| Scale | Mode | Driven by | Check |
|---|---|---|---|
| **Local (plate)** | Skin pocket / web / flange plate buckling between stiffeners | Plate slenderness b/t, edge support, stress field | Plate buckling coefficient k (loading + boundary), σ_cr = k·π²E/[12(1−ν²)]·(t/b)² |
| **Stiffener** | **Tripping** (lateral-torsional rotation of the stiffener) and **crippling** (local plastic collapse of stiffener elements) | Stiffener torsional stiffness, flange outstand | Tripping eigen-mode in the panel model; crippling by Needham/Gerard semi-empirical (Σ of element crippling) |
| **Global** | Euler column buckling of the whole stiffened panel between frames/supports | Panel EI, support spacing L, end fixity | Euler P_cr = π²EI/(KL)²; column curves (χ) for imperfection + residual stress |
| **Interaction** | Local-then-global; post-local **effective width**; skin shedding load to stiffeners | Sequence and coupling of the above | Effective-width method; combined / interaction check; FE GMNIA captures it directly |

**Effective width / post-buckled load redistribution.** A flat plate buckles locally but **keeps carrying load** (stable post-buckling, §4) — the membrane stress redistributes to the stiffened edges. The classic design idealization replaces the buckled plate with an **effective width** b_eff of fully-effective material at the edge stress (von Kármán / Winter). The stiffener then carries a disproportionate share and can fail by tripping/crippling or trigger global buckling — **the interaction is what governs**, and designing each mode in isolation is unconservative. Aerospace stiffened-panel methods (and the crippling allowables) exist precisely to capture this. [7][8]

**Crippling** is *local plastic post-buckling collapse* of thin outstanding elements (angle/zee/channel flanges), not elastic buckling — semi-empirical (Needham, Gerard) curves give the crippling stress as a function of element b/t and material; the section crippling load is the sum over elements. It sets the practical compressive strength of thin extrusions/formed sections below their Euler load. [8]

**Tripping** (stiffener lateral-torsional instability) and **mode-jumping** between local half-wave patterns both appear naturally in an FE eigenvalue/GMNIA of the panel — but only if the **mesh resolves the local half-waves** (several elements per buckle half-wavelength) and the **symmetry BCs are off** (§6). A coarse mesh or a symmetry plane silently filters the governing local/antisymmetric mode.

---

## 6. Stress-stiffening / preload, thermal, lateral-torsional, plasticity

**Stress-stiffening & preload.** Tension stiffens, compression softens — the geometric stiffness `K_g` from an existing stress state shifts the buckling (and natural-frequency) result. A pre-tensioned member buckles at a higher load; a preloaded/compressed member at a lower one. Always carry the real pre-stress into the buckling solve (Ansys `PSTRES,ON` + `STATSUB`; Abaqus `*BUCKLE` referencing the loaded base state; Nastran SOL 105 with the static subcase). This is the **same geometric-stiffness mechanism** that shifts modal frequencies — cross-ref `dynamics-nvh-acoustics.md` stress-stiffening / pre-stressed modal, and `solver-numerics.md` PSTRES. Bolt preload, spin (centrifugal), thermal pre-stress, and pressure all feed `K_g`. [solver-numerics §2; dynamics-nvh]

**Thermal buckling.** A constrained member that is heated cannot expand freely → it develops compressive stress = a buckling driver. The "load" is the temperature field, and the eigenvalue gives the critical ΔT (or a temperature multiplier). Watch for: temperature-dependent E (the shell softens as it heats, lowering the critical load further), follower thermal stress, and that the *restraint* (not just the heat) creates the compression — an unrestrained free expansion never buckles. Common in exhaust/hot structures, panels with through-thickness gradients, and cryogenic-to-warm fixtures.

**Lateral-torsional buckling (LTB).** A beam bent about its strong axis can buckle by combined lateral deflection + twist of the compression flange — an out-of-plane instability of an in-plane-loaded member. Governed by the **critical moment M_cr** (function of unbraced length L_b, warping constant C_w, torsion constant J, and the moment gradient factor C_b). Brace the compression flange to raise L_b/reduce the effective length. EN 1993-1-1 / AISC give χ_LT reduction curves analogous to column curves. An FE LBA of a beam in bending will return the LTB mode — again **only with symmetry BCs off** (LTB is antisymmetric).

**Plasticity reduces buckling.** For stocky (low-slenderness) members the material yields before the elastic critical load, so the **tangent-modulus / reduced-modulus (Shanley)** theory governs: buckling occurs at the load where the *tangent* stiffness, not the elastic one, can no longer hold equilibrium. Slenderness λ̄ = √(f_y·A/P_cr,elastic) sets the regime — **inelastic buckling** at low λ̄ (curve approaches the squash/yield load), **elastic (Euler) buckling** at high λ̄, with a transition (column curves) between. This is why GMNIA (material + geometric + imperfections) is the reference for metal shells: the imperfection drives early yielding at the dimple, plasticity softens locally, and collapse follows below both the elastic eigenvalue *and* the plastic squash load. [2]

---

## 7. Acceptance gates (buckling)

Run this checklist before reporting any stability result:

- **LBA mode is physically sensible** — it is a structural mode (skin pocket, panel, global sway), **not a single-element mesh artifact** (a lone distorted element, a tiny stress concentration, a connection-stiffness ghost). If the mode is a one-element wrinkle, refine the mesh and re-extract; a real buckling mode is mesh-convergent in shape and load factor.
- **Enough modes extracted** — never just mode 1. Thin shells and stiffened panels have **closely-spaced** eigenvalues; extract a band and check whether several modes cluster near λ_min (if so, the imperfection must combine them, §3). Confirm the eigensolver did not miss modes (Sturm check, `solver-numerics.md` §2).
- **Imperfection amplitude is justified** — tied to the fabrication tolerance / measured envelope / code class, **not** an arbitrary number; report the collapse-load-vs-amplitude sensitivity (§3).
- **GNIA/GMNIA traced *past* the limit point** — the arc-length solve actually went over the peak and onto the descending branch (you can see the limit load), not just up to the first non-converged step. The reported strength is the **peak**, not the last converged load before divergence.
- **Stabilization energy ≪ strain energy** — if `STABILIZE`/viscous damping was used to get through local instabilities, the artificial dissipation must be a small fraction (a few % at most) of strain energy, or it props up a fake load (`solver-numerics.md` §3 gate). Prefer arc-length to over-stabilizing.
- **KDF source cited** — if you applied a knockdown to LBA, name the curve and edition (SP-8007 Rev 2, EN 1993-1-6 capacity curve, SBKF-justified value). A bare "×0.65" with no source is not defensible.
- **Symmetry BCs are OFF** — symmetry planes filter out **antisymmetric and global** modes, which are frequently the *governing* (lowest) ones for shells, columns, LTB, and stiffened panels. Model the full structure (or use cyclic-symmetry with harmonic indices that admit the relevant modes) for any buckling analysis. A "symmetric" buckling model can silently report a load **far above** the true antisymmetric critical load.
- **Pre-stress carried correctly** — the geometric stiffness reflects the real loaded state (preload, pressure, spin, thermal), not the unloaded one (§6).
- **Level matches the consequence** — LBA for screening only; KDF-on-LBA or GMNIA for a reported strength; GMNIA (with imperfections + plasticity) for thin metal shells and anything imperfection-sensitive (§1–§2).

---

## 8. Condensed quick-reference

- **Levels (EN 1993-1-6):** LBA = `Kφ=−λK_gφ`, cheap, **upper bound, mode-extraction only**. GNA/GNIA = large-deflection + imperfection, arc-length past the limit point. GMNIA = + plasticity = the design collapse load for thin metal shells.
- **Knockdown factor** ρ = N_design/N_classical: thin cylinders in axial compression are the most imperfection-sensitive case; **SP-8007 Rev 2 (2020)** lower-bound ρ can be **~0.2** for very thin shells; **SBKF/NESC** earns **0.7–0.9** with measured imperfections + QC + GMNIA. Two routes: KDF×LBA, or GMNIA-with-imperfections direct.
- **Imperfection menu:** 1st eigen-mode (default), worst multi-mode combo (closely-spaced spectra), measured/as-built scan (highest fidelity), **SPLA/DLP** single-dimple (deterministic lower bound), manufacturing signature. **Amplitude tied to tolerance**; sweep it.
- **Path topology → control:** stable-symmetric = benign (plates, post-buckling reserve); unstable bifurcation = shells (sharp drop, KDF driver); **limit/snap-through → displacement or arc-length**; **snap-back → arc-length only**; mode-jumping → dynamic.
- **Built-up:** check **local plate**, **stiffener tripping/crippling**, **global Euler**, and their **interaction (effective width)** — isolation is unconservative.
- **Also:** stress-stiffening/preload shifts buckling (carry pre-stress); thermal buckling = restraint × ΔT; LTB of beams (antisymmetric — symmetry off); plasticity reduces buckling (tangent-modulus, slenderness sets elastic vs inelastic).
- **Gates:** sensible (non-mesh-artifact) mode; enough/clustered modes; justified imperfection amplitude; GNIA traced past the limit; stabilization energy ≪ strain energy; **KDF cited**; **symmetry BCs OFF**.

**See also:** `solver-numerics.md` §2 (eigensolvers for the buckling pencil, Sturm/mode-completeness, prestressed modal), §3 (arc-length / Riks / Crisfield, `STABILIZE` energy gate, load-vs-displacement control, the contact-loss caveat), §6 (negative-pivot = physical in post-limit buckling); `dynamics-nvh-acoustics.md` (stress-stiffening / pre-stressed modal — same geometric-stiffness mechanism); `composites-analysis.md` (panel/sandwich buckling — face wrinkling, dimpling, core crimping, layered-shell limits); `material-modeling.md` (plasticity for GMNIA).

---

## SOURCES

Reliability key: **H** = primary standard / NASA technical publication / vendor theory manual (highest); **M** = reputable practitioner / handbook / cross-checked encyclopedic; **L** = forum/secondary (corroborative only).

1. EN 1993-1-6 — *Eurocode 3: Design of steel structures — Part 1-6: Strength and stability of shell structures* (LA/GNA/MNA/GMNIA nomenclature; stress-design capacity curves; GMNIA imperfection classes Δw₀ via fabrication-quality parameter Q; calibration-against-known-case requirement). — **H** (standard).
2. EN 1993-1-1 — *Eurocode 3 Part 1-1* (column buckling curves a–d, χ reduction for out-of-straightness + residual stress; lateral-torsional χ_LT; slenderness λ̄). Corroborated by AISC 360 (Chapters E/F). — **H** (standard).
3. NASA SP-8007 Rev 2 (2020) — *Buckling of Thin-Walled Circular Cylinders* (empirical KDF ρ vs R/t lower bound; 2020 revision of the 1968 monograph incorporating high-fidelity analysis & SBKF data; axial compression as the most imperfection-sensitive case). https://ntrs.nasa.gov/api/citations/20205011530/downloads/20205011530%20Rev%202FINALa%201-2023.pdf — **H** (NASA technical standard).
4. NESC — *Shell Buckling Knockdown Factor (SBKF)* project, incl. buckling KDFs for composite cylinders (measured imperfections + QC + high-fidelity GMNIA reach ~0.7–0.9 of classical; 1968 lower bound shown over-conservative for modern hardware). https://www.nasa.gov/sites/default/files/atoms/files/nesc_tb_16-01_buckling_knockdown_factors_for_composite_cylinders.pdf ; https://ntrs.nasa.gov/citations/20240000391 — **H** (NASA/NESC technical bulletin).
5. NESC SBKF program assessments / NTRS test-vs-analysis correlation (large-scale cylinder buckling tests validating higher analysis-based KDFs). https://ntrs.nasa.gov/citations/20240000391 — **H** (NASA).
6. Single-Perturbation-Load Approach (SPLA / DLP) & imperfection-sensitivity / stability landscape — deterministic dimple-load lower bound for axially-compressed cylinders; imperfection-sensitivity reviews. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9922549/ ; https://ntrs.nasa.gov/api/citations/20100016259/downloads/20100016259.pdf — **M/H** (peer-reviewed + NASA).
7. Effective-width / post-buckled plate redistribution (von Kármán / Winter) and stiffened-panel interaction — stability handbooks (Timoshenko & Gere, *Theory of Elastic Stability*; Bruhn, *Analysis & Design of Flight Vehicle Structures*). — **M** (canonical handbooks).
8. Crippling (Needham/Gerard semi-empirical) and column/local/global interaction for thin-walled sections — Bruhn (flight-vehicle structures); NACA/NASA crippling allowables lineage. — **M** (canonical handbook / NACA lineage).
9. (Cross-ref) Arc-length/Riks/Crisfield, `STABILIZE` energy gate, eigensolvers for the buckling pencil, negative-pivot interpretation — see `solver-numerics.md` §2/§3/§6 and its Abaqus/Ansys/Nastran source list. — **H** (vendor manuals, cited there).
