# Plasticity & Inelastic Assessment — Design-by-Analysis Reference

A practitioner's reference for the **assessment side** of inelastic structural analysis: cyclic-plasticity regimes (shakedown / ratcheting), the Bree diagram, limit-load / plastic-collapse analysis, the ASME VIII-2 Part 5 **elastic-plastic route**, **stress linearization & categorization** (the FE→code-limit bridge), forming (springback / FLD), and creep-plasticity relaxation. Generalizable across **Ansys**, **Abaqus**, **Simcenter / MSC Nastran**, and **COMSOL**.

> **Scope split — read this first.** The **constitutive** side (yield criteria, isotropic/kinematic/Chaboche hardening, true-vs-engineering stress, Considère, Johnson-Cook, Cowper-Symonds, creep laws, ductile-damage GTN/GISSMO) lives in **`material-modeling.md` §2 (plasticity), §4 (creep/viscoelasticity), §5 (damage)** — this file does **not** repeat it; it cross-links. The **SCL mechanics** (membrane/bending/peak decomposition, P_m/P_b/F, SCL meshing) live in **`meshing-convergence.md` §6–§7** — this file cross-links those and adds the **stress-categorization + code-limit layer** on top (what category each stress is, what allowable it is compared to, and why you linearize a singularity at all).
>
> **Governing rule.** A model is only as good as the *mode it was validated against that it did not see*. Ratcheting and shakedown predictions are **hyper-sensitive to the kinematic-hardening parameters** — never trust a Chaboche fit to one stabilized loop to predict the ratchet strain; validate on an unseen ratcheting test (material-modeling §10).

Each substantive claim is cross-checked against ≥2 authoritative sources (ASME BPVC III & VIII-2 Part 5 + Annex 5.A, Bree 1967 / König shakedown theory, NAFEMS, EN 13445 Annex B, recognized practitioners). Citations are inline as `[n]`; the source list with reliability ratings is at the end.

---

## 0. The one-paragraph mental model

An elastic FE stress at a discontinuity (a nozzle corner, a fillet, a clamp) is **not a number you compare to an allowable** — it can be unbounded (a singularity, meshing-convergence §6.1) and it mixes stresses of *completely different consequence*. The whole discipline is: **(1)** decide whether the inelastic behavior is benign (the structure yields once, then responds elastically forever = **shakedown**) or malignant (it accumulates strain every cycle = **ratcheting**, or it collapses = **plastic collapse**); **(2)** turn the raw field into **categorized** stresses (primary, which can cause collapse; secondary, which is self-limiting; peak, which only matters for fatigue) along a **Stress Classification Line**, and compare each category to its own allowable; or **(3)** skip categorization entirely and run a full **elastic-plastic** model with factored loads, where *convergence itself* is the collapse check. The two recurring blunders: comparing **raw von Mises to S** (wrong allowable, wrong category — a top reason FEA submissions are rejected, meshing-convergence §7), and using **isotropic hardening for cyclic load** (misses Bauschinger, fakes shakedown — material-modeling §2). [S1][S2][S6]

---

## 1. Cyclic-plasticity regimes — shakedown vs ratcheting

Under a **steady primary load** (mechanical, e.g. pressure → constant stress σ_P) combined with a **cyclic secondary load** (usually thermal → cyclic stress range σ_t), an elastic-plastic component settles into one of four regimes. This is the central design distinction for pressure vessels, piping, nuclear components, and anything thermally cycled. [S3][S4][S5]

| Regime | Hysteresis loop | Behavior | Design status |
|---|---|---|---|
| **Purely elastic** | none | stresses stay below yield everywhere, all cycles | safe, trivial |
| **Elastic shakedown** | closes after the first few cycles → a stable *elastic* cycle | initial plastic strain on cycle 1–N, then **no further plasticity** | **the design target** — safe against both ratcheting and LCF (low-cycle fatigue) |
| **Plastic shakedown** (alternating plasticity) | closed but *non-zero-width* stable loop | reversed plasticity each cycle, **no net strain growth** | bounded — but the cyclic plastic strain drives **low-cycle fatigue** (assess with ε-N, see `fatigue-durability.md`) |
| **Ratcheting** (incremental collapse) | **open** loop, drifts each cycle | net plastic strain accumulates every cycle → progressive distortion → **incremental collapse** | **must be excluded** by code |

**Why isotropic hardening hides this.** A purely isotropic model cannot ratchet and cannot reproduce a stable open loop — it artificially predicts shakedown. Reversed/cyclic plasticity needs **kinematic (back-stress) hardening to capture the Bauschinger effect**; ratcheting specifically needs **nonlinear kinematic (Armstrong-Frederick / Chaboche)** with the dynamic-recovery term, optionally with a small isotropic (Voce) component (material-modeling §2). Linear (Prager/Ziegler) kinematic hardening *over-predicts* ratcheting badly. [S1][S5]

**Predicting ratcheting with Chaboche — and validating it.** Calibrate the Chaboche back-stresses from **strain-controlled symmetric loops** (stabilized hysteresis) plus **stress-controlled asymmetric (mean-stress) tests** for the ratchet rate (material-modeling §10). Then:
- Run a **cyclic elastic-plastic** FE analysis (apply the steady primary load, then cycle the secondary load for enough cycles to see whether the strain stabilizes or drifts).
- **Validation gate:** ratcheting is *extremely* sensitive to the kinematic parameters — many parameter sets fit one loop equally well yet predict wildly different ratchet rates. **Predict an unseen ratcheting test** (a different mean stress / amplitude than the fit) and compare the per-cycle strain accumulation. A Chaboche model that only reproduces its own training loop is **unverified for ratcheting** (material-modeling §10). [S1] The two-decay-rate (dual-back-stress) and modified Ohno-Wang / Chaboche-with-threshold variants exist precisely because the basic Armstrong-Frederick rule **over-predicts** uniaxial ratcheting. [S1]

---

## 2. The Bree diagram — the classic shakedown map

The **Bree diagram** (Bree, 1967, for a thin tube under steady internal pressure + cyclic through-wall thermal gradient — the canonical fuel-can/pressure-vessel problem) maps the four regimes onto a plane of **primary stress vs secondary (thermal) stress**, normalized by yield. It is the analytical backbone of the ASME III / VIII-2 ratcheting rules. [S3][S4]

- **Axes:** X = primary membrane stress ratio **X = σ_P / σ_y** (steady mechanical load); Y = secondary stress ratio **Y = σ_t / σ_y** (cyclic thermal-bending range). Both ≤ 1 for the elastic regime in the simplest construction.
- **Regions** (elastic-perfectly-plastic Bree construction):
  - **E** — elastic (low X and Y).
  - **S** — **elastic shakedown** (first-cycle yield, then purely elastic). It lies *above* the elastic limit **X + Y = 1** (the E/S boundary, for X ≤ ½); its *upper* edges are the **reversed-plasticity limit Y = 2** at low X and the **ratchet boundary X·Y = 1** for ½ ≤ X ≤ 1 (the hyperbola running from (½, 2) to (1, 1)).
  - **P** — **plastic shakedown / reversed plasticity** (alternating plasticity, no net growth) — low X with **Y ≥ 2**.
  - **R** — **ratcheting** (forbidden) — beyond the **X·Y = 1** branch at high X.
  - *(These are the distinct curves of the classic elastic-perfectly-plastic Bree construction — not one formula. `X·Y = 1` is the shakedown↔ratchet boundary at high X, **not** a general "shakedown boundary"; reproduce the full diagram for your hardening model before relying on it.)*
- **Reading it:** keep the operating point inside **E** or **S**. The famous lesson is that a *modest* steady primary stress combined with a *large* cyclic thermal stress ratchets even though neither alone would — ratcheting is a **combined-load** phenomenon, which is exactly why thermal transients matter so much in pressure equipment. [S3]
- **Hardening shifts the boundaries:** the textbook Bree diagram is elastic-perfectly-plastic; real hardening (especially kinematic) enlarges the shakedown region. Codes apply the perfectly-plastic Bree limits as conservative bounds, or demonstrate shakedown directly by elastic-plastic FE (§4). [S4][S5]

> **Connection to categorized stress (§5).** The ASME elastic-route ratcheting check **P_L + P_b + Q ≤ 3S_m** *is* the Bree shakedown boundary expressed in categorized-stress language: 3S_m ≈ 2σ_y keeps the secondary (Q) range from driving ratcheting/alternating plasticity. The two views — Bree diagram and the 3S_m rule — are the same physics. [S2][S6]

---

## 3. Limit load & plastic collapse

The **limit load** is the load at which an elastic-**perfectly-plastic** structure forms enough of a plastic mechanism that displacement grows without bound (gross plastic deformation / collapse). It bounds the static strength independent of strain-hardening reserve. [S2][S7]

- **Lower-bound (static) limit analysis.** By the lower-bound theorem of plasticity, any statically-admissible stress field that nowhere violates yield gives a **safe (conservative) lower bound** on the collapse load. In FE practice: run elastic-perfectly-plastic, ramp the load, and find where the solution **fails to converge / displacement runs away** — that non-convergence load is the numerical limit load (use arc-length or displacement control near the limit point — solver-numerics §3; load control diverges *at* the limit point). [S2][S7]
- **Collapse load from a load–deflection curve.** When you do include hardening (so there is no sharp limit point), define the collapse load from a characteristic displacement vs load plot:
  - **Twice-elastic-slope (TES) method (ASME):** draw a line from the origin at **twice the slope of the initial elastic line**; its intersection with the load-deflection curve is the **plastic collapse load** Φ_PC. The standard ASME construction. [S2]
  - **0.2 %-offset / tangent-intersection** methods are alternatives; TES is the code default.
- **Design margin** = collapse (or limit) load / applied load; codes embed this as load factors (§4).
- **Plastic-hinge / mechanism** intuition (beams/frames): collapse forms when enough plastic hinges (M_p = plastic moment) turn the structure into a mechanism; useful as a hand-check on the FE limit load.

> **Mesh note.** The limit load is a *global* (integral) quantity and is far less mesh-sensitive than peak stress, but **under-refinement raises the apparent limit load** (a coarse mesh is too stiff and delays the mechanism). Confirm the limit load is converged with mesh, like any QoI (meshing-convergence §5). Use **fully-integrated or reduced-integration-with-hourglass-control** elements appropriate for incompressible plastic flow (plastic flow is volume-preserving → watch **volumetric locking**; B-bar/F-bar/mixed u-P remedies — meshing-convergence element-technology). [S7]

---

## 4. The ASME VIII-2 Part 5 elastic-plastic route (protection against failure)

ASME BPVC **VIII-2 Part 5** (Design-by-Analysis) and **Section III** offer two routes: the **elastic stress-analysis route** (categorize stresses, §5) and the **elastic-plastic route** (run a nonlinear model with factored loads). The elastic-plastic route is generally **less conservative and clearer for complex 3-D geometry**, at the cost of a nonlinear solve. It comprises three distinct protections — each is a *separate analysis with its own load case and criterion*. [S2][S6]

### 4.1 Protection against plastic collapse — *global* criterion
- Run an **elastic-plastic** model (true stress-strain curve, large-deflection on) with **factored loads** (VIII-2 Part 5 prescribes load-combination factors, e.g. on the order of **2.4× design pressure** for the global criterion, combined with other loads per the load-case table — use the current edition's exact factors).
- **The acceptance criterion is convergence itself:** if the solution **converges** at the factored load, the component is protected against global plastic collapse (a converged solution *is* a statically-admissible equilibrium below the limit load). **Non-convergence = collapse.** [S2][S6]
- This neatly fuses with §3: the factored-load convergence check is a one-shot lower-bound limit-analysis statement.

### 4.2 Protection against local failure — *triaxiality-weighted* strain limit
- A converged global solution can still fail **locally** by ductile rupture where triaxiality is high (e.g. inside a thick section, at a crack-like notch). Check the **local total equivalent plastic strain** against a **triaxiality-weighted limiting strain**:

  **ε_peq ≤ ε_L · exp[ −(α_sl / (1 − α_sl)) · ( (σ_m / σ_e) − 1/3 ) ]**

  where σ_m/σ_e is the **stress triaxiality** (hydrostatic / von Mises), ε_L is the uniaxial limiting strain (a material property, from VIII-2 Annex 3-D tables), and α_sl is a material constant (≈ 2.2 for many ferritics — use the code table). **High triaxiality drives the allowable strain down exponentially** — the same physics as the Johnson-Cook / GTN triaxiality dependence in material-modeling §5. [S2][S6]
- Apply at the factored load case for local failure (a different, typically higher, factor than the global case).

### 4.3 Protection against ratcheting — *shakedown demonstration*
- Run the **cyclic** elastic-plastic analysis (steady primary + cyclic secondary, several cycles) and **demonstrate elastic shakedown**: after the first few cycles there is **no further plastic strain accumulation** (the plastic strain stabilizes, the loop closes elastically). [S2][S6]
- Equivalent to staying in regions **E/S** of the Bree diagram (§2). This is the direct, model-based alternative to the elastic-route **P_L + P_b + Q ≤ 3S_m** rule.
- Use **at least kinematic (Chaboche) hardening** — an isotropic model will falsely show shakedown (§1). The hardening model and its validation (material-modeling §10) are the weak link; document them.

> The elastic-plastic route **does not need stress linearization/categorization at all** for the collapse and ratcheting checks — that is its main appeal for messy 3-D parts where SCL placement is ambiguous. You still linearize for the elastic route (§5) and for fatigue (peak-stress extraction).

---

## 5. Stress linearization & categorization — the FE↔code bridge (HOLE 8)

This is the answer to the single most common bridge question in pressure-equipment FEA: *"the elastic model gives 800 MPa at the nozzle corner — what do I report, and against what limit?"* The peak there may be a non-convergent singularity (meshing-convergence §6.1) and it lumps together stresses of completely different consequence. You **decompose** the through-wall field along a Stress Classification Line, **categorize** each part by its mechanical role, and **compare each category to its own allowable**. [S2][S6]

> **Mechanics cross-reference (do not duplicate).** The *how* of the SCL decomposition — drawing the Stress Classification Line **through the wall, normal to both surfaces**; splitting the field into **membrane P_m (constant average), bending P_b (linear part), and peak F (nonlinear remainder)**; and the **SCL meshing requirements** (≥~9 nodes through the wall without interpolation, ~4–5 with cubic-spline interpolation; too few nodes over-reports membrane+bending) — is developed in **`meshing-convergence.md` §6.4 and §7**. This section adds the **categorization + code-limit layer** on top: *which category* each stress belongs to and *which allowable* it is checked against. [S8][S2]

### 5.1 The categories (mechanical role, not just the math)

The decisive question for each stress is: **is it load-controlled (it will not relax as the material yields — it can cause collapse) or deformation-controlled (it is self-limiting — yielding relieves it)?**

| Category | Symbol | What it is | Self-limiting? | Drives |
|---|---|---|---|---|
| **General primary membrane** | **P_m** | average stress from sustained mechanical load, away from discontinuities (e.g. pressure hoop stress) | **No** — load-controlled | gross plastic collapse |
| **Local primary membrane** | **P_L** | primary membrane elevated by a *gross structural discontinuity* (e.g. at a nozzle), over a limited region | No (but localized) | local collapse |
| **Primary bending** | **P_b** | bending part of a primary (sustained-load) stress | No | collapse via plastic hinge |
| **Secondary** | **Q** | self-equilibrating stress from **compatibility / thermal / discontinuity** (e.g. thermal gradient through wall, structural discontinuity bending) | **Yes** — yielding relaxes it | ratcheting / shakedown |
| **Peak** | **F** | the **non-linear remainder** — notch/fillet/local concentration, including the non-convergent singular part | Yes (very local) | **fatigue only** |

The **primary vs secondary distinction is judgment, not arithmetic** — the SCL gives you membrane/bending/peak, but *you* classify each as P or Q from its mechanical origin (is the load externally applied and sustained, or is it a thermal/compatibility self-stress?). Misclassifying a primary stress as secondary is unconservative (it gets the looser 3S_m limit). Thermal stresses are *almost always* Q **except** thermal stress that produces a net mechanical load path (rare). [S2][S6]

### 5.2 The code limits (ASME VIII-2 / III stress-categorization route)

With S_m the design stress intensity (≈ ⅔ σ_y or ⅓ σ_uts, whichever governs):

| Check | Limit | What it protects against |
|---|---|---|
| General primary membrane | **P_m ≤ S_m** | gross plastic collapse |
| Local membrane + primary bending | **P_L + P_b ≤ 1.5 S_m** | local collapse / plastic hinge |
| Primary + secondary (range) | **P_L + P_b + Q ≤ 3 S_m** | **ratcheting / shakedown** (the Bree 3S_m rule, §2) |
| Peak | **F → fatigue analysis** | crack initiation (S-N / ε-N — `fatigue-durability.md`) |

- The **1.5 factor** on bending is the shape factor that lets the outer fibre yield without collapse (a rectangular section has a plastic shape factor of 1.5). [S2]
- The **3S_m** range limit (≈ 2σ_y) is the shakedown criterion: if the *range* of primary+secondary stays below 2σ_y, the structure shakes down elastically (no ratcheting, no alternating plasticity) — directly the Bree boundary (§2). If **3S_m is exceeded**, you cannot use the simplified elastic route's shakedown assumption; go to the **simplified elastic-plastic analysis** (ASME, with a plasticity-correction/penalty factor K_e on the fatigue strain range) or the full **elastic-plastic ratcheting demonstration** (§4.3). [S2][S6]
- **F (peak)** never has a stress *limit* — it feeds the fatigue curve. This is why you never compare the singular nozzle-corner peak to S_m: it is category F, destined for the fatigue assessment, not the collapse check.

### 5.3 SCL placement rules

- Place the SCL **normal to the wall mid-surface**, spanning the full thickness, at the section of interest. [S2][S8]
- **Away from gross structural discontinuities** where possible — at a discontinuity the membrane part is **P_L (local)**, classified and limited differently (1.5 S_m on P_L+P_b) than general P_m. If the SCL must sit at a discontinuity, classify accordingly. [S2][S8]
- Span the **shortest through-wall path** (don't run the SCL obliquely through extra material — it dilutes the bending term).
- For 3-D / complex junctions where a clean normal-to-wall line is ambiguous, prefer the **elastic-plastic route (§4)** which avoids categorization altogether.

### 5.4 Averaged vs unaveraged nodal stress (the input-quality caveat)

The stress you feed the SCL must be trustworthy. **Nodal-averaged** stress smooths across element boundaries and *hides* discretization error; **unaveraged (element-nodal)** stress exposes it. **A large averaged-vs-unaveraged gap at the SCL location signals an under-resolved mesh** — the linearization is then unreliable (it sits on noisy data). Check the gap before trusting the categorized result; refine until the unaveraged field is smooth across the SCL elements. This ties the categorization back to the mesh-convergence gate. [S8]

> **Why you linearize a singularity at all (the unifying point).** The raw FE peak at a sharp corner is non-convergent (meshing-convergence §6.1) — it is *not a reportable stress*. Linearization is the sanctioned way to extract the convergent, classifiable membrane+bending content (which is real and finite) and quarantine the non-convergent peak into category **F** (where it is handled by fatigue, not by a stress limit). The same singular peak is treated three ways across disciplines: **categorization** puts it in F (here); **fracture** reads the path-independent J/K from an integral rather than the tip stress (see fracture treatment); **fatigue** extracts it by a fixed hot-spot/notch extrapolation (weld hot-spot, `mechanical-connections.md` §5; notch correction, `fatigue-durability.md`). All three refuse to compare the singular peak to an allowable directly. [S8][S2]

---

## 6. Forming & inelastic manufacturing effects

Metal-forming simulation is plasticity-dominated and has its own assessment quantities. The constitutive requirements (anisotropic yield Hill/Barlat, r-values, true-stress curve past necking) are in material-modeling §2; the *analysis/assessment* points: [S9][S10]

- **Springback** = the elastic recovery after the tool is removed. Predicting it well requires:
  - **Kinematic (or combined) hardening**, not isotropic — forming reverses the bending strain on the die radius (the Bauschinger effect controls springback). An isotropic model mispredicts springback. [S9]
  - **Enough through-thickness integration points** in shells — **5–7 (often 7–9) points** through the thickness to resolve the bending-stress distribution and its elastic unload; 3 points (the default for elastic shells) is far too few for springback. [S9]
  - Accurate **unloading modulus** (the chord modulus on unload is below the initial E for many AHSS — degrades with plastic strain; model it if springback-critical).
- **Forming Limit Diagram (FLD).** Plot the computed **major vs minor principal surface strain** for each element against the material's **Forming Limit Curve (FLC)**; elements above the curve indicate **localized necking / failure**, those near it indicate marginal formability. The FLD is the standard pass/fail map for sheet stamping. (FLC is strain-path dependent — non-proportional paths shift it; use stress-based FLSD or a path-independent criterion if the strain path is complex.) [S10]
- **Anisotropy → earing & thinning.** The Lankford **r-values** (r₀, r₄₅, r₉₀, material-modeling §2) drive **earing** (height undulation at the rim of a drawn cup) and directional **thinning**; normal anisotropy r̄ controls draw depth, planar anisotropy Δr controls ear count/height. Use Hill/Barlat anisotropic yield, not von Mises, for sheet.

---

## 7. Creep–plasticity interaction & relaxation

Combine plasticity with **creep** (material-modeling §4, Norton-Bailey / time- vs strain-hardening) when the component is hot and held under load. The assessment points: [S11][S12]

- **Stress relaxation** = constant *total* strain, where creep converts elastic strain to creep strain so **stress decays over time**. The two industrial cases:
  - **Bolt-preload loss** — a hot bolted/flanged joint relaxes: the preload decays as the bolt (and gasket/flange) creep, risking leakage. Model: apply preload (mechanical-connections §bolt-preload), then a **load-then-hold** transient with creep active; read the preload vs time. Prefer the **strain-hardening** creep form (it tracks variable/redistributing stress better than time-hardening — material-modeling §4). [S11]
  - **Weld residual-stress relaxation** — post-weld heat treatment / high-temperature service relaxes weld residual stress by creep; the same relaxation analysis predicts how much locked-in stress survives.
- **Sequencing matters.** **Load (or preload) first, then hold** — the order of plastic loading and creep hold changes the result because creep acts on the *current* stress state. Apply the mechanical/thermal step, *then* let it creep; don't superpose.
- **Creep–fatigue interaction.** Cyclic load at high temperature combines creep (hold-time) damage with fatigue damage. Assess by **damage summation** D_fatigue + D_creep ≤ D_allow (ASME III Division 5 / former NH; RCC-MR) or strain-range partitioning. The **thermo-mechanical fatigue (TMF)** treatment (in-phase vs out-of-phase, Sehitoglu) is in `fatigue-durability.md` — cross-link, don't duplicate. [S12]

---

## 8. Verification gates (inelastic assessment)

Run these before reporting an inelastic-assessment result:

1. **Right hardening rule for the load history.** Cyclic/thermal-cycled load ⇒ **kinematic/Chaboche**, never isotropic (isotropic fakes shakedown, misses Bauschinger — material-modeling §2). [S1]
2. **Ratcheting/shakedown model validated on an unseen test.** Chaboche fit to one loop is unverified for ratcheting (material-modeling §10). State the validation mode. [S1]
3. **True stress / true plastic strain** input (not engineering), curve extended past necking by inverse-FE or a fitted law (material-modeling §2). A *falling* (engineering) curve causes spurious softening. [S1]
4. **Limit/collapse load converged with mesh** and read with **arc-length or displacement control** through the limit point (load control diverges *at* the limit — solver-numerics §3). Watch **volumetric locking** in fully-plastic regions (B-bar/F-bar/mixed u-P). [S7]
5. **Stress categorized before comparing to S** — never raw von Mises vs S_m (meshing-convergence §7). SCL normal to wall, away from gross discontinuity; enough through-wall nodes (≥~9, or ~4–5 with cubic interpolation — meshing-convergence §7). [S2][S8]
6. **Averaged-vs-unaveraged nodal stress gap small** at the SCL/assessment location (else the mesh is under-resolved and the linearization is on noise). [S8]
7. **Primary vs secondary classification justified by mechanical origin**, not by convenience (misclassifying P as Q is unconservative). [S2]
8. **Elastic-plastic route:** convergence at the factored load (= global collapse pass); local triaxiality-strain check done at its own factored case; shakedown demonstrated over enough cycles. Document the hardening model. [S2][S6]
9. **Springback:** kinematic hardening + 5–9 through-thickness integration points; FLD checked against the correct (strain-path-aware) FLC. [S9][S10]
10. **Creep relaxation:** load-then-hold sequencing; strain-hardening creep form for redistributing stress; valid (σ, T) window of the creep law (material-modeling §4). [S11]

---

## See also

- **`material-modeling.md`** — §2 yield criteria & isotropic/kinematic/Chaboche hardening, true-vs-engineering stress, Considère; §4 creep (Norton-Bailey) & viscoelasticity; §5 ductile damage (Johnson-Cook/GTN/GISSMO, triaxiality); §10 calibration & validate-on-held-out (the Chaboche-ratcheting gate). *The constitutive home — this file never repeats it.*
- **`meshing-convergence.md`** — §6 singularity vs concentration (why the peak is non-convergent and what to do); §6.4 SCL as singularity remedy; §7 stress-linearization **mechanics** (membrane/bending/peak, SCL node-count requirements). *The SCL-mechanics home — this file adds categorization on top.*
- **`mechanical-connections.md`** — bolt preload (relaxation input); gasket pressure-closure nonlinearity; **weld hot-spot** fatigue (the weld special case of stress extraction, §5).
- **`fatigue-durability.md`** — peak stress (category F) → S-N/ε-N; notch (Neuber/Glinka) correction; creep-fatigue & TMF (in-phase/out-of-phase, Sehitoglu); spectral fatigue.
- **`solver-numerics.md`** — §3 arc-length/Riks & energy stabilization (limit points, post-collapse), Newton-Raphson / auto-incrementation.
- **`specialized-analyses.md`** — the one-line plasticity/buckling pointers this file expands.

---

## SOURCES

Reliability key: **[A]** code/standard or peer-reviewed canonical · **[B]** vendor theory manual / recognized engineering body · **[C]** practitioner article corroborated by ≥1 [A]/[B].

- **[S1] [A/B]** ASME BPVC Section VIII Division 2 Part 5 & Section III (cyclic plasticity, hardening for ratcheting); Chaboche calibration & ratcheting sensitivity — *Sensitivity & calibration of Chaboche kinematic hardening for ratcheting*, MDPI Appl. Sci. 9(12):2578; *Determination of Chaboche dual-backstress parameters for ratcheting*, Int. J. Fatigue. (Cross-ref material-modeling §2/§10.)
- **[S2] [A]** ASME BPVC **VIII-2 Part 5 (Design-by-Analysis)** — protection against plastic collapse (global factored-load criterion), local failure (triaxiality-weighted strain limit), ratcheting/shakedown demonstration; **stress-categorization route** (P_m/P_L/P_b/Q/F, S_m / 1.5S_m / 3S_m limits); **Annex 5.A** stress linearization.
- **[S3] [A]** J. Bree, *Elastic-plastic behaviour of thin tubes subjected to internal pressure and intermittent high-heat fluxes with application to fast-nuclear-reactor fuel elements*, J. Strain Analysis 2(3), 1967 — the **Bree diagram**.
- **[S4] [A]** ASME Section III (NB) ratcheting/shakedown rules; EN 13445 Annex B / EN 1993 shakedown limits — design use of the Bree map.
- **[S5] [A]** König / Melan shakedown theory; Ohno-Wang and modified Chaboche ratcheting models (over-prediction of basic Armstrong-Frederick) — plasticity texts (Lemaitre & Chaboche, *Mechanics of Solid Materials*).
- **[S6] [B]** NAFEMS — *Design-by-Analysis* / elastic-plastic vs elastic-route guidance; ASME VIII-2 Part 5 application notes (factored loads, convergence-as-collapse, K_e simplified elastic-plastic).
- **[S7] [B]** NAFEMS — limit-load / plastic-collapse analysis; twice-elastic-slope construction (ASME); lower-bound limit analysis & FE non-convergence as limit load.
- **[S8] [A/B]** ASME VIII-2 Annex 5.A & NAFEMS *"How To Do Stress Linearisation"* — SCL placement (normal to wall, away from discontinuity), through-wall node-count for <5% linearization error, averaged-vs-unaveraged caveat. (Mechanics in meshing-convergence §7.)
- **[S9] [B/C]** Sheet-forming / springback practice — combined (kinematic) hardening requirement, 5–9 through-thickness integration points, chord/unloading-modulus degradation for AHSS (LS-DYNA / Abaqus forming guides; AutoForm/PAM-STAMP practice).
- **[S10] [A/B]** Forming Limit Diagram / Forming Limit Curve (Keeler-Goodwin); strain-path dependence and stress-based FLSD — sheet-metal-forming references and ISO 12004 (FLC determination).
- **[S11] [A/B]** Norton-Bailey creep & stress relaxation (material-modeling §4); bolt-preload-loss / flange relaxation at temperature — ASME, COMSOL/Ansys creep theory.
- **[S12] [A]** ASME BPVC Section III Division 5 (elevated-temperature, former Subsection NH) / RCC-MR — creep-fatigue damage summation D_f + D_c ≤ D_allow; strain-range partitioning. (TMF detail in fatigue-durability.md.)
