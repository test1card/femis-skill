# Fracture mechanics — practitioner-grade analysis brief

Scope: the **analysis and post-processing discipline** of cracked bodies — **linear-elastic fracture mechanics (LEFM)**, **elastic-plastic fracture mechanics (EPFM)**, stress-intensity / J extraction, crack-tip meshing, the contour/domain-integral verification gate, the **method-selection problem** (contour integral vs VCCT vs XFEM vs CZM vs automated remesh growth), **fatigue crack growth (FCG)**, and **mixed-mode growth direction**. Cross-verified against the Ansys Mechanical APDL Fracture Analysis Guide (`CINT`/SMART), the Abaqus contour-integral / XFEM documentation, and the ASTM E08 fracture-test standards. Numbers are method conventions / industry rules of thumb; confirm against your installed version and the governing certification standard. Citations are bracketed `[n]` → SOURCES at end; `[VERIFIED-web]` = cross-checked against multiple public sources, `[DOCS-ONLY]` = derived from a single vendor manual or standard.

The governing rule for the whole topic: **fracture is not a stress-allowable problem — the crack-tip stress is singular and never converges.** You drive the analysis with a **field parameter computed from an integral over a region away from the tip** (K, G, or J), verify it is **path-independent**, and compare it to a **material toughness** (K_IC, J_IC, J-R curve) — never to a peak nodal stress. Choosing the wrong driving force (K where the tip has yielded) or reading the singular tip stress instead of the integral are the two errors that invalidate most first-time fracture runs.

---

## 1. LEFM core relations — when K is the right driving force

Linear-elastic fracture mechanics applies when the crack-tip plastic zone is **small compared to the crack length, ligament, and all in-plane dimensions** (small-scale yielding, SSY). The crack-tip stress field is then a one-parameter family governed by the **stress-intensity factor K**.

- **Crack-tip asymptotic field.** σ_ij ≈ **K/√(2πr)** · f_ij(θ) + **T-stress** + O(√r). The leading singular term scales as **1/√r**; K sets its amplitude. The **T-stress** is the first non-singular (constant) term and sets **in-plane constraint / biaxiality**. [VERIFIED-web]
- **Three modes.** Mode I (opening), Mode II (in-plane shear / sliding), Mode III (out-of-plane shear / tearing). Each has its own K_I, K_II, K_III.
- **Energy release rate G** (Irwin) — the energy available per unit new crack area:

> **G = K²/E′**, with **E′ = E** (plane stress) or **E′ = E/(1−ν²)** (plane strain), for Mode I. General mixed mode: **G = K_I²/E′ + K_II²/E′ + K_III²/(2μ)** (μ = shear modulus). [VERIFIED-web]

- **J = G in the linear-elastic limit.** The J-integral reduces to G when the response is elastic; this equivalence is the bridge between LEFM and EPFM (§2). [VERIFIED-web]
- **Fracture criterion (LEFM).** Crack advances when **K_I ≥ K_IC** (Mode-I plane-strain fracture toughness, ASTM **E399**), or an equivalent mixed-mode K_eq ≥ K_C (§7). Toughness is a **material/temperature/thickness** property; thin sections show higher apparent toughness (plane stress, K_C > K_IC) — report the constraint state.

**T-stress and constraint (why apparent toughness moves).** Two specimens with the same K can fail at different loads if their **constraint** differs. A high (positive) T-stress raises crack-tip triaxiality → lower apparent toughness; a strongly **negative T-stress loses constraint → raises apparent toughness**. For transferring toughness from a lab specimen to a structure, report a **two-parameter** characterization — **K–T** (elastic) or **J–Q** (elastic-plastic, §2). Ignoring constraint is the classic reason a "safe" component fails below its handbook K_IC, or a "cracked" structure survives far past it. [VERIFIED-web]

| Quantity | Symbol | Role | Valid regime |
|---|---|---|---|
| Stress-intensity factor | K_I, K_II, K_III | amplitude of 1/√r singular field | LEFM / SSY |
| Energy release rate | G | energy per unit crack area; G=K²/E′ | LEFM (=J elastic) |
| T-stress | T | constant in-plane term; sets constraint | LEFM constraint |
| J-integral | J | nonlinear energy release rate / HRR amplitude | LEFM **and** EPFM |
| Constraint parameter | Q | deviation of tip field from SSY reference | EPFM constraint |

---

## 2. EPFM — when K fails and J takes over

When the plastic zone is **no longer small** (the tip yields appreciably relative to the ligament), the 1/√r field and K **lose meaning** (large-scale yielding, LSY). The driving force becomes the **J-integral** — Rice's path-independent contour integral that equals the nonlinear energy release rate and the amplitude of the **HRR** (Hutchinson–Rice–Rosengren) crack-tip field for a power-law-hardening material. [VERIFIED-web]

- **J is valid in both regimes.** Use J as the default extraction even for elastic problems (it returns G); switch your *interpretation* to EPFM when plasticity grows. **K is only trustworthy under SSY.**
- **LSY check (the regime gate).** Estimate the plastic-zone size r_p ≈ (1/2π)(K/σ_Y)² (plane stress) or (1/6π)(K/σ_Y)² (plane strain). If r_p is more than a small fraction (~1/50–1/10) of the crack length / ligament, you are **out of LEFM** — report J, not K. ASTM **E399** validity for K_IC has explicit thickness/ligament size requirements (B, a ≥ 2.5(K_IC/σ_Y)²); if they fail, the test is K_Q (invalid K_IC) → use J-based **E1820**. [VERIFIED-web]
- **J-R (tearing-resistance) curve.** Ductile materials do not fail at a single J — they tear stably along a rising **J vs Δa** curve (ASTM **E1820**). Initiation toughness **J_IC** (≈ J at the 0.2 mm-offset blunting line) and the **tearing modulus** T_R = (E/σ_0²)(dJ/da) characterize stable-vs-unstable tearing. Instability when the applied dJ/da exceeds the material's. [VERIFIED-web]
- **CTOD / δ** — crack-tip opening displacement (ASTM E1820 / BS 7448) is an alternative EPFM parameter (δ ≈ J/(m σ_Y), m≈1–2); common in weld/structural-integrity (BS 7910, FAD/R6) assessments.
- **J–Q constraint.** The EPFM analog of K–T: Q measures how far the actual tip field deviates from the high-constraint SSY reference. Transfer toughness on a **J–Q locus**, not single-parameter J, for shallow cracks / thin sections / tension-dominated geometries. [VERIFIED-web]
- **Brittle-transition statistics.** In the ductile-to-brittle transition of ferritic steels, toughness is **scatter-dominated and size-dependent**; ASTM **E1921 master curve** characterizes the median K_Jc(T) via the reference temperature **T_0** and a Weibull (weakest-link) distribution — use it instead of a single K_IC for transition-region steels. [VERIFIED-web]

> **Decision: K or J?** SSY (small plastic zone, brittle/high-strength, thick section) → **K / K_IC**, with T for constraint. LSY (ductile, thin, tension, hot) → **J / J-R**, with Q for constraint. Transition-region ferritic steel → **E1921 master curve**. When unsure, compute **J** (it degrades gracefully to G) and check the LSY criterion.

---

## 3. SIF / J extraction methods — accuracy order and the path-independence gate

All robust methods extract the driving force from a **region integral away from the singular tip**, not from the tip stress itself. Listed best-to-worst for accuracy:

1. **Interaction (M-) integral** — a domain/volume integral that superposes the actual field with an **auxiliary** asymptotic field to **separate K_I, K_II, K_III individually** and to recover the **T-stress**. Most accurate, path-independent, mixed-mode-capable. Generic invocation: a contour-integral request of type "SIFS" (stress-intensity factors) and "TSTRESS". This is the method of choice for **stationary cracks** where you want mode-resolved SIFs. [DOCS-ONLY]
2. **J via the domain / equivalent-domain integral (EDI)** — converts Rice's line integral to an **area integral (2-D) / volume integral (3-D)** over a ring of elements using a weighting (q-) function. Far more accurate and mesh-robust than evaluating a single contour, because it averages element-integration-point data over a region. The default J method in modern solvers. [VERIFIED-web]
3. **Displacement-correlation / extrapolation (DCT)** — fits the near-tip opening displacements to the analytical 1/√r form to back out K. **Legacy, least accurate**, strongly dependent on having **quarter-point singular elements** (§4) and on the chosen correlation radius. Acceptable as a sanity cross-check, not as the primary result.
4. **VCCT (Virtual Crack Closure Technique)** — computes **G** (and, via G=K²/E′, K) from the **nodal forces at the tip × the crack-opening displacements one element behind the tip**, on the principle that the energy to close a crack increment equals the energy to extend it. Excellent for **defined crack planes** (interfaces, delamination) where the crack advances **self-similarly** along a known path; gives mode-separated G_I, G_II, G_III directly from the normal/shear force–displacement products. Requires a node-conforming crack plane and a uniform small element behind the tip. **Constitutive/G_c side of VCCT lives in `material-modeling.md` §5 — cross-link, do not duplicate.** [VERIFIED-web]

### The #1 verification gate — contour / path independence

> **Always request ≥ 3–6 contours (rings) and check that J (or K) is path-independent.** For a valid LEFM/EPFM extraction the **outer contours agree to within a few percent**. The **innermost 1–2 contours are routinely discarded** (they hug the singular tip and the distorted first element ring and are inaccurate by design); the converged value is read from the **outer, stabilized contours**. [VERIFIED-web]

| Contour symptom | Likely cause | Action |
|---|---|---|
| Outer contours agree ≤ ~2–5 % | converged | report the outer-contour value (drop ring 1–2) |
| Large spread / monotonic drift across rings | mesh too coarse, plasticity reaching the integration domain, or domain crossing a load/contact | refine tip mesh; enlarge the crack-front region; check the integral domain doesn't cut a load |
| First contour wildly off, rest fine | normal — that ring touches the singularity | discard ring 1; use outer rings |
| 3-D: J varies non-physically along the front | not enough elements through thickness, or domain near a free surface / corner singularity | refine along the front; treat free-surface point separately (loses plane-strain constraint) |

Loss of path-independence in EPFM also signals **non-proportional loading or unloading** at the tip (J theory assumes deformation-plasticity / monotonic, proportional loading); if the structure unloads locally, J is no longer rigorously the energy release rate.

---

## 4. Crack-tip mesh — focused rosette and singular elements

The near-tip field is singular, so the mesh must either **reproduce the analytic singularity** (conformal mesh + singular elements) or **avoid needing to mesh it** (XFEM/enrichment, §5). For conformal-mesh contour-integral work:

- **Focused spider / rosette.** Build a **fan of elements collapsed to the crack tip** (in 2-D) or swept along the crack front (3-D), so element edges radiate from the tip and rings are concentric. This is what lets the domain integral average cleanly over rings.
- **Singular (quarter-point) elements** — capture the field without an absurdly fine mesh:

| Crack type | Element trick | Singularity captured |
|---|---|---|
| **LEFM** (elastic) | quadratic element with **mid-side node moved to the 1/4 point** | **1/√r** stress (correct LEFM) [VERIFIED-web] |
| **EPFM** (elastic-plastic) | **collapsed** tip element (degenerate quad/brick) **with quarter-point AND independent/free tip nodes** | stronger **1/r strain** singularity (HRR) [VERIFIED-web] |

The quarter-point trick (Henshaw & Shih / Barsoum) shifts the mid-side node to ¼ of the edge so the isoparametric mapping reproduces the √r displacement → 1/√r strain field exactly with standard quadratic elements. For EPFM, **collapse** one side of the element to the tip and leave the coincident tip nodes **free to move independently** (so the tip can blunt) — this admits the 1/r strain singularity.

- **Ring rules.** Sweep roughly **8–20 elements circumferentially** around the tip (more for mixed mode); first-ring radius **~a/10 to a/20** of the crack length; grade outward smoothly. The domain integral needs **several clean rings** beyond ring 1 to give path independence (§3).
- **3-D crack fronts** want a tube of focused elements swept along the front, refined enough that J varies smoothly along the front; treat **free-surface / corner** points specially (constraint differs).

> **Read J/K from the integral, NOT from the singular tip stress.** Like a re-entrant corner or a weld toe, the **peak tip stress diverges with mesh refinement and never converges** — it is meaningless as an allowable. The contour/domain integral, by contrast, **converges**. (Cross-ref the singularity / non-convergence discussion in `meshing-convergence.md`.) If someone reports "the stress at the crack tip is X MPa," they have mis-run the analysis.

---

## 5. Method-selection decision table — contour vs VCCT vs XFEM vs CZM vs auto-remesh

The single biggest setup decision. Match the method to **what the crack is doing** (stationary vs growing, known plane vs arbitrary path, brittle vs ductile process zone):

| Need | Method | Mesh requirement | Driving force | Notes |
|---|---|---|---|---|
| SIF / J / T at a **stationary, known** crack | **Contour / interaction integral** | conformal focused rosette, quarter-point singular elements | K_I/II/III, J, T | most accurate stationary result; the "measure it" tool |
| **Delamination / interface** crack on a **known plane** | **VCCT** | conformal, node-conforming/tied crack plane, uniform element behind tip | G_I/II/III (→K) | self-similar growth; mode-separated G; G_c side in `material-modeling.md` §5 |
| Crack of **unknown / arbitrary path**, brittle-ish, **no remesh** | **XFEM** (enriched DOF + level sets) | structured mesh; crack is **independent of the mesh** | K/J via enrichment, or damage-initiation criterion | crack propagates through elements; check enrichment radius and that the level-set crack didn't snap to element edges |
| **Ductile tearing** / sizeable **cohesive process zone**, or bond-line | **CZM** (traction–separation, G_c) | cohesive elements/surfaces; **≥ 3–5 elements within the cohesive zone length** | G_c (area under traction-separation) | constitutive law + numbers in `material-modeling.md` §5 — cross-link |
| **Automated static / fatigue crack GROWTH** (3-D, evolving front) | **Auto-remesh growth** (generic "smart"/UMM-style adaptive tet remesh) or **XFEM-LEFM** or **VCCT node-release** | regenerated each step (auto-remesh) or fixed (XFEM/VCCT) | K/G per step → growth law (§6) | remeshing handles arbitrary 3-D fronts and curving; XFEM cheaper but mesh-locked path artifacts; VCCT needs a pre-defined path |

Practical guidance:
- **Stationary assessment** (margin against fracture, ASME/BS 7910 FAD, damage-tolerance K at a flaw) → **contour/interaction integral**. Don't grow anything.
- **Composite/adhesive delamination** → **VCCT** (LEFM, self-similar) or **CZM** (if there is a real process zone / nonlinear softening). VCCT is cheaper and standard for thin tough-adhesive-free interfaces; CZM when the bond softens gradually. See `material-modeling.md` §5 for G_c, penalty stiffness, and the cohesive-zone element-count rule.
- **Arbitrary 3-D growth in metals** → **auto-remesh adaptive growth** is the modern default: it re-meshes a focused mesh around the advancing front each increment, recomputes K along the front, and advances per a fatigue or static criterion (no pre-defined path). **XFEM** avoids remeshing but is most reliable for **brittle, near-planar** growth and can show **mesh-direction bias**; for ductile/curving 3-D cracks the remeshing approach is generally more robust.
- **CZM vs LEFM growth:** use CZM when the **process zone is not small** (ductile, soft adhesive, concrete, composite matrix); use LEFM-based growth (contour/VCCT/XFEM-LEFM) when SSY holds.

---

## 6. Fatigue crack growth (FCG) — Paris and beyond

Once a crack exists, **sub-critical growth under cyclic load** governs damage-tolerant life. Driven by the **stress-intensity range ΔK = K_max − K_min** over a cycle.

### Growth-rate law (the da/dN curve, three regions)

> **Region II (Paris): da/dN = C·(ΔK)ᵐ** — a straight line on log–log axes; C and m are material constants. **Region I:** below the **threshold ΔK_th** the crack does **not grow** (da/dN → 0). **Region III:** as **K_max → K_C** growth accelerates to **fast (unstable) fracture**. [VERIFIED-web]

- **C, m** from ASTM **E647** da/dN tests. Typical metallic m ≈ 2–4. C carries the units (system-dependent) — keep ΔK and da/dN units consistent.
- **ΔK_th** is the fatigue-design analog of an endurance limit; flaws below it are dormant (but **load history can lower it**, see closure).

### Mean-stress / R-ratio (R = K_min/K_max)

The same ΔK is more damaging at higher mean (R) because the crack stays open longer. Corrections, increasing in fidelity:

| Model | Form | Captures |
|---|---|---|
| **Walker** | da/dN = C·[ΔK·(1−R)^(γ−1)]ᵐ (equivalently ΔK_eff = ΔK/(1−R)^(1−γ)) | R-dependence via one extra exponent γ |
| **Forman** | da/dN = C·ΔKᵐ / [(1−R)·K_C − ΔK] | R **and** Region-III instability (K_max → K_C) |
| **NASGRO / Newman** | full sigmoidal: da/dN = C·[(1−f)/(1−R)·ΔK]ᵐ · (1−ΔK_th/ΔK)^p / (1−K_max/K_C)^q | ΔK_th **and** K_C **and** closure (f) — all three regions in one equation |

The **NASGRO equation** (NASA/Newman, the basis of NASGRO® and AFGROW lineage) is the aerospace damage-tolerance standard because it spans all three regions with R-dependence and crack-closure built in. [VERIFIED-web]

### Crack closure (why ΔK_eff < ΔK)

**Plasticity-induced closure** (Elber): the wake of plastically-stretched material behind the tip props the crack faces shut for part of the unloading cycle, so the crack only "feels" load above the opening level K_op. The **effective range ΔK_eff = K_max − K_op < ΔK**, most pronounced at **low R**. Closure (also roughness- and oxide-induced) explains R-dependence and the threshold; the NASGRO f-function is an empirical closure model. [VERIFIED-web]

### Life integration

> **N = ∫(from a₀ to a_crit) da / [C·(ΔK(a))ᵐ]** — integrate the growth law from the **initial flaw a₀** to the **critical size a_crit**, where K_max(a_crit) = K_IC (fast fracture) or the net section yields (plastic collapse), whichever is smaller.

- **ΔK(a)** uses the geometry factor: **ΔK = Y(a)·Δσ·√(πa)**, with Y from handbooks (Tada–Paris–Irwin, Murakami) or FE. Y grows with a → growth accelerates; the integral is usually done numerically with **cycle-by-cycle** or block integration (and **rainflow** + sequence effects for variable amplitude — cross-ref `fatigue-durability.md`).
- **a₀** comes from **NDI capability** (the largest flaw the inspection could miss, damage-tolerance philosophy) or **EIFS** (equivalent initial flaw size back-calculated to fit test life). The choice of a₀ dominates predicted life — state and justify it.
- **Retardation/sequence effects** (overloads enlarge the plastic zone → temporary slow-down) need a retardation model (Wheeler/Willenborg) for spectrum loading; constant-amplitude Paris over-predicts damage after overloads.

---

## 7. Mixed-mode crack growth direction and equivalent K

For a crack under combined K_I/K_II (and K_III), you need both **whether** it grows (criterion) and **which way** it turns (kink angle).

- **Growth direction (kink angle θ_c):**
  - **MTS — Maximum Tangential (hoop) Stress** (Erdogan–Sih): the crack kinks along the direction that **maximizes σ_θθ**; closed-form θ_c from K_I, K_II. The most-used criterion.
  - **Maximum energy release rate (max-G):** crack turns to maximize G of the kinked increment.
  - **K_II = 0 (local symmetry):** the crack reorients until the kinked-tip K_II vanishes (pure local Mode I). MTS and K_II=0 give very similar angles in practice.
- **Equivalent (effective) K for the growth law.** Reduce mixed-mode to a single K_eq feeding da/dN or the fracture check. Forms vary — **state which you use**; a common one:

> **K_eq = (K_I⁴ + 8·K_II⁴)^¼** (one MTS-consistent form); others use √(K_I² + K_II²) or √(K_I² + K_II² + K_III²/(1−ν)). The constants matter — cite the source.

- **Growth under mixed mode** then advances each front point along θ_c by an increment set by da/dN(ΔK_eq) (fatigue) or until K_eq ≥ K_C (static), re-meshing/extending and recomputing the now-rotated mode mix each step (§5 auto-remesh / XFEM). Mode III adds front twisting and lurching ("factory-roof" fracture) — a 3-D effect the planar criteria approximate.

---

## 8. Verification gates (fracture) — run these every time

- **Path-independence of J/K** — ≥ 3–6 contours, outer rings agree to a few %, discard the inner 1–2 (§3). The single most important gate.
- **Right driving force** — LSY check passed (K still valid) or switched to J (§2); for transition-region ferritic steel use E1921, not a single K_IC.
- **Singular-element geometry correct** — quarter-point nodes actually at ¼ edge; collapsed-and-free tip for EPFM; focused rosette with clean rings (§4). And: **J read from the integral, never the tip stress.**
- **Constraint reported** — T-stress (elastic) or Q (plastic) when transferring toughness from specimen to structure; free-surface / thin-section points flagged as low-constraint.
- **VCCT** — self-similar growth on a defined plane; **uniform small element directly behind the tip**; node-conforming crack plane; check the G mode-split is physical.
- **XFEM** — enrichment radius covers the tip field; the **level-set crack did not snap to element edges** (mesh-direction artifact); refine and re-check the path.
- **Auto-remesh growth** — front mesh regenerates cleanly each step (no inverted elements); K varies smoothly along the front; growth increment small enough that the path/mode-mix is converged (halve it and re-check).
- **FCG life** — a₀ source stated (NDI/EIFS); ΔK_th and closure model appropriate for R; spectrum loads rainflow-counted with retardation if overloads present (cross-ref `fatigue-durability.md`); a_crit from min(fast fracture, plastic collapse).
- **Material data provenance** — K_IC/J_IC/J-R from a **valid** ASTM test (E399 size requirements met, or E1820/E1921); C, m, ΔK_th from E647 at the right R and environment.

---

## 9. Condensed quick-reference

- **LEFM:** σ ~ K/√(2πr) + T; **G = K²/E′** (E′=E plane stress, E/(1−ν²) plane strain); fail at K_I ≥ K_IC (E399). Report **T-stress** for constraint.
- **EPFM:** when the tip yields (LSY), **K is invalid → use J** (=G when elastic). J_IC / J-R curve from **E1820**; **J–Q** for constraint; **E1921 master curve** for ferritic transition region.
- **Extraction (best→worst):** interaction/M-integral (separates K_I/II/III + T) > domain/volume J-integral > displacement-correlation > VCCT (interfaces, defined plane). **Always check ≥3–6 contours for path independence; drop the inner 1–2 rings.**
- **Mesh:** focused rosette; **quarter-point** singular elements (1/√r LEFM), collapsed-and-free tip (1/r EPFM); 8–20 elements around the tip, first ring ~a/10–a/20. **Read J from the integral, not the singular tip stress.**
- **Method choice:** stationary K/J/T → **contour/interaction**; interface/delamination → **VCCT** (or **CZM** if real process zone); arbitrary brittle path no-remesh → **XFEM**; ductile/3-D growth → **auto-remesh adaptive**; soft/ductile process zone → **CZM** (constitutive in `material-modeling.md` §5).
- **FCG:** **da/dN = C·ΔKᵐ** (Region II); ΔK_th floor; **Walker / Forman / NASGRO** for R-ratio + closure; **N = ∫da/(C·ΔKᵐ)** from a₀ (NDI/EIFS) to a_crit (K_IC or net yield). **ΔK_eff < ΔK** from plasticity-induced closure.
- **Mixed mode:** kink by **MTS / max-G / K_II=0**; reduce to **K_eq** (state the form); re-evaluate mode mix each growth step.
- **ASTM:** **E399** K_IC, **E1820** J-R/CTOD, **E647** da/dN, **E1921** master curve (T_0).

---

## See also

- `material-modeling.md` **§5** — CZM/VCCT **constitutive** side (traction–separation law, G_c, penalty stiffness, ≥3–5 elements in the cohesive zone) and Hashin/Puck composite failure. **The "what is the material's toughness/cohesive law" half of fracture lives there; this file is the "how do I run the analysis and extract the driving force" half.**
- `fatigue-durability.md` — S-N / ε-N initiation life, rainflow counting, Miner damage, multiaxial and spectral fatigue. **FCG (§6 here) is the propagation half of damage tolerance; initiation life and rainflow live there.**
- `meshing-convergence.md` — the **singularity / non-convergence** discussion (re-entrant corners, weld toes): the same reason the crack-tip stress never converges and must be replaced by an integral parameter.
- `solver-numerics.md` — negative-pivot / indefinite-matrix handling (relevant to softening CZM and unstable crack growth), arc-length/Riks for snap-back during unstable propagation.

---

## SOURCES

Reliability key: **H** = primary vendor theory/user manual, peer-reviewed paper, or standards body (highest); **M** = vendor knowledge-base / reputable practitioner / encyclopedic reference cross-checked; **L** = forum/secondary (corroborative only).

1. Ansys Help — Mechanical APDL *Fracture Analysis Guide* (ansyshelp.ansys.com, via your licensed Ansys Help) — `CINT` contour-integral evaluation (J, SIFS via interaction integral, T-stress, C\*-integral, energy release rate), domain/volume integral, multiple contours, and SMART (Separating Morphing & Adaptive Remeshing) automated crack growth. — **H** (vendor guide). `[DOCS-ONLY]` for the CINT TYPE keyword conventions; method physics `[VERIFIED-web]`.
2. Abaqus Analysis User's Manual — contour-integral evaluation (J based on the domain/area-2-D / volume-3-D integral; **interaction integral** for individual SIFs K_I/K_II/K_III; T-stress), VCCT, and XFEM (enrichment + level sets, crack independent of mesh). Summarized in the engineeringdownloads fracture-mechanics-and-simulation survey. https://engineeringdownloads.com/everything-engineers-need-to-know-about-fracture-mechanics-and-simulation/ — **H/M** (vendor-method survey).
3. J-integral concept & **domain-integral verification (multiple-contour path-independence)** — peer-reviewed/educational treatment of the equivalent-domain integral and contour convergence. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11846709/ — **H**.
4. LEFM relations (K, G = K²/E′ with E′ plane-stress/plane-strain, modes I/II/III, crack-tip 1/√r field, T-stress as first non-singular term) — Anderson, T.L., *Fracture Mechanics: Fundamentals and Applications*, 4th ed. (CRC Press, 2017) (primary); Tada, Paris & Irwin, *The Stress Analysis of Cracks Handbook*, 3rd ed. (ASME). Orientation: Wikipedia *Fracture mechanics* / *Stress intensity factor*, https://en.wikipedia.org/wiki/Fracture_mechanics ; https://en.wikipedia.org/wiki/Stress_intensity_factor — **M** (encyclopedic, cross-checked). `[VERIFIED-web]`
5. J-integral / HRR field / EPFM validity (J as nonlinear energy release rate, valid where K fails under LSY; CTOD) — Rice, J.R. (1968) *A path-independent integral…*, J. Appl. Mech. 35:379 (primary); Hutchinson (1968) & Rice–Rosengren (1968) HRR field; Anderson, *Fracture Mechanics* (as [4]). Orientation: Wikipedia *J-integral*, https://en.wikipedia.org/wiki/J-integral — **M**. `[VERIFIED-web]`
6. Quarter-point / collapsed singular crack-tip elements (Barsoum / Henshaw–Shih; mid-side node at ¼ edge → 1/√r; collapsed-and-free tip → 1/r HRR strain) — Barsoum, R.S. (1976) *On the use of isoparametric finite elements in linear fracture mechanics*, Int. J. Numer. Methods Eng. 10:25 (primary); Henshell & Shaw (1975) IJNME 9:495. Orientation: https://en.wikipedia.org/wiki/Singularity_(mathematics)#Finite_element_method — **M/H**. `[VERIFIED-web]`
7. VCCT (Virtual Crack Closure Technique) — Rybicki & Kanninen (1977) *Eng. Fract. Mech.* 9:931 (primary); Krueger, R. (2004) *Virtual crack closure technique: history, approach, and applications*, Appl. Mech. Rev. 57:109 (review). Orientation: https://en.wikipedia.org/wiki/Virtual_crack_closure_technique — **M**. `[VERIFIED-web]`
8. Paris law / FCG regions (da/dN = C·ΔKᵐ; threshold ΔK_th; Region-III instability) and crack closure (Elber, plasticity-induced; ΔK_eff) — Paris & Erdogan (1963) *J. Basic Eng.* 85:528 (primary); Elber, W. (1970) *Fatigue crack closure under cyclic tension*, Eng. Fract. Mech. 2:37; ASTM E647 (da/dN test). Orientation: Wikipedia *Paris' law* / *Crack closure*, https://en.wikipedia.org/wiki/Paris%27_law ; https://en.wikipedia.org/wiki/Crack_closure — **M**. `[VERIFIED-web]`
9. **NASGRO / Forman / Walker** crack-growth equation lineage (NASA/Newman; R-ratio, closure f-function, ΔK_th & K_C limits in one sigmoidal law; AFGROW lineage) — Forman & Mettu (1992, ASTM STP 1131); Newman, J.C. (1984) closure model; NASGRO Reference Manual (NASA-JSC) & AFGROW documentation. Orientation: https://en.wikipedia.org/wiki/Crack_growth_equation — **M/H**. `[VERIFIED-web]`
10. Mixed-mode growth direction — Erdogan & Sih (1963) *On the crack extension in plates under plane loading and transverse shear*, J. Basic Eng. 85:519 (primary, MTS criterion); maximum-energy-release-rate and K_II=0 (local symmetry) criteria. Orientation: https://en.wikipedia.org/wiki/Fracture_mechanics#Mixed-mode_fracture — **M**. `[VERIFIED-web]`
11. ASTM fracture-toughness & FCG standards — **E399** (plane-strain K_IC, size requirements B,a ≥ 2.5(K_IC/σ_Y)²), **E1820** (J-R / J_IC / CTOD), **E647** (da/dN), **E1921** (master curve, reference temperature T_0). ASTM E08 committee standards. https://www.astm.org/e0399-23.html ; https://www.astm.org/e1820-23.html ; https://www.astm.org/e0647-15e01.html ; https://www.astm.org/e1921-23.html — **H** (standards body). `[VERIFIED-web]`
12. Constraint / two-parameter fracture — **K–T** and **J–Q** theory: O'Dowd & Shih (1991/1992) *Family of crack-tip fields characterized by a triaxiality parameter (Q)*, J. Mech. Phys. Solids 39:989 & 40:939 (primary); Williams, M.L. (1957) T-stress; Anderson, *Fracture Mechanics* (constraint chapter). Orientation: Wikipedia *T-stress*, https://en.wikipedia.org/wiki/T-stress — **M/H**. `[VERIFIED-web]`
