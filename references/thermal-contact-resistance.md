# Thermal Contact Resistance / Conductance (TCR / TCC / h_c) — FEM/CAE Reference

A quantitative, practical reference for modeling heat flow across joints in Ansys
Mechanical/MAPDL, Simcenter 3D / Simcenter Nastran, and Ansys Thermal Desktop (SINDA).
Use this when a thermal or thermo-elastic model has a mechanical interface (bolted,
clamped, pressed, glued, shrink-fit) where the temperature drop across the joint matters.

---

## 1. Physics — why a joint resists heat

When two solids are pressed together, **real contact occurs only at a finite set of
microscopic asperity peaks** (Fig. 2 in Wikipedia/COMSOL refs). The **real contact area
is a tiny fraction (typically ~1–2%) of the apparent (nominal) area**. Heat flowing
through the joint must "funnel" through these few small spots — the streamlines
constrict toward each contact spot and spread out on the other side. This
**constriction / spreading resistance** is the dominant microscopic mechanism. Even a
near-ideal interface has a finite *thermal boundary conductance* from electron/phonon
mismatch, but that only matters at nanoscale.

**Three parallel heat paths across the interface** (COMSOL/DSPE):
joint conductance `h = h_c + h_g + h_r`

1. **Solid–solid conduction** through the actual contact spots (`h_c`, constriction
   conductance) — usually dominant.
2. **Conduction/convection through the interstitial fluid/gas** filling the gaps
   (`h_g`, gap conductance). At the small gap scales involved this is mostly *conduction*
   through the gas, not convection. Governed by the gas conductivity and the Knudsen
   number (rarefaction).
3. **Radiation across the gap** (`h_r`). Generally negligible below ~300–600 °C; only
   matters at high temperature or when the solid path is very poor and there is no gas.

**Why vacuum (spacecraft) dramatically raises resistance:** removing the interstitial
gas deletes the entire `h_g` path. In air `h_g` can rival or exceed `h_c`; in vacuum only
the few contact spots conduct, so contact resistance rises sharply (often by a large
factor at low pressure). This is why TCR is a first-order concern for spacecraft thermal
design and cryogenics, and often a second-order one in air-cooled electronics.

### Definitions and units

| Symbol | Name | Units | Relation |
|---|---|---|---|
| `h_c` | thermal contact **conductance** (per unit area) | W/m²·K | `q'' = h_c · ΔT` (heat flux) |
| `R''_c` | area-specific contact **resistance** | m²·K/W | `R''_c = 1 / h_c` |
| `R_c` | total joint resistance | K/W | `R_c = 1 / (h_c · A) = R''_c / A` |
| `A` | apparent (nominal) contact area | m² | — |
| `ΔT` | temperature jump across interface | K | `ΔT = Q · R_c = Q / (h_c · A)` |

`Q = h_c · A · ΔT`.  Note: solver "conductance" `G` [W/K] for a coupling/conductor is
`G = h_c · A`. Keep the per-area vs total distinction straight — it is the #1 unit error.

---

## 2. Dependencies — direction and rough magnitude

| Driver | Effect on `h_c` | Magnitude / scaling |
|---|---|---|
| **Contact pressure P** | ↑ strongly with P | `h_c ∝ (P/H_c)^0.95` in CMY plastic model — nearly linear (exp ≈ 0.8–0.95). More pressure → more & larger contact spots. |
| **Surface roughness σ (RMS)** | ↓ as σ ↑ | `h_c ∝ 1/σ` (smoother → fewer, taller gaps → better contact). |
| **Asperity slope m (mean abs. slope)** | ↑ with m | `h_c ∝ m` (steeper micro-slopes pack more contact spots per area). |
| **Flatness / waviness (macro)** | ↓ if non-flat | Out-of-flatness opens macro-gaps → larger `R`; not captured by σ alone. |
| **Microhardness H_c (softer body)** | ↓ as H_c ↑ | Softer material → asperities flatten more under load → more real area. `h_c ∝ (P/H_c)^0.95`. |
| **Solid conductivities k₁,k₂** | ↑ with conductivity | enters as **harmonic mean** `k_s = 2 k₁k₂/(k₁+k₂)`. |
| **Interstitial material** | ↑ with gas/fluid k & pressure | grease/TIM raise `h_g` an order of magnitude vs air; vacuum sets `h_g≈0`. |
| **Temperature** | material-dependent | k(T), H_c(T) shift `h_c`. At **cryo, h_c falls steeply** (k of metals and contact-spot conduction drop): roughly `G ∝ T` to `T²` for pressed metals at low T. |

---

## 3. Typical value tables

> **Ballpark band:** most measured TCR falls in **R''_c ≈ 5×10⁻⁶ … 5×10⁻⁴ m²·K/W**,
> i.e. **h_c ≈ 2,000 … 200,000 W/m²·K** (Yovanovich/Bahrami contact-conductance correlations;
> bare-metal values cross-checked against nuclear-power.com). TCR matters for good conductors
> (metals) and is usually negligible for insulators.

### 3a. Bare metal–metal, in air

| Interface | Conditions | `h_c` (W/m²·K) | Source |
|---|---|---|---|
| Aluminum–aluminum | σ≈10 µm, 1 atm interface pressure | **~3,640** | nuclear-power.com |
| Stainless–stainless | σ≈2.5 µm, P≈1 MPa | **~3,000** | nuclear-power.com |
| Generic "sturdy mechanical / bolted" interface | dry, moderate pressure, air | **~1,000** (rule of thumb) | nuclear-power.com |
| Al 6063 heat sink – Al₂O₃ package, air gap | P 0.007→0.35 MPa | `R''≈2.67→1.90 cm²·K/W` → **h_c ≈ 375→525** | electronics-cooling |

### 3b. Bare metal–metal, in **vacuum** (no gas path)

Removing `h_g` typically drops effective conductance well below the air values above.
For nominally flat rough metal in vacuum at low/moderate load, expect **h_c ~ 10²–10³
W/m²·K** (strongly pressure-dependent; rises ~linearly with P). Low-pressure vacuum
contacts can fall to **tens of W/m²·K**. *Always treat vacuum metal contacts as
pressure-calibrated, not tabulated.*

### 3c. With interstitial enhancers (electronics, air)

From the Yovanovich Al–alumina worked example (electronics-cooling), P = 0.007–0.35 MPa:

| Interface filler | `R''_c` (cm²·K/W) | `h_c` (W/m²·K) | Note |
|---|---|---|---|
| Air (bare) | 2.67 → 1.90 | ~375 → 525 | worst case |
| **Silicone grease** | 0.335 → 0.213 | ~3,000 → 4,700 | ~10× better than bare |
| **Ceramic-filled (conductive) grease** | < 0.065 | > **15,000** | best |

General TIM guidance: thermal greases/gap pads have **k ≈ 1–10 W/m·K** (e.g. Chomerics
THERM-A-GAP PAD 30 = 3.2 W/m·K, 80LOE = 8.0 W/m·K). For a pad/grease *layer* of thickness
`t`, the layer conductance is `h ≈ k/t` in **series** with the two contact resistances —
thin bond lines matter as much as the material k.

### 3d. Joints, fits, foils

| Joint type | Behavior / typical | Note |
|---|---|---|
| Bolted joint (dry, air) | ~1,000 W/m²·K near bolts; very non-uniform | conductance concentrated in a pressure cone under each bolt head; midspan can be ~0 |
| Indium foil (soft metal) | high; conforms to fill gaps | excellent gap-filler, especially cryo & vacuum |
| Thermal grease | h_c × ~10 vs bare | fills gas path |
| Pressed / shrink fit | high but interference-dependent | model via interference pressure → CMY |
| Gold plating | improves bare-metal contact | soft, non-oxidizing; common cryo finish |

### 3e. CRYOGENIC joints

At cryo temperatures, contact conductance **falls steeply with T** (metal k and
contact-spot conduction drop). Enhancers behave differently than at room temperature:

- **Pressed metal contacts at LHe (4.2 K):** total conductance roughly
  **G ≈ 10⁻³ … 10⁻¹ W/K** for Cu assemblies at ~670 N applied force; conservative Cu–Cu
  fit `G ≈ 0.0624·T − 0.00023 W/K` (roughly **linear in T**) (cryo bolted-Cu refs).
- **Indium foil or Apiezon N grease between surfaces** improves uncoated contacts by
  **~×3 for stainless steel up to ~an order of magnitude for copper** (NASA Salerno;
  Salerno & Kittel).
- **Apiezon N grease caveat:** it improves Al/brass/Cu contacts and outperforms gold
  plating and indium in some cases — **but it becomes rigid at LHe temperatures.** If
  good contact is not achieved at room temperature, the thick non-deforming grease layer
  can **separate from the surfaces on cooldown and increase resistance.** Apply thin,
  mate warm.
- **Indium foil** stays soft and **flows** to fill gaps — robust gap-filler down to 4 K.
- **Gold plating** (e.g. ~20 µin Au over ~50 µin Ni on Cu) reduces oxide resistance and
  is a standard cryo joint finish.
- Specially prepared **Al/Cu joints** (zincate + gold) reach electrical contact down to
  ~5 nΩ (proxy for very high thermal conductance).

> Cryo design rule: do not extrapolate room-temperature `h_c` to 4 K/77 K. Use measured
> low-T data, apply soft metal (In) or gold plating, maximize bolt preload, and verify
> the enhancer stays compliant at temperature.

---

## 4. Correlations and how to get values

### 4a. Yovanovich conforming-rough-surface model (the workhorse)

`h_j = h_c + h_g`

**Plastic-contact (Cooper–Mikic–Yovanovich, CMY)** constriction conductance:

```
h_c = 1.25 · k_s · (m / σ) · (P / H_c)^0.95
```

- `k_s = 2·k₁·k₂/(k₁+k₂)`  — harmonic mean conductivity of the two solids
- `m`  — effective mean absolute asperity slope, `m = sqrt(m₁² + m₂²)`
- `σ`  — effective RMS surface roughness, `σ = sqrt(σ₁² + σ₂²)`
- `P`  — apparent contact pressure
- `H_c` — microhardness of the **softer** of the two solids (Vickers-correlated; depends
  on Brinell hardness `H_B`, with `H_0 = 3.178 GPa` and Vickers coefficients `c₁,c₂` for
  `1.30 < H_B < 7.60 GPa`)

If the slope `m` is not measured, a common fallback correlates `m` to `σ`
(`m ≈ 0.125·(σ·10⁶)^0.402` with σ in m). Assumes plastic asperity deformation, Gaussian
height distribution, isotropic roughness.

**Mikic elastic correlation** (same surface stats, elastic asperities) replaces the plastic
microhardness `H_c` with an effective elastic modulus `E_contact`
(`1/E_contact = (1−ν₁²)/E₁ + (1−ν₂²)/E₂`). `h_c` rises monotonically with the **relative
contact pressure** — the governing group is `P/H_c` in the plastic (CMY) model but
`P/(E_contact·m)` (asperity slope `m`) in the elastic (Mikic) model. There is no single
"perfect-contact" pressure threshold: conductance keeps climbing as the mean plane
separation `Y` → 0. **Use the regime-appropriate pressure scale — do NOT apply the plastic
`H_c` criterion to the elastic case** (the two regimes were just distinguished above).

### 4b. Gap conductance `h_g`

Conduction through the interstitial gas across the mean gap. Increases with gas
conductivity and gas pressure; reduced by rarefaction (Knudsen number / temperature-jump
distance). In **vacuum, h_g → 0**.

### 4c. Radiative conductance `h_r`

Gray-diffuse parallel-plate model (matters > ~600 °C):
`h_r = ε_eff · σ_SB · (T_u² + T_d²)·(T_u + T_d)`, with `1/ε_eff = 1/ε_u + 1/ε_d − 1`.

### 4d. Practical routes to a number

1. **Calibrate from measurement:** measure `Q` and `ΔT` across the real joint →
   `h_c = Q/(A·ΔT)`. The gold standard; back it out and feed it to the solver.
2. **CMY/Yovanovich** with measured σ, m, H_c, P (best when no test data).
3. **Handbook / literature values** for the material pair, finish, and environment (use
   tables in §3; cite the source and conditions).
4. **"When in doubt" defaults:** bolted dry metal in air ≈ 1,000 W/m²·K; with grease
   ≈ 3,000–5,000; bare metal in vacuum → calibrate (~10²–10³, P-dependent); cryo →
   measured low-T data only.

---

## 5. Modeling in each tool

### 5a. Ansys MAPDL / Mechanical

**Element set:** surface-to-surface contact `CONTA171/172` (2D) or `CONTA173/174` (3D)
paired with `TARGE169/170`. Thermal DOF (TEMP) must be active (`KEYOPT(1)` includes the
thermal/structural-thermal option, e.g. thermal contact or coupled).

**TCC real constant:** the contact conductance is the **14th real-constant field
(TCC)** of the CONTA element, with `q = TCC·(T_contact − T_target)` (units
heat/time/area/temp = W/m²·K).

APDL command-object pattern (works inside a Mechanical contact branch; `cid`/`tid` are
auto-resolved by Mechanical):

```apdl
! arg1 = desired TCC value (W/m^2/K)
r,cid               ! real-constant set for the contact element type
rmore,,,,,,         ! skip fields 7-12
rmore,,arg1         ! field 14 = TCC
r,tid               ! repeat for target side (symmetric contact)
rmore,,,,,,
rmore,,arg1
```

Direct MAPDL: `RMODIF,<set>,14,<TCC>`.

**Mechanical (Workbench) GUI exposure** — Contact → *Thermal Conductance*:
- **Program Controlled (default):** Ansys computes a *large* TCC from the bodies'
  conductivities so the joint behaves as **near-perfect** contact (negligible ΔT,
  numerically stable). Use when TCR is irrelevant.
- **Manual:** enter your `h_c` [W/m²·K] (e.g. from §3/§4). **Throttle TCC down** to model
  real resistance — smaller TCC → larger ΔT across the joint.
- **Bonded contact = perfect thermal conductance** (the default for imported assemblies;
  uses TARGE170/CONTA174, TCC effectively infinite → no temperature drop). Bonded ignores
  TCR entirely.
- Note: TCC is *not* a Mechanical parameter by default → use the APDL command object above
  to parametrize it for a DOE/optimization.

**Gap conductance & radiation across an open gap:** `KEYOPT`/real constants let TCC act
across a pinball/gap region; radiation across a gap is added via `KEYOPT(9)`/surface
radiation or `RDSF`/`AUX12` radiosity. Modeling tip (SimuTech): put the **contact side on
the lower-conductivity body** and refine its mesh; set detection to *Nodal—Projected
Normal from Contact* for a smooth flux distribution.

### 5b. Simcenter Nastran / Simcenter 3D Thermal

**Solvers:** steady-state `SOL 153`, transient `SOL 159` (advanced thermal).

**Thermal contact / coupling:** define a **Thermal Coupling** simulation object (Simcenter
3D Thermal/Space Systems Thermal) between faces/edges. Magnitude (Input Value) types:
- **Total Conductance** [W/K] — absolute `G = h_c·A` (imported to Thermal Desktop as a
  *contactor, Input Value Type = Absolute*).
- **Conductance per Area** [W/m²·K] — your `h_c` directly (per-area, scaled by face area).
- **Conductive Gap** — a gap with a given thermal conductivity; treated as a material of
  thickness 1 m / per-area, i.e. a `k/t` layer.
- Constant, time-dependent, or temperature-difference-dependent tables supported.

**Bulk-data path:** glued/contact thermal coupling via `BCTSET` (contact set),
`BSURFS`/`BSURF` (contact surfaces/regions), `BGSET`/`BGADD` (glue), and `BCTPARM`
(contact parameters); a finite **interface conductance** value on the coupling/glue gives
TCR. **Gap elements** (`CGAP`/`PGAP` analogs) handle open/closing gaps. "Glue" =
bonded/perfect coupling (no ΔT). Face-to-face thermal contact with an explicit
conductance value is the standard finite-TCR route.

### 5c. Ansys Thermal Desktop / SINDA (spacecraft)

Thermal Desktop builds the FD/FE node + conductor network and launches **SINDA/FLUINT** to
solve; **RadCAD** computes radiation exchange (view factors → radiation conductors `GR`),
which is how **radiation across a gap** is captured (Monte-Carlo ray trace between the two
surfaces). Steps:

- **Contactor** between two surfaces/solids defines the contact conductance. Set the
  **conductance per unit area** (W/m²·K) — Thermal Desktop multiplies by the overlap area
  to build the linear conductor `G = h_c·A`. *Input Value Type* options: **Per Area /
  Length** (enter `h_c`) or **Absolute** (enter total `G` in W/K).
- A **Conductive-Gap**-type coupling is implemented as a thermophysical material
  (`k = gap conductance value`, thickness 1 m, Use Material on).
- **Conductors:** linear conductors (`G` [W/K]) directly link nodes; a contactor is the
  area-driven way to generate them. Hand-set `G = h_c·A` for a lumped joint.
- **Radiation:** RadCAD builds `GR` radiation conductors (`Q = σ·GR·(T₁⁴−T₂⁴)`) across the
  gap from surface optical properties (ε, α) and geometry — separate from the contactor.
- **Symbols** parametrize the contactor conductance for trade studies; CaseSet `.Run()`
  (OpenTD) executes batches.

---

## 6. Decision guidance

### When to use which contact model

| Use… | When |
|---|---|
| **Perfect / Bonded / Glue** (ignore TCR) | Joint resistance ≪ the conductive resistance of the parts (insulators, low-flux, joint far from the QoI); or contact is metallurgical (welded/brazed/soldered). Default for quick structural-thermal screening. |
| **Explicit finite conductance** (set `h_c`/TCC/coupling) | TCR is comparable to or larger than bulk resistance: metals, vacuum, cryo, high heat flux, precision thermal control. The normal engineering case for real hardware. |
| **Full nonlinear contact** (pressure-dependent TCC) | `h_c` varies across the interface with the actual contact pressure field (bolted joints, interference fits) — couple a structural solution → pressure → CMY → TCC, or use pressure-dependent TCC tables. |

### When TCR matters most
- **Vacuum / spacecraft** — no gas path; contact resistance can dominate.
- **Cryogenics** — `h_c` collapses at low T; enhancer choice (In, Au, Apiezon) is decisive.
- **High heat flux / power electronics** — even modest `R''_c` causes large ΔT.
- **Precision thermal / dimensional stability** — small ΔT at a joint maps to figure error.
- **Good-conductor assemblies** — metal-to-metal, where the joint is the bottleneck.

### Common mistakes
- **Assuming perfect (bonded) contact** by default — silently deletes a real, often
  dominant, resistance. Imported assemblies default to bonded in Mechanical.
- **Ignoring vacuum** — using air-derived `h_c` for a spacecraft/vacuum joint overstates
  conductance by a large factor (the `h_g` path doesn't exist).
- **Wrong area** — confusing per-area `h_c` [W/m²·K] with total `G` [W/K]; or using
  *apparent* area where the model wants the conductor `G = h_c·A`. Check the tool's Input
  Value Type (Per Area vs Absolute).
- **Extrapolating room-T values to cryo** (or vice-versa).
- **Uniform `h_c` on a bolted joint** — conductance is concentrated under bolt heads;
  a single averaged value can mislocate the heat path.
- **Apiezon grease too thick / mated cold at cryo** — separates on cooldown, raises R.

---

## Sources

- [Thermal Contact Resistance / Conductance — nuclear-power.com](https://www.nuclear-power.com/nuclear-engineering/heat-transfer/thermal-conduction/thermal-resistance-thermal-resistivity/thermal-contact-resistance-thermal-contact-conductance/)
- Madhusudana, *Thermal Contact Conductance*, 2nd ed. (Springer, 2014) — primary textbook for the constriction/three-path model and order-of-magnitude bands. Orientation: [Thermal contact conductance — Wikipedia](https://en.wikipedia.org/wiki/Thermal_contact_conductance)
- [Thermal contact conduction — DSPE (precision engineering)](https://www.dspe.nl/knowledge/thermomechanics/chapter-1-basics/1-2-heat-transfer/thermal-contact-conduction/)
- [Theory for Thermal Contact (CMY, Mikic, gap, radiation) — COMSOL docs](https://doc.comsol.com/5.5/doc/com.comsol.help.heat/heat_ug_theory.07.66.html)
- [Calculating Interface Resistance (Yovanovich model, TIM/grease values) — Electronics Cooling](https://www.electronics-cooling.com/1997/05/calculating-interface-resistance/)
- [Contact Conductance Correlations (Yovanovich/Waterloo MHTL)](https://www.mhtlab.uwaterloo.ca/pdf_papers/mhtl96-2.pdf)
- [Four Decades of Research on Thermal Contact, Gap, and Joint Resistance — Yovanovich (Waterloo MHTL)](http://www.mhtlab.uwaterloo.ca/pdf_papers/mhtl05-11.pdf)
- [Thermal Contact Resistance: Effect of Elastic Deformation — Bahrami, Yovanovich, Culham (SFU)](https://www.sfu.ca/~mbahrami/pdf/2005/M.%20Bahrami,%20M.%20M.%20Yovanovich,%20J.%20R.%20Culham%20-%20Thermal%20contact%20resistance:%20Effect%20of%20elastic%20deformation.pdf)
- [Thermal Contact Conductance at Low Contact Pressures — Milanez, Yovanovich, Mantelli](https://lepten.ufsc.br/publicacoes/tucal/eventos/2003/AIAA/milanez_yovanovich_mantelli.pdf)
- [A review of thermal contact resistance at cryogenic temperature — USPAS/FNAL](https://uspas.fnal.gov/materials/21onlineSBU/Background/Further%20reading%20-%20Contact%20resistance%20at%20cryo%20temperature.pdf)
- [Apiezon N Grease Cryogenic Thermal Conductance (LHe) — M&I Materials](https://apiezon.com/wp-content/uploads/2023/10/Apiezon_N_Grease_Cryogenic_Thermal_Conductance.pdf)
- [Thermal conductance measurements of bolted copper joints (SuperCDMS) — CERN/INSPIRE](https://s3.cern.ch/inspire-prod-files-4/446b26ae67f613f748ccfe073c3b3333)
- [Pressed copper and gold-plated copper contacts at low temperatures — OSTI](https://www.osti.gov/servlets/purl/1542958)
- [Making TCC a Parameter in ANSYS Mechanical (APDL command object, real constant 14) — PADT](https://www.padtinc.com/2017/04/06/ansys-mechanical-contact-condutance-apdl/)
- [Thermal Contact Settings in Ansys Mechanical Workbench — SimuTech](https://simutechgroup.com/thermal-contact-settings-in-mechanical/)
- [What is thermal conductance in contact / Program Controlled value — Ansys Knowledge](https://innovationspace.ansys.com/knowledge/forums/topic/what-is-the-meaning-of-thermal-conductance-defined-in-contact-what-is-the-program-controlled-thermal-conductance-value-how-to-achieve-partial-conductance-through-the-contact/)
- [Ansys Mechanical APDL Contact Technology Guide (CONTA17x / TCC)](https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/pdf/ANSYS_Mechanical_APDL_Contact_Technology_Guide.pdf)
- [Thermal coupling magnitudes (Total Conductance / Per Area / Conductive Gap) — Maya HTT / Simcenter 3D](https://help.mayahtt.com/tmx/v2/topics/importing_thermal_couplings_magnitudes.html)
- [Simcenter 3D Thermal datasheet — Siemens](https://acam.at/wp-content/uploads/Siemens-PLM-Simcenter-3D-Thermal-fs-6709-A7.pdf)
- [Thermal Desktop (contactors, conductors, RadCAD, SINDA) — C&R Technologies](https://www.crtech.com/products/thermal-desktop)
- [Introduction to Thermal Desktop — TFAWS/NASA training](https://tfaws.nasa.gov/TFAWS03/software_training/thermal_desktop.pdf)
- [Chomerics THERM-A-GAP gap pad (TIM k values) — Parker](https://www.parker.com/us/en/divisions/chomerics-division/solutions/thermal-management/gap-fillers/therm-a-gap-pad.html)
