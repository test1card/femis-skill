# Meshing, Element Technology, and Mesh Convergence — Practitioner Brief

Scope: solver-agnostic best practices for structural / thermal / coupled FEM, with the
numbers, criteria, and failure modes that decide whether a result is trustworthy. Vendor
specifics (Ansys / Simcenter-Nastran / Abaqus / COMSOL) are called out only where they
diverge. Citations are keyed to the SOURCES list at the end.

> The single most important idea: **a result is not valid because the solver converged
> (equilibrium) — it is valid only when the *quantity of interest* (QoI) stops changing as
> the mesh is refined (discretization convergence), and that change is reported as a number.**
> Everything below serves that goal. [S1][S15][S22]

---

## Contents

- [1. Element family & order selection](#1-element-family-order-selection)
- [2. Locking, hourglassing, and the integration scheme](#2-locking-hourglassing-and-the-integration-scheme)
- [3. Mesh quality metrics & thresholds](#3-mesh-quality-metrics-thresholds)
- [4. Meshing strategy](#4-meshing-strategy)
- [5. Mesh independence & the Grid Convergence Index (GCI)](#5-mesh-independence-the-grid-convergence-index-gci)
- [5A. A-posteriori / recovery-based error estimation](#5a-a-posteriori-recovery-based-error-estimation-the-single-mesh-complement-to-gci)
- [5B. Goal-oriented (output) error control — dual-weighted residual (DWR)](#5b-goal-oriented-output-error-control-dual-weighted-residual-dwr)
- [5C. h- vs p- vs hp-refinement](#5c-h--vs-p--vs-hp-refinement-order-is-itself-a-refinement-lever)
- [5D. Element technology consolidated](#5d-element-technology-consolidated-locking-b-bar-eas-reduced-integration-shells)
- [6. Converging the QoI vs singular peaks](#6-converging-the-qoi-vs-singular-peaks-the-trap-that-breaks-naïve-studies)
- [7. Stress linearization](#7-stress-linearization-turning-a-non-convergent-field-into-a-code-compliant-number)
- [8. Top mistakes (each with the fix and citation)](#8-top-mistakes-each-with-the-fix-and-citation)
- [9. Quick-reference defaults](#9-quick-reference-defaults-sane-starting-points-then-verify-by-convergence)
- [SOURCES](#sources)
- [Related references](#related-references)

## 1. Element family & order selection

### 1.1 Linear vs quadratic (the first decision, and the most consequential)
- **Quadratic (2nd-order) elements capture bending and stress gradients with far fewer
  elements than linear ones.** A quadratic edge can curve and represents a linear strain
  field exactly; a linear edge stays straight and represents only constant strain per
  element. [S6][S5]
- **Default to quadratic for stress/strain accuracy**, especially anywhere bending,
  curvature, or stress concentrations matter. Use linear elements when (a) the field is
  dominated by membrane/axial behavior, (b) you need many elements through a thickness in
  contact/impact, or (c) explicit dynamics (linear elements are standard there). [S5][S6]
- **TET4 (linear tet) is the worst common element — avoid it for stress.** It is
  over-stiff and famously inaccurate; one element resolves only constant strain. If you must
  use tets, use **TET10 (quadratic)**. [S5][S7]
- Cost note: quadratic elements have more nodes/DOF per element and more integration points,
  so cost-per-element is higher — but the *accuracy-per-DOF* is usually far better for
  smooth solid mechanics, so the total solve to a target accuracy is typically cheaper. [S6]

### 1.2 Tet vs hex vs wedge (prism)
- **Hex (HEX8/HEX20) is the gold standard** for accuracy-per-DOF and is preferred wherever
  the geometry can be swept or mapped. Linear hex (HEX8) generally beats both linear and
  even quadratic tet in many nonlinear/elasto-plastic problems. [S5][S7]
- **Quadratic tet (TET10) is the workhorse for arbitrary geometry.** Large-scale comparative
  studies (Schneider et al., ACM TOG 2022; Coreform hex-vs-tet) find TET10 performs *equal
  to or better than* hex for many elliptic-PDE / structural problems with today's automatic
  meshers — and tets mesh robustly and automatically where hex meshing is labor-intensive or
  impossible. The old "hex is always better" rule is too strong once you control for order.
  [S7][S5]
- **Practical rule:** sweepable/blocky geometry → hex (sweep/MultiZone); messy organic
  geometry → TET10. Don't hand-build hex meshes for complex parts to chase a marginal
  accuracy gain you can recover with TET10 + local refinement. [S5][S7]
- **Wedges/prisms (PENTA6/PENTA15)** are transition elements: use them in boundary layers,
  as the prism layer in hex-dominant/MultiZone meshes, and in sweep transitions. Avoid large
  regions of linear wedges as primary stress elements — they share the stiffness pathologies
  of linear tets in bending. [S8]
- **Pyramids (PYRA5/13)** exist only to bridge hex→tet faces; keep them out of high-stress
  regions.

### 1.3 Shell vs solid vs beam (idealization)
- **Beam (1D):** use when two dimensions ≪ the third (struts, frames, stiffeners,
  trusses). Captures axial/bending/torsion/shear via section properties. Cheapest by orders
  of magnitude; correct for slender members. Verify with NAFEMS beam benchmarks. [S5]
- **Shell (2D):** use when wall thickness is small vs in-plane dimensions. Common
  rule-of-thumb thresholds:
  - **Thin-walled if smallest dimension (thickness) is ≳ 10–20× smaller than the largest
    in-plane dimension** (i.e. span/thickness ≳ 10–20). Many shops use **span/thickness ≥ 20
    → clearly shell, ≤ ~5–8 → clearly solid, in-between → judgment.** [S9][S12]
  - Shell models the **mid-surface**; thickness is a property, not geometry. Stress is
    assumed to **vary linearly through the thickness** (membrane + bending), so shells
    **cannot resolve true through-thickness stress profiles** (e.g. contact bearing, bolt
    pre-load bearing, weld-toe 3D fields). [S9]
  - **Thin vs thick shell:** thin (Kirchhoff) neglects transverse shear — valid for
    span/thickness ≳ 20; thick (Mindlin–Reissner) includes transverse shear — use for
    moderately thick shells. Most solvers default to thick-shell formulations now. [S9]
- **Solid (3D):** use when through-thickness stress matters, for thick parts, contact
  bearing, or when you cannot cleanly extract a mid-surface. [S9][S12]

#### Shell vs solid — the modern caveat (important, often-missed)
The classic advice "only use solid on thin walls if you can fit ≥3 elements through
thickness, else use shell" is **based on first-order elements**, which are rarely the
default today. With **2nd-order solids, a *single* element through the thickness is as
accurate as a shell**; even solids somewhat larger than the wall thickness give good results,
with accuracy only declining beyond ~3× thickness. The dominant accuracy driver for thin-walled
parts is then **resolving tightly curved geometry (use curvature-based sizing)**, not
through-thickness element count. Conversely, **shells can dangerously *underestimate* stress
at certain features** (e.g. where local 3D effects dominate) — so don't treat shell as
automatically conservative. [S12]

### 1.4 Shell offsets (the classic silent error)
A shell mesh sits on the **mid-surface** by default. If you mesh on a CAD face that is the
**top or bottom** surface (common when extracting from solids), you must apply a **shell
offset** of ±t/2 to put the reference surface at the true mid-plane — otherwise you
introduce geometric thickness errors and, in assemblies, artificial gaps/overlaps and wrong
bending stiffness/eccentricity (especially for stiffened panels and joints). Always set the
offset explicitly (`TOP`/`BOTTOM`/`MID`, or a numeric offset) and verify the rendered solid
thickness visually. [S9]

### 1.5 2D idealizations: plane stress / plane strain / axisymmetric
- **Plane stress:** σ_z ≈ 0 — thin planar parts loaded in-plane (sheet, bracket, plate with
  free out-of-plane surfaces). Out-of-plane strain is free.
- **Plane strain:** ε_z ≈ 0 — long prismatic bodies where one dimension ≫ others and ends
  are constrained (dams, long pipes/tunnels, a slice of a long roller). Out-of-plane stress
  develops.
- **Axisymmetric:** geometry, loads, and BCs all symmetric about an axis (pressure vessels,
  nozzles, shafts, O-rings). Models one radial-axial slice; cannot represent non-axisymmetric
  loads/modes. Hoop behavior is captured automatically.
- Choosing the wrong 2D idealization changes effective stiffness substantially (plane-strain
  is stiffer than plane-stress for the same material) and is a frequent source of error. Use
  2D whenever it legitimately applies — it is cheap and avoids many 3D pitfalls. [S1]

---

## 2. Locking, hourglassing, and the integration scheme

These are the element-technology pathologies that produce wrong answers even on a "good"
mesh. Know the symptom, the cause, and the remedy.

### 2.1 Shear locking (too STIFF)
- **Symptom:** displacements/strains under-predicted in bending; result improves slowly with
  refinement.
- **Cause:** **fully-integrated first-order** elements (e.g. C3D8 / linear quad/hex). A
  straight-edged linear element cannot bend, so under bending it develops **parasitic
  (spurious) shear strain** that absorbs energy and over-stiffens the element. Worst when
  element in-plane size ≈ or > thickness. [S2][S3]
- **Quantified example (Fidelis):** a fully-integrated linear hex (C3D8) **under-predicted
  deflection by ~34.5%** in a bending test. [S3]
- **Remedies (in order):** (1) **use 2nd-order elements** (C3D20); (2) **reduced
  integration** (removes the parasitic shear, but see hourglassing); (3) **incompatible
  modes / enhanced assumed strain**; (4) refine — at least **4–5 linear elements through the
  thickness** to keep error < ~5% if you must stay linear. [S2][S3]

### 2.2 Volumetric locking (too STIFF, near-incompressible)
- **Symptom:** grossly over-stiff response; checkerboard/oscillating pressure field.
- **Cause:** **fully-integrated** elements with **(nearly) incompressible** material —
  metals at full plasticity, rubber/elastomers, ν → 0.5. The incompressibility constraint at
  every integration point over-constrains the element. [S1][S3]
- **Remedies:** **B-bar / selective reduced integration** (integrate the *volumetric* part
  with reduced order while the deviatoric part is full); **mixed u-p / hybrid elements**
  (independent pressure DOF — required for true incompressibility, e.g. hyperelastics);
  **enhanced assumed strain**; reduced integration (with hourglass control). [S1][S2]

### 2.3 Hourglassing (too FLEXIBLE — zero-energy modes)
- **Symptom:** displacements *over*-predicted; a distinctive zig-zag "hourglass" deformation
  pattern; nonsensical strain energy. [S3]
- **Cause:** **first-order reduced-integration** elements (e.g. C3D8R) have a single
  integration point at the centroid. Certain deformation modes produce **zero strain at that
  point → zero stiffness → uncontrolled "zero-energy" / spurious modes.** Worse as elements
  get larger (each carries more bending). [S1][S3]
- **Quantified example (Fidelis):** a reduced-integration linear hex (C3D8R) **over-predicted
  deflection by ~32%** in the same test where the fully-integrated element under-predicted by
  ~34.5%. The two errors bracket the truth — a useful sanity check. [S3]
- **Remedies:** **hourglass control / stabilization** (artificial stiffness added *only* to
  the hourglass modes — Flanagan–Belytschko 1981; Bower uses κ ≈ 0.01·μ; **too large →
  re-introduces over-stiffening**); **use 2nd-order elements**; **≥ 4 elements through
  thickness**; mesh fine enough that hourglass energy < ~5–10% of internal energy (monitor
  ALLAE/hourglass energy ratio in explicit). [S1][S3]
- **Health warning:** hourglass control can fail for finite-strain problems and can inject
  spurious low-frequency modes / low wave speeds in dynamics. [S1]

### 2.4 Full vs reduced integration — decision summary
| Scheme | Pros | Cons | Use when |
|---|---|---|---|
| Full integration, linear | No hourglassing | Shear & volumetric locking | Avoid for bending; OK for membrane-only |
| **Reduced integration, linear** | Cheap; cures shear locking; better coarse-mesh accuracy | **Hourglassing** (needs stabilization) | Bulk/large models with hourglass control + adequate mesh |
| Full integration, quadratic | Accurate, no hourglassing, little locking | More DOF/cost | **Default for accurate solid stress** |
| Reduced integration, quadratic | Accurate, robust | Slight rank issues on coarse meshes | Large quadratic models |
| B-bar / SRI / mixed u-p / EAS | Cures volumetric (and shear) locking | More complex | Incompressible / bending-dominated |

[S1][S2][S3]

### 2.5 Remedy taxonomy (one line each)
- **Reduced integration:** fewer Gauss points → removes parasitic shear; needs hourglass
  control on linear elements. [S2]
- **Incompatible modes:** add internal strain modes not tied to nodal displacements → kills
  shear locking in bending (small-strain; Simo–Rifai EAS for finite strain). "Spectacular"
  improvement on linear elements. [S1]
- **B-bar:** replace volumetric strain at Gauss points with the element-averaged volumetric
  strain → kills volumetric locking; generalizes to finite strain. Does **not** fix shear
  locking. [S1][S2]
- **Enhanced Assumed Strain (EAS) / Hu–Washizu mixed:** independent enhanced-strain field;
  fixes **both** shear and volumetric locking. [S2]
- **Mixed u-p / hybrid:** independent pressure DOF — mandatory for fully incompressible
  hyperelastics; increases solve cost (pressure DOF can't be condensed out). [S1]

---

## 3. Mesh quality metrics & thresholds

Bad elements cause local error and, in nonlinear/CFD, **divergence**. Always inspect the
*worst* elements, not the average, and locate them (isolate by metric / isovolume). Negative
Jacobian = inverted element = fatal. [S4][S10][S11]

| Metric | Ideal | Good / acceptable | Reject (FEA) | Notes |
|---|---|---|---|---|
| **Jacobian ratio** | 1.0 | 1–10 for ≥90% of elements | > ~30–40; **any < 0 fatal** | Shape vs ideal element; checks mid-side node placement on quadratics. [S4][S10] |
| **Skewness** | 0 | 0–0.5 excellent; ≤ 0.75 ok | > ~0.9 (and SimScale FEA hard max ≈ **10** on its scale) | Deviation from ideal symmetric shape; the dominant CFD metric. [S4][S11] |
| **Orthogonal quality** | 1.0 | 0.2–1 acceptable; > 0.7 good | < ~0.1–0.15 | 0 worst, 1 best; key for finite-volume/CFD and contact normals. [S4][S11] |
| **Aspect ratio** | 1 (square/cube) | < 5 ideal; up to ~20 ok in low-gradient regions | > ~20–30 in stress regions (SimScale FEA max ≈ 30; tet max ≈ 16) | Longest/shortest edge; high AR fine only along low-gradient directions (boundary layers). [S4][S10][S11] |
| **Warping factor** | 0 | small | large | Out-of-plane twist of quad/shell faces; degrades shells & hex faces. [S10] |
| **Parallel deviation** | 0 | < ~70° | large | Opposite-edge non-parallelism (quads). [S10] |
| **Max corner angle** | 90° (quad) / 60° (tri) | < ~155° | near 180° | Near-degenerate corners. [S10] |
| **Element quality** | 1 | > ~0.3–0.5 | near 0 | Ansys composite volume/edge metric. [S10] |

Practical guidance:
- **One or two bad elements in a low-stress, far-field region rarely matter; bad elements in
  the QoI region always matter.** Fix quality where the answer lives. [S11]
- **High aspect ratio is acceptable only when the long axis aligns with low gradients**
  (boundary layers, thin-wall sweeps). High AR across a steep gradient is an error. [S4][S11]
- A low-quality mesh in CFD/nonlinear FEA "is very likely to diverge"; SimScale publishes
  hard maxima (FEA: aspectRatio 30, tet AR 16, skewness 10; CFD: non-orthogonality 88) as
  divergence thresholds. [S11]
- Mid-side node placement on quadratic elements matters: badly placed mid-nodes (e.g. on a
  fillet) wreck the Jacobian even when corner geometry looks fine. [S4][S10]

---

## 4. Meshing strategy

### 4.1 Method selection (Ansys vocabulary, concepts general)
- **Automatic:** tries to sweep solids / quad-mesh surfaces; falls back to patch-conforming
  tets if not sweepable. Acceptable starting point, not a final answer. [S13]
- **Sweep:** mesh a source face, sweep through to a topologically identical target face →
  structured hex/wedge. Requires a "sweepable" body (same source/target topology, no
  branching). Best accuracy & DOF efficiency for prismatic/extruded geometry. [S13]
- **MultiZone:** ICEM-Hexa blocking approach → **pure hex where possible**, unstructured fill
  elsewhere. Use for bodies that are *almost* sweepable or have multiple sweep directions;
  more robust than plain sweep. [S13]
- **Patch-conforming tet:** bottom-up (edges→faces→volume); **respects all faces, edges, and
  boundaries** → clean conformal mesh that honors small features. Default robust tet method.
  [S13]
- **Patch-independent tet:** top-down (volume first, then project to faces); **can ignore
  small/dirty features** → robust on poor CAD and built-in defeaturing, but does not
  guarantee all faces/edges are captured (be careful where you need named-surface BCs). [S13]
- **Shared topology vs contact at part interfaces:**
  - **Share topology (conformal / glued mesh):** nodes are *merged/coincident* across the
    interface — exact, cheap, no contact solver. Use for bonded/welded/monolithic
    connections and within multibody parts. The interface between a patch-conforming and a
    patch-independent method is fully protected; patch-independent↔patch-independent protects
    only the boundary. [S13]
  - **Contact (non-conformal):** independent meshes joined by contact/constraint equations
    (bonded, frictional, etc.). Required for parts that can separate/slide or where meshes
    can't be made conformal. More expensive, adds contact convergence concerns. **Rule:
    prefer shared topology when the connection never separates; use contact when it can.**

### 4.2 Defeaturing & virtual topology
- **Defeature** small features irrelevant to the QoI (tiny fillets, logos, small holes,
  chamfers) *before* meshing — reduces element count and removes nuisance singularities. But
  **never defeature a feature that drives the QoI** (a fatigue fillet, a notch you're
  assessing). Defeaturing a fillet to a sharp corner *creates* a stress singularity — fine if
  you're not reading stress there, fatal if you are. [S15]
- **Virtual topology / share topology cleanup:** merge slivers, suppress short edges, and
  combine faces to let the mesher place better elements without editing CAD. Use it to
  control where nodes land and to avoid forced tiny elements at CAD artifacts.
- **Set a defeaturing/min-feature size** and a **curvature-based sizing** so curved walls get
  enough facets (target ≥ ~12 elements around a full hole/fillet circle; thin-wall curvature
  resolution often matters more than through-thickness count). [S12]

### 4.3 Refinement & boundary layers at concentrations
- **Bias/inflate mesh toward stress concentrations, contact zones, fillets, holes, and
  thermal/flux gradients.** Use sphere-of-influence, edge sizing, body sizing, or inflation
  layers to add resolution locally rather than globally. [S15]
- Use a **smooth size transition** (growth rate ≤ ~1.2–1.5) from fine to coarse to avoid
  abrupt element-size jumps that create artificial gradients and quality drops.
- In thermal/CFD, resolve boundary layers / near-wall gradients with inflation (anisotropic
  prism/hex layers) — high aspect ratio aligned with the wall is correct here. [S11]

---

## 5. Mesh independence & the Grid Convergence Index (GCI)

This is the verification core (ASME V&V 20-2009; Roache 1994/1997). The GCI converts a grid
refinement study into a **numerical uncertainty band** on the QoI — it is *the* defensible way
to report mesh adequacy. [S1*][S16][S17][S18]

### 5.1 Procedure (three systematically-refined grids)
1. **Pick the QoI(s)** — a *global or local scalar* you actually care about (peak stress at a
   converging location, max deflection, reaction, first natural frequency, total heat rate).
   Do **not** GCI a singular peak (see §6). [S16]
2. **Build 3 grids** with representative cell sizes h₁ < h₂ < h₃ (1 = fine). Use a
   **refinement ratio r = h_coarse/h_fine ≥ 1.3** (Roache's recommended minimum so the
   solutions are clearly distinguishable). Refine *uniformly/systematically* (same refinement
   everywhere, ideally same element type), not just locally. For 3D, halving h multiplies
   element count ~8×. [S16][S17][S18]
   - Representative size: **h = [ (1/N) Σ ΔV_i ]^(1/3)** in 3D (cube root of average element
     volume), or **(1/N)^(1/d)** for uniform refinement. [S17]
3. Solve all three, extract QoI: f₁ (fine), f₂ (medium), f₃ (coarse).

### 5.2 Observed order of accuracy p
With constant ratio r (r₂₁ = r₃₂ = r):

  **p = ln( (f₃ − f₂) / (f₂ − f₁) ) / ln(r)**

(For unequal ratios, p is solved iteratively including a sign term — the
Celik/ASME V&V 20 procedure.) Worked example (curiosityFluids/OpenFOAM cavity): with
f₃−f₂ = 0.002849, f₂−f₁ = 0.000796, r = 2 → p = ln(3.579)/ln(2) ≈ **1.84** (close to the
formal 2nd-order scheme — a good sign). p should land **near the formal order** of the scheme;
a wildly different p signals you are **not in the asymptotic range** (grids too coarse,
oscillatory convergence, or singularity contamination). [S17]

### 5.3 Richardson extrapolation (estimate the "exact"/h→0 value)
  **f_exact ≈ f₁ + (f₁ − f₂) / (r^p − 1)**

This is the zero-mesh-size extrapolated QoI; report it as the best estimate. [S17]

### 5.4 Grid Convergence Index
  **GCI_fine (21) = F_s · |(f₁ − f₂)/f₁| / (r^p − 1) × 100%**

- **Safety factor F_s = 1.25** when you have **3 grids** and a reliably observed p; **F_s = 3.0**
  for a **2-grid** estimate (assumed p). The GCI is a ~95%-confidence numerical uncertainty
  band. [S16][S17]
- Report GCI as a **± band on the QoI**, e.g. "peak von Mises = 212 MPa, GCI_fine = 2.1%."
  A few % is typically acceptable for engineering; tighten for code/safety work. [S16][S18]

### 5.5 Asymptotic-range check (don't skip this)
Compute GCI for both refinement steps and verify:

  **GCI₃₂ / ( r^p · GCI₂₁ ) ≈ 1.0**

A value near 1 confirms the solutions are **in the asymptotic range** — i.e. the GCI band is
meaningful. If it's far from 1, your grids are too coarse or convergence is non-monotonic;
refine further before trusting any extrapolation. [S17][S18]

### 5.6 The pragmatic version (when full GCI is overkill)
At minimum: run **≥ 3 meshes**, plot **QoI vs DOF (or vs 1/h)**, and **refine until the QoI
changes by less than your tolerance** (commonly **< 2–5%** between the two finest meshes for
general work; tighter for certification). A flat tail on the QoI-vs-mesh curve is the visual
proof of mesh independence; the GCI just quantifies the residual band. Always report which
mesh was used and the convergence evidence. [S15][S22]

> Pitfall: "the solver converged" (residuals/equilibrium) ≠ "the mesh converged"
> (discretization). They are independent. Report both. [S1*][S15]

---

## 5A. A-posteriori / recovery-based error estimation (the single-mesh complement to GCI)

GCI (§5) **estimates** discretization error by **refining the mesh ≥3×** (a conservative band via
the safety factor F_s, not a guaranteed bound). An **a-posteriori error estimator** **estimates** the
error of **one solved mesh** directly from its own fields, and — crucially — tells you **where** to
refine. Treat recovery-based (ZZ/SPR) and goal-oriented (DWR) numbers as *estimates*; only
residual/equilibrated estimators (§5A.2) carry **proven** upper/lower bounds. The two are complementary, not rival: use an estimator to *target*
refinement (put DOF where the error is), then use GCI (or a p-extension, §5C) to *certify* the final
band on the QoI. This is the standard rigorous machinery of computational mechanics and is what the
"adaptive mesh refinement" button in commercial codes actually runs. [S26][S27][S30]

### 5A.1 Recovery-based estimator — Zienkiewicz–Zhu (ZZ) on Superconvergent Patch Recovery (SPR)
The most common estimator, and the easiest to bolt onto any displacement FE code.
- **Idea.** The raw FE stress σ_FE is discontinuous between elements and least accurate at nodes.
  Build a **smoothed, superconvergent** stress field **σ\*** by least-squares-fitting a polynomial
  over a **patch of elements** around each node, *sampled at the superconvergent (optimal) Gauss
  points* — this is **Superconvergent Patch Recovery (SPR)**. The recovered field is markedly more
  accurate than σ_FE. [S26]
- **Error indicator.** The element-wise energy-norm error indicator is
  **η_e = ‖σ\* − σ_FE‖_{E,e}** (the recovered field minus the raw field, in the energy norm); the
  **global relative error ≈ ‖σ\* − σ_FE‖_E / ‖σ\*‖_E**. [S26][S27]
- **Effectivity index θ = (estimated error)/(true error).** A good estimator has **θ → 1** as the
  mesh refines — i.e. it becomes **asymptotically exact**. SPR-based ZZ is asymptotically exact when
  the recovery is genuinely superconvergent; this is its defining theoretical property and why it is
  trusted to drive adaptivity. Quote θ (or its asymptotic behaviour on a benchmark) when you rely on
  the estimator. [S27][S28]
- **Drives adaptive refinement.** Refine every element whose η_e exceeds a target, or the worst
  fraction of total error (**Dörfler / "greedy" marking**), then re-solve and iterate until the
  global estimate < tolerance. Most commercial adaptive-mesh features are ZZ/SPR-driven. [S26][S30]

### 5A.2 Residual-based estimator
Bounds the energy-norm error from the **PDE residual of the discrete solution** — element-interior
residuals plus inter-element flux jumps. Explicit/implicit variants come with **provable upper bounds
(reliability)** and **lower bounds (efficiency)**, so they are preferred where *guaranteed* bounds
matter. More rigorous but less common in commercial codes than recovery-based. [S26][S30]

### 5A.3 Discipline — where a recovery estimator is meaningless
A recovery estimator is **meaningless at a singularity** (§6): the recovered field σ\* also diverges,
so the difference ‖σ\* − σ_FE‖ keeps growing. That is not a failure — it **correctly flags the
singular region as high-error**, which is the signal to **defeature / add the real fillet /
linearize (§6, §7)**, *not* to keep refining a stress that will never converge. For a reported QoI,
confirm the estimator is in its asymptotic regime (θ near 1) or fall back to GCI; **recovery error
and GCI should agree in the asymptotic range — if they disagree, you are not converged.** [S26][S29]

## 5B. Goal-oriented (output) error control — dual-weighted residual (DWR)

The energy-norm error of §5A is rarely what the engineer actually cares about; the **quantity of
interest** J(u) is — a stress at a point, a reaction, a flux, a drag/lift coefficient, a
stress-intensity factor. **Goal-oriented error estimation** estimates the error **in J directly** (an
error representation, made a rigorous bound only with equilibrated/residual machinery), and is the
embodiment of this brief's headline rule, *converge the QoI, not the peak*. [S31][S32]

- **Dual-weighted-residual (DWR).** Solve the original ("primal") problem for u, then solve an
  **adjoint / dual problem** whose load is the functional J — its solution z is the **sensitivity of
  J to local residuals**. The output error is then estimated by weighting the primal residuals by the
  dual solution: **err(J) ≈ Σ_e (primal residual)_e · (dual weight)_e**. Refine the elements with the
  largest **contribution to err(J)** — not the largest energy error. [S31][S32]
- **Why it pays.** Energy-norm refinement spends DOF resolving regions that don't affect J; DWR puts
  DOF exactly where they reduce the error *in J*, typically reaching a target accuracy in J at a
  **fraction of the DOF** of uniform or energy-norm refinement. Methods exist that bound the output
  error from **both sides** (upper and lower). [S32][S33]
- **Cost & use.** One extra (linear) **adjoint solve per adaptive cycle**. Use it for
  **single-number deliverables** (a margin, a peak fillet stress, a drag coefficient, an SIF);
  adjoint-based goal-oriented adaptation is the standard behind **drag-/lift-adaptive CFD meshes** and
  pointwise thermo-mechanical QoIs. Still report a final convergence band on J — DWR targets the
  error efficiently but the *reported* number should carry its uncertainty (GCI or a converged
  p-extension). [S31][S33]

> An adaptive run is **not self-certifying.** "The adaptive mesher converged" ≠ "the QoI is
> mesh-independent." Confirm the estimator's effectivity (θ ≈ 1, or compare against a one-step-finer
> solve on a sample problem) and report a final GCI band — or a converged p-/hp-sequence — on the
> reported QoI. [S26][S30]

## 5C. h- vs p- vs hp-refinement (order is itself a refinement lever)

The GCI grid study of §5 refines by **element size h at fixed order**. Order is an *independent*
convergence lever, and choosing the right combination of size and order changes both the rate of
convergence and how you design the convergence study. [S34][S35][S36]

- **h-refinement** — smaller elements at fixed polynomial order. **Algebraic** convergence (error ~
  h^p ~ DOF^(−p/d)); the basis of the GCI grid study. Robust, universal, what most workflows do. [S34]
- **p-refinement (p-version FEM)** — raise the **polynomial order** on a *fixed* mesh (hierarchic
  bases routinely go to order 8+). On **smooth** solutions p-extension converges **faster than h for
  the same DOF**, and a single well-designed mesh plus a **p-extension sequence (p = 1, 2, 3, …)**
  yields a built-in convergence study from **one mesh topology** — the basis of StressCheck-style
  Simulation Governance (cross-ref vv-uq.md). Verify by watching the QoI (and an a-posteriori error
  estimate) flatten as p rises. [S34][S35]
- **hp-refinement** — combine **small elements near singularities** with **high order in smooth
  regions**. **Babuška–Guo / Szabó–Babuška: properly graded hp gives *exponential* convergence**
  (error ~ e^(−γ·N^β) in DOF N, β > 0) even for problems with **corner/edge singularities** — versus
  merely algebraic for h-refinement alone. This is why graded-hp meshes resolve notch/fillet fields so
  efficiently. [S35][S36]
- **Practical guidance.** For a **smooth** stress field, a p-study on a fixed mesh is often a faster,
  less error-prone convergence demonstration than three remeshes (no re-meshing artefacts, same
  topology throughout). For **singularity-dominated** fields, **geometric h-grading toward the corner
  + high p elsewhere** is optimal — and pairs naturally with goal-oriented (DWR) marking. Report which
  path you used (h, p, or hp) and the converged QoI either way. [S34][S35][S36]

---

## 5D. Element technology consolidated (locking, B-bar, EAS, reduced integration, shells)

§2 covers the element-technology pathologies and their cures in the meshing/convergence context.
This subsection collects the same content as a **single reference point** that the nonlinear,
near-incompressible, composite, and fracture references can lean on — when a downstream reference
says "use a locking-free element," this is the menu it means. Nothing here is new physics; it is the
one-stop index. [S1][S2][S3]

### 5D.1 The locking modes (one line each, with the cure)
- **Shear locking** (too stiff in bending) — fully-integrated **first-order** elements develop
  parasitic shear; cure with **2nd-order**, **reduced integration**, or **incompatible modes / EAS**;
  see §2.1. [S2][S3]
- **Volumetric locking** (too stiff, near-incompressible: ν→0.5, full plasticity, rubber) — the
  incompressibility constraint over-constrains a fully-integrated element; cure with **B-bar /
  selective reduced integration**, **mixed u-P / hybrid**, or **EAS**; see §2.2. [S1][S2]
- **Membrane locking** (curved shells/beams in bending) — spurious membrane strain in low-order
  curved elements; cure with **reduced/selective integration** or **assumed-strain (ANS)**
  shells. [S1]
- **Hourglassing** (the opposite failure — *too flexible*) — first-order **reduced-integration**
  elements admit zero-energy modes; cure with **hourglass control/stabilization** (artificial
  stiffness on the hourglass modes only — too much re-introduces stiffening) or **2nd-order**
  elements; monitor hourglass/artificial energy < ~5–10% of internal energy; see §2.3. [S1][S3]

### 5D.2 The remedies (what each fixes)
| Technique | Fixes shear lock | Fixes volumetric lock | Adds DOF/cost | Note |
|---|---|---|---|---|
| **2nd-order (quadratic)** | yes | partly | more DOF | the simplest robust default for stress [S6] |
| **Reduced integration** | yes | yes | cheaper | needs **hourglass control** on linear elements [S2] |
| **Selective reduced integration (SRI)** | — | yes | ~same | reduced on volumetric part only [S1][S2] |
| **B-bar (B̄)** | no | yes | ~same | element-averaged volumetric strain; finite-strain capable [S1][S2] |
| **Incompatible modes** | yes | — | small | internal strain modes; small-strain; "spectacular" on linear bending [S1] |
| **Enhanced Assumed Strain (EAS) / Hu–Washizu** | yes | yes | moderate | independent enhanced-strain field; Simo–Rifai finite strain [S2] |
| **Mixed u-P / hybrid** | — | yes (true incompressible) | higher (pressure DOF) | mandatory for fully-incompressible hyperelastics; pressure DOF can't be condensed out [S1] |

**Decision shortcut:** bending-dominated → 2nd-order or incompatible-modes/EAS; near-incompressible
(rubber, full plasticity) → mixed u-P (true incompressible) or B-bar/SRI (mild); large/explicit
models → reduced integration + hourglass control. Cross-ref §2.4 for the full integration-scheme
table. [S1][S2][S3]

### 5D.3 Shell modelling choices (for nonlinear/composite/sandwich work)
- **Conventional (layered) shell** — degenerate-continuum or stress-resultant; thickness is a
  property; stress assumed **linear through thickness** (membrane + bending). Cheapest; **blind to
  true through-thickness / interlaminar stress** (the composite caveat — a layered shell cannot see
  delamination drivers; see §1.3 and the composites reference). Thin (Kirchhoff) vs thick
  (Mindlin–Reissner, includes transverse shear). [S9]
- **Continuum (solid) shell** — a solid-element topology (nodes on top & bottom faces, displacement
  DOF only) that behaves like a shell but **stacks through the thickness** and carries a 3D
  constitutive law — use when you need several layers through the wall, two-sided contact, or
  through-thickness stress while keeping shell-like aspect ratios. [S9][S12]
- **Solid-shell** — a single solid element with shell-quality bending (assumed natural strain +
  EAS to beat shear/thickness locking); bridges shell efficiency and solid generality for
  thin-walled nonlinear problems. [S2][S9]
- **Full solid** — when through-thickness stress is the QoI (contact bearing, weld-toe 3D field) and
  you can afford it; with **2nd-order** solids a *single* element through the wall matches a shell
  (§1.3 caveat). [S12]

Rule: **layered shell** for global stiffness/stress of thin parts; **continuum-shell / solid-shell**
when interlaminar/through-thickness behaviour or two-sided contact matters but shell economy is
wanted; **full solid** when the through-thickness field itself is the deliverable. [S9][S12]

---

## 6. Converging the QoI vs singular peaks (the trap that breaks naïve studies)

### 6.1 Singularity vs concentration — the decisive distinction
- **Stress concentration:** real, finite stress raiser (hole, fillet, section change,
  contact). **Refine → stress converges to a finite value** (e.g. Kirsch plate-with-hole →
  the analytical SCF). These *should* be converged and reported. [S19]
- **Stress singularity:** stress → ∞ as h → 0 — **it never converges; each refinement gives a
  higher peak.** Caused by: sharp **re-entrant corners** (external angle < 180°), **point
  loads / point restraints** (σ = P/A, A→0), and **idealized BC corners** (a node forced to
  be both free-edge and fully fixed). [S19][S20][S21]
- **Diagnostic:** if peak stress keeps rising with each refinement instead of leveling off,
  you have a singularity, not a result. [S19][S20]

### 6.2 What to do
1. **Ignore it (most common, via Saint-Venant).** **St. Venant's principle:** local
   disturbances stay local — the field is correct **roughly one feature-size away** from the
   singularity. **Read stress 1–2 elements away**, not at the singular node. Displacements,
   reactions, and stress *integrals* are also correct despite the singularity, so for
   stiffness/load-transfer QoIs you can ignore it entirely. **Defeaturing** sharp corners is
   the deliberate use of this. [S19][S21]
2. **Model the real geometry.** If the stress *there* is the QoI, **add the real fillet
   radius** — this turns the singularity into a (convergeable) concentration, then run a mesh
   convergence study on the fillet. Never assess fatigue/strength at a modeled sharp corner.
   [S19][S20]
3. **Fix idealized loads/BCs.** Replace point loads/restraints with distributed
   pressure/coupling/RBE over a realistic patch; the resultant is what St. Venant guarantees.
   [S19][S21]
4. **Stress linearization (pressure-vessel / weld practice).** Extract membrane and bending
   components along a **Stress Classification Line (SCL)** and discard the non-convergent peak
   — see §7.

### 6.3 The cantilever lesson
Even a textbook 2D cantilever has singularities at the clamped corners (free-edge σ=0 meets
fixed restraint). A solid-element model's corner stress will *not* converge, yet the stress a
short distance into the beam converges to beam theory (σ = My/I). This is why "compare against
the analytical / beam-element benchmark away from the support" is the right validation, and
why naïvely reporting peak nodal stress at a constraint is a classic blunder. [S19]

---

## 7. Stress linearization (turning a non-convergent field into a code-compliant number)

Used heavily in ASME VIII-2 / Section III design-by-analysis, and broadly for separating
classifiable stress from peaks. [S14][S24][S25]

- **Stress Classification Line (SCL):** a straight line **through the thickness, normal to
  both surfaces**, at the location of interest (e.g. nozzle-shell junction). Stresses along
  it are decomposed into:
  - **Membrane (P_m):** the **constant average** stress across the section. [S24]
  - **Bending (P_b):** the **linearly varying** part (difference inside↔outside surface). [S24]
  - **Membrane + bending (P_m + P_b):** the linearized total.
  - **Peak (F):** the remaining nonlinear part — *this is where singular/notch peaks live and
    is intentionally excluded from membrane/bending limits.* [S14][S24]
- **Why it matters:** **comparing raw von Mises directly to the allowable S is a top reason
  FEA submissions are rejected** — the allowable applies to the *categorized* primary
  membrane stress P_m, not to total nodal stress. Categorize before you compare. [S14]
- **SCL meshing requirements (practitioner numbers):**
  - Result quality depends strongly on **number of nodes on the SCL.** Without interpolation,
    **≥ ~9 nodes** are needed to keep linearization error < 5%; **with cubic-spline
    interpolation, ~4–5 nodes** suffice. Too few nodes **over-reports** membrane and
    membrane+bending. So **put enough through-thickness elements on the SCL** (favor several
    quadratic elements through the wall, or a structured hex/sweep there). [S25]
  - Place the SCL **away from gross structural discontinuities** where possible (or accept
    that at discontinuities the classification is P_L local-membrane, with its own higher
    allowable). [S24][S25]

---

## 8. Top mistakes (each with the fix and citation)

1. **Reporting equilibrium/solver convergence as if it were mesh convergence.** Fix: always
   run ≥3 meshes + GCI / QoI-vs-mesh plot. [S15][S1*]
2. **Reading peak stress at a sharp corner / point load / restraint and refining it.** It
   never converges. Fix: model the fillet, distribute the load, or read 1–2 elements away
   (St. Venant). [S19][S20][S21]
3. **Linear tets (TET4) for stress.** Over-stiff, inaccurate. Fix: TET10 or hex. [S5][S7]
4. **Fully-integrated linear elements in bending → shear locking (~34% too stiff).** Fix:
   2nd-order, reduced integration, or incompatible modes; ≥4 elements through thickness. [S3]
5. **Reduced-integration linear elements without hourglass control → hourglassing (~32% too
   soft).** Fix: enable hourglass control, monitor hourglass/artificial energy < ~5–10%,
   refine, or go 2nd-order. [S1][S3]
6. **Fully-integrated elements on near-incompressible material → volumetric locking.** Fix:
   B-bar / selective reduced integration / mixed u-p / EAS. [S1][S2]
7. **Shell mesh on a top/bottom face without setting the offset.** Wrong thickness placement
   and eccentricity. Fix: set mid-surface offset explicitly and verify rendered thickness. [S9]
8. **Assuming shell is always conservative / always fine for thin walls.** Shells can
   *under*-predict local stress, and 2nd-order solids need only 1 element through thickness.
   Fix: choose by what physics you need through the thickness; resolve curvature. [S12][S9]
9. **Wrong 2D idealization (plane stress vs plane strain).** Large stiffness error. Fix: match
   plane stress (thin, free out-of-plane) vs plane strain (long, constrained) vs
   axisymmetric. [S1]
10. **Judging mesh by *average* quality.** The worst elements in the QoI region drive error
    and divergence. Fix: isolate worst elements by metric (Jacobian < 0, skewness/AR maxima).
    [S4][S11]
11. **Defeaturing the feature that matters / not defeaturing the ones that don't.** Fix:
    defeature only far-field nuisances; keep (and refine) QoI-driving features. [S15]
12. **Comparing raw von Mises to allowable in code work.** Fix: linearize on an SCL with
    enough through-thickness nodes (≥9 raw, ~5 with interpolation) and categorize. [S14][S25]
13. **Abrupt size jumps / high growth rate.** Creates artificial gradients & bad elements.
    Fix: growth rate ≤ ~1.2–1.5, smooth transitions, local refinement not global. [S15]
14. **Trusting "adaptive mesh refinement" as self-certifying.** A ZZ/SPR-driven adaptive run
    *targets* error, it does not *certify* the QoI. Fix: confirm estimator effectivity (θ ≈ 1),
    report a final GCI band or converged p-/hp-sequence on the QoI. [S26][S30] (§5A/§5C)
15. **Refining a singular region because the error estimator flags it.** A recovery estimator
    diverges at a singularity — it correctly marks high error, but more h won't converge it. Fix:
    defeature / add the real fillet / linearize (§6, §7); estimator-flagged ≠ refine-here. [S26][S29]
16. **Energy-norm-refining when one number is the deliverable.** Wastes DOF away from the QoI.
    Fix: use goal-oriented (DWR) refinement to target the output error directly. [S31][S32] (§5B)

---

## 9. Quick-reference defaults (sane starting points, then verify by convergence)

- **Element:** 2nd-order solids (TET10/HEX20) for stress; hex by sweep/MultiZone where
  sweepable, TET10 elsewhere; shells for span/thickness ≳ 20 with explicit offset; beams for
  slender members. [S5][S7][S9]
- **Integration:** quadratic full integration as default; reduced integration + hourglass
  control for large/explicit; B-bar/mixed for incompressible. [S1][S2][S3]
- **Quality gates (FEA):** Jacobian > 0 (and > 0.6 desirable), skewness < 0.75, orthogonal
  quality > 0.2, aspect ratio < ~20 in stress regions (tet < 16), growth rate ≤ 1.5. [S4][S10][S11]
- **Through-thickness:** ≥ 4 linear or 1–2 quadratic elements; ≥ ~12 elements around a hole/fillet
  circumference; ≥ 5 quadratic elements through wall on any SCL. [S3][S12][S25]
- **Convergence:** ≥ 3 grids, refinement ratio r ≥ 1.3, report GCI (F_s=1.25 for 3 grids) and
  the asymptotic-range check ≈ 1; QoI change < 2–5% between two finest meshes. [S16][S17][S18]
- **Error estimation:** for a one-solve error band, use a recovery (ZZ/SPR) or residual a-posteriori
  estimator (effectivity θ → 1) to *target* refinement; for a single-number QoI use goal-oriented
  (DWR) marking; recovery error and GCI must agree in the asymptotic range. [S26][S30][S31] (§5A/§5B)
- **Refinement path:** h (size), p (order — a one-mesh p-extension study), or hp (graded near
  singularities → exponential convergence). Smooth field → prefer p; singular field → hp. [S34][S35][S36] (§5C)
- **Singularities:** identify (peak keeps rising), then ignore-via-St-Venant, model-the-fillet,
  or linearize. Never certify a modeled sharp corner. [S19][S20][S21]

---

## SOURCES

- **[S1] A.F. Bower, *Applied Mechanics of Solids*, Ch. 8.6 "Advanced Element Formulations"** —
  http://solidmechanics.org/Text/Chapter8_6/Chapter8_6.php — High reliability: graduate
  textbook (Brown Univ.), with derivations + reference code for selective reduced integration,
  hourglass control (Flanagan–Belytschko), B-bar, incompatible modes, hybrid u-p.
- **[S1*] ASME V&V 20-2009 / V&V 10** (Standard for Verification & Validation in Computational
  Fluid Dynamics and Heat Transfer; and Computational Solid Mechanics) — Authoritative
  consensus standard defining the GCI uncertainty method (referenced via [S16][S17]).
- **[S2] COMSOL Documentation, "Using Reduced Integration"** —
  https://doc.comsol.com/6.0/doc/com.comsol.help.sme/sme_ug_modeling.05.161.html — High
  reliability: solver vendor theory docs on reduced integration, hourglassing, B-bar, EAS.
- **[S3] Fidelis Engineering, "Hourglassing and Shear Locking — What Are They..."** —
  https://www.fidelisfea.com/post/hourglassing-and-shear-locking-what-are-they-and-why-does-it-matter
  — Reliable practitioner blog with quantified Abaqus C3D8/C3D8R bending study (~34.5% / ~32%
  errors; 4–5 elements through thickness rule).
- **[S4] Mechead, "Ansys Mesh Metrics Explained"** —
  https://www.mechead.com/mesh-quality-checking-ansys-workbench/ — Reliable practitioner
  summary of Ansys metrics (Jacobian, skewness, aspect ratio, orthogonal quality, warping,
  parallel deviation, max corner angle) and thresholds.
- **[S5] Mindli, "FEA Element Types and Selection"** —
  https://mind.li/explore/31592-fea-element-types-and-selection — Practitioner reference for
  linear-vs-quadratic and tet/hex/shell/beam selection heuristics.
- **[S6] FEA Tips, "Linear vs Quadratic FE Elements"** —
  https://featips.com/2019/03/29/linear-vs-quadratic-fe-elements/ — Reliable practitioner
  explanation of why quadratic elements capture bending/gradients (accessed via search
  summary; direct fetch was 403).
- **[S7] Schneider et al., "A Large-Scale Comparison of Tetrahedral and Hexahedral Elements
  for Solving Elliptic PDEs with FEM," ACM TOG 2022** —
  https://dl.acm.org/doi/10.1145/3508372 (preprint arXiv:1903.09332) — High reliability:
  peer-reviewed large-scale study showing TET10 ≥ hex for many problems; Coreform hex-vs-tet
  whitepaper (https://coreform.com/papers/hex_tet_comparison.pdf) corroborates.
- **[S8] Abaqus Analysis User's Manual, continuum/wedge elements** —
  https://classes.engineering.wustl.edu/2009/spring/mase5513/abaqus/docs/v6.6/books/usb/pt06ch22s01alm01.html
  — High reliability: solver theory manual on element families incl. wedge/prism use.
- **[S9] Factreehub, "Shell vs. Solid Elements ... Pressure Vessel FEA"** —
  https://factreehub.com/blog/shell-vs-solid-elements-making-the-right-choice-for-pressure-vessel-fea/
  — Practitioner guidance on shell mid-surface, thin-wall thresholds, through-thickness linear
  stress assumption, thin/thick shell, offsets.
- **[S10] FEA Tips, "Ansys Mesh Metrics Explained"** —
  https://featips.com/2022/11/21/ansys-mesh-metrics-explained/ — Practitioner detail on each
  Ansys metric incl. warping, parallel deviation, max corner angle, Jacobian on quadratics
  (accessed via search summary; direct fetch was 403).
- **[S11] SimScale Docs, "Mesh Quality"** —
  https://www.simscale.com/docs/simulation-setup/meshing/mesh-quality/ — Reliable vendor docs
  with hard divergence thresholds (FEA: aspectRatio 30, tet AR 16, skewness 10; CFD:
  non-orthogonality 88) and worst-element isolation workflow.
- **[S12] Engineering.com (Dr. J. Muelaner), "Shell or Solid Elements for Thin Walled Parts?"**
  — https://www.engineering.com/shell-or-solid-elements-for-thin-walled-parts/ — Reliable
  practitioner article with convergence studies: 2nd-order solids need only 1 element through
  thickness; curvature resolution (1/10–1/20 of radius) dominates; shells can underestimate
  stress.
- **[S13] Ansys Meshing User's Guide / Help (Automatic, Sweep, MultiZone, Patch
  Conforming/Independent, shared topology)** —
  https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/wb_msh/ds_multizone_method_option.html
  and meshing methods overview (https://featips.com/2022/12/27/ansys-mesh-methods-explained/)
  — High reliability: solver vendor documentation of meshing methods and interface protection
  rules.
- **[S14] ideaMetrics / e2g "Fundamentals of Design by Analysis"; FEA Tips "Stress
  Linearization Explained"** —
  https://ideametricsglobalengineering.com/from-simulation-to-code-compliance-using-fea-for-asme-design-validation/
  ; https://e2g.com/industry-insights-ar/fundamentals-of-design-by-analysis/ — Reliable: ASME
  VIII-2 stress categorization, why raw von Mises ≠ allowable.
- **[S15] ideaMetrics, "Convergence in FEA Analysis"** —
  https://ideametricsglobalengineering.com/convergence-in-fea-analysis-validation-guide/ —
  Practitioner guide on convergence study procedure, defeaturing, local refinement.
- **[S16] Roache, P.J. (1994), "Perspective: A Method for Uniform Reporting of Grid Refinement
  Studies," J. Fluids Eng. 116(3):405; (1997) Annu. Rev. Fluid Mech.** —
  https://asmedigitalcollection.asme.org/fluidsengineering/article-abstract/116/3/405/411554/
  (also https://www3.nd.edu/~coast/jjwteach/www/www/60130/CourseLectureNotes/Roache_1994.pdf)
  — Highest reliability: the original peer-reviewed GCI definition (F_s=1.25/3.0, r≥1.3).
- **[S17] curiosityFluids, "Establishing Grid Convergence"** —
  https://curiosityfluids.com/2016/09/09/establishing-grid-convergence/ — Reliable worked
  example (OpenFOAM cavity) of observed order p = ln((f3−f2)/(f2−f1))/ln(r), Richardson
  extrapolation, GCI, and asymptotic-range check; cites NASA & Roache.
- **[S18] EngineeringDownloads, "Mastering Grid Convergence Index (GCI)"; Volupe GCI
  Calculator** — https://engineeringdownloads.com/grid-convergence-index-gci-simulations/ ;
  https://volupe.com/support/grid-convergence-index-calculator/ — Practitioner GCI references
  (asymptotic-range ratio ≈1, reporting). (Volupe direct fetch 403; via search summary.)
- **[S19] Acin.Net, "Stress singularities, stress concentrations and mesh convergence"** —
  http://www.acin.net/2015/06/02/stress-singularities-stress-concentrations-and-mesh-convergence/
  — Reliable FEA-specialist article: singularity vs concentration, St. Venant, cantilever &
  plate-with-hole convergence examples, defeaturing.
- **[S20] Fidelis Engineering, "Stress Singularities At Reentrant Corners"** —
  https://www.fidelisfea.com/post/stress-singularities-at-reentrant-corners-a-fundamental-problem-in-fea
  — Reliable: re-entrant-corner singularity, non-convergence diagnostic, fillet remedy.
- **[S21] Enterfea, "Stress singularity — an honest discussion"** —
  https://enterfea.com/stress-singularity-an-honest-discussion/ — Reliable practitioner
  (Ł. Skotny, PhD) discussion of singularity sources and how to handle them via St. Venant.
- **[S22] Mechead, "Is Your Mesh Good Enough?"** —
  https://www.mechead.com/mesh-good-enough/ — Practitioner mesh-independence study guidance
  (refine until QoI stops changing).
- **[S24] GraspEngineering, "What is Stress Linearization?"** —
  https://www.graspengineering.com/what-is-stress-linearization/ — Reliable: SCL/SCP
  definitions, membrane/bending/peak decomposition per ASME.
- **[S25] Pressure Vessel Engineering, "The Nuts and Bolts of Stress Linearization"** —
  https://www.pveng.com/the-nuts-and-bolts-of-stress-linearization-post/ — Reliable: SCL
  node-count requirements (≥9 raw, ~4–5 with cubic-spline interpolation), over-reporting with
  too few nodes, integration method.
- **[S26] Zienkiewicz, O.C. & Zhu, J.Z. (1992), "The superconvergent patch recovery and a
  posteriori error estimates. Part 1: The recovery technique," Int. J. Numer. Methods Eng.
  33(7):1331–1364** — https://onlinelibrary.wiley.com/doi/10.1002/nme.1620330702 — Highest
  reliability: the original peer-reviewed SPR recovery technique (2000+ citations).
- **[S27] Zienkiewicz, O.C. & Zhu, J.Z. (1992), "…Part 2: Error estimates and adaptivity," Int.
  J. Numer. Methods Eng. 33(7):1365–1382** —
  https://onlinelibrary.wiley.com/doi/10.1002/nme.1620330703 — Highest reliability: ZZ error
  estimate from SPR, effectivity index, and adaptivity (effectivity → 1 under superconvergent
  recovery).
- **[S28] Zhang, Z. & Naga, A. / SPR a-posteriori analysis, Comput. Methods Appl. Mech. Engrg.** —
  https://www.sciencedirect.com/science/article/abs/pii/0045782595007805 ;
  https://www.sciencedirect.com/science/article/abs/pii/S0045782598000103 — High reliability:
  analysis proving asymptotic exactness (effectivity → 1) of the SPR-based estimator.
- **[S29] Ainsworth, M. & Oden, J.T., *A Posteriori Error Estimation in Finite Element Analysis*
  (Wiley, 2000)** — standard monograph; recovery- and residual-based estimators, reliability /
  efficiency bounds, behaviour at singularities. (Authoritative textbook reference for §5A.)
- **[S30] Verfürth, R., *A Posteriori Error Estimation Techniques for Finite Element Methods*
  (Oxford, 2013); residual-based estimators & Dörfler marking** — High reliability: residual
  estimators with provable upper (reliability) / lower (efficiency) bounds and adaptive marking
  strategies used in practice.
- **[S31] Becker, R. & Rannacher, R. (2001), "An optimal control approach to a posteriori error
  estimation in finite element methods," Acta Numerica 10:1–102** —
  https://doi.org/10.1017/S0962492901000010 — Highest reliability: the canonical
  dual-weighted-residual (DWR) goal-oriented survey (1000+ citations).
- **[S32] Oden, J.T. & Prudhomme, S. (2001), "Goal-oriented error estimation and adaptivity for
  the finite element method," Computers & Mathematics with Applications 41:735–756** —
  https://doi.org/10.1016/S0898-1221(00)00317-5 — High reliability: upper/lower bounds on the
  output (functional) error.
- **[S33] Rabizadeh, E. et al. (2020), "Pointwise dual-weighted-residual goal-oriented a-posteriori
  error estimation and adaptive refinement in 2D/3D thermo-mechanical problems," Comput. Methods
  Appl. Mech. Engrg.** — Reliable recent application: DWR goal-oriented adaptivity for pointwise
  thermo-mechanical QoIs.
- **[S34] Szabó, B. & Babuška, I., *Finite Element Analysis* / *Introduction to Finite Element
  Analysis: Formulation, Verification and Validation* (Wiley)** — and Szabó & Babuška, *The
  p-Version of the Finite Element Method* —
  https://onlinelibrary.wiley.com/doi/10.1002/0470091355.ecm003g — Highest reliability: the
  p-version FEM and Simulation-Governance framing (h vs p, p-extension as a one-mesh convergence
  study).
- **[S35] Babuška, I. & Guo, B.Q. (1986), "The h-p version of the finite element method," Comput.
  Mech. 1:21–41 & 203–220** — https://link.springer.com/article/10.1007/BF00298636 — Highest
  reliability: hp-FEM exponential convergence for piecewise-analytic solutions with singularities.
- **[S36] hp-FEM overview (exponential convergence by combining h+p refinement)** —
  https://en.wikipedia.org/wiki/Hp-FEM — Orientation only (secondary summary of the hp
  exponential-rate result); the authoritative primaries are Szabó & Babuška [S34] and
  Babuška & Guo [S35], which it merely corroborates.

*Cross-verification note: GCI methodology corroborated across Roache [S16], curiosityFluids
[S17], EngineeringDownloads/Volupe [S18], and ASME V&V 20 [S1*]. Locking/hourglassing
corroborated across Bower [S1], COMSOL [S2], Fidelis [S3], and the JLab "Shear Locking and
Hourglassing in MSC Nastran, ABAQUS, and ANSYS" comparison
(https://www.jlab.org/sites/default/files/physics/ansys/shearLocking.pdf). Mesh-quality
thresholds corroborated across Ansys-derived [S4][S10], SimScale [S11]. Singularity/St-Venant
corroborated across Acin [S19], Fidelis [S20], Enterfea [S21]. A-posteriori recovery/ZZ/SPR
corroborated across the original Zienkiewicz–Zhu papers [S26][S27], the asymptotic-exactness
analyses [S28], and the standard monographs [S29][S30]; DWR goal-oriented control across
Becker–Rannacher [S31] and Oden–Prudhomme [S32]; hp exponential convergence across Szabó–Babuška
[S34] and Babuška–Guo [S35].*

---

## Related references
- **`vv-uq.md`** — numerical uncertainty, MMS code verification, ASME V&V 10/20/40, Simulation
  Governance (Szabó–Babuška), and the convergence/credibility reporting contract. The a-posteriori
  estimators (§5A), goal-oriented DWR (§5B), and p-/hp-refinement (§5C) here are the single-mesh and
  order-based complements to that file's multi-mesh GCI.
- **Nonlinear / plasticity / forming references** — lean on the element-technology menu in **§5D**
  (locking modes, B-bar/SRI, EAS, reduced integration + hourglass control, mixed u-P) when choosing
  a locking-free element for near-incompressible or bending-dominated work.
- **Composites / fracture references** — lean on **§5D.3** (layered vs continuum-shell vs solid-shell
  vs full solid) for through-thickness/interlaminar fidelity, and on §6/§7 for the
  singularity-and-linearization treatment of crack-tip / notch fields.
