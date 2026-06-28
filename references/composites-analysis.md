# Composite Analysis, Damage & Sandwich/Draping/Environment — Practitioner Brief

Dense, web-sourced best-practices reference for the **analysis, damage-progression, regularization, sandwich, draping and environmental** side of composite structural simulation. Generalizable across Ansys / Abaqus / LS-DYNA / Simcenter / COMSOL. Numbers are practitioner rules-of-thumb cross-verified against CMH-17, the criterion authors (Hashin / Puck / LaRC), Bažant crack-band theory, and standard sandwich-design references (HexWeb / MIL-HDBK-23 / Zenkert). Treat every number as a default to confirm against the governing program spec, not a law of nature.

> **Governing rule:** The constitutive layer (CLT/ABD, the failure *criteria* and their strengths, CZM traction-separation numbers) lives in **`material-modeling.md` §5–§6** — do not re-derive it here. This file is the **workflow**: which failure philosophy governs, how progressive damage actually runs and stays mesh-objective, how delamination is set up, how sandwich modes are sized, how as-draped angles change everything downstream, and what environment does to the allowables. A first-ply margin from a perfect criterion is still wrong if the laminate is mis-oriented by draping, the mesh isn't regularized, or the hot-wet corner wasn't checked.

**See also:** `material-modeling.md` §5 (Hashin/Puck/LaRC criteria, lamina strengths, CZM/VCCT constitutive numbers, GISSMO regularization for metals), §6 (CLT/ABD, B-coupling, effective laminate CTE); `fracture-mechanics.md` (VCCT/CZM energy-release, mixed-mode B-K, J/G, crack-tip mesh); `buckling-stability.md` (sandwich/panel/skin buckling, knockdown factors, imperfection seeding); `meshing-convergence.md` (free-edge singularity, mesh sensitivity gate); `vv-uq.md` (allowables basis, validation discipline).

---

## 0. Mental model and workflow order

A composite analysis is a **stack of decisions**, each of which can silently invalidate the next:

1. **Idealization** — layered shell vs continuum/stacked solid vs solid-with-cohesive (sets whether interlaminar stress and delamination are even *visible* to the model).
2. **Orientation reality** — nominal angles vs **as-draped/as-steered** angles mapped element-by-element (sets stiffness, strength *and* CTE).
3. **Failure philosophy** — first-ply (FPF) vs progressive damage (CDM) vs last-ply (LPF) (sets what "the answer" means: a conservative margin or an ultimate-strength prediction).
4. **Regularization** — characteristic-length / fracture-energy scaling whenever softening is active (sets whether the answer is mesh-objective or a mesh artifact).
5. **Environment** — which hot-wet / cold-dry corner governs, with knockdowns applied to the matrix-dominated allowables.
6. **Verification** — ply-by-ply review, mesh-sensitivity study, energy/momentum balance for explicit, correlation to coupon/element tests.

Top systemic mistake: predicting *ultimate* strength with a *first-ply* criterion (or vice versa). Second: running progressive damage **without** length/energy regularization and reporting a single mesh. Third: feeding **nominal** ply angles into a part that was draped over double curvature.

---

## 1. Failure philosophy — first-ply vs progressive (CDM) vs last-ply, and when each governs

| Philosophy | What it predicts | Cost / complexity | Use when |
|---|---|---|---|
| **First-ply failure (FPF)** | Lowest load at which *any* ply reaches a failure criterion | Cheap — linear/static + criterion post-process | Quick margins, preliminary sizing, conservative design point, fatigue/durability initiation, certification by **no-first-ply-at-limit** philosophy |
| **Progressive damage / CDM** | Load–response *through* damage to **ultimate (last-ply, LPF)** | Expensive — nonlinear, softening, regularization, often arc-length/explicit | Ultimate strength, crashworthiness, **BVID residual strength / damage tolerance**, notched/open-hole strength, post-buckled strength |
| **Last-ply failure (LPF)** | Total laminate collapse (all load-carrying plies failed) | = endpoint of CDM | Ultimate-strength reserve factor when redistribution after first ply is allowed |

**How to choose.** FPF is the right *design* point for many primary structures (especially matrix-cracking-sensitive or fatigue-critical parts — once the matrix cracks, the durability clock starts). But FPF is **over-conservative for ultimate strength**: a laminate routinely carries far more load after the first (usually matrix/transverse) ply fails, because load sheds to the fibers and to neighbouring plies. When the deliverable is the *ultimate* load — open-hole compression/tension (OHC/OHT), filled-hole, bearing, crush energy, residual strength after impact — you **must** run progressive damage to capture redistribution. Reporting an FPF number as if it were ultimate wastes structure; reporting a CDM ultimate where the design philosophy forbids matrix cracking is non-conservative. State which philosophy the program requires. *(Confidence: high — this FPF↔LPF gap is foundational in CMH-17 and every progressive-failure benchmark, e.g. the World-Wide Failure Exercise.)*

**Ply-discount (legacy) vs continuum damage.** The oldest progressive method is **sudden ply discount**: when a ply fails a criterion, zero (or strongly reduce) the relevant moduli in one step and re-solve. It is simple and still used for quick LPF estimates, but the instantaneous stiffness drop causes convergence cliffs and is mesh/load-step sensitive. Modern practice uses **continuum damage mechanics (CDM)** with *gradual* energy-based softening (below), which is both more physical and more robust.

---

## 2. Continuum damage mechanics (CDM) — the progressive-damage engine

**Damage variables.** A 2-D (in-plane, plane-stress shell) CDM model carries **four mode-specific damage variables**, each in [0,1] (0 = intact, 1 = fully failed):

| Variable | Mode | Driven by | Physical event |
|---|---|---|---|
| **d_ft** | Fiber tension | σ₁₁ > 0 mode of Hashin/Puck/LaRC | Fiber rupture |
| **d_fc** | Fiber compression | σ₁₁ < 0 mode | **Kink-banding** (see §4) |
| **d_mt** | Matrix tension | σ₂₂ > 0 / shear mode | Transverse/matrix cracking |
| **d_mc** | Matrix compression | σ₂₂ < 0 / shear mode | Matrix crushing / shear failure |

3-D solid CDM adds through-thickness (σ₃₃, τ₁₃, τ₂₃) modes. Each variable degrades the relevant entries of the ply stiffness C(d): fiber damage knocks down E₁ (and coupling), matrix damage knocks down E₂ and G₁₂; a shear-damage variable (or coupling of d_mt/d_mc into G₁₂) handles in-plane shear softening. Damage is **irreversible and monotonic** (it does not heal on unload; unloading returns to origin with the degraded secant stiffness).

**Damage activation.** A mode "initiates" when its Hashin/Puck/LaRC index reaches 1 (criteria and strengths in `material-modeling.md` §5). Initiation ≠ failure — it starts the *softening* that runs the damage variable from 0 toward 1.

**Energy-based bilinear softening (the standard evolution law).** After initiation, the traction–(equivalent-)displacement response is **bilinear**: linear-elastic rise to the initiation point (σ_eq^0, δ_eq^0), then a linear **softening** branch down to a final displacement δ_eq^f at which d→1 and the ply carries no load in that mode. The area under the full bilinear curve equals the **mode fracture energy G_c** (energy dissipated per unit crack area):

> Area = ½ · σ_eq^0 · δ_eq^f = **G_c / L_c**   (per unit volume, with L_c the characteristic length — see §3)

The damage variable at any state is the standard bilinear form
**d = δ_eq^f (δ_eq − δ_eq^0) / [ δ_eq (δ_eq^f − δ_eq^0) ]**, clamped to its historical max. This is the in-plane analog of the cohesive traction-separation law used at interfaces (`material-modeling.md` §5) — same energy bookkeeping, applied inside the ply rather than between plies.

**Equivalent displacement / equivalent stress.** Because each mode mixes several stress components (e.g. matrix tension couples σ₂₂ and τ₁₂), CDM collapses them into a single scalar **equivalent displacement** δ_eq (typically built from the element characteristic length times an equivalent strain) and a work-conjugate **equivalent stress** σ_eq, so the bilinear law is 1-D per mode. The exact δ_eq definition is model-specific (Lapusta/Maimí/Camanho, the Abaqus built-in Hashin-damage, LS-DYNA MAT54/MAT58/MAT261/MAT262) — **state which model and its δ_eq convention**, because the dissipated energy depends on it.

**Solving.** Softening makes the global response **snap-back-prone** and the tangent stiffness can lose positive-definiteness. Stabilize with: viscous regularization (a small artificial viscosity that adds rate-dependent over-stress — keep the dissipated viscous energy ≪ total, and report it), **arc-length/Riks** (cross-ref `buckling-stability.md` / `solver-numerics.md`), or run it **explicit** (LS-DYNA, Abaqus/Explicit) where snap-back is naturally handled. Element **deletion** on full failure (all modes d→1) is common in explicit crush/impact — track the deleted mass/energy (see §6 and `material-modeling.md` §5 GISSMO note).

---

## 3. Mesh objectivity — characteristic length & fracture-energy regularization (MANDATORY)

This is the single most-skipped step in composite damage analysis, and the composite analog of **GISSMO `LCREGD`** for metals (`material-modeling.md` §5).

**The problem.** Strain-softening **localizes** into a single band one element wide. Without correction, the dissipated energy = (energy density) × (band volume) ∝ element size, so **a finer mesh dissipates less energy and predicts a lower, faster, more brittle failure** — the result does not converge; it diverges. A model that "looks converged" on stress can be wildly mesh-dependent on strength/energy.

**The fix — crack-band / smeared-crack regularization (Bažant & Oh).** Scale the softening branch by the **element characteristic length L_c** so that the *energy per unit crack area* — not per unit volume — is held fixed at the material **G_c**:

> softening slope set so that  ∫ σ_eq dδ_eq = G_c / L_c

so that **G_c × (crack area) is mesh-independent**. As elements shrink, the softening branch becomes correspondingly steeper (smaller δ_eq^f), keeping total dissipation constant. This is exactly the smeared-crack / crack-band method; CDM packages implement it via an **element characteristic length** supplied to the damage-evolution law.

**Characteristic length L_c — definitions and traps.**
- Common definitions: cube-root of element volume (3-D solids), √(element area) (2-D shells), or the length **along the crack-propagation direction** (most correct — the band width the crack actually traverses).
- **Aligned vs skewed cracks:** L_c is exact only when the crack runs along a mesh line. For cracks crossing elements at an angle, the projected band width differs, introducing residual mesh-orientation dependence — a known limitation; mitigate with reasonably **aligned/structured meshes** in the damage zone.
- **Element-size floor (snap-back at the material level):** if L_c is too large, the required softening slope can exceed the elastic slope (δ_eq^f < δ_eq^0), giving a *negative* dissipation / immediate snap-back — i.e. the element is too big to dissipate G_c gradually. The limit is roughly **L_c ≲ c·E·G_c / σ_strength²** with **c = O(1–2) set by the softening law** (c ≈ 2 for linear softening; mode/stiffness-dependent — *derive it for your own CDM law, don't treat "2" as universal*); above it the model is unusable. This caps the *maximum* element size in the damage region — coarse meshes are not just inaccurate, they are *inadmissible*.

**Always report mesh sensitivity.** Run at least two or three mesh densities through the damage event and show the predicted **ultimate load and energy converge** (not the local peak stress, which never converges — like a weld toe or crack tip). A composite-damage result without a mesh-sensitivity study is unverified. *(Confidence: high — Bažant crack-band and the L_c requirement are universal across CDM implementations; the exact L_c definition and the size-floor constant are implementation-dependent.)*

---

## 4. Ply strength refinements: in-situ strength and fiber kinking

**In-situ ply strength (don't use lamina-level transverse/shear strength blindly).** A thin ply *embedded* between plies of different orientation is **stronger in transverse tension and in shear** than the same material tested as a thick or surface ply, because the neighbouring plies constrain matrix-crack onset (the crack cannot grow freely through the thickness). The **in-situ** transverse tensile strength Y_t^is and shear strength S^is increase as the ply gets thinner and depend on whether the ply is embedded or at the surface (free surface = weaker). LaRC and modern Puck-based CDM use in-situ values derived from a fracture-mechanics (energy) argument; **ignoring in-situ effects is over-conservative for thin-ply and thin-interior-ply laminates** (the whole point of thin-ply / spread-tow technology is to delay matrix cracking). Surface plies and thick blocked plies get the lower (lamina) values. *(Confidence: medium-high — direction is robust and standard in LaRC03/04; the exact in-situ multiplier is thickness- and model-dependent.)*

**Fiber compression = kink-banding, not a stress maximum.** Compressive fiber failure is a **micro-buckling / kink-band** instability: slight fiber misalignment + matrix shear softening lets a band of fibers rotate and collapse, at a stress strongly **knocked down by initial misalignment angle and matrix shear nonlinearity**. Consequences for analysis:
- A simple "σ₁₁ < X_c" max-stress check (and even Hashin compression) is **crude** — it misses the misalignment/matrix-shear coupling and tends to be non-conservative or insensitive.
- **Puck** and **LaRC** treat compression on the **fracture action plane** with the misaligned-fiber frame and nonlinear shear — preferred for compression-critical design (OHC, post-buckling).
- Matrix in-plane shear is **strongly nonlinear** (Ramberg-Osgood-like) and feeds kinking — include shear nonlinearity in the ply law for compression and shear-dominated cases, not just linear-elastic + a strength cap.

---

## 5. Delamination — onset vs propagation, and the modeling-fidelity choice

Delamination is an **interlaminar** (between-ply) failure and is invisible to a single-layer shell. Treat onset and propagation as two distinct questions.

**Onset — free-edge and interlaminar stress.** Even far from any hole, **free edges** of a laminate develop a 3-D interlaminar stress state (σ_zz, τ_xz, τ_yz) that is **theoretically singular** at the free-edge/interface corner and peaks at interfaces between dissimilar orientations (e.g. ±45 and 90 interfaces) due to the mismatch in ply Poisson and shear response. This drives delamination *onset* even when in-plane criteria are satisfied.
- **Resolve it with stacked/continuum solids** (several elements through thickness, mesh refined toward the free edge); a layered shell cannot see it (cross-ref `material-modeling.md` §6, `meshing-convergence.md` free-edge singularity).
- **Onset criteria:** a **quadratic interlaminar stress** criterion (e.g. (σ_zz/Z_t)² + (τ_xz/S_xz)² + (τ_yz/S_yz)² = 1, Brewer–Lagace style) over a small averaged distance (the stress is singular, so use a characteristic-distance average or an energy criterion, *not* the peak node — same logic as a weld toe / crack tip).

**Propagation — energy-based, mixed-mode.** Once a delamination exists (or onsets), its growth is governed by **interlaminar fracture energy**, predicted with **CZM or VCCT** under a **mixed-mode** law:
- **B-K (Benzeggagh–Kenane)** is the standard mixed-mode criterion: G_c(ψ) = G_Ic + (G_IIc − G_Ic)·(G_II/G_T)^η, where the **mode mix** ψ = G_II/(G_I+G_II) and η is the B-K exponent (from MMB tests). Power-law mixed-mode is the common alternative.
- **CZM** (cohesive elements/surfaces at the interface) handles **onset + propagation with no pre-crack**; needs ≥3–5 elements in the cohesive zone or G_c is under-integrated — see the constitutive numbers in `material-modeling.md` §5 and the energy/crack-tip treatment in `fracture-mechanics.md`.
- **VCCT** handles **propagation of a defined crack** efficiently (energy release from nodal forces × openings one element behind the front) — accurate but needs a defined crack plane and fine front mesh; cross-ref `fracture-mechanics.md`.

**Modeling-fidelity choice for through-thickness work:**

| Need | Model | Sees interlaminar? | Cost |
|---|---|---|---|
| In-plane stiffness/strength of thin part | **Layered shell** (one element, section = stack) | **No** | Cheap |
| Free-edge / interlaminar stress, no growth | **Stacked solids / continuum shell** (≥several through-thickness) | Yes | Moderate |
| Delamination onset + growth | **Stacked solids + cohesive interfaces** (or continuum-shell + cohesive) | Yes + crack | High |
| Existing crack propagation only | Solids + **VCCT** on the defined plane | Yes (defined) | High |

Rule of thumb: use layered shells for global response and in-plane margins; switch to stacked-solids-plus-cohesive (or sub-model the region, `specialized-analyses.md` submodeling) only where interlaminar failure governs (free edges, ply drops, joints, impact, thick laminates).

---

## 6. Sandwich structures — failure modes WITH sizing formulas

A sandwich = thin stiff **facesheets** + thick light **core** (honeycomb, foam, balsa). Bending stiffness comes from the faces at a large lever arm; the core's job is **transverse shear** and keeping the faces apart and flat. An **equivalent-continuum (homogenized) core** captures global bending/shear to ~5–10% but is **blind to local face/core instabilities** — so always hand-check the local modes below with closed-form sizing, and use a discrete (modeled-cell or detailed) core when a local mode governs. *(Confidence: medium — the coefficients below are classic design-handbook values with documented scatter; treat as sizing checks, confirm against test or detailed FE.)*

| Mode | Physics | Sizing / check | Notes |
|---|---|---|---|
| **Global (overall) buckling** | Whole panel buckles as a thick plate/column | Euler/plate buckling with **shear-corrected** flexural rigidity D (core shear flexibility lowers P_cr vs a solid plate) | Cross-ref `buckling-stability.md`; never use solid-plate D for a sandwich |
| **Shear crimping** | Short-wavelength global buckling **dominated by core shear** (a limiting case of global buckling) | P_cr,crimp ≈ G_c · (t_c) per unit width form; occurs when core shear modulus G_c is low / core thick | Often mistaken for a "material" failure; it is a stability mode set by **core shear stiffness** |
| **Face wrinkling** | Facesheet buckles locally on the elastic foundation of the core (short wavelength) | **σ_wr ≈ 0.5·(E_f · E_c · G_c)^⅓** (anti-/symmetric wrinkling; coefficient ~0.5, commonly 0.43–0.82 by derivation/BCs) | E_f face modulus, E_c core through-thickness modulus, G_c core shear modulus. The classic Hoff–Mautner / Plantema result. The **face-instability check the homogenized core misses** |
| **Intracell dimpling** (honeycomb) | Face dimples into individual honeycomb **cells** | σ_dimple ≈ k·E_f·(t_f / s)² with s = cell size, t_f = face thickness (k≈2 for fixed-edge plate idealization) | **Cell-size driven** — only matters for honeycomb; foam cores don't dimple |
| **Core shear failure** | Core exceeds its shear strength under transverse load | τ_core = V/(d·b) ≤ τ_core,allow (d ≈ distance between face centroids) | The most common static sandwich failure; check at supports/load introductions |
| **Local indentation / crushing** | Concentrated load punches the face into the core | Face acts as beam/plate on crushable-core foundation; check core compressive (crush) strength + face local bending | Governs at hard points, fasteners, supports; pair with insert/potting design |
| **Face yielding / tension** | Face stress exceeds in-plane allowable | σ_face = M/(d·t_f·b) ≤ X_face | Standard beam stress; usually not the limiter for thin faces |

Design rule: a sandwich must be checked against **all** of these, not just global bending — the governing mode is frequently a **local** one (wrinkling, dimpling, indentation) that a homogenized-core global model never reports.

---

## 7. Draping / fiber-steering — as-manufactured angles change stiffness, strength AND CTE

Nominal stacking angles are an idealization. Forming a flat ply over **double curvature** **shears the fabric** (the tows rotate to accommodate the surface), so the **as-draped fiber angles deviate from nominal**, sometimes by tens of degrees in corners. This is not a detail — it changes the local laminate.

**Kinematic (pin-jointed-net) drape.** The standard fast drape simulation idealizes a woven ply as a **pin-jointed net**: tows are inextensible, crossover points are pin joints, and the fabric accommodates curvature by **trellis shear** (in-plane scissoring) between warp and weft. The model marches the net over the tool surface from a seed point/curve and reports the local **shear (deviation) angle** everywhere. Fast and good for layup feasibility and angle maps; it ignores bending/wrinkling mechanics (for those, use a finite-element drape with fabric constitutive behavior).

**Locking angle.** Trellis shear is benign up to a material-specific **locking angle** (commonly **~45–60°** of shear for typical weaves) at which the tows jam together; beyond it the fabric **wrinkles / buckles out of plane** instead of shearing. Drape results that exceed the locking angle flag a manufacturing problem (wrinkles, bridging) — redesign the ply boundary, add darts/splices, or change the seed.

**Feed as-draped angles back into the structural model.** The deliverable of drape analysis is an **element-wise fiber-orientation field** mapped onto the structural mesh. Using it (instead of nominal angles) corrects:
- **Stiffness** — local A/B/D change with real angles (a "0°" ply at 25° in a corner carries load very differently);
- **Strength** — the failure criteria (§1–§4) see the real angle, so margins shift;
- **CTE** — the **effective laminate CTE is orientation-dependent** (`material-modeling.md` §6), so as-draped angles change thermal strains and warpage — this is the same as-built-anisotropy effect that matters for dimensionally-stable and thermally-loaded structures.

**AFP / fiber steering (automated fiber placement).** Steering tows along curved paths imposes a **minimum steering radius**: too tight a radius causes **tow buckling/wrinkling on the inner edge** and **gaps/overlaps** between courses (which become resin-rich/void defects and stress risers). Steered-tow angle fields must likewise be mapped to the structural model, and the defect content (gaps/overlaps) knocked down per program allowables.

---

## 8. Environment — hot-wet vs cold-dry knockdowns, moisture, through-thickness CTE, T_g

Composite properties are **temperature- and moisture-dependent**, and the dependence is concentrated in the **matrix-dominated** properties. Design checks the **worst environmental corner**, not just room-temperature-dry (RTD).

**The two governing corners.**
- **Hot/Wet (HW, "ETW" elevated-temperature-wet)** — heat + absorbed moisture **plasticize the matrix**: transverse tension/compression, in-plane shear, matrix toughness, **and the glass-transition temperature T_g** all drop. **HW governs compression and any matrix/shear-driven mode** (OHC, bearing, shear panels, kink-banding) and any mode near T_g.
- **Cold/Dry (CD, "CTD" cold-temperature-dry)** — the matrix is stiffest/most brittle and **thermal-residual stresses** from the cure-down mismatch are largest. **CD governs tension, matrix-cracking onset, residual-stress-sensitive and CTE-driven cases.**

**Knockdown factors.** Apply **environmental compensation/knockdown factors** to the matrix-dominated allowables for the governing corner (per **CMH-17** test-derived data — `material-modeling.md` §9). Fiber-dominated tension (X_t) is comparatively insensitive; matrix-dominated Y_t, Y_c, S, and interlaminar G_c can drop substantially HW. *(Confidence: medium — magnitudes are material/resin-system-specific; take values from the program allowables database, not a generic table.)*

**Moisture as a strain (CME).** Absorbed moisture **swells** the matrix, producing a **coefficient of moisture expansion (CME)** strain ε = β·ΔM that is mathematically analogous to thermal strain (β = swelling coefficient, ΔM = moisture-content change). Hygro-elastic analysis adds it alongside thermal strain; like CTE, the **laminate CME is directional** and matters for dimensional stability and for relieving/adding to cure residual stress. Diffusion (Fickian) sets the through-thickness moisture profile and conditioning time.

**The T_g operating-margin gate.** Wet T_g (T_g,wet) is **lower** than dry; the structure's **maximum service temperature must keep a margin below the (wet) T_g** (commonly the design uses T_g,wet, and a service-temperature margin of order tens of °C below it). Running near or above T_g collapses matrix stiffness/strength — a hard design limit, not a knockdown.

**Through-thickness CTE.** Even when the **in-plane** laminate CTE is engineered near zero (quasi-iso or tailored), the **through-thickness (z) CTE is large and positive** (matrix-dominated, ~tens of ppm/°C) — it drives warpage of thick sections, ply-drop residual stress, and bond-line stress at metal interfaces. Do not assume isotropy; compute the CTE tensor from CLT (`material-modeling.md` §6) and carry the z-direction value.

---

## 9. Stacking-sequence design rules (the layup hygiene that prevents most pathologies)

These rules keep the laminate well-behaved before any analysis number is trusted:

- **Symmetric** about the mid-plane → **B = 0** (no extension–bending coupling), so in-plane loads don't warp the part and cure-down warpage is minimized (`material-modeling.md` §6). The default for almost all structure.
- **Balanced** (equal numbers of +θ and −θ plies) → **no extension–shear coupling** (A₁₆ = A₂₆ = 0); load doesn't shear the laminate. Symmetric-and-balanced is the standard.
- **10% rule** — keep **≥10% of plies in each of the four standard directions (0, +45, −45, 90)** to avoid a matrix-dominated direction and to give damage-tolerant, repairable, robust behavior. (Some programs use 8% or directionally-tailored variants.)
- **Block limits** — do **not block more than ~3–4 same-angle plies together**; thick blocks of one orientation concentrate interlaminar stress at the block edges and promote **delamination and large matrix cracks** (and reduce in-situ strength, §4).
- **±45 grouping / surface plies** — favor ±45 plies near the surface for impact, handling and surface-strain robustness; group +θ/−θ adjacently where shear-coupling control is needed.
- **Ply-drop taper** — drop plies **gradually**, dropped-ply taper ratio **≤ ~1:10 to 1:20** (one ply terminated per 10–20 thickness of run-out length), drop interior plies (not surface), and stagger drop locations — abrupt drops are delamination initiation sites and stress risers under fatigue. *(Confidence: medium — ratios are common-practice ranges; confirm against the program's ply-drop spec.)*
- **Disorientation** — minimize the **angle jump between adjacent plies** (avoid 0 next to 90); large mismatches maximize interlaminar stress at the interface (the same physics as free-edge stress, §5).

A layup that violates these is not "wrong" everywhere, but it loads the analysis with avoidable coupling, residual stress and delamination risk — fix the layup before chasing the FE result.

---

## 10. Verification gates (composite analysis)

- **Right idealization for the question** — layered shell cannot report interlaminar/free-edge stress or delamination; if those govern, you need stacked solids (± cohesive) or a sub-model (§5).
- **As-draped / as-steered orientations** mapped element-wise where curvature or steering is significant — not nominal angles (§7); check no element exceeds the locking angle / min steering radius.
- **Failure philosophy stated and matched** — FPF for conservative/initiation margins, CDM→LPF for ultimate strength; don't report one as the other (§1).
- **Mesh-objectivity proven** — characteristic-length / G_c regularization active whenever softening runs; **mesh-sensitivity study** showing ultimate load & energy converge; element size below the snap-back floor (L_c ≲ c·EG_c/σ², c = O(1–2) law-dependent; §3). A CDM result on a single mesh is unverified.
- **In-situ strength and compression model appropriate** — in-situ Y_t/S for thin embedded plies; Puck/LaRC (not bare max-stress/Hashin) for compression/kinking-critical cases (§4).
- **Delamination set up correctly** — quadratic/energy onset over a characteristic distance (not peak node); CZM zone resolved by ≥3–5 elements; mixed-mode B-K/power-law with MMB-fitted exponent (§5; numbers in `material-modeling.md` §5).
- **Sandwich local modes checked** — wrinkling σ_wr, dimpling, crimping, core shear and indentation by closed form even when a homogenized-core global model is used (§6).
- **Governing environmental corner analyzed** — HW for compression/matrix/T_g, CD for tension/residual-stress; knockdowns applied to matrix-dominated allowables; through-thickness CTE carried; service temperature margin below wet T_g (§8).
- **Explicit (crush/impact) energy balance** — hourglass <5–10%, deleted (eroded) element mass/energy small and tracked, total energy ≈ constant (cross-ref `solver-numerics.md`); re-run refined to prove insensitivity.
- **Correlated to test** — coupon (UD/laminate strengths, DCB/ENF/MMB for G_c), then **element/building-block** (OHT/OHC, bearing, sandwich beam) before trusting a structural prediction (CMH-17 building-block; `vv-uq.md`).

---

## SOURCES

Progressive damage / CDM, equivalent displacement, characteristic-length regularization:
- 3D Hashin progressive damage (CDM + cohesive, equivalent displacement, characteristic-length regularization), MDPI Materials 2024: https://www.mdpi.com/1996-1944/17/21/5176
- Hashin damage in Abaqus — characteristic element length for energy regularization: https://caeassistant.com/blog/hashin-failure-criteria-hashin-damage-abaqus/
- Puck progressive failure (damage-coupled FE), Composite Structures: https://www.sciencedirect.com/science/article/abs/pii/S0263822314005807
- Bažant & Oh, crack-band theory for concrete/quasi-brittle (the smeared-crack regularization composites inherit), Matériaux et Constructions 1983.

In-situ strength, fiber kinking, LaRC / Puck:
- LaRC criteria (in-situ strengths, nonlinear shear, fiber kinking on the action plane), PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC9697538/
- Camanho et al., in-situ effect & LaRC03/04 (NASA/TM) lineage — fracture-mechanics derivation of in-situ Y_t, S.
- Puck & Schürmann, action-plane (inter-fiber) failure and kinking, Composites Science and Technology.

Delamination onset / propagation, mixed-mode:
- VCCT vs CZM for delamination propagation — Liu et al., *Aerospace Systems* 6:621–632 (2023): https://doi.org/10.1007/s42401-023-00231-8
- Benzeggagh & Kenane (B-K) mixed-mode criterion, Composites Science and Technology 1996.
- Cohesive models for damage evolution in laminated composites — Camanho, Dávila & de Moura, *Int. J. Fracture* (2005): https://doi.org/10.1007/s10704-005-4729-6
- (Cross-ref) CZM/VCCT constitutive numbers in `material-modeling.md` §5; J/G and crack-tip mesh in `fracture-mechanics.md`.

Sandwich failure modes & sizing:
- Hoff & Mautner / Plantema — face wrinkling σ_wr ≈ 0.5(E_f E_c G_c)^⅓ lineage; Zenkert, *An Introduction to Sandwich Construction*.
- HexWeb / Hexcel honeycomb sandwich design guide (wrinkling, dimpling, crimping, core shear, indentation); MIL-HDBK-23.

Draping / fiber steering:
- Kinematic (pin-jointed-net) drape & locking angle — composites manufacturing texts; ESAComp / Simcenter Laminate Composites drape documentation.
- AFP fiber-steering minimum radius, tow buckling and gap/overlap defects — automated fiber placement literature.

Environment, moisture (CME), T_g, allowables, building-block:
- CMH-17 (Composite Materials Handbook) — environmental knockdowns, hot-wet/cold-dry, allowables, building-block test methods (also cited `material-modeling.md` §9).
- Springer/handbook treatments of coefficient of moisture expansion (CME) and Fickian moisture diffusion in polymer composites.

Stacking-sequence rules:
- CMH-17 and aerospace laminate-design guidelines — symmetric/balanced, 10% rule, block limits, ply-drop taper, disorientation.
