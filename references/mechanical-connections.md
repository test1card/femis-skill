# Mechanical Connections & Joints in FEM/CAE — Engineering Reference

A practitioner's decision reference for modeling joints, contacts, constraints, bolts, welds, springs, and remote points in **Ansys MAPDL**, **Ansys Mechanical (Workbench)**, **Simcenter / MSC Nastran**, and **Abaqus**. Quantitative thresholds, "use X when Y" guidance, per-platform commands, and the numbers + citations behind them throughout.

Each substantive claim is cross-checked against ≥2 authoritative sources (NAFEMS, vendor theory manuals, VDI 2230, weld-fatigue codes IIW/Eurocode 3, Shigley, recognized practitioners). Citations are inline as [n]; the source list with reliability ratings is at the end.

---

## Contents

- [0. The one-paragraph mental model](#0-the-one-paragraph-mental-model)
- [0a. Master Decision Table — Pick a Connection](#0a-master-decision-table-pick-a-connection)
- [1. CONTACT TYPES — behavior, linearity, when](#1-contact-types-behavior-linearity-when)
- [2. CONTACT FORMULATIONS & TUNING](#2-contact-formulations-tuning-penetration-vs-conditioning-vs-chatter)
- [2a. DISCRETIZATION / ENFORCEMENT — NTS vs mortar / dual-Lagrange / Nitsche](#2a-discretization-enforcement-nts-vs-mortar-dual-lagrange-nitsche-and-the-contact-patch-test)
- [2b. HERTZIAN CONTACT — the analytical cross-check](#2b-hertzian-contact-the-analytical-cross-check-for-contact-pressure-fea)
- [3. CONSTRAINT / RIGID ELEMENTS — RBE2 vs RBE3](#3-constraint-rigid-elements-rbe2-vs-rbe3-the-most-misused-pair)
- [4. BOLTED CONNECTIONS — preload, torque, VDI 2230, fidelity ladder](#4-bolted-connections-preload-torque-vdi-2230-fidelity-ladder)
- [5. WELDS & FASTENER ELEMENTS](#5-welds-fastener-elements)
- [6. SPRINGS / BUSHINGS / CONNECTORS](#6-springs-bushings-connectors)
- [7. KINEMATIC JOINTS (mechanism / flexible multibody)](#7-kinematic-joints-mechanism-flexible-multibody)
- [8. REMOTE POINTS / REMOTE LOADS / point-to-surface coupling](#8-remote-points-remote-loads-point-to-surface-coupling)
- [9. THERMAL CONTACT CONDUCTANCE (TCC / h_c) — note](#9-thermal-contact-conductance-tcc-h_c-note)
- [10. Top mistakes — quick gotcha checklist](#10-top-mistakes-quick-gotcha-checklist)
- [SOURCES](#sources)

## 0. The one-paragraph mental model

A connection in FEA is a statement about **relative motion** and **load path**, not about geometry. Every choice trades **fidelity vs cost vs robustness**. The two errors that dominate real review findings: (1) **over-stiffening** — using a rigid element (RBE2/CERIG, bonded-everywhere, too-high penalty) where the structure should deform, which hides compliance, shifts modes up, and creates fake stress hot-spots; (2) **over-constraint / ill-conditioning** — redundant rigid links, RBE3 driving rotation off coplanar nodes, double-dependent DOF, or Lagrange formulations that chatter. Choose the *least stiff* connection that still carries the real load path, and refine to nonlinear contact only at the joint that drives the answer (submodel). [NAFEMS PMJC, R0081; Fidelis; Ansys CTG]

---

## 0a. Master Decision Table — Pick a Connection

| Goal / situation | Use this | Adds stiffness? | Cost | Platform commands |
|---|---|---|---|---|
| Permanently joined parts, no slip, want fast linear solve | **Bonded contact** | Yes (couples normal+tangent) | Linear | Bonded contact / `CONTA17x KEYOPT(12)=5` / Nastran glue (`BGSET`) / Abaqus `*TIE` |
| Parts that may separate but no friction | **Frictionless contact** | Nonlinear | Medium | Frictionless / `KEYOPT(12)=0`, MU=0 |
| Realistic sliding interface | **Frictional contact** | Nonlinear | High | Frictional, MU=0.1–0.6 / Nastran `BCTABLE` FRIC / Abaqus `*FRICTION` |
| Rigid link, master drives slaves rigidly | **RBE2 / CERIG / MPC184-rigid** | Yes (over-stiffens) | Cheap | `CERIG`, `MPC184` / `RBE2` / Abaqus `*KINEMATIC COUPLING` |
| Spread a load/mass to a patch without stiffening | **RBE3 / deformable remote point** | No | Cheap | `RBE3` cmd / `RBE3` / Abaqus `*DISTRIBUTING COUPLING` |
| Bolt, quick load path only | **Beam + RBE3 spider** | Beam stiffness only | Cheap | `BEAM188`+`RBE3` / `CBAR/CBEAM`+`RBE3` |
| Bolt, need preload & local stress | **Solid bolt + pretension** | Full | Expensive | `PRETS179`+`SLOAD` / `BOLT`+`BOLTFOR` / Abaqus `*PRE-TENSION SECTION` |
| Spot weld / rivet between shells | **CWELD / CFAST** | Beam-like | Cheap | (beam+contact) / `CWELD`,`CFAST` / Abaqus `*FASTENER` |
| Compliant joint (bushing, mount, bearing) | **CBUSH / COMBIN14 / bushing** | 6-DOF spring | Cheap | `COMBIN14`,`MATRIX27` / `CBUSH` |
| Mechanism DOF (hinge, slider, ball) | **Kinematic joint** | Constraint only | Cheap | `MPC184` joint / Nastran joints / Abaqus connectors |
| Apply force/moment/disp at a point off the part | **Remote point / remote load** | Depends on behavior | Cheap | Remote Point / `RBE3`/`RBE2` |

---

## 1. CONTACT TYPES — behavior, linearity, when

Five canonical behaviors. The decisive split is **linear (one pass) vs nonlinear (Newton–Raphson with status changes)** — the nonlinear ones cost 10–100×. [Ansys CTG; SimuTech]

| Type | Normal behavior | Tangential behavior | Linear? | Use when | Avoid when |
|---|---|---|---|---|---|
| **Bonded (glued)** | No separation, no penetration | No sliding | **Linear** | Welds, glue/adhesives, press-fit you treat as fixed, mesh-independent part joins, modal/global/quick studies | You need to capture gapping/slip; bonding across a wide gap (transmits fictitious moments) |
| **No Separation** | No separation, no penetration | **Frictionless sliding allowed** | **Linear** | Press-fit/pinned where parts stay touching but can slide; bearing-like | Real lift-off / separation occurs |
| **Frictionless** | Can separate, cannot penetrate | Free sliding (MU=0) | Nonlinear | Parts that lift off; conservative lower-bound load path | Friction governs the result |
| **Rough** | Can separate | **No sliding (MU=∞)** | Nonlinear | Perfectly rough faying surface, no-slip but can gap/lift | You need finite friction |
| **Frictional** | Can separate, cannot penetrate | Coulomb slip at τ = MU·p | Nonlinear | Realistic bolted/clamped joints, slip/fretting studies | When linear bonded is sufficient (wasted cost) |

**What bonded does to DOF:** it ties the contact-side DOF to the target through the contact stiffness (penalty) or MPC equations (MPC bonded), effectively removing relative motion. With MPC-based bonded the DOF are *eliminated* (true constraint equations, zero penetration); with penalty bonded a stiff spring resists relative motion (small residual penetration).

**Friction coefficients (engineering values, dry unless noted):** steel–steel ~0.6 (dry), ~0.1 (lubricated); steel–aluminum ~0.45; clamped bolted faying surfaces ~0.3–0.5; PTFE ~0.04. When unsure for a bolted joint, **MU ≈ 0.2–0.3**. [Shigley §8; VDI 2230; Wikipedia bolted joint (orientation)]

**Cost rule of thumb:** Bonded / No-Separation = one linear pass. Frictionless/Rough/Frictional = Newton–Raphson iterations + status changes (can be 10–100× cost). Start bonded for global behavior, refine to frictional only at the joint of interest (submodel).

**Practitioner workflow:** start everything **bonded** to get the global load path and modes, confirm the model is sound, then switch the *one* governing interface to frictional and submodel it. NAFEMS R0081 (the standard contact benchmark suite) exists precisely because contact, gapping and sliding are the hardest things to get numerically right — validate your settings against a known benchmark before trusting a production result. [NAFEMS R0081]

**Platform commands**
- **MAPDL:** surface-to-surface pair `TARGE170` + `CONTA174` (3D) / `CONTA172` (2D). Behavior via `KEYOPT(12)`: `0`=standard (frictionless/frictional via MU), `1`=rough, `2`=no separation (sliding), `3`=bonded, `4`=no separation (always), `5`=bonded (always), `6`=bonded initial contact. Friction set by `MP,MU,...`.
- **Mechanical:** Connections → Contact → *Type* dropdown (Bonded / No Separation / Frictionless / Rough / Frictional). Frictional exposes the Friction Coefficient field.
- **Nastran:** Glue/bonded = `BGSET`+`BGPARM` (or `BCTABLE` with glue), SOL101 (linear glue). Touching/sliding contact = `BCTABLE`/`BCTABL1` + `BCPARA`/`BCTPARM`; friction coefficient `FRIC` field; nonlinear in SOL400/401/402.
- **Abaqus:** `*CONTACT` / `*SURFACE INTERACTION` with `*FRICTION`; "rough" via `ROUGH`; tied/bonded via `*TIE`.

---

## 2. CONTACT FORMULATIONS & TUNING — penetration vs conditioning vs chatter

How the no-penetration condition is enforced. Every formulation trades **penetration** against **matrix conditioning** against **convergence (chatter)**. [Ansys CTG; FEA Tips; Mechead]

| Formulation | Enforcement | Penetration | Extra DOF? | Conditioning | Use when |
|---|---|---|---|---|---|
| **Pure Penalty** | Spring force ∝ penetration | Some (controlled by FKN) | No | Good | Robust default for bonded/general; bulk-dominated |
| **Augmented Lagrange** (Ansys default) | Penalty + iterative λ augmentation to meet FTOLN | Small, controlled | No | Good | General nonlinear contact; **recommended default** (penetration control of Lagrange, robustness of penalty) |
| **Normal Lagrange** | Pressure as Lagrange-multiplier DOF | ≈ zero | Yes (pressure DOF) | Worse; needs direct solver; can over-constrain/chatter | When penetration must be near-zero; not over-constrained |
| **MPC bonded** | Constraint equations bind DOF | Zero | No (DOF eliminated) | Excellent | Bonded/no-separation only; large-deflection bonded; best for ties; **cannot detect new contact** |
| **Beam (bonded)** | Massless beams between faces | Zero | No | Excellent | Bonded across a gap; spot-weld-like; transmits moments cleanly |

### Key parameters (penalty-based only — FKN/FTOLN are ignored by Normal-Lagrange/MPC)

- **FKN — normal stiffness factor** (scales the code-computed penalty stiffness).
  - Default **1.0** for frictionless/rough/frictional; **10.0** for bonded/no-separation.
  - **Bending-dominated** or convergence trouble → reduce to **0.1 or 0.01** (softer, more penetration, easier convergence).
  - **Bulk/compression-dominated**, penetration too large → raise toward 1–10. Useful range is roughly **0.01–10**.
  - Auto-updated each iteration from element stress + allowed penetration; set **Update Stiffness = Each Iteration** so FKN re-scales from element stress every iteration. [FEA Tips; Mechead; Ansys Innovation Space]
- **FTOLN — penetration tolerance** (augmented Lagrange): a *fraction of the underlying element depth*, default **0.1 (10%)**. If penetration exceeds FTOLN, augmented Lagrange runs another augmentation iteration to pull it back. Tighten (e.g. 0.01) for accuracy; loosen for convergence. [Ansys CTG; FEA Tips]
- **FTOLN/FKT — tangential** stiffness analog for friction.
- **Pinball region (PINB):** search radius defining when contact is "near."
  - For **bonded/no-separation**: anything inside the pinball is bonded — keep it *small*, just big enough to close the real gap, or you glue unintended faces and transmit **fictitious moments** across gaps. This is one of the most common silent errors in assembly models.
  - For separable contact: a larger pinball is safer (catches incoming contact in large-deflection problems) with less risk.

### Detection: node-to-surface vs surface-to-surface

Surface-to-surface (Gauss-point detection, Ansys default) is smoother and preferred for general area contact. Node-to-surface is better for point/edge contact, sharp corners, and when one side is much finer; it can pass penetration on coarse targets. Pure node-to-node (`CONTA178`/gap elements) suits small-sliding point contacts only. **Mesh the contact pair so the finer/stiffer body is the *contact* surface and the coarser/softer body is the *target*** — this convention reduces penetration and improves convergence. [Ansys CTG; CONTA178 ref]

### Chattering — the #1 nonlinear-contact convergence failure

Pressure/status oscillates open↔closed between iterations. Causes: contact stiffness too high; long flexible parts with low contact pressure; abrupt status change (impact). Remedies, in order: (1) lower **FKN** (0.1–0.01); (2) switch Normal-Lagrange → **Augmented Lagrange**; (3) add **contact stabilization damping** (Ansys `FDMN`/stabilization, Abaqus `*CONTACT STABILIZE`); (4) set a small **initial interference / offset** to establish contact in step 1; (5) use **time-step cutback / smaller substeps**; (6) ramp loads. [Ansys CTG; Mechead; SimuTech]

### Initial contact status is decisive

Real-world geometry rarely touches exactly. Use contact tools to inspect initial gap/penetration, then set **`KEYOPT(9)`/Interface Treatment**: *Adjust to Touch* (close small gaps, no stress), *Add Offset* (apply known interference/shrink fit), or *No Adjustment*. A model that "won't converge in step 1" is usually rigid-body motion from a tiny initial gap — close it, don't crank FKN. [Ansys CTG; FEA Tips]

### Decision guide

- Default → **Augmented Lagrange** (good penetration control, no extra DOF, iterative solver OK).
- Penetration must be ~0 and model not over-constrained → **Normal Lagrange** (watch for chattering: pressure oscillates open/closed → add damping/stabilization or switch back).
- Bonded contact, especially with large deflection or curved gaps → **MPC** (zero penetration, no FKN tuning, but cannot detect new contact — bonded status fixed at start).
- Bonded across a gap or weld-like → **Beam** formulation.

> **FKN/FTOLN do nothing for Normal-Lagrange or MPC** — a frequent wasted-effort mistake.

**Platform**
- **MAPDL:** `CONTA174/172` `KEYOPT(2)`: `0`=Augmented Lagrange, `1`=Pure Penalty, `2`=MPC (used with bonded `KEYOPT(12)`), `3`=Normal Lagrange (Lagrange on normal, penalty on tangent), `4`=Pure Lagrange (normal+tangent). Real constants: `FKN`, `FTOLN`, `PINB`, `FKT`, `FTOL`. Set via `RMODIF`.
- **Mechanical:** Contact → *Formulation* (Augmented Lagrange / Pure Penalty / MPC / Normal Lagrange / Beam). Normal Stiffness = FKN, Penetration Tolerance = FTOLN, Pinball Region under Advanced/Geometric Modification.
- **Nastran:** `BCTPARM`/`BCPARA` controls the algorithm (penalty values `PENN` normal, `PENT` tangential, `PENTYP`; contact search distance / max activation distance `MAXS`/`SRCHDIS`; number of contact iterations). Glue uses `BGPARM`.

---

## 2a. DISCRETIZATION / ENFORCEMENT — NTS vs mortar / dual-Lagrange / Nitsche, and the contact patch test

§2 covered *how* the no-penetration condition is enforced numerically (penalty / augmented Lagrange / normal Lagrange / MPC) and *how* contact is detected (node-to-surface vs surface-to-surface, §2 "Detection"). This section is the orthogonal axis: *how the constraint is discretized across the interface* — node-by-node versus weak/integral — which governs whether the interface transmits pressure **correctly** and converges at the element rate. The two axes combine: e.g. an "augmented-Lagrange mortar" pairs the §2 enforcement with the mortar discretization here. [Yang-Laursen-Meng 2005; Popp-Wall 2014]

### The contact patch test

A correct contact discretization must transmit a **uniform pressure exactly** across the interface: press a flat block on a flat block, and the contact pressure must come out **constant**, regardless of how the two meshes line up across the joint. This is the contact analogue of the standalone element patch test. [Taylor-Papadopoulos 1991]

**Classical node-to-segment (NTS, "node-to-surface") contact fails the patch test on non-matching meshes** — it cannot reproduce a constant pressure when the slave nodes do not align with target segment boundaries — and it **degrades the spatial convergence rate**: the contact pressure shows spurious oscillations and the error no longer drops at the element order under refinement. [Yang-Laursen-Meng 2005; Taylor-Papadopoulos 1991]

### Mortar (segment-to-segment) methods

**Mortar** methods impose the non-penetration (and friction) constraint in a **weak, integral sense over the interface** — the constraint is satisfied on average over mortar segments formed by intersecting the two surface meshes, not pointwise node-by-node. Consequences:
- They **pass the contact patch test** and **preserve optimal convergence on non-matching meshes**.
- They produce **smooth, non-oscillatory contact tractions** (no NTS pressure spikes).
- This is why mortar / segment-to-segment is the modern research and high-end commercial standard for **large-sliding** and **dissimilar-mesh (non-conforming)** contact, where pressure accuracy matters. [Yang-Laursen-Meng 2005; McDevitt-Laursen 2000; Puso-Laursen 2004]

### Dual (biorthogonal) Lagrange-multiplier mortar

The efficient enabler of mortar in production: choose the multiplier shape functions **biorthogonal** to the displacement (trace) functions so the coupling (mortar) matrix is diagonal/locally invertible. Then:
- The multiplier (pressure) DOF can be **condensed out element-locally** → system size unchanged, **no indefinite saddle-point** block (contrast normal-Lagrange in §2, which adds pressure DOF and needs a direct solver).
- A **semi-smooth Newton / primal-dual active-set** scheme folds contact status, friction, geometric and material nonlinearity into **one Newton loop** — robust, and crucially with **no user penalty / FKN parameter** to tune (contrast penalty / augmented-Lagrange in §2, which always carry FKN/FTOLN). [Popp-Wall 2014; Gitterle et al. 2010]

### Nitsche's method

The **variationally consistent penalty-type** alternative: it augments the weak form with the consistent interface flux terms plus a stabilization term, so it needs **no extra multiplier DOF** and, when properly stabilized, has **no penalty-parameter sensitivity** (unlike pure penalty / augmented Lagrange in §2, where FKN must be tuned). Popular for **embedded / cut-interface** problems and small-deformation contact. [Nitsche 1971; Chouly et al.]

### When each matters

| Situation | Prefer | Why |
|---|---|---|
| Matching meshes, small sliding, pressure not the deliverable | NTS / penalty / aug-Lagrange (§2) is fine | Patch-test failure is mild when nodes align; existing §2 guidance is workable |
| **Non-matching (dissimilar) meshes** at the interface | **Mortar / segment-to-segment** | NTS fails the patch test → spurious pressures; mortar preserves convergence |
| **Large sliding** (slave traverses many target segments) | **Mortar (dual-Lagrange)** | Smooth tractions, no FKN tuning, single Newton loop |
| **Contact pressure / traction is the deliverable** (sealing, wear, fretting, fatigue) | **Mortar** | Non-oscillatory, patch-test-exact pressure |
| **Embedded / cut interfaces, no extra DOF wanted** | **Nitsche** | Consistent, no multiplier DOF, no penalty sensitivity |
| Near-zero penetration on a *matching* mesh | **Normal Lagrange / MPC (§2)** | Already covered; watch chatter (§2) |

### Practitioner takeaways

1. If your solver offers a **mortar / segment-to-segment / "augmented-Lagrange mortar"** option, prefer it for **non-matching meshes and large sliding** — it removes penalty-parameter tuning and oscillatory pressures.
2. If you must use **NTS**, **run a contact patch test** (uniform pressure across the joint → confirm a flat, oscillation-free pressure) before trusting interface tractions, and refine the slave/contact side (see §2 contact-vs-target meshing rule).
3. Report **contact-pressure convergence**, not a single-mesh peak.

**Platform note:** vendor naming varies — "segment-to-segment", "mortar", "dual mortar", or "augmented-Lagrange contact" on a surface-to-surface pair. Some codes default detection to Gauss-point/surface-to-surface (§2) but still discretize the *constraint* node-wise; check the theory manual for whether the formulation is true mortar (integral) before relying on patch-test behavior.

---

## 2b. HERTZIAN CONTACT — the analytical cross-check for contact-pressure FEA

Before trusting an FE contact-pressure result (bearings, gears, seals, cam-follower, ball/roller contacts, press-fit pins), **compute the closed-form Hertz solution first and compare**. Hertz theory (Hertz 1882; the canonical modern treatment is K.L. Johnson, *Contact Mechanics*, 1985) gives the contact patch size, peak pressure, approach, and sub-surface stress for **smooth, non-conforming, frictionless elastic bodies under small strains** (contact patch ≪ body size, no yielding, no adhesion). It is the contact analogue of "check your beam-bending FE against `PL³/48EI`": if the FE peak pressure doesn't land within a few percent of `p_max`, the mesh, formulation (§2), or detection (§2 "Detection") is wrong — not the physics. This complements the contact-patch / convergence checks of §2a: §2a confirms the discretization transmits a *uniform* pressure correctly; Hertz confirms a *curved* contact gives the right *peak*.

### The two effective quantities (combine the bodies first)

Every Hertz formula is written in terms of one **effective (reduced) modulus** and one **effective (relative) radius** — compute these once, then read the row:

- **Effective elastic modulus** `E*` (a.k.a. contact modulus):
  `1/E* = (1−ν₁²)/E₁ + (1−ν₂²)/E₂`  — for a rigid + elastic pair the rigid body's term drops, so `E* = E/(1−ν²)`.
- **Effective radius** `R*`:
  `1/R* = 1/R₁ + 1/R₂`  — a **flat** counterface is `R₂ = ∞` (term → 0); a **concave / cup / internal** surface (ball in a race, pin in a hole) takes a **negative** radius, `1/R* = 1/R₁ − 1/R₂`, which enlarges `R*`, grows the patch, and lowers `p_max` (this is why conforming contacts are gentler).

### Closed-form solutions

`F` = total normal load; for line contact `F` is the **total** load over engaged length `L` (so `F/L` is load per unit length). `p_mean` = F / (contact area).

| Configuration | Contact patch | Peak pressure `p_max` | `p_max / p_mean` | Elastic approach `δ` |
|---|---|---|---|---|
| **Sphere–sphere** (point → circle radius `a`) | `a = (3 F R* / 4E*)^{1/3}` | `p_max = 3F / (2π a²)` | **3/2** | `δ = a²/R* = (9F² / 16 E*² R*)^{1/3}` |
| **Sphere–flat** (`R₂=∞` ⇒ `R*=R₁`) | same `a` formula with `R*=R₁` | `p_max = 3F / (2π a²)` | **3/2** | `δ = a²/R₁` |
| **Cylinder–cylinder, parallel axes** (line → half-width `b`, length `L`) | `b = (4 F R* / π L E*)^{1/2}` | `p_max = 2F / (π b L) = (F E* / π L R*)^{1/2}` | **4/π ≈ 1.27** | (logarithmic; geometry-dependent, no simple closed form) |

- **Force–approach (stiffening) law, sphere:** `F = (4/3) E* √R* · δ^{3/2}` — contact stiffens as it grows (`dF/dδ ∝ √δ`), so a Hertz contact is a **nonlinear spring**; a *linear* contact-stiffness `FKN` (§2) is only a local tangent.
- **Pressure distribution:** hemispherical/semi-elliptical, `p(r) = p_max·√(1 − (r/a)²)` (circle) or `p(x) = p_max·√(1 − (x/b)²)` (line). The peak is at the center, zero at the edge — so a *uniform* contact pressure out of FE is a red flag (wrong formulation or a bonded/over-stiff patch).

### Sub-surface stress — where contacts actually fail

The maximum **shear** stress is **below** the surface, not at it — which is why rolling contacts fail by sub-surface initiation (pitting, spalling), and why a surface-only stress plot misses the governing stress:

- **Depth of max shear:** `z ≈ 0.48 a` for a circular (point) contact at ν ≈ 0.3 (Johnson, *Contact Mechanics* gives `z ≈ 0.49 a` at ν = 0.33; Wikipedia orientation); `z ≈ 0.78 b` for line contact.
- **Magnitude:** `τ_max ≈ 0.31 · p_max` (point, ν = 0.3); `τ_max ≈ 0.30 · p_max` (line). So peak shear ≈ ⅓ of the peak contact pressure, one half-patch-radius deep.

### Mesh-refinement requirement at the contact patch

The contact patch (`2a` or `2b`) is tiny relative to the parts, so a global mesh **cannot** resolve it. Rule of thumb: **≥ ~6 elements across the contact half-width** (`a` or `b`) — i.e. resolve the *predicted* patch, which means you must run the Hertz calc *first* to know how fine to mesh. Too coarse and the FE `p_max` reads low (the peak is smeared); the curved pressure profile and the sub-surface shear peak both need this density. Use quadratic elements or local refinement / submodeling at the patch, and confirm `p_max` converges toward the Hertz value as you refine (cf. §2a: report pressure convergence, not a single-mesh peak). For detection/formulation, the §2 contact-vs-target meshing rule (finer/stiffer body = contact side) and an augmented-Lagrange or mortar (§2a) formulation give the cleanest peak.

### What breaks the cross-check (when FE *should* differ from Hertz)

Hertz is the **elastic, frictionless, non-conforming, small-strain** baseline. Legitimately expect divergence — and trust the FE over Hertz — when: the contact **yields** (plasticity caps `p_max`; compare `p_max` to ~`1.6·σ_y`–`3·σ_y` for onset/full plasticity); **friction** or tangential load shifts the stress field toward the surface; the surfaces are **conforming** (large contact angle — deep-groove races, cylindrical journal in a close bore — where the half-space assumption fails); there is **adhesion** (soft/clean contacts → JKR/DMT, §"Adhesive contact" regimes); or **edge/finite-thickness** effects matter (short rollers show end stress spikes Hertz omits). In those cases Hertz is still the right *sanity floor*: the FE peak should be ≥ the Hertz peak for added friction/edge effects, or ≤ it once plasticity sets in.

**Cross-links:** contact *behavior* (frictionless/frictional, separable) → §1; *enforcement & stiffness* (penalty/augmented-Lagrange/`FKN`, the nonlinear-spring tangent) → §2; *discretization & the uniform-pressure patch test* → §2a; *thermal* contact across the same interface → §9.

---

## 3. CONSTRAINT / RIGID ELEMENTS — RBE2 vs RBE3 (the most-misused pair)

This is, by consensus of NAFEMS and practitioners, the single most common source of FEA modeling error. **RBE2 adds rigid stiffness; RBE3 does not.** [Fidelis; hiStructural; Predictive Engineering; NAFEMS PMJC]

### RBE2 / CERIG / rigid link (kinematic / "rigid body element")
- **Physical meaning:** an infinitely rigid body. One **independent (master)** node drives a set of **dependent (slave)** nodes; all slaves move with exactly the master's translation+rotation, no relative motion.
- **DOF coupled:** the specified DOF of every dependent node are tied rigidly to the master (written as MPC equations). All 6 DOF by default in 3D (UX,UY,UZ,ROTX,ROTY,ROTZ).
- **Load transfer:** rigid — distributes a master force/moment to slaves in proportion to a rigid-body assumption.
- **Use when:** genuinely rigid connection (thick lug, rigid clamp), connecting a bearing race you treat as rigid, attaching a rigid mass, applying enforced displacement/rotation to a whole patch.
- **Pitfall — artificial stiffening:** the bonded patch cannot deform. Over a flexible shell/skin this creates a false stiff spot, raises local stiffness, shifts modes up, and dumps **artificial stress concentrations** at the boundary. Over-constraint can also conflict with other constraints → solver errors.
- **Commands:** MAPDL `CERIG` (rigid region) or `MPC184` rigid link/beam, or `CP` for simple DOF coupling. Nastran `RBE2` (and `RBAR` for a 2-node rigid bar). Abaqus `*KINEMATIC COUPLING`.

### RBE3 / distributed coupling
- **Physical meaning:** distributes load/mass from a **reference (dependent) node** to a set of **independent** nodes using a weighted average (typically area/distance weights) — **without** adding stiffness. The reference node's motion is the weighted average of the independent nodes' motion.
- **DOF coupled:** the dependent (reference) node's DOF are defined as a weighted combination of independent nodes' DOF. It does **not** constrain the relative motion *among* the independent nodes → no rigidity.
- **Load transfer:** a force/mass at the reference node is spread to the independent set by weighting factors; the patch is free to deform.
- **Use when:** spreading a remote force/moment onto a face without stiffening it; representing a point mass connected to a structure; averaging the motion of a hole/edge; applying a bearing load.
- **Pitfalls (the ones that bite):**
  - **Rotational-DOF singularity / ill-conditioning** if independent nodes are collinear or coplanar and you try to drive the reference node's **rotation** through translation-only independent nodes (the weighted average can't resolve rotation from coplanar points → near-singular). Best practice: put only translational DOF (1-2-3) on the independent set; include rotational DOF (4-5-6) on the independent nodes only where the geometry genuinely supports it. [Predictive Engineering; MSC]
  - **Double-dependency (Nastran fatal):** a node that is *dependent* in one rigid element (RBE2/RBE3/RBAR) must not be *dependent* in another, and an RBE3 dependent DOF **cannot** also appear in an SPC/MPC.
  - The reference DOF is already dependent — you **cannot** additionally constrain or load that same DOF directly.

**Canonical example (cross-checked, Fidelis):** a point-mass engine on four mounts. RBE2 → all four mounts deform *together* (rigid raft) and over-stiffen the cradle; RBE3 → each mount displaces independently and the load is distributed by weight, preserving cradle compliance. For mass attachment and load spreading, **RBE3 is almost always the right default.** [Fidelis]

### Constraint equations (CE) and coupling (CP)
- **CP (coupling):** forces a set of nodes to share the **same value** of a DOF in a given direction (e.g. all nodes move together in UY). DOF eliminated to one prime DOF; forces summed onto prime. Use for symmetry, cyclic, "move as one" without full rigidity.
- **CE (constraint equation):** general linear equation `Σ Cᵢ·DOFᵢ = const`. Most general; RBE2/RBE3/CERIG are auto-generated CEs underneath. Use for custom kinematics, periodicity, mesh-incompatible ties.
- **Compatibility rule (MAPDL):** DOF removed by `CP` cannot appear in any `CE`/`CERIG`.

### Summary table

| Element | Rigid? | Constrains relative motion of attached set? | Adds stiffness | Typical use | Main pitfall |
|---|---|---|---|---|---|
| RBE2 / CERIG / `MPC184`-rigid | Yes | Yes | Yes | Rigid links, enforced motion, rigid mass | Artificial stiffening / over-constraint |
| RBE3 | No | No | No | Load/mass spreading, motion averaging | Rotational-DOF singularity, double-dependency |
| RBAR | Yes (2 nodes) | Yes | Yes | Rigid bar between 2 grids | Same as RBE2 |
| CP (coupling) | Partial | Same DOF value | Eliminates DOF | Symmetry, "move together" | Removed DOF can't be reused in a CE |
| CE / MPC | Custom | Custom | Per equation | Periodic, mesh-incompatible | Manual, easy to mis-specify |

**Platform commands:** MAPDL `CE`, `CERIG`, `CP`, `RBE3`, `MPC184`. Nastran `RBE2`, `RBE3`, `RBAR`, `MPC`/`MPCADD`. Abaqus `*KINEMATIC COUPLING` (≈RBE2), `*DISTRIBUTING COUPLING`/`*COUPLING` with `DISTRIBUTING` (≈RBE3), `*MPC`.

---

## 4. BOLTED CONNECTIONS — preload, torque, VDI 2230, fidelity ladder

### 4.1 The two governing numbers (cross-verified)

- **Target preload `Fi ≈ 0.75·Fp`** (proof load) for **non-permanent / reused** fasteners; **`Fi ≈ 0.90·Fp`** for **permanent** connections (Shigley §8), where proof load `Fp = At·Sp` (tensile-stress area × proof strength). Common shorthand: preload ≈ **0.7× proof / yield**. [Shigley §8; VDI 2230; Wikipedia bolted joint (orientation)]
- **Torque–tension `T = K·F·d`**, nut factor **K ≈ 0.20** as-received steel (≈0.15 lubricated, ≈0.30 dry/plated). Independently grounded: K≈0.20 follows from μ≈0.15 thread/collar friction (Shigley §8 torque-tension derivation; VDI 2230) and a measured study back-calculated **K = 0.208**. Ansys Workbench hard-codes the simplified `T = 0.2·F·d`. [Shigley §8; VDI 2230; Wikipedia bolted joint (orientation)]

> **Friction dominates.** ~85–90% of tightening torque is spent on head/thread friction; only ~10–15% becomes bolt tension. This is *why* torque control is inaccurate. [VDI 2230; Bossard]

### 4.2 Preload scatter by method — design against the *minimum* preload (cross-verified)

| Tightening method | Preload accuracy (scatter) | VDI 2230 tightening factor αA |
|---|---|---|
| Torque wrench, unlubricated | **± 35 %** | ~1.7–4 (high scatter) |
| Torque wrench, lubricated | ± 25–30 % | ~1.6–2.5 |
| Torque + angle (angle-of-turn) | ± 15 % | ~1.4–1.6 |
| Yield-point / torque-to-yield | ± 8 % | ~1.2–1.4 |
| Bolt elongation (ultrasonic / strain gauge) | ± 3–5 % | ~1.1–1.3 |

**αA (Anziehfaktor) = max preload / min preload** for a method; you size the bolt for the *max* preload but guarantee clamp / anti-separation at the *min*. Better tightening control → αA→1 → less over-dimensioning. [VDI 2230 (primary); Wikipedia bolted joint accuracy table (orientation); eAssistant]

### 4.3 Joint stiffness & load factor (why preload protects fatigue)

The clamped-member stiffness **does not change the preload that torque produces**, but the **ratio of bolt to member stiffness, Φ = k_b/(k_b+k_m), sets the fraction of an external tension load that the bolt actually sees.** Members are typically far stiffer than the bolt, so Φ is small (~0.1–0.3): most external load *unloads the clamped members* rather than adding to bolt tension — until **separation**, after which the bolt takes 100%. Adequate preload keeps the joint below separation, which (a) minimizes the bolt's *stress range* → dramatically improves **bolt fatigue life**, and (b) prevents slip → prevents **fretting fatigue** of the members. This is the entire reason bolted joints are preloaded. [Shigley §8; Wikipedia bolted joint]

### 4.4 VDI 2230 — the systematic guideline (the authoritative bolt standard)

VDI 2230 Part 1 is the reference systematic calculation for high-duty bolted joints, an **R0–R13 step sequence**: R0 dimensions → R1 **tightening factor αA** (defines scatter, the first major input) → tightening torque, working/thermal loads, load factor Φ, embedding loss Fz, required assembly preload FM, surface pressure under head, endurance (fatigue) safety, slip safety. It also supplies friction-coefficient and tightening-method databases from field data. Use VDI 2230 to *set* the preload and safety factors, then verify the load path and local stress in FEA. [VDI 2230; PCB whitepaper; elbcore; eAssistant]

### 4.5 Fidelity ladder (climb only as far as the question demands)

| Level | Model | Captures | Misses | Cost | When to use |
|---|---|---|---|---|---|
| 0 | **Bonded / glue** (no bolt) | Load path, global stiffness | No preload, no slip, no bolt stress | ~free | Conceptual/global FEM, modal, when bolts aren't the concern |
| 1 | **Spring/beam bolt (1D)**: beam + RBE3/RBE2 spider to each hole | Axial+shear+bending load path, bolt force extraction | Local clamping pressure, head/nut contact stress, preload (unless added) | Cheap | Many bolts (joint pattern), aircraft/automotive panel joints, fastener load survey |
| 2 | **Beam bolt + pretension + contact** | Above + preload + faying-surface separation/slip | True 3D bolt stress field | Medium | Bolt force + joint separation checks |
| 3 | **Solid bolt + pretension + contact** under head/nut | Full bolt stress, thread region (if modeled), realistic clamp cone (~30° half-angle) | Most expensive | High | Detailed bolt/lug stress, fatigue hot-spots, critical single joints |

### 4.6 Modeling notes

- **Beam vs solid:** beam (CBEAM/BEAM188) is fine when you want the *load path and bolt force*, not the bolt's own stress; solid is required when **bolt stress / thread / head-bearing** is the deliverable.
- **Spider:** a **RBE2** spider at the hole over-stiffens the plate around the hole (false rigid ring) → use an **RBE3** spider for the head/nut footprint when you want realistic plate compliance; RBE2 only if the head is genuinely rigid relative to the sheet. [NAFEMS HT50; SimScale; Predictive]
- **Contact under head/nut** is what produces the realistic **clamp cone (~30° half-angle)** pressure distribution — needed for accurate faying-surface separation and bolt bending.
- **Apply preload in load step 1, then "lock"** (fix the pretension displacement) in subsequent steps so service loads ride on top of the locked preload. Displacement/adjustment (stretch) input converges more robustly than force input. [Ansys CTG; Simcenter Nastran BOLT/BOLTFOR]

### 4.7 Thermal effect on preload (CTE)

Preload **changes with temperature** when bolt and clamped members have different CTE or see a ΔT — differential thermal expansion adds or relieves clamp force (e.g. an aluminum flange with a steel bolt *loses* preload when heated; cryogenic cooldown of dissimilar metals can *gain* or lose clamp). VDI 2230 includes a thermal-load term in the preload balance; in FEA, apply the bolt pretension, lock it, then apply the thermal load step and **re-read the bolt force**. This is first-order for cryo/space hardware. [VDI 2230; Shigley]

### 4.8 Gaskets

A gasketed joint is **pressure-closure (crush) governed**, not linear-elastic: use a **gasket material model** (Ansys `GASKET`/`INTER19x` elements with a measured loading/unloading pressure-closure curve; Abaqus `*GASKET`; Nastran gasket via nonlinear contact + crush curve). Model preload first, then internal pressure, and check the gasket stays in compression everywhere (no separation/leak). The clamp cone from the bolts must cover the gasket seat. [Ansys CTG; NAFEMS PMJC]

**Platform commands**
- **MAPDL:** `PSMESH` to slice the bolt shank and insert `PRETS179` pretension elements; apply `SLOAD` — first load step `SLOAD,...,FORC,...,preload`; subsequent steps `SLOAD,...,LOCK`. Bolt = `SOLID185/187` or `BEAM188`.
- **Mechanical:** insert **Bolt Pretension** load on bolt body (needs a coordinate system with Z along shaft) or on the cylindrical face (auto CS). Step 1 = *Load* (preload force) or *Adjustment* (stretch); later steps = *Lock*. Adjustment (displacement) input is more robust for convergence than force.
- **Nastran:** `BOLT` bulk entry defines the bolt (grids/elements/cross-section); `BOLTFOR` sets the preload force; `BOLTLD` combines/scales `BOLTFOR` sets across subcases (selected by `BOLTLD` case control). Supported in SOL101/103/105/111 and nonlinear SOL401/402 (and SOL601). MSC Nastran also offers preload via `BOLT`/3D-bolt or classic MPC/`SPCD` enforced-strain methods.
- **Abaqus:** `*PRE-TENSION SECTION` + pre-tension node load (then `*BOUNDARY` fix to lock).

---

## 5. WELDS & FASTENER ELEMENTS

### 5.1 Weld connector elements

| Connector | Models | Mesh requirement | Use when | Platform |
|---|---|---|---|---|
| **Spot weld** | Discrete weld nugget between sheets | Faces near-flat at weld, not highly curved | Resistance spot welds in sheet-metal assemblies | Nastran `CWELD` (+`PWELD`, GS point); Ansys spot-weld via shared nodes / contact / beam+`CONTA` or *Spot Weld* object; Abaqus mesh-independent fastener / `*ELEMENT` |
| **Seam weld** | Continuous line of weld | Edge/line definition | Continuous welded seams, fillet/lap welds | Nastran row of `CWELD`/`CFAST`; Ansys bonded edge contact or seam-weld mesh objects |
| **Fastener (rivet/bolt patch)** | Flexible connector between sheets, accounts for sheet thickness | Sheets within reach `D`+gap | Riveted/bolted sheet joints, **mesh-independent** (no node alignment needed) | Nastran `CFAST` (+`PFAST`, diameter); GA-GB (element-to-element) or GS (point) form; Abaqus `*FASTENER` |

**Why CWELD/CFAST over RBE2 chains or bare CBUSH:** they are **mesh-independent** (don't need coincident nodes), satisfy **rigid-body invariance**, are easy to generate in bulk (hundreds of fasteners), and give clean fastener force/moment recovery. RBE2 chains tend to over-stiffen; bare CBUSH needs aligned nodes. [Altair; NX Nastran; Predictive]

- **CFAST:** behaves like a flexible rod/beam (PFAST gives stiffness K1–K6) connecting projected points on two patches — good for **rivets and bolts in shell assemblies**.
- **CWELD:** weld element representing the physical nugget; `GS` field = weld location.
- **Ansys equivalent:** there's no single CWELD card; use a **beam (BEAM188) + bonded/spider contact**, the **Spot Weld** connection object, or node-merge for continuous welds. For mesh-independent fastener behavior use a beam with `MPC`/`RBE3` ends.

### 5.2 Weld fatigue — the stress hierarchy (high-value content)

A raw FE peak stress at a weld toe is **mesh-dependent and meaningless** for fatigue (it diverges as you refine). Weld-fatigue codes (IIW, Eurocode 3 EN 1993-1-9, DNV) define which stress to extract, paired with a matching S-N (FAT) curve. **You must use the stress definition that the chosen S-N curve was derived with — never mix them.** [IIW Recommendations; Eurocode 3]

| Method | Stress used | Mesh sensitivity | S-N curve basis | When |
|---|---|---|---|---|
| **Nominal stress** | section stress away from the weld (P/A + M/Z) | none | detail-category FAT tables (Eurocode, IIW) | simple details with a defined nominal section; design codes |
| **Structural / hot-spot stress** | surface stress **extrapolated to the weld toe**, excluding the local notch | low *if extrapolation rule is followed* | hot-spot FAT (IIW: typically **FAT 90/100** for toe) | plate/shell welded structures, complex geometry without a clear nominal section |
| **Effective notch stress** | stress at the toe modeled with a **fictitious 1 mm rounding** (Neuber) | high — needs very fine mesh | notch FAT (IIW **FAT 225** for steel) | local detail assessment, weld profile studies |
| **Fracture mechanics (LEFM)** | ΔK crack growth | — | Paris law / da/dN | crack-tolerant / remaining-life |

**Hot-spot (structural-stress) extraction — IIW mesh rules (cross-verified):**
- **Fine mesh (shell or solid):** element size ≈ **t × t** (plate thickness) at the hot spot; read surface stress at **0.4t and 1.0t** from the toe and **linearly extrapolate** to the toe (Type "a" hot spots, weld toe on plate surface).
- **Fine, ≤4 mm elements:** read at **4, 8, 12 mm** and **quadratically extrapolate** — fatigue strength becomes essentially **independent of element size/type once elements are ≤4 mm** at the reference points.
- **Coarse shell mesh:** element ≈ 10 mm, read at the **0.5t and 1.5t** mid-side points and extrapolate. If you refine in-plane, **refine through-thickness as well.**
[IIW Recommendations for Fatigue Design of Welded Joints (Hobbacher); Niemi/Fricke designer's guide]

**The mesh-convergence trap (top weld mistake):** structural/notch stress methods are the *opposite* of normal stress-convergence intuition — peak toe stress **never converges** (it keeps rising with refinement). You do **not** refine to convergence; you refine to the **prescribed extraction mesh** and read at the **prescribed points**. Reporting "peak von Mises at the weld toe" as a fatigue stress is wrong by construction. [IIW; Eurocode 3; NAFEMS welds]

**Mean-stress / weld residual stress:** as-welded joints carry high tensile residual stress, so weld-fatigue FAT curves are largely **mean-stress-independent** (the residual field dominates) — do not apply a Goodman mean-stress correction to a code FAT class unless the code says so. [IIW; Eurocode 3]

---

## 6. SPRINGS / BUSHINGS / CONNECTORS

| Element | DOF / stiffness | Coupling | Use when | Notes |
|---|---|---|---|---|
| **COMBIN14** (Ansys spring-damper) | 1 axial **or** 1 torsional DOF (longitudinal/torsional) | Single DOF along element axis | Simple axial/torsional spring, ground spring, gap-free compliance | One stiffness K (+ damping); not a full 6-DOF bushing |
| **CBUSH** (Nastran) | **6 independent stiffnesses** (K1–K6: 3 transl + 3 rot) in a defined coord system | Uncouples the 6 DOF | Compliant joints, bushings, rubber mounts, bolt stiffness, bearing radial stiffness, **bolt force extraction** | Zero-length OK; preferred over CELAS (no grounding/coord pitfalls); define orientation carefully |
| **MATRIX27** (Ansys) | Arbitrary 12×12 stiffness/damping/mass matrix between 2 nodes | Fully general (can couple all DOF) | Anisotropic/coupled bushings, bearings with cross-coupling, superelement-like stiffness | You supply the matrix; powerful but error-prone |
| **Bushing** (Mechanical) | 6×6 stiffness | Per-DOF | Compliant connection in Workbench | GUI equivalent of CBUSH |
| **COMBI214** (Ansys) | 2D bearing, cross-coupled K/C | Couples 2 directions | Rotordynamics journal/oil-film bearings | Speed-dependent coefficients |

**When to model a joint as a bushing (CBUSH/MATRIX27), not RBE2:**
- The connection has **measurable compliance** you want to capture (rubber mount, elastomer bush, bolted-joint local flexibility, bearing radial/axial stiffness) — replacing it with a rigid link (RBE2) would falsify the dynamics.
- You need **modal / NVH** accuracy: joint stiffness shifts frequencies; a rigid link gives wrong modes.
- You want **load recovery at the joint**: CBUSH gives force = K·Δ directly (clean bolt/mount loads), which is why CBUSH is the standard bolt-load-extraction element.
- **Bearing:** represent radial stiffness with the transverse CBUSH terms (K2,K3), leave the axial/rotational soft or free as the bearing allows; for circumferentially varying radial stiffness, use multiple CBUSH/MATRIX27 around the race. [Predictive; Altair; NAFEMS PMJC]

**Ansys ↔ Nastran mapping:** Ansys CBUSH-equivalent is **`COMBIN14`** (per-DOF, multiple elements) or **`MATRIX27`** (one 6-DOF element), or the Mechanical **Bushing** connection (6×6 stiffness). Nastran spring family: `CELAS1-4` (scalar), `CBUSH` (6-DOF, recommended).

---

## 7. KINEMATIC JOINTS (mechanism / flexible multibody)

A joint connects two nodes (12 DOF total) and constrains some of the **6 relative DOF**; the rest are free (the joint's articulation). Constraints applied via **Lagrange multipliers** in `MPC184`.

| Joint | Free relative DOF | Constrained relative DOF | Physical analog |
|---|---|---|---|
| **Fixed** | 0 | all 6 | Welded/rigid tie |
| **Revolute** | 1 rotation (about hinge axis) | 3 transl + 2 rot | Hinge / pin |
| **Cylindrical** | 1 transl + 1 rot (same axis) | 2 transl + 2 rot | Shaft sliding+rotating in bore |
| **Translational (slot/prismatic)** | 1 translation | 2 transl + 3 rot | Linear slider/rail |
| **Slot** | 1 transl + 3 rot | 2 transl | Pin in a slot |
| **Spherical (ball)** | 3 rotations | 3 translations | Ball-and-socket |
| **Universal** | 2 rotations | 3 transl + 1 rot | Cardan/U-joint |
| **Planar / Point-in-plane** | in-plane motion | out-of-plane transl | Point constrained to a plane |
| **General** | user picks any subset | the complement | Custom mechanism DOF |

- **Where used:** flexible multibody dynamics (mechanisms with flexible links), kinematic studies, deployment, linkages — joints transmit motion between flexible/rigid bodies and can carry **stops, locks, actuating loads, stiffness/damping/friction** on the free DOF.
- **Friction:** Coulomb friction available on revolute, slot, translational, spherical joints.
- **Pitfall:** joints are enforced with Lagrange multipliers (extra equations) → can over-constrain if combined redundantly with other rigid links; ensure the mechanism isn't kinematically over-determined.

**Platform**
- **MAPDL:** `MPC184` with the joint `KEYOPT(1)` selecting type (revolute/universal/slot/point/translational/cylindrical/planar/spherical/general/screw); section `SECTYPE,...,JOINT`; relative-DOF BCs via `DJ`/`SECJOINT`; loads/limits via joint inputs.
- **Mechanical:** Connections → **Joint** (Fixed/Revolute/Cylindrical/Translational/Slot/Universal/Spherical/Planar/General/Bushing), reference vs mobile scoping.
- **Nastran:** SOL402 (kinematic/multibody) joint elements (e.g. `JOINTG` with `JCONSET`), or classic constraint sets; MSC Nastran ADAMS interface / SOL400 connectors.
- **Abaqus:** `*CONNECTOR SECTION` connectors (HINGE, CYLINDRICAL, SLOT, JOIN, etc.) with `*CONNECTOR BEHAVIOR`.

---

## 8. REMOTE POINTS / REMOTE LOADS / point-to-surface coupling

A **remote point** is a single pilot node connected to a face/edge/vertex set; it lets you apply a load or BC "from a distance" and is the mechanism behind **remote force, remote displacement, moment, bearing load, point mass**. Its **behavior** picks the underlying constraint:

| Behavior | Underlying element | Patch can deform? | Adds stiffness | Use when |
|---|---|---|---|---|
| **Rigid** | RBE2 / CERIG | No | Yes | Patch genuinely rigid; point mass on a stiff boss; enforced motion of whole face |
| **Deformable** | RBE3 | Yes | No | Spread a remote force/moment onto a flexible face without stiffening (most common, default-ish) |
| **Coupled** | CP (same-DOF coupling) | Constrained to equal pilot DOF | Eliminates DOF | Tie face DOF to pilot value (e.g. uniform motion) |
| **Beam** | Massless beam(s) | Adds finite, defined stiffness | Yes (tunable) | When you want a *known* connection stiffness, not infinite (rigid) or zero (deformable) |

- **Remote force / moment:** apply at the pilot; transmitted to the scoped face per the behavior. Use **deformable** so you don't artificially stiffen; use **rigid** only if the face is truly rigid.
- **Remote displacement / rotation:** prescribe pilot DOF; rigid behavior drives the face rigidly, deformable lets it warp.
- **Bearing load:** a remote force applied with a **compressive (cosine/projected) distribution** over the loaded half of a cylindrical bore — represents a shaft pushing on a hole; do **not** use rigid behavior (it would prevent ovalization).
- **Pitfalls:**
  - Multiple **rigid** remote points sharing nodes → over-constraint / conflicting MPCs.
  - **Deformable** remote point that must transmit a **moment** through few/collinear nodes → ill-conditioned (same RBE3 rotational-DOF issue as §3).
  - Two boundary conditions on the same deformable remote-point DOF can conflict (the DOF is already dependent).

**Platform:** Mechanical → **Remote Point** (or per-load *Behavior* = Rigid/Deformable/Coupled/Beam) → generates `MPC184`/`RBE3`/`CP`/`CONTA174`+`TARGE170` MPC under the hood. MAPDL: build directly with `RBE3`, `CERIG`, `CP`, or pilot-node `TARGE170`. Nastran: `RBE2` (rigid remote), `RBE3` (deformable remote), `FORCE`/`MOMENT`/`SPCD` on the reference grid.

---

## 9. THERMAL CONTACT CONDUCTANCE (TCC / h_c) — note

When a thermal or thermo-elastic model crosses a mechanical interface (bolted, clamped, pressed, shrink-fit), the temperature drop across the joint is governed by **TCC**, not by the bulk conductivity. **Three parallel paths:** `h = h_c (solid-spot conduction) + h_g (interstitial gas) + h_r (radiation)`. Real solid contact is only **~1–2% of the apparent area** — heat funnels through asperity spots (constriction/spreading resistance). [Madhusudana, *Thermal Contact Conductance* (Springer); COMSOL theory; Wikipedia TCC (orientation)]

**Units (the #1 error):** `h_c` [W/m²·K] is *per area*; `q″ = h_c·ΔT`. Total joint conductance `G = h_c·A` [W/K]; `R_c = 1/(h_c·A)` [K/W]; `ΔT = Q/(h_c·A)`. Keep per-area vs total straight.

**Dependencies (direction + scaling):** h_c rises **strongly with contact pressure** (≈ `(P/H)^0.8–0.95`, nearly linear); rises as **roughness σ falls** (≈1/σ) and as asperity slope rises; falls with out-of-flatness/waviness; rises with the **harmonic-mean conductivity** `k_s = 2k₁k₂/(k₁+k₂)`; a soft interstitial (grease/TIM) or indium foil raises h an order of magnitude. [Madhusudana (primary); Wikipedia TCC (orientation)]

**Orders of magnitude (cross-verified band):** most measured TCC in air falls in **R″_c ≈ 5×10⁻⁶ … 5×10⁻⁴ m²·K/W**, i.e. **h_c ≈ 2,000 … 200,000 W/m²·K**. Bare Al–Al ≈3,600, SS–SS ≈3,000 W/m²·K are **low-pressure (~0.1 MPa) illustrative values only** — h_c scales **1–2 orders of magnitude with joint pressure** (see the scaling above), so never apply a bare-metal number without its contact pressure; with thermal grease/TIM, much higher. [Madhusudana; nuclear-power.com; Wikipedia TCC (orientation)]

**Vacuum / cryogenic drop (the spacecraft/cryo headline):**
- **Vacuum deletes the `h_g` gas path entirely.** In air, `h_g` can rival or exceed `h_c`; in vacuum only the few contact spots conduct, so TCC drops sharply — TCC is a first-order concern for space and cryo hardware, often second-order in air-cooled electronics. [Madhusudana; ESA/NASA practice; Wikipedia TCC (orientation)]
- **Cryogenic temperature drop:** measured pressed-metal contact conductance **falls roughly one order of magnitude between 200 K and ~20 K**, scaling approximately **G ∝ T to T²** for pressed metals at low T (contact-spot conduction and metal k both drop). For pressed Cu–Cu / Al–Al / SS the literature (Salerno NASA TM, ALBA/synchrotron and cryo TCC studies) reports data **4–300 K** at 0.4–14 MPa; high-purity Cu/Al do *not* track bulk k(T) because RRR-dependent conduction and constriction interact. **Indium foil or Apiezon grease at the interface is the standard cryo fix** to recover conductance. [Salerno NASA TM 110429; Gmelin; ScienceDirect cryo TCC studies]

**Modeling TCC:** apply a measured/correlated `h_c` (or temperature- and pressure-dependent table) to the interface — Ansys `CONTA17x` with `TCC` real constant or table; Simcenter/Nastran thermal contact / TMG conductance; SINDA/Thermal Desktop contactor conductor `G = h_c·A`. If contact pressure is computed by a structural pass, drive `h_c(P)` from it (Ansys supports pressure-dependent TCC). **Do not** use bulk conductivity across a bolted/clamped joint — it can under-predict ΔT by an order of magnitude. (See the companion `thermal-contact-resistance.md` reference for full TCC physics/tables.) [Ansys CTG; Madhusudana]

---

## 10. Top mistakes — quick gotcha checklist

1. **RBE2 everywhere → falsely stiff structure & fake stress hot-spots.** Default to RBE3/deformable for load/mass spreading; reserve RBE2/rigid for truly rigid links.
2. **RBE3 driving rotation off coplanar/collinear nodes → singular.** Keep the independent set translational; add rotational DOF only where geometry supports it.
3. **A node can be dependent in only ONE rigid element** (RBE2/RBE3/RBAR), and an RBE3 dependent DOF can't also be in an SPC/MPC — else Nastran fatal / double-dependency.
4. **Bonded + large pinball → fictitious moments glued across gaps.** Keep bonded pinball tight.
5. **Normal-Lagrange chatters** (pressure oscillates) and needs a direct solver → fall back to Augmented Lagrange; lower FKN; add stabilization; close the initial gap instead of cranking FKN.
6. **FKN/FTOLN do nothing** for Normal-Lagrange or MPC formulations.
6a. **NTS (node-to-segment) contact fails the patch test on non-matching meshes** → spurious contact pressures and lost convergence rate. For dissimilar meshes, large sliding, or when contact pressure is the deliverable, prefer **mortar / dual-Lagrange** (or Nitsche); if stuck on NTS, run a contact patch test first (§2a).
7. **Bolt preload:** size for *max* preload (αA), guarantee clamp at *min*; apply in step 1, **LOCK** after; prefer displacement/adjustment input; **re-check bolt force after a thermal step** (CTE changes preload).
8. **Torque control is ±25–35%** — design against the minimum preload, not the nominal.
9. **Weld fatigue: never report peak toe stress.** It never converges. Use nominal / hot-spot (extrapolate at the IIW-prescribed points on a t×t or ≤4 mm mesh) / notch stress, each with its matching FAT curve; don't mix definitions or add a mean-stress correction to a FAT class.
10. **CBUSH/CFAST for fastener forces**, not RBE2 chains — mesh-independent, invariant, clean recovery.
11. **Linear (bonded/no-sep) first**, refine to nonlinear contact only at the governing joint (submodel) to control cost.
12. **TCC, not bulk k, across joints** — and remember vacuum deletes the gas path, cryo drops conductance ~10× from 200→20 K; use indium/grease to recover it.

---

## SOURCES

Reliability key: **A** = standard/code or vendor theory manual (authoritative); **B** = recognized practitioner / peer-reviewed / textbook; **C** = secondary reference, corroborating only.

**Standards, codes, vendor theory manuals (A)**
- VDI 2230 Part 1 — *Systematic calculation of highly stressed bolted joints* (αA tightening factor, R0–R13 steps, friction/torque databases). Overviews: https://www.elbcore-engineers.de/en/blog/vdi-2230/ ; PCB whitepaper https://www.pcb.com/Contentstore/mktgcontent/WhitePapers/WPL_22_Guideliner_VDI_2230.pdf ; eAssistant Ch.14 https://eassistant.at/fileadmin/dokumente/eassistant/etc/HTMLHandbuch/en/eAssistantHandbch14.html — **A**
- IIW — *Recommendations for Fatigue Design of Welded Joints and Components* (Hobbacher), doc XIII-1823-07 (nominal/hot-spot/notch stress, mesh rules, FAT classes): https://community.ptc.com/.../XIII-1823-07%20IIW%20Recommendations%20...%202008.pdf (PDF fetch flaky; content cross-confirmed via WebSearch and the Niemi/Fricke designer's guide) — **A**
- Eurocode 3, EN 1993-1-9 *Fatigue* (detail categories / nominal & geometric stress) — **A**
- Ansys Mechanical APDL *Contact Technology Guide* (R2025) (KEYOPTs, FKN/FTOLN/PINB, formulations, interface treatment): https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/pdf/ANSYS_Mechanical_APDL_Contact_Technology_Guide.pdf — **A**
- CONTA174 element reference: https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/ans_elem/Hlp_E_CONTA174.html — **A**
- CONTA178 element reference: https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_elem/Hlp_E_CONTA178.html — **A**
- Ansys *Multibody Analysis Guide* (MPC184 joints): https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/ans_mul/Hlp_G_MULMODCOMPJT.html — **A**
- MPC184 joint element (overview): https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_elem/Hlp_E_MPC184.html ; Revolute/Cylindrical/General joints: https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_elem/Hlp_E_MPC184revo.html — **A**
- Ansys remote point / geometry behavior (Rigid/Deformable/Coupled/Beam): https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/wb_sim/ds_Geometry_Behavior.html — **A**
- Ansys CE/CP/CERIG coupling & constraint equations: http://mechanika2.fs.cvut.cz/old/pme/examples/ansys55/html/guide_55/g-mod/GMOD12.htm ; CP command: https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_cmd/Hlp_C_CP.html — **A**
- Ansys Innovation Space / Knowledge — Update Stiffness (FKN) recommendation: https://innovationspace.ansys.com/knowledge/forums/ — **A**
- Bolt pretension elements: PRETS179 https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_elem/Hlp_E_PRETS179.html ; Ansys Help — Mechanical APDL element reference, PRETS179, and the SLOAD command (ansyshelp.ansys.com, via your licensed Ansys Help) — **A**
- Simcenter/NX Nastran — BOLT/BOLTFOR/BOLTLD: http://www2.me.rochester.edu/courses/ME204/nx_help/en_US/tdocExt/content/7/id677877.xml ; CWELD/CFAST: http://www2.me.rochester.edu/courses/ME204/nx_help/en_US/tdocExt/content/3/id1265513.xml ; CBUSH: http://www2.me.rochester.edu/courses/ME204/nx_help/en_US/tdocExt/content/6/id489896.xml — **A**
- Solid pretensioned bolts SOL101 — Iberisa/Predictive: https://iberisa.wordpress.com/2019/09/15/tornillos-pretensados-con-elementos-solidos-chexa/ — **A**
- Nastran BCTABLE/BCTPARM contact (SOL101): https://www.aerospacengineering.net/how-to-create-contacts-with-a-bctable-card-by-nastran-sol101/ — **A**
- Salerno, L.J. — *Thermal Contact Conductance*, NASA TM 110429 (cryo TCC, 4–300 K): https://ntrs.nasa.gov/api/citations/19970026086 (fetch refused; numbers via WebSearch) — **A**

**NAFEMS (A — independent FE authority)**
- *Practical Modelling of Joints and Connections* (PMJC): https://www.nafems.org/training/e-learning/joints-connections/ — **A**
- R0081 *Benchmark Tests for FE Modelling of Contact, Gapping and Sliding*: https://www.nafems.org/publications/resource_center/r0081/ — **A**
- HT50 *How to Model Bolted and Riveted Joints*: https://www.nafems.org/publications/resource_center/ht50/ — **A**

**Practitioner / peer-reviewed / textbook (B)**
- Shigley's *Mechanical Engineering Design* §8 (preload 0.75/0.90·Fp, nut factor K, joint stiffness/load factor Φ) — Budynas & Nisbett, McGraw-Hill (primary text); cross-check VDI 2230 Part 1 (systematic bolted-joint calculation). Orientation: Wikipedia "Bolted joint", https://en.wikipedia.org/wiki/Bolted_joint — **B**
- Fidelis Engineering — RBE2 vs RBE3 (engine-mass example): https://www.fidelisfea.com/post/what-is-the-difference-between-a-kinematic-rbe2-and-a-distributing-rbe3-coupling-in-fea — **B**
- hiStructural — RBE2 vs RBE3 in Nastran: https://www.histructural.com/post/understanding-rbe2-vs-rbe3-in-nastran — **B**
- Predictive Engineering — *NX Nastran Connection Elements RBE2/RBE3/CBUSH* whitepaper: https://www.predictiveengineering.com/sites/default/files/predictive_engineering_white_paper_on_nx_nastran_connection_elements_rbe2_rbe3_and_cbush_rev-1.pdf — **B**
- When to use RBE2 vs RBE3 — Gantovnik tips: https://gantovnik.com/bio-tips/2020/09/115-rbe3-vs-rbe2/ — **B**
- Niemi, Fricke, Maddox — *Structural Hot-Spot Stress Approach to Fatigue Analysis: Designer's Guide* (Springer): https://link.springer.com/book/10.1007/978-981-10-5568-3 — **B**

**Hertzian contact (analytical cross-check) (A/B)**
- Hertz, H. (1882) — *Über die Berührung fester elastischer Körper* (J. reine angew. Math. 92:156–171) — the original contact-stress theory. — **A**
- Johnson, K.L. (1985) — *Contact Mechanics*, Cambridge University Press — the standard modern reference (E*, R*, a/b, p_max, δ, sub-surface stress, z≈0.48a, τ_max≈0.31 p_max). — **A**
- Shigley's *Mechanical Engineering Design* §3.19 "Contact Stresses" (sphere & cylinder contact, p_max, max-shear depth) — basis of the AmesWeb calculator: https://amesweb.info/HertzianContact/HertzianContact.aspx — **B**
- Contact mechanics — classical non-adhesive solutions (sphere–half-space `a³=3FR/4E*`, two spheres/cylinders `1/R=1/R₁+1/R₂`, parallel-cylinder `p₀=(E*F/πLR)^½`, max shear at `z≈0.49a` for ν=0.33): **primary** = Johnson, K.L., *Contact Mechanics* (Cambridge, 1985), cross-confirmed against the A sources above. Orientation: Wikipedia — *Contact mechanics*, https://en.wikipedia.org/wiki/Contact_mechanics — **C**

**Variationally consistent contact — mortar / dual-Lagrange / Nitsche / patch test (B)**
- Taylor, R.L. & Papadopoulos, P. (1991) — *On a patch test for contact problems in two dimensions*, in Nonlinear Computational Mechanics (Wriggers & Wagner, eds.), Springer — the contact patch test; NTS fails uniform-pressure transmission. — **B**
- Yang, B., Laursen, T.A. & Meng, X. (2005) — *Two-dimensional mortar contact methods for large deformation frictional sliding*, Int. J. Numer. Methods Eng. 62:1183–1225 — NTS drawbacks (fails patch test, degraded convergence); mortar preserves optimal rates. — **B**
- Popp, A. & Wall, W.A. (2014) — *Dual mortar methods for computational contact mechanics — overview and recent developments*, GAMM-Mitteilungen 37(1):66–84 — dual (biorthogonal) Lagrange condensation, semi-smooth Newton, no penalty parameter. — **B**
- Puso, M.A. & Laursen, T.A. (2004) — *A mortar segment-to-segment contact method for large deformation solid mechanics*, Comput. Methods Appl. Mech. Eng. 193:601–629 — segment-to-segment, patch-test-passing tractions. — **B**
- McDevitt, T.W. & Laursen, T.A. (2000) — *A mortar-finite element formulation for frictional contact problems*, Int. J. Numer. Methods Eng. 48:1525–1547 — variationally consistent contact pressures. — **B**
- Gitterle, M. et al. (2010) — *Finite deformation frictional mortar contact using a semi-smooth Newton method with consistent linearization*, Int. J. Numer. Methods Eng. 84:543–571 — single-loop treatment of all nonlinearities. — **B**
- Nitsche, J. (1971) — *Über ein Variationsprinzip zur Lösung von Dirichlet-Problemen bei Verwendung von Teilräumen, die keinen Randbedingungen unterworfen sind*, Abh. Math. Sem. Univ. Hamburg 36:9–15 — origin of Nitsche's method (later applied to contact/embedded interfaces, e.g. Chouly et al.). — **B**
- Madhusudana — *Thermal Contact Conductance* (Springer); cryo TCC studies (ScienceDirect, ALBA synchrotron): e.g. https://www.sciencedirect.com/science/article/abs/pii/S1359431122013424 — **B**
- FEA Tips — contact types: https://featips.com/2025/03/31/ansys-contact-types-explained-which-one-to-choose-and-why-it-matters/ ; contact formulations: https://featips.com/2022/07/13/ansys-contact-formulations-which-one-to-use/ ; contact settings (FKN/FTOLN/pinball): https://featips.com/2022/09/27/ansys-contact-settings-explained/ — **B**
- SimuTech / Ozen (contact modeling intro): https://simutechgroup.com/resources/blog/understanding-contacts-in-ansys-mechanical/ ; https://blog.ozeninc.com/resources/understanding-contacts-in-ansys-mechanical — **B**
- Mechead — Ansys contact behaviours/formulations & chatter: https://www.mechead.com/ansys-contact-behaviours-formulations/ — **B**
- Bolt pretension in Ansys Workbench — FEA Tips/Wassee: https://wassee.wordpress.com/2021/04/10/a-guide-to-applying-bolt-pretension-preload-in-ansys-workbench/ — **B**

**Secondary / corroborating (C)**
- Thermal contact conductance (paths, vacuum, orders of magnitude) — **primary** = Madhusudana, *Thermal Contact Conductance* (Springer); Yovanovich correlations (Waterloo MHTL). Orientation: Wikipedia — *Thermal contact conductance*, https://en.wikipedia.org/wiki/Thermal_contact_conductance — **C**
- Fatigue (S-N method) — **primary** = Shigley §6; Dowling, *Mechanical Behavior of Materials*. Orientation: Wikipedia — *Fatigue (material)*, https://en.wikipedia.org/wiki/Fatigue_(material) — **C**
- nuclear-power.com — bare-metal h_c values (Al–Al ~3,640; SS–SS ~3,000 W/m²·K) — **C**
- Altair HyperMesh/OptiStruct — Nastran connector types & CBUSH: https://2022.help.altair.com/2022/hwdesktop/hm/topics/pre_processing/connectors/nastran_connector_types.htm ; CBUSH bulk entry: https://2021.help.altair.com/2021/hwsolvers/os/topics/solvers/os/cbush_bulk_r.htm — **C**
