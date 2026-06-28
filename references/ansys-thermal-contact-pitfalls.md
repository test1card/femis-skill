# Ansys Mechanical — Headless Fix for Thermally-Inert Structural Contacts (CONTA174)

> **STATUS LEGEND (applies throughout the skill — tag every recipe at point of use):**
> **[VERIFIED]** = reproduced on a representative test model.
> **[DOCS-ONLY — not executed]** = plausible from documentation, NOT yet run on a model — confirm once on the
> real model before trusting it as ground truth. Never let a DOCS-ONLY recipe carry the same authority as a
> VERIFIED one.

**Problem recap.** Thermal contacts (TCC / R_tc) generated under a **Static Structural**
system produce `CONTA174` elements with **structural DOF only** — `KEYOPT(1)=0`
(`UX,UY,UZ`). They carry **no `TEMP` DOF**, so heat cannot cross the joint in any
downstream thermal solve regardless of the TCC value set. `ETCHG,STT` does **not**
fix this (CONTA174 has no companion element in the conversion table). A `KEYOPT`
snippet placed in the *structural* environment also does nothing, because the DOF
set on a contact element is fixed by the **physics of the environment that writes
the input deck**, not by snippets that run before the deck physics is locked.

---

## Contents

- [0. Root cause (one sentence)](#0-root-cause-one-sentence)
- [1. Decision tree (ranked, all headless)](#1-decision-tree-ranked-all-headless)
- [2. Canonical Workbench fix — share the Model cell with a Thermal system](#2-canonical-workbench-fix-share-the-model-cell-with-a-thermal-system)
- [3. PyMAPDL / APDL escape hatch (most robust headless)](#3-pymapdl-apdl-escape-hatch-most-robust-headless)
- [3a. After ANY contact change, rebuild the mesh (or it's a no-op)](#3a-after-any-contact-change-rebuild-the-mesh-or-its-a-no-op)
- [3b. Connectivity gate (catch islanded bodies BEFORE solving)](#3b-connectivity-gate-catch-islanded-bodies-before-solving)
- [4. Why the ~14 GUI/headless "fixes" all fail](#4-why-the-14-guiheadless-fixes-all-fail)
- [4b. PROVEN headless fix — supersedes guesswork in §2](#4b-proven-headless-fix-reproduced-on-a-representative-multi-body-assembly-supersedes-guesswork-in-2-verified)
- [4c. Recovering & GATING thermal connectivity headless](#4c-recovering-gating-thermal-connectivity-headless-answers-live-open-questions)
- [4d. "Topology connected but the cold chain won't propagate" — conduction triage](#4d-topology-connected-but-the-cold-chain-wont-propagate-conduction-triage-round-2)
- [4e. Robust fallback — LINK33 thermal-conductor network](#4e-robust-fallback-link33-thermal-conductor-network-when-bonded-contacts-wont-conduct-verified)
- [5. Version flags](#5-version-flags)
- [Sources](#sources)

## 0. Root cause (one sentence)

> The contact element's active DOF set is decided by **the solving environment's
> physics** at deck-write time. A Static Structural environment writes a
> **structural** deck → CONTA174 gets `KEYOPT(1)=0` (no `TEMP`). Only a **thermal
> environment** (or a hand-built APDL thermal deck) writes `TEMP` DOF on the
> contact (`KEYOPT(1)=2`, pure thermal, or `=1`, thermal-structural).

Confirmed CONTA174 `KEYOPT(1)` map (Ansys element reference):

| KEYOPT(1) | DOF set | Use |
|-----------|---------|-----|
| **0** | `UX, UY, UZ` | structural only — **thermally inert** (the bug) |
| **1** | `UX, UY, UZ, TEMP` | thermal–structural coupled |
| **2** | `TEMP` (or TBOT/TTOP/TEMP via KEYOPT(13)) | **pure thermal** — what a thermal environment writes |

TCC (thermal contact conductance) is **real-constant field 14** of the 17x contact
elements (order: `R1, R2, FKN, FTOLN, ICONT, PINB, PMAX, PMIN, TAUMAX, CNOF, FKOP,
FKT, COHE, **TCC**(14), FHTG, SBCT, …`). Heat flux across the closed gap:
`q = TCC · (T_target − T_contact)`. The gap must be **inside the pinball** for any
conduction to occur.

### Diagnostic signatures (how the bug shows up)
- **Transient thermal:** bodies sit at **exactly the initial temperature** forever (no heat enters/leaves the islanded body) — looks like "nothing is happening."
- **Steady-state thermal:** **singular solve** — tiny negative pivot (`min pivot ~ −6e-14`), no `.rth` written (an isolated body has no thermal path → singular conductance matrix).
- A steady single-BC thermal solve is therefore also a **connectivity test** (see §3b): singular ⇔ some body is thermally isolated.

### Recommended MAPDL thermal-contact KEYOPTs (debugged, work)
`KEYOPT(1)=2` (TEMP DOF) · **`KEYOPT(2)=1` (penalty — penalty *honors* the TCC value; MPC may not)** · `KEYOPT(12)=5` (bonded-always for a fixed mating joint). This trio gives a thermally-active bonded contact that conducts through the field-14 TCC.

### Cannot be fixed post-hoc (confirmed by ~14 failed attempts)
A contact element's `KEYOPT(1)` **cannot change after the element is generated**; a Mechanical **environment APDL snippet runs too late** to alter the assembled DOF; and `analysis.Delete()` on the Static system is a **no-op** for this. The only cures are (A) author the thermal analysis/contacts **fresh in a thermal environment**, or (C) build the contact in **MAPDL** with the KEYOPTs above.

---

## 1. Decision tree (ranked, all headless)

```
START
 │
 ├─ (A) PREFERRED — pure-Workbench, keeps Mechanical's contact/mesh/defeature:
 │      Create a Steady-State (or Transient) Thermal system that SHARES the
 │      Model cell. The thermal ENVIRONMENT regenerates CONTA174 with TEMP DOF
 │      and applies the contact's "Thermal Conductance" (Program Controlled or
 │      Manual TCC). Drive via wbjn (system/share) + PyMechanical (mesh/loads/solve).
 │      → §2.  Use this unless you need APDL-level control.
 │
 ├─ (B) If you must stay in ONE system (no new thermal cell) but on a Mechanical
 │      model whose ENVIRONMENT is thermal: set Manual TCC with a Commands
 │      (APDL) snippet under the Contact Region using the cid/tid real-const IDs
 │      Mechanical injects.  → §2.4.  (Does NOT rescue a Static Structural env —
 │      a structural env still writes KEYOPT(1)=0.)
 │
 └─ (C) ESCAPE HATCH — most robust headless, full control: drop to MAPDL.
        Either (C1) re-solve an existing structural deck as thermal by flipping
        element types, or (C2) build the thermal-contact deck from scratch.
        → §3.  Use when WB sharing/regeneration is unreliable, when you already
        live in PyMAPDL, or when you need exact KEYOPT/real-constant control.
```

---

## 2. Canonical Workbench fix — share the Model cell with a Thermal system

### 2.1 Why sharing works
A second analysis system whose **Model** cell is *shared* (not just geometry-shared)
with the structural system reuses the same mesh/connections tree, but each system
owns its **Environment** (Analysis branch). When Mechanical writes the thermal
environment's deck, it emits `CONTA174` with `TEMP` DOF and writes the contact's
**Thermal Conductance** real constant. This is the documented "create a thermal
contact pair across the joint **in the thermal environment**" behavior. The cost
you already observed: a **Model Update** (regen) and a **re-defeature** because the
thermal branch triggers a fresh mesh/geometry refresh.

### 2.2 wbjn (Workbench project journal) — add a shared Steady-State Thermal system

Run headless: `runwb2 -B -R project.wbjn` (Windows/Linux; `-B` batch, `-R` run journal).
`<SYS>` is the existing Static Structural system's name (inspect with
`GetAllSystems()` / look in the `.wbpj`).

```python
# project.wbjn  (Workbench/IronPython context — NOT PyMechanical)
import os

# 1) open the existing project
Open(FilePath=r"path/to/project.wbpj")

structural = GetSystem(Name="SYS")          # existing Static Structural

# 2) create a Steady-State Thermal template instance
tmpl = GetTemplate(
    TemplateName="Steady-State Thermal",
    Solver="ANSYS")
# (use "Transient Thermal" for a transient cooldown)

# 3) create the new system so it SHARES the Model cell of the structural system.
#    Sharing the Model cell also shares Engineering Data + Geometry upstream.
thermal = tmpl.CreateSystem(
    Position="Right",
    RelativeTo=structural,
    DataTransferFrom=[Set(
        FromComponent=structural.GetComponent(Name="Model"),
        TransferName=None,
        ToComponentTemplate=tmpl.GetComponentTemplate(Name="Model"))])

# 4) force a project-level update so the shared Model regenerates the thermal env
Update()
Save(Overwrite=True)
```

Notes / version-dependent:
- The exact `Set(FromComponent=…, ToComponentTemplate=…)` share-link form is the
  pattern Workbench records when you drag a system's *Model* cell onto another's.
  **Easiest, most reliable way to get the precise call for your release:** do the
  share **once** in the GUI, then read `File ▸ Scripting ▸ Record Journal…`
  (or the auto `*.wbjn` in the project) and lift the exact `CreateSystem(... 
  DataTransferFrom=[...])` line. Template names ("Steady-State Thermal",
  "Transient Thermal") are stable across 2019R1–2026R1.
- Sharing **Model** (not just Geometry) is what makes the *connections/contacts*
  carry over and be re-emitted by the thermal environment.

### 2.3 PyMechanical / ACT — refresh model, mesh, defeature, loads, solve

Two ways to reach the thermal environment headless:
- **Embedded** (`ansys.mechanical.core.App`) — run scripted Mechanical with no GUI.
- **Remote session** (`launch_mechanical()` → `mechanical.run_python_script(...)`).
- **From a wbjn**: `system.GetContainer(ComponentName="Model").Edit(Interactive=False)`
  then `SendCommand(Language="Python", Command="…ACT…")`.

ACT script (runs *inside* the thermal Model/Mechanical):

```python
# --- ACT / PyMechanical, executed in the THERMAL system's Mechanical session ---
model    = ExtAPI.DataModel.Project.Model

# (a) refresh materials / geometry so the shared model is current
model.RefreshMaterials()                 # re-read Engineering Data
# geometry/CAD refresh if attached through a CAD link:
# ExtAPI.DataModel.Project.Model.Geometry.UpdateGeometryFromSource()

# (b) ensure the thermal analysis branch exists (if not created via wbjn share)
analysis = model.Analyses[0]
if analysis.AnalysisType != Ansys.Mechanical.DataModel.Enums.AnalysisType.SteadyStateThermal:
    analysis = model.AddSteadyStateThermalAnalysis()   # or AddTransientThermalAnalysis()

# (c) re-apply defeaturing BEFORE meshing (virtual topology / mesh defeature size)
mesh = model.Mesh
mesh.Defeaturing          = True
mesh.DefeatureSize        = Quantity("0.5 [mm]")    # your defeature tolerance
# (virtual topology, if you used it:)
# vt = model.GeometryImportGroup  # or Model.AddVirtualTopology(); vt.GenerateVirtualCells()

# (d) regenerate the mesh on the shared model
mesh.GenerateMesh()

# (e) make the contact THERMAL and set conductance
for conn in model.Connections.Children:
    for cr in conn.Children:
        if cr.DataModelObjectCategory == Ansys.Mechanical.DataModel.Enums.DataModelObjectCategory.ContactRegion:
            cr.ContactType = Ansys.Mechanical.DataModel.Enums.ContactType.Bonded   # or Rough/NoSeparation as needed
            # ---- Thermal Conductance property (ACT ContactRegion) ----
            # Program Controlled = "perfect"/auto-calculated high conductance:
            cr.ThermalConductance = Ansys.Mechanical.DataModel.Enums.ContactFormulation.ProgramControlled
            #   (enum name is ThermalConductanceType in some releases)
            # Manual finite TCC:
            cr.ThermalConductance      = Ansys.Mechanical.DataModel.Enums.ThermalConductanceType.Manual
            cr.ThermalConductanceValue = Quantity("5000 [W m^-1 m^-1 C^-1]")  # = W/(m^2·K); units follow project

# (f) thermal boundary conditions (example: fix temps on two faces)
hot  = analysis.AddTemperature();  hot.Location  = ExtAPI.DataModel.GetObjectsByName("hot_face")[0];  hot.Magnitude.Output.SetDiscreteValue(0, Quantity("300 [K]"))
cold = analysis.AddTemperature();  cold.Location = ExtAPI.DataModel.GetObjectsByName("cold_face")[0]; cold.Magnitude.Output.SetDiscreteValue(0, Quantity("4 [K]"))

# (g) solve, headless
analysis.Solution.Solve(True)     # True = wait/synchronous
# results -> analysis.Solution.Children (Temperature, Heat Flux, Reaction Probe...)
```

**Property-name caveats (version-dependent — verify against your release's ACT
API browser, `Mechanical Scripting ▸ API ▸ ContactRegion`):**
- `ContactRegion.ThermalConductance` → the *method* selector enum
  (`ProgramControlled` / `Manual`). In some 20xx releases the enum type is
  `ThermalConductanceType`; in others the property pair is
  `.ThermalConductanceType` + `.ThermalConductanceValue`.
- `ContactRegion.ThermalConductanceValue` → the finite TCC magnitude (a `Quantity`),
  active only when the selector = `Manual`.
- If your build exposes neither cleanly, fall back to the APDL snippet in §2.4
  (always works).

### 2.4 Manual TCC via a Commands (APDL) snippet under the Contact Region

When you add a **Commands** object under a Contact Region in a *thermal* Mechanical
tree, Mechanical injects parameters `cid` (contact real-const set) and `tid`
(target real-const set) — the very IDs printed in `solve.out` as
`Real Constant Set For Above Contact Is <cid> & <tid>`. TCC is field 14, reached
with `R` (fields 1–6) + `RMORE` (7–12, 13–18, …). This is the robust headless way
to set a *finite* manual TCC and is environment-agnostic to property-name churn:

```apdl
! Commands(APDL) object UNDER a Contact Region in a THERMAL environment.
! ARG1 (Details view) = desired TCC value.  cid/tid auto-supplied by Mechanical.
r,cid              ! select contact pair real-constant set
rmore,,,,,,        ! step over fields 7-12 (blank = keep Mechanical defaults)
rmore,,arg1        ! field 14 = TCC  (7→ , 8 , 9 , 10 , 11 , 12 | 13 , 14=arg1)
                   ! pattern: rmore fields are (7,8,9,10,11,12) then (13,14,...)
r,tid              ! repeat on target side for symmetric (auto-asymmetric) contact
rmore,,,,,,
rmore,,arg1
```
> The `rmore,,arg1` here places `arg1` in the **14th** real-constant slot because
> the first `rmore` covers 7–12 and the second begins at 13; the value after the
> first comma of the second `rmore` is field 14. (This is PADT's published pattern;
> confirm slot alignment by `RLIST` after solve on your model.)

---

## 3. PyMAPDL / APDL escape hatch (most robust headless)

### 3.1 Can you reuse an existing structural contact deck and just re-solve thermal?

**Yes, with three changes** — and `ETCHG,STT` does only part of the job:

| Entity | Structural | Thermal | How to convert |
|--------|-----------|---------|----------------|
| Solid elements | SOLID185/186/187 | SOLID70 / SOLID90 / SOLID87 | **`ETCHG,STT`** (185→70, 186→90, 187→90) *and* assign thermal `KXX`. |
| Target | TARGE170 | TARGE170 (unchanged) | nothing — TARGE170's DOF follow the paired CONTA174. |
| Contact | CONTA174 `KEYOPT(1)=0` | CONTA174 `KEYOPT(1)=2` | **manual `KEYOPT,<contype>,1,2`** — *not* touched by ETCHG (no companion). |

`ETCHG,STT` element-pair table (from the command reference) contains
`185 > 70`, `186 > 90`, `187 > 90`, `181 > 131`, etc., but **CONTA174/TARGE170 are
absent** — i.e. "elements without a companion element are not switched." So after
`ETCHG,STT` you must still hand-set the contact element type's `KEYOPT(1)=2`
(pure thermal) or `=1` (thermal-structural). Also: `ETCHG` does **not** create
material conductivity — define `MP,KXX` (and `MP,C`,`MP,DENS` for transient).

```apdl
/PREP7
ETCHG,STT          ! SOLID185->70, SOLID186/187->90/90 ; CONTA174/TARGE170 untouched
ET,<contype>,174   ! (already 174) ; now flip its DOF to thermal:
KEYOPT,<contype>,1,2   ! CONTA174 -> TEMP DOF (pure thermal). Use 1 for UX,UY,UZ,TEMP.
MP,KXX,<solidmat>,<k> ! thermal conductivity (ETCHG does NOT add this)
RMODIF,<rcset>,14,<TCC>   ! set/keep TCC in field 14 of the contact real-const set
FINISH
/SOLU
ANTYPE,STEADY      ! or ANTYPE,TRANS for transient
! ... apply D,...,TEMP and SOLVE (see §3.2)
```
> Practical caveat: round-tripping a Mechanical-exported structural `ds.dat` is
> fiddly (you must find each solid `ET` and the contact `ET`/`rcset` numbers).
> For reliability, prefer **building the thermal deck cleanly** (§3.2) or the
> Workbench share (§2).

### 3.2 Minimal working PyMAPDL thermal-contact deck (build clean)

Two blocks (e.g. two cubes touching) with a finite TCC across the interface,
steady-state. `RMODIF`/`R` field **14 = TCC** confirmed.

```python
from ansys.mapdl.core import launch_mapdl
mapdl = launch_mapdl(run_location="./mapdl_thermal", nproc=4)  # headless

mapdl.clear(); mapdl.prep7()

# ---- thermal solids: SOLID90 (20-node) or SOLID70 (8-node); SOLID87 for tets ----
mapdl.et(1, "SOLID90")
mapdl.mp("KXX", 1, 15.0)     # W/(m.K)  -- body 1 (Ti-ish)
mapdl.mp("KXX", 2, 150.0)    # W/(m.K)  -- body 2 (Al-ish)
# (transient also: mapdl.mp("C",1,..); mapdl.mp("DENS",1,..))

# geometry: two stacked blocks sharing a coincident interface plane at z=1
mapdl.block(0,1, 0,1, 0,1)              # vol 1
mapdl.block(0,1, 0,1, 1,2)             # vol 2
mapdl.vsel("S","VOLU","",1); mapdl.mat(1); mapdl.type(1); mapdl.esize(0.25); mapdl.vmesh("ALL")
mapdl.vsel("S","VOLU","",2); mapdl.mat(2); mapdl.type(1); mapdl.vmesh("ALL")
mapdl.allsel()

# ---- contact pair: TARGE170 + CONTA174 with THERMAL DOF ----
rcset = 3
mapdl.et(2, "TARGE170")
mapdl.et(3, "CONTA174")
mapdl.keyopt(3, 1, 2)      # *** KEYOPT(1)=2 -> TEMP DOF (thermal contact) ***
mapdl.keyopt(3, 2, 1)      # algorithm: 1 = penalty (robust for thermal); MPC also ok
mapdl.keyopt(3, 12, 5)     # 5 = bonded always (perfect mating); use 0 for standard

mapdl.r(rcset)             # open real-constant set 3
mapdl.rmodif(rcset, 14, 2000.0)   # *** field 14 = TCC = 2000 W/(m^2.K) ***  (finite resistance)
# (omit TCC / leave default -> MAPDL uses a high "near-perfect" conductance)

# build target on top face of body1 (z=1), contact on bottom face of body2 (z=1)
mapdl.real(rcset); mapdl.type(2)                 # TARGE170
mapdl.asel("S","LOC","Z",1); mapdl.nsla("S",1)
mapdl.esln("S",0); mapdl.esurf()                 # generate target segments
mapdl.allsel()
mapdl.real(rcset); mapdl.type(3)                 # CONTA174
mapdl.asel("S","LOC","Z",1); mapdl.nsla("S",1)   # (in practice scope to the body2 side)
mapdl.esurf()                                    # generate contact elements
mapdl.allsel()

# ---- steady-state thermal analysis ----
mapdl.finish(); mapdl.slashsolu()
mapdl.antype("STEADY")            # ANTYPE,0  (steady-state); use TRANS for transient
# boundary temperatures
mapdl.nsel("S","LOC","Z",0);  mapdl.d("ALL","TEMP",300.0)   # hot base
mapdl.nsel("S","LOC","Z",2);  mapdl.d("ALL","TEMP",4.0)     # cold top
mapdl.allsel()
mapdl.solve(); mapdl.finish()

# ---- read .rth ----
mapdl.post1()
mapdl.set("LAST")
mapdl.post_processing.nodal_temperature()         # array of T
# or: result = mapdl.result ; nnum, temp = result.nodal_temperature(0)
mapdl.exit()
```

Transient variant: `mapdl.antype("TRANS")`, add `MP,C` and `MP,DENS`, set
`TIMINT,ON`, `IC,ALL,TEMP,<T0>`, time-step with `TIME`/`DELTIM`/`SOLVE`, read the
`.rth` at each substep. CONTA174 `KEYOPT(1)=2` and TCC@field-14 are identical.

**Key confirmations:**
- `KEYOPT(3,1,2)` → CONTA174 gets `TEMP` DOF (thermal). `1` would give
  `UX,UY,UZ,TEMP`.
- `RMODIF(rcset, 14, TCC)` → TCC is real-constant **field 14**. `q = TCC·ΔT`.
- `ESURF` after selecting the interface nodes generates both target (TARGE170)
  and contact (CONTA174) elements onto the underlying solid faces.
- Default/blank TCC ⇒ MAPDL applies a calculated **high** conductance
  (near-perfect contact); set field 14 for finite resistance.

---

## 3a. After ANY contact change, rebuild the mesh (or it's a no-op)

**Contact elements are part of the mesh.** Adding/deleting/regenerating a contact, or
flipping its DOF, does nothing at solve time unless the mesh is regenerated — and
`mesh.GenerateMesh()` **alone is a no-op if Mechanical doesn't think the mesh is stale.**

```python
model.Mesh.ClearGeneratedData()   # force the mesh (incl. contact elements) stale
model.Mesh.GenerateMesh()         # now contact elements are re-emitted
# only then: analysis.Solution.Solve(True)
```

## 3b. Connectivity gate (catch islanded bodies BEFORE solving)

After defeaturing/contact regeneration, build the **active-contact graph** — edges
`(source_body, target_body)` from the *regenerated, analysis-correct* contacts (NOT
stale structural ones) — and run **union-find**. Verify every **BC body** and every
**QoI body** falls in **one connected component**. Notes:
- A **steady** single-BC thermal solve is itself a connectivity test: singular ⇔ an
  isolated body exists.
- A **transient** solve is non-singular even with islands — islanded bodies just stay
  at their initial temperature (silent failure). So run the union-find check explicitly
  rather than relying on the transient to error out.

---

## 4. Why the ~14 GUI/headless "fixes" all fail

All of these fail for the **same** reason: they operate on geometry/mesh/contact
*detail* while the **solving environment is still structural**, so when Mechanical
writes the deck it emits `CONTA174 KEYOPT(1)=0` (no `TEMP` DOF). The DOF set is a
property of the **environment physics at deck-write time**, not of the contact
object, the mesh, or any pre-solve snippet.

| Attempted fix | Why it can't work |
|---|---|
| Regenerate contact in **structural** context | Structural env ⇒ deck still structural ⇒ `KEYOPT(1)=0`. |
| Mesh **clear + rebuild** | Re-meshes solids; contact DOF still set by structural env at write. |
| **Pinball** radius increase | Controls *which* gaps conduct, not *whether* the element has a TEMP DOF. With `KEYOPT(1)=0` there is no thermal DOF to conduct through. |
| **Adjust-to-Touch** / interface treatment | Closes the gap geometrically; irrelevant to DOF set. |
| **KEYOPT snippet in the structural env** | Mechanical (re)writes the contact `ET`/KEYOPTs for a *structural* deck; even if the snippet runs, the env's physics overrides DOF, and TEMP equations are never assembled. |
| **Delete the Static Structural** branch | Removing the *solved* system doesn't change that the *current* environment writing the deck is structural; you need a **thermal** environment to exist and write the deck. |
| `ETCHG,STT` | Converts solids (185→70, 186/187→90) but **CONTA174/TARGE170 have no companion** in the ETCHG pair table → contact is left structural. |
| Set TCC real constant alone (`RMODIF …,14,…`) | Writes a conductance value onto an element with **no TEMP DOF** ⇒ value is never used; nothing conducts. |

**The only things that actually flip the DOF set:**
1. A **thermal environment** writes the deck (Workbench Model-cell share, §2), or
2. You **manually** set CONTA174 `KEYOPT(1)=1` or `2` in an **APDL thermal solve**
   (§3) where the assembled equations include `TEMP`.

---

## 4b. PROVEN headless fix (reproduced on a representative multi-body assembly) — supersedes guesswork in §2   `[VERIFIED]`

The reliable way to make Workbench emit a correct **thermal** deck (verified):
```python
# pywb.launch_workbench → Open(project) → start_mechanical_server('SYS')
#   → connect_to_mechanical(...)  (PyMechanical, same Model)
analysis = Model.AddSteadyStateThermalAnalysis()      # or AddTransientThermalAnalysis()
analysis.WriteInputFile(r"path/to/steady.dat")        # emits the thermal deck — no GUI
```
The emitted deck carries the **correct thermal contact**: `et,N,291` (**SOLID291** higher-order thermal tet;
SOLID279/285 also thermal), `keyo,cid,1,2` (**CONTA174 KEYOPT(1)=2 = pure thermal**), and **TCC on
real-constant field 14**. Confirms §0/§3.

Patterns this exposes:
- **TCC values encode the R_tc material classes** → grouping real-constant sets by TCC value = ready-made
  calibration knobs (e.g. 5000 = Ti–Ti, 10000 = Ti–Cu, 20000 = Cu–Cu). **⚠️ A "Program-Controlled" thermal
  conductance is auto-calculated VERY HIGH (≈ near-perfect, from the bodies' `KXX`) — it is NOT a physical R_tc;
  for calibration you MUST set a manual TCC on real-constant field 14.**
- **Each body gets its own MAT** (`MP,KXX,1..N`) → `ESEL,S,MAT,,i` selects exactly one body.
- **Drive the deck without auto-solving:** truncate the deck at the first `/solu`, append `finish`,
  `mapdl.input(deck)` → full `/prep7` model in memory; then issue your own `/SOLU`, BCs, `SOLVE`.
  (`mapdl.input()` of a ~100 MB / 1.3 M-line deck works; truncating gives control.)

## 4c. Recovering & GATING thermal connectivity headless (answers live open-questions)

**Do NOT build the body-connectivity graph from `mapdl.mesh.grid` (pyvista).** `[VERIFIED]` The VTK
grid silently **drops TARGE170** (and some link/surface elements) — `ansys_elem_type_num` shows only
`[174, 279, 291]` and `grid.n_cells` < model element count. A union-find from the grid sees each CONTA174 surface touching only ONE
body → every pair maps to one body → all-singleton components (false "everything disconnected").

**`get_array(ELEM,ATTR,REAL/MAT)` does not honor `ESEL,ENAME`** `[VERIFIED]` (it fills by element
number over the master set, returning identical real-constant IDs across different element types, e.g. CONTA174 and TARGE170) — don't use it to
pair reals to bodies.

**`[DOCS-ONLY — not executed]` Recipe — contact pair → (bodyA, bodyB) by splitting the two sides under each real via ENAME** (the MAPDL-selection route; **run once to confirm** — the offline deck parse below is the verified path):
```python
def bodies_of_real(mapdl, r, body_mat_ids):
    sides = {}
    for ename, tag in ((174, "A"), (170, "B")):          # contact side / target side
        def reselect():
            mapdl.allsel(); mapdl.esel("S","REAL","",r); mapdl.esel("R","ENAME","",ename)
            mapdl.nsle("S"); mapdl.esln("S",0); mapdl.esel("R","ENAME","",291)  # thermal solids only
        reselect(); mats=[]
        for k in body_mat_ids:
            mapdl.esel("R","MAT","",k)
            if int(mapdl.get("n","ELEM","","COUNT"))>0: mats.append(k)
            reselect()
        sides[tag]=mats
    return sides["A"], sides["B"]
```
(Per-MAT `ESEL,R` + COUNT is deterministic; sidesteps the `get_array` quirk and the "cid/tid consecutive" assumption.)

**PREFERRED — offline deck parse (most reliable; avoids BOTH traps above)** `[VERIFIED]`**:**
in the WB deck, **solids use MAT 1..N, one MAT per body**, named in `/com,Elements for Body N '<name>'`;
**contact element types use MAT/TYPE/REAL ≥ N+1 and are declared by PARAMETER name** (`*set,cid,192` then
`et,cid,174`) — so a numeric `et,N,M` regex **misses them**. Each `/wb,contact` "Create Contact Region" block
holds the contact eblock (compact) + a comment `… Real Constant Set … Is 193 & 192`. Map contact-element nodes
→ body via the solid node→body table, and read the companion pair from that comment → direct (real → bodyA,bodyB)
map, no MAPDL selection, no pyvista grid.

**⚠️ Symmetric (deformable-deformable) contact breaks the cid/tid split** `[VERIFIED]`: when both
bodies carry **both** CONTA174 (cid) **and** TARGE170 (tid) — the Workbench default for many auto pairs —
splitting interface nodes by **element type** (174 vs 170) does **not** separate the two bodies; it yields
**self-links** (a node matched to itself, gap≈0, `n_contact == n_target`). **You MUST split interface nodes by
OWNING SOLID BODY** (node→MAT from the solid eblocks, MAT ≤ N_bodies; body name in the preceding
`/com,… Elements for Body N '...'`), then match body-A nodes to the **nearest** body-B nodes (KD-tree on the
single `nblock` coords) for the real cross-gap pairs. **Bug symptom: ~all matched pairs have gap≈0 and nc==nt.**
(The `bodies_of_real` ENAME recipe above is valid only for *asymmetric* contact.)

**`CNCHECK` — which pairs actually CLOSE (zero-conduction filter), HIGH VALUE** `[DOCS-ONLY — not executed; CNCHECK semantics from the command ref, run to confirm output format]`**:**
```apdl
CNCHECK,DETAIL    ! lists EVERY pair WITHOUT solving: real set, elem counts, status (closed/near-open/far-open), gap, penetration
CNCHECK,POST      ! partial solution → writes Jobname.RCN (read initial contact status in /POST1)
CNCHECK,ADJUST    ! physically MOVE contact nodes onto the target to close gaps/penetration (MORPH also morphs the solid mesh)
```
A bonded thermal pair that is **far-open conducts ZERO regardless of TCC** — either **exclude** open/far pairs
from the conduction graph, **or `CNCHECK,ADJUST`** to close a pair that *should* be touching (e.g. a real joint
lost to defeature tolerance — this can restore a severed cold path). **⚠️ But on symmetric pairs or large (≫pinball) gaps, `CNCHECK,ADJUST` and PINB-enlarge can backfire (spurious double-detection → *less* conduction) — there, drop the contacts for a LINK33 network (§4e).** Capture CNCHECK output to a
file (it floods context) and parse it.

### Post-defeature thermal-connectivity GATE (do BEFORE any cryo-contact calibration)
1. `CNCHECK,DETAIL` → keep only **closed** (conducting) pairs.
2. Map each closed pair → its two bodies (recipe above) → **union-find**; confirm every BC body and QoI body
   are in **ONE component** reaching the intended boundary.
3. **Confirm empirically:** a single-anchor transient (anchor ONE body) — the bodies that move off the initial
   temperature **are** the reachable component. (Steady single-anchor solve = connectivity test: singular ⇔
   isolated body; transient just leaves islands at init T.)

**Why it matters (a real production finding):** defeaturing removed bridge/decoupler bodies, leaving a large gap (much greater than the pinball radius) with
**no conduction path** from the cold anchor to the assembly downstream bodies — the spatial FEM then cannot reproduce series
conduction at any TCC. A **physics** failure introduced by geometry prep, invisible unless you gate connectivity
on *closed* pairs. If the path is severed, anchor at **measured** flange temps and predict downstream downstream bodies via
the internal series chain — but only if body↔body pairs are themselves closed.

---

## 4d. "Topology connected but the cold chain won't propagate" — conduction triage (round-2)

**Crucial nuance: a deck-topology union-find showing ONE component does NOT mean the assembly conducts in
finite time.** With penalty thermal contact each junction has resistance `R = 1/(TCC·A_contact)`. **TCC (real-constant field 14) is PER-AREA** (heat/time·area·temp, i.e. W/(m²·K)) so the junction conductance is `TCC·A_contact` — a large-looking TCC over a tiny real contact area is still a weak link (TCC may be a `%TABLE%` for pressure/temperature/spatial variation). If the real
contact area is small, per-junction R is huge and a transient propagates cooling only **~1–2 bodies past an
anchor** even though every body is "connected" on paper. (Illustration: a deck that forms **one connected
component** over the whole assembly can still leave bodies two-or-more junctions from the anchor sitting at their
initial temperature for the entire transient — graph-connectivity is not finite-time conduction.)

**Correction to §4:** a Workbench-**emitted thermal deck already has correct thermal contacts**
(`keyo,cid,1,2` TEMP DOF + `keyo,cid,12,5` bonded-always + `keyo,cid,9,1` ignore-gaps + TCC field 14).
Inserting KEYOPT "before the eblock" changed nothing → **DOF was not the blocker here.** The §4 DOF trap is
specific to **reusing STRUCTURAL contacts**; for a properly emitted thermal deck, suspect conductance/time or
topology instead.

### Triage ladder — which symptom ⇒ which cause
1. **KEYOPT(1) = 2?** (TEMP DOF). Correct thermal deck: yes; reused structural: no → §4 trap. Also note
   **KEYOPT(2): penalty (0/1) conducts via the finite TCC; MPC (2) imposes temperature-equality = *perfect*
   conduction, TCC ignored** — **don't use MPC if you want a finite TCC**, and MPC constraints are **silently
   skipped at nodes that already carry a prescribed (Dirichlet) temperature BC** (lost-bond / over-constraint
   trap). Switching a pair to MPC (or huge TCC) is a perfect-conduction probe.
2. **`CNCHECK,DETAIL`** closed-pair count — far-open bonded pairs conduct **zero**; `CNCHECK,ADJUST` to close
   pairs that should touch.
3. **Topology union-find** (offline deck parse, §4c) — one component on paper?
4. **★ Decisive HIGH-TCC transient:** `[DOCS-ONLY]` `RMODIF` **every** contact real's field 14 → e.g. **1e7**, anchor, re-run
   the transient. (⚠️ a *too-large* TCC can cause numerical instability — if the high-TCC solve diverges/oscillates
   instead of conducting, back off to a large-but-moderate value; the Program-Controlled default is deliberately
   "large enough, not too large.")
   - Chain **now cools** ⇒ **conductance + finite-time limited (best case)** — the model is FINE; raising TCC
     (your calibration knob) propagates cooling.
   - Chain **still local** ⇒ not conductance → step 5.
5. **Long / steady solve** with high TCC:
   - Steady **connects** (only a few genuinely-free bodies stay singular) ⇒ it was finite-time/conductance.
   - Steady **still fragments** ⇒ **genuine topological fragmentation** — the deck-graph overcounts (contact
     elements on coincident/degenerate nodes = false edges); the true *conducting* topology is clustered. Fix
     with **explicit inter-stage bridges**: `CP,…,TEMP` couples the two faces to ONE temperature DOF (**perfect
     bond, ZERO resistance — `CP` precludes any thermal resistance**) or add real conducting geometry — not by tuning TCC.

| Symptom | Cause | Action |
|---|---|---|
| Local cooling; **high-TCC fixes it** | per-junction R too high for the time window | raise TCC = calibrate; model viable |
| Local cooling; high-TCC + steady **still** fragment | true topological fragmentation (false deck edges) | add inter-stage bridges / temperature couples |
| **No** contact conducts (not even neighbours) | DOF / formulation | check `keyo,cid,1,2`; MPC or huge TCC for perfect-conduction probe |

**Localize a broken junction directly** (more decisive than reading temperatures): measure the heat through each
stage's cross-section — `NSEL` the surface → `ESLN` → `FSUM` → `*GET,q,FSUM,0,ITEM,HEAT` (needs **Nodal-Forces
output ON**, else zero). If heat flows *into* body 1 but not *out* toward body 2, that junction is the break.

---

## 4e. Robust fallback — LINK33 thermal-conductor network (when bonded contacts won't conduct) `[VERIFIED]`

> **Worked example (representative — a generic illustrative case, not a specific project result):** the
> LINK33 network solved end-to-end (steady anchor non-singular, all bodies reach the anchor) and calibrated
> against a representative measured cooldown dataset (better than a single-node lumped model); the
> `AREA=(A/N)·L` trick (L cancels) held up and the calibration-knob landscape was convex single-basin.
> **Key physics lesson (generalizable):** the joint conductances (R_tc) can turn out **orders of magnitude more
> conductive than the solid conduction path** ⇒ the cooldown is then **SOLID-conduction-limited and R_tc is NOT
> the lever** (it is left unconstrained by the cooldown data).
> **Generalizable gate — "is R_tc even the lever?":** before calibrating contact R_tc, set **all** joint
> conductances very high and check whether the QoI barely moves; if so the response is solid-path-limited and
> R_tc is not the knob (calibrate the solid conductance / geometry instead). This is the same high-TCC probe as
> §4d, repurposed as a sensitivity gate.

When a **defeatured multi-body import** has interface gaps up to ~mm–cm (≫ pinball), bonded thermal contacts
can't be made to conduct reliably headless — KEYOPT-before-eblock, high TCC, PINB-enlarge, and `CNCHECK,ADJUST`
all failed or made it **worse** (on **symmetric** pairs, enlarging PINB causes spurious double-detection that
*reduces* conduction). Robust fix: **delete the contacts and build an explicit LINK33 (2-node thermal bar)
conductor network** — a guaranteed conducting graph with exactly your calibration knobs.

```apdl
ESEL,S,ENAME,,174 $ EDELE,ALL          ! drop CONTA174
ESEL,S,ENAME,,170 $ EDELE,ALL          ! drop TARGE170
ET,900,LINK33                           ! 2-node thermal conduction bar
MP,KXX,901,5000   ! one MP per R_tc class; KXX numerically = the per-class TCC (5000 Ti–Ti / 10000 Ti–Cu / 20000 Cu–Cu)
! per-link real constant: AREA = (A_region / N_links) * L_link
!   → G_link = KXX·AREA/L = KXX·(A_region/N)  →  Σ over N links = KXX·A_region
R,<rid>,<(A_region/N)*L_link>           ! L CANCELS → robust for near-coincident OR far gaps
```
Build links by matching interface node pairs across the gap (use the **symmetric-contact body split**, §4c).
Cap ~60 links/region (subsample) to bound element count (~18k); preserve total conductance by rescaling `A/N`.
**⚠️ LINK33 cannot be zero-length** (nodes I,J must not be coincident) — for coincident / near-coincident
interface pairs use `NUMMRG,NODE` (perfect bond) instead, or enforce a min link length; the `AREA=(A/N)·L`
formula also degenerates as `L→0`.
**⚠️ In a TRANSIENT, keep the LINK33 conductors PURE — set `MP,DENS=0` / `MP,C=0`** (KXX only). LINK33 with
DENS+C adds **thermal mass** (heat capacity) per bar; ~18k bars would inject spurious capacitance into the
cooldown. The real bodies' solids (SOLID291 + their DENS/C) carry the mass; the links must only **conduct**.

**Why LINK33, not `CP,…,TEMP`:** `CP` (temperature couple) connects but gives **R = 0 (perfect, not
calibratable)**; LINK33 gives a finite, tunable conductance where **the 3 class `KXX` values ARE the physical
calibration knobs** and link length `L` cancels — insensitive to the messy defeatured gaps. Total interface
conductance = `KXX·A_region` (matches `Q = TCC·A·ΔT`). This sidesteps ALL contact-status/pinball/DOF issues.

**Calibration loop efficiency:** the sweep changes only the 3 class `MP,KXX` values — **re-`SOLVE` without
remeshing** (geometry/mesh/BC unchanged): keep the model in `/prep7`, loop `MP,KXX` → `/SOLU` → `SOLVE` → read
`.rth`. Far cheaper than rebuilding the LINK33 network or re-meshing per iteration.

## 5. Version flags

- Element/KEYOPT/real-constant semantics (CONTA174 KEYOPT(1) map, TCC=field 14,
  ETCHG pair table) are stable across MAPDL 2019R1 → 2026R1.
- **PyMechanical ACT property names** for the contact thermal-conductance selector
  drift between releases (`ThermalConductance` enum vs `ThermalConductanceType` +
  `ThermalConductanceValue`). Verify in your release's Mechanical Scripting API
  browser; if unclear, use the §2.4 APDL `R`/`RMORE` snippet (release-proof).
- **wbjn `CreateSystem(... DataTransferFrom=[Set(...)])`** share syntax: record it
  once from the GUI for your exact release rather than hand-writing it.
- `runwb2 -B -R file.wbjn` batch flags and `launch_mechanical` / embedded
  `App` APIs are current for PyAnsys with 2023R1+ (embedded app needs 2023R2+).

---

## Sources

- CONTA174 element reference (KEYOPT(1) DOF map; real-constant list incl. TCC):
  https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_elem/Hlp_E_CONTA174.html
- TARGE170 element reference (DOF follow paired contact element):
  https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_elem/Hlp_E_TARGE170.html
- ETCHG command reference (STT pair table; "no companion element not switched"):
  https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_cmd/Hlp_C_ETCHG.html
- PADT — "Making Thermal Contact Conductance a Parameter … with an APDL Command
  Object" (TCC = 14th real constant; `r,cid`/`rmore,,arg1` snippet):
  https://www.padtinc.com/2017/04/06/ansys-mechanical-contact-condutance-apdl/
- PADT — "ANSYS Mechanical Contact and Thermal Contact Conductance" (overview):
  https://www.padtinc.com/blog/ansys-mechanical-contact-and-thermal-contact-conductance/
- SimuTech — "Thermal Contact at Joints in Ansys Workbench Mechanical" (joints/
  contacts carry heat only when defined in the thermal environment):
  https://simutechgroup.com/thermal-contact-at-joints-in-ansys-v14-5-workbench-mechanical/
- SimuTech — "Heat Conduction Across a Contact Element Gap" (pinball gate, TCC):
  https://simutechgroup.com/heat-conduction-across-a-contact-element-gap-in-ansys-workbench-mechanical/
- SimuTech — "Optimal Thermal Contact Settings | Ansys Mechanical Workbench":
  https://simutechgroup.com/thermal-contact-settings-in-mechanical/
- Mechanics and Machines — "Setting Mechanical Contact Stiffness and Thermal
  Contact Conductivity … using Command Snippets" (cid/tid real-const IDs):
  https://mechanicsandmachines.com/?p=258
- PyMechanical — Steady-State Thermal example (ExtAPI, AddSteadyStateThermal-
  Analysis, GenerateMesh, AddTemperature, Solution.Solve):
  https://mechanical.docs.pyansys.com/version/stable/examples/gallery_examples/01_basic/steady_state_thermal_analysis.html
- PyWorkbench — PyMechanical integration example (system creation + run_python_script):
  https://examples.workbench.docs.pyansys.com/version/stable/examples/pymechanical-integration/main.html
- PyMAPDL documentation (launch_mapdl, prep7 contact, post1/.rth reading):
  https://mapdl.docs.pyansys.com/version/stable/
- Ansys Knowledge — "How to transfer systems from one WB project to another"
  (wbjn system/share patterns):
  https://innovationspace.ansys.com/knowledge/forums/topic/how-to-transfer-systems-from-one-wb-project-to-another-2/
