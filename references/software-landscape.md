# CAE Software Landscape & Selection Brief

Scope: the most popular commercial and open-source CAE tools for structural/multiphysics, CFD, thermal,
multibody, electromagnetics, plus open-source FEA/meshing/post/coupling and pre/post platforms.
Audience: a public CAE Agent Skill that must (a) pick the right tool for a job and (b) drive it
**headless/batch** wherever possible. Conventions: License = Commercial / Free (closed, no cost) /
OSS (open-source, license named). "Headless entry point" = the exact CLI/API used to run without a GUI.

---

## 1. Structural / Multiphysics — commercial

| Tool | Vendor | Primary use | License | Scripting & headless entry point | Key formats | Standout |
|---|---|---|---|---|---|---|
| **Ansys Mechanical / MAPDL** | Ansys | General FEA: static, modal, nonlinear, thermal, coupled | Commercial | **Fully headless.** MAPDL `ansysNNN -b -i in.dat -o out.out -j job` (`-np`, `-dis`). PyMAPDL (`launch_mapdl`), PyMechanical (`ansys.mechanical.core`), Workbench journals (`runwb2 -B -R jrnl.wbjn`) | `.cdb` (deck), `.db`, `.rst`/`.rth` (results), `.inp` (APDL) | Deepest multiphysics + best Python ecosystem (PyAnsys) |
| **Abaqus Standard / Explicit** | Dassault SIMULIA | Nonlinear FEA, contact, implicit + explicit dynamics | Commercial | **Fully headless.** Solver `abaqus job=Job input=m.inp cpus=N int`. Scripting: `abaqus cae noGUI=script.py` (full CAE/Python kernel) or `abaqus python script.py` (no CAE modules) | `.inp` (deck), `.odb` (results), `.cae`/`.jnl` | Gold-standard nonlinear/contact; Python Scripting Interface |
| **MSC Nastran** | Hexagon | Aerospace/auto FEA, dynamics, optimization (SOL 200) | Commercial | **Fully headless.** `nastran job.bdf scr=yes mem= sdir=` ; DMAP for solver customization | `.bdf`/`.dat` (bulk), `.op2`/`.f06`/`.h5`, `.pch` | Reference Nastran; certification heritage, SOL 200 |
| **Simcenter Nastran** | Siemens | Same Nastran lineage; tight NX/Simcenter 3D integration | Commercial | **Solve fully headless** (`nastran`). **Pre/post (NX CAE) is GUI-bound** for authoring `.sim`/`.fem` — pre-seed in GUI, then `run_journal.exe` | `.bdf`/`.dat`, `.op2`, `.sim`/`.fem` (NX) | SOL 401/402 multistep; Simcenter 3D coupling |
| **Altair OptiStruct** | Altair | Structural + **topology/shape/size optimization**, NVH | Commercial (Altair Units) | **Fully headless.** `optistruct.bat "file.fem" -option` (Win) / `optistruct file.fem` (Unix); `-nt` threads, `-mpi` | `.fem` (Nastran-like bulk), `.h3d`, `.op2`, `.out` | Industry-leading structural optimization |
| **MSC Marc** | Hexagon | Strongly nonlinear, large-strain, contact, manufacturing | Commercial | **Headless.** `run_marc -jid job -nps N`; Mentat pre/post drives Python (`py_*`) | `.dat` (deck), `.t16`/`.t19` (post) | Robust large-deformation / coupled nonlinear |
| **COMSOL Multiphysics** | COMSOL | Equation-based multiphysics (EM, thermal, structural, chem, acoustics) | Commercial | **Batch headless.** `comsol batch -inputfile m.mph -outputfile o.mph`; `comsol compile`; LiveLink for MATLAB/Java API (same COMSOL Java API underneath) | `.mph` (model+results), MATLAB `.m`, Java | Arbitrary PDE coupling; built-in physics interfaces |
| **LS-DYNA** | Ansys | Explicit dynamics: crash, impact, blast, drop, forming | Commercial (separate from core Ansys) | **Fully headless.** `lsdyna i=in.k ncpu=N memory=Nm` (+`OMP_NUM_THREADS`); MPP `mpirun … ls-dyna_mpp` | `.k`/`.key` (keyword deck), `d3plot`/`d3thdt` (binary), `.binout` | De-facto explicit/crash solver |
| **Altair Radioss** | Altair | Explicit dynamics (crash/impact), competitor to LS-DYNA | Commercial | **Headless.** `radioss runname_0000.rad` (starter) → engine `_0001.rad`; `-nt`/`-np` | `.rad` (deck), `.h3d`, A001 anim | Strong multi-domain crash; in HyperWorks |
| **ESI PAM-CRASH** | ESI (Keysight) | Automotive crash & safety, occupant/airbag | Commercial | **Headless.** `pamworld`/solver CLI with `.pc` deck; Visual-Crash pre/post | `.pc`/`.ps` (deck), `DSY`/`THP` (results) | Automotive passive-safety pedigree |

---

## 1b. Geomechanics / civil-FEM (geotechnical, rock, soil-structure)

Specialized FEM/FDM tools for soil, rock, and soil-structure interaction — built around **pressure-dependent constitutive models** (Mohr-Coulomb, Drucker-Prager + cap, Modified Cam-Clay), **effective-stress / coupled consolidation** (pore-pressure ↔ stress), staged construction, and **limit/stability analysis** (slopes, foundations, tunnels, excavations, dams). General-purpose codes (Abaqus, Code_Aster) cover much of this too via their geotechnical material libraries; the dedicated tools add geotechnical workflows, constitutive-model libraries, and reporting. (For the constitutive-model menu see `material-modeling.md` §2b; for the analysis types see `specialized-analyses.md`.)

| Tool | Vendor | Primary use | License | Scripting & headless entry point | Key formats | Standout |
|---|---|---|---|---|---|---|
| **PLAXIS 2D/3D** | Bentley (Seequent) | Industry-standard geotechnical FEA: soil/rock deformation, stability, consolidation, dynamics | Commercial | **Remote-scripting / batch via Python API** (PLAXIS `plxscripting` server over HTTP) — drives modeling, staged calc, output | native project, Python | The de-facto geotechnical FEA; deep soil constitutive library + staged construction |
| **GeoStudio** (SLOPE/W, SIGMA/W, SEEP/W, …) | Bentley (Seequent) | Modular slope-stability (LEM), seepage, stress-deformation, thermal/geothermal | Commercial | Mostly GUI; some command/automation | native `.gsz` | Coupled module suite (limit-equilibrium + FE) |
| **OptumG2 / G3** | Optum CE | **Limit analysis** (upper/lower-bound) + elastoplastic FE; rapid strength/stability | Commercial | GUI-centric; scripting limited | native | Direct collapse-load / FoS via limit analysis (no incremental push to failure) |
| **Itasca FLAC / FLAC3D** | Itasca | Explicit **finite-difference** continuum; large-strain soil/rock, mining, dynamics | Commercial | **Fully scriptable.** Native **FISH** language + **Python** API; batch/headless | `.f3dat`/`.dat` (FISH), `.sav` | Explicit FD handles large deformation / progressive failure robustly |
| **Itasca 3DEC / UDEC** | Itasca | **Discrete-element** jointed rock mass (blocky media) | Commercial | **FISH + Python**; batch/headless | `.dat`, `.sav` | Discontinuum (joints/blocks) for fractured rock |
| **RS2 / RS3** (formerly Phase2) | Rocscience | 2D/3D **rock & soil FE** — tunnels, slopes, excavations, groundwater | Commercial | GUI-centric; some automation | native | Rock-engineering FE focus; companion to Slide (LEM) |
| **Abaqus / Code_Aster (geotechnical)** | Dassault / EDF (OSS) | General FEA used geotechnically: MC/DP-cap/Cam-Clay, coupled pore-fluid consolidation ("u-p") | Commercial / **OSS (GPL-3)** | **Fully headless** (see §1 / §6 entries: `abaqus job=`, `as_run`) | `.inp`/`.odb`; `.comm`/`.med` | General-purpose nonlinear FEA with geomechanical material & coupled-consolidation capability |

---

## 2. CFD

| Tool | Vendor | Primary use | License | Scripting & headless entry point | Key formats | Standout |
|---|---|---|---|---|---|---|
| **Ansys Fluent** | Ansys | General-purpose finite-volume CFD (most widely used) | Commercial | **Fully headless.** `fluent 3ddp -g -t N -i journal.jou` (`-g` no GUI). **TUI journals** (text commands) + **Scheme**; **PyFluent** (`ansys.fluent.core`) for Python | `.cas`/`.dat` (case/data), `.msh`, CGNS, EnSight | Broadest physics + meshing; TUI fully scriptable |
| **Ansys CFX** | Ansys | Turbomachinery & rotating-machinery CFD | Commercial | **Fully headless.** `cfx5solve -def file.def -par-dist …`; CFX Command Language (**CCL**); `cfx5pre`/`cfx5post` batch (`-batch session.pre`) | `.def`/`.res`, `.ccl`, `.cse` | Coupled solver, turbomachinery focus |
| **Simcenter STAR-CCM+** | Siemens | Industrial CFD + multiphysics, automated meshing | Commercial | **Fully headless.** `starccm+ -batch macro.java -np N -podkey …`; **Java macros** (record→replay) + Simulation Operations; Python beta | `.sim` (all-in-one), `.ccm`, EnSight | Single integrated env; powerful Java automation |
| **OpenFOAM** | OpenFOAM Found. / ESI (.com) | Open finite-volume CFD toolbox (simpleFoam, pimpleFoam, …) | **OSS (GPL-3)** | **CLI-native, fully headless.** Per-app solvers (`simpleFoam`, `interFoam`); `decomposePar` → `mpirun -np N solver -parallel`; `Allrun` scripts; PyFoam | dictionary case dir (`system/controlDict`, `0/`, `constant/`), VTK, EnSight | Free, infinitely customizable; HPC standard in academia |
| **SU2** | Stanford / community | Compressible/incompressible RANS, **adjoint optimization** | **OSS (LGPL-2.1)** | **CLI-native.** `SU2_CFD config.cfg`; `mpirun -n N SU2_CFD`; Python wrappers (`SU2_CFD.py`, pySU2) | `.cfg` (config), SU2 native mesh, **CGNS**, VTK | Open-source adjoint/design optimization |
| **CONVERGE** | Convergent Science | Engine/combustion CFD with **autonomous adaptive meshing (AMR)** | Commercial | **Headless.** input dirs + `converge` solver, MPI batch | `*.in` input files, post via EnSight/Tecplot | No mesh prep — runtime AMR; combustion |
| **Autodesk CFD** | Autodesk | Mainstream design/HVAC/electronics-cooling CFD | Commercial (retiring 2026) | Mostly GUI; limited batch/API | native, STEP import | Easy CAD-coupled design CFD (legacy) |

---

## 3. Thermal (incl. spacecraft / electronics cooling)

| Tool | Vendor | Primary use | License | Scripting & headless entry point | Key formats | Standout |
|---|---|---|---|---|---|---|
| **Ansys Thermal (Mechanical)** | Ansys | Conduction/convection/radiation FEA thermal & thermal-stress | Commercial | **Headless** (same as MAPDL/Mechanical) | `.rth`, `.cdb` | Tight thermal→structural coupling (`LDREAD,TEMP`) |
| **Ansys Icepak** | Ansys | Electronics cooling (board/package/system), CFD-based | Commercial | In AEDT → **PyAEDT** non-graphical; or Fluent-based batch | AEDT project, `.cas` | ECAD-aware electronics thermal |
| **Simcenter Flotherm** | Siemens | Electronics cooling (specialized, SmartParts) | Commercial | Command/scripting + FloMCAD; batch solve | `.flo`/`.pdml` | Fast electronics-thermal modeling |
| **Simcenter 3D Thermal / TMG** | Siemens | General FE thermal + spacecraft/orbital radiation | Commercial | Solve headless; **GUI for `.sim` authoring** (NX CAE); **TMG Correlation** for thermal model-updating | `.sim`/`.fem`, TMG files | Orbital heating + thermal correlation |
| **Thermal Desktop + SINDA/FLUINT** | C&R Technologies | Spacecraft lumped-parameter thermal + fluid networks | Commercial | **Solve/sweep/post headless via OpenTD** (.NET API; Python+pythonnet/C#) on an existing `.dwg`; geometry **authoring is GUI (AutoCAD)** | `.dwg`, SINDA `.out`, save files | Aerospace thermal standard; RadCAD ray-trace |
| **6SigmaET** | Cadence (Future Facilities) | Dedicated electronics thermal (object-based) | Commercial | Scripting API; batch solve | native | Object/scenario-based electronics thermal |

---

## 4. Multibody Dynamics (MBD)

| Tool | Vendor | Primary use | License | Scripting & headless entry point | Key formats | Standout |
|---|---|---|---|---|---|---|
| **MSC Adams** | Hexagon | Rigid/flexible multibody mechanism dynamics | Commercial | **Solve headless.** `adams20xx ru-s i model.acf`/`.adm`; Adams View command language + **Python**; Adams Car batch | `.adm`/`.acf` (solver), `.cmd`, `.res`/`.req` | Industry MBD reference; vehicle (Car/Driveline) |
| **Simcenter Motion** | Siemens | MBD inside Simcenter 3D / NX | Commercial | Solve headless; **GUI authoring** (NX CAE journals) | `.sim`, solver deck | CAD-integrated MBD + FE flex bodies |
| **RecurDyn** | FunctionBay | MBD with strong large-scale flexible/contact | Commercial | ProcessNet (.NET/VB/C#) scripting; batch solve | `.rdyn`, native | Robust contact + flex multibody |
| **Project Chrono** | UChicago/community | OSS multibody + DEM + FEA + vehicle | **OSS (BSD-3)** | **Library-native** C++/**PyChrono** scripts; fully headless | Python/C++ API, OBJ/VTK out | Free, scalable, granular + vehicle dynamics |

---

## 5. Electromagnetics (EM)

| Tool | Vendor | Primary use | License | Scripting & headless entry point | Key formats | Standout |
|---|---|---|---|---|---|---|
| **Ansys HFSS** | Ansys | High-frequency 3D full-wave (antennas, RF, SI) | Commercial | **Non-graphical** via **PyAEDT** (`Hfss(non_graphical=True)`) or IronPython batch (`-ng -batchsolve -batchoptions`) | AEDT project, Touchstone `.sNp` | Gold-standard full-wave EM |
| **Ansys Maxwell** | Ansys | Low-frequency EM (motors, magnetics, transformers) | Commercial | Same AEDT/**PyAEDT** non-graphical | AEDT project | Motor/magnetic design (+ Motor-CAD) |
| **Dassault CST Studio Suite** | Dassault SIMULIA | Broadband 3D EM (time + frequency domain) | Commercial | VBA macros; **Python** (`cst` library) control; batch/distributed solve | `.cst`, Touchstone | Time-domain (FIT/TLM) breadth |
| **Simcenter MAGNET** | Siemens | Low-frequency EM / electric machines | Commercial | Scripting API (VBScript/Python COM); batch | native | Focused machine/actuator EM |

---

## 6. Open-source FEA / Multiphysics / Meshing / Post / Coupling

| Tool | Type | Primary use | License | Scripting & headless entry point | Key formats | Standout |
|---|---|---|---|---|---|---|
| **CalculiX** | FEA solver | Abaqus-syntax implicit/explicit FEA + thermal | **OSS (GPL-2)** | **CLI.** `ccx -i jobname` (reads `jobname.inp`); pre/post `cgx` | `.inp` (Abaqus-like deck), `.frd`/`.dat` | Free Abaqus-like solver; preCICE adapter |
| **Code_Aster** | FEA solver | EDF industrial-grade nonlinear/thermal/dynamics | **OSS (GPL-3)** | **CLI.** `as_run study.export`; Python `.comm` command files; in **Salome-Meca** | `.comm`, `.med` (mesh/results), `.rmed` | Very deep validated FEA; Python command language |
| **FEniCS / FEniCSx** | FEM library | Write PDEs in near-math (UFL) Python | **OSS (LGPL-3)** | **Library-native, headless.** Python (`dolfinx`) + MPI; JIT-compiled | XDMF/HDF5, `.msh` in, VTK out | PDE-from-weak-form; rapid custom physics |
| **Elmer** | Multiphysics FEM | Coupled thermal/EM/flow/structural | **OSS (GPL)** | **CLI.** `ElmerSolver case.sif` (+ `ElmerGrid`); MPI parallel; ElmerGUI optional | `.sif` (solver input), `.vtu`, `.ep` | Broad free multiphysics coupling |
| **MFEM** | FEM library | High-order/scalable finite elements (HPC) | **OSS (BSD)** | **Library-native** C++/Python, MPI; headless | `.mesh`, VTK, VisIt | High-order + AMR + massive parallel |
| **deal.II** | FEM library | Research-grade adaptive FEM C++ framework | **OSS (LGPL)** | **Library-native** C++, MPI; headless | VTK/VTU, `.msh` | Mature adaptive-FEM research library |
| **Kratos Multiphysics** | Framework | Coupled FSI/structural/CFD/DEM application platform | **OSS (BSD)** | **Python-driven** (`MainKratos.py`) + JSON params; MPI; headless | `.mdpa` (model), JSON, VTK/HDF5 | Modular multiphysics application builder |
| **Gmsh** | Mesher + post | 3D FE mesh generation (CAD via OpenCASCADE) | **OSS (GPL-2)** | **CLI** `gmsh model.geo -3 -o out.msh`; rich **Python/C++/Julia API**; fully headless | `.geo`, `.msh` (native), STEP/IGES in, UNV/MED/VTK out | Scriptable mesher with built-in CAD kernel |
| **Netgen / NGSolve** | Mesher (+FEM) | Tet/surface meshing; NGSolve adds FEM | **OSS (LGPL)** | Python API; CLI; headless | STL/STEP in, `.vol`, Neutral | Robust tet meshing + Python FEM |
| **ParaView** | Post-processor | Large-scale scientific visualization & analysis | **OSS (BSD)** | **`pvbatch script.py` / `pvpython`** (Python trace); client-server; fully headless | **VTK/VTU/VTM**, EnSight, CGNS, Exodus, XDMF | The de-facto OSS post-processor; scriptable |
| **preCICE** | Coupling library | Partitioned multiphysics (FSI, CHT) — couples existing solvers | **OSS (LGPL-3)** | **Library + `precice-config.xml`**; official adapters (OpenFOAM, SU2, CalculiX, deal.II, FEniCS, Nutils); headless | `precice-config.xml`, solver-native | Black-box coupling of independent solvers |

---

## 7. Pre/Post & Platforms

| Tool | Vendor | Primary use | License | Scripting & headless entry point | Key formats | Standout |
|---|---|---|---|---|---|---|
| **Altair HyperMesh** | Altair | High-end FE pre-processing / meshing for any solver | Commercial | **Tcl/Tk** + Python; batch `hmbatch -tcl script.tcl` | `.hm`, exports Nastran/Abaqus/LS-DYNA/OptiStruct decks | Best-in-class multi-solver meshing |
| **Altair HyperView** | Altair | Multi-solver results post/animation | Commercial | Tcl/Python; batch templates | `.h3d`, op2/odb/d3plot readers | Unified post for all major solvers |
| **Femap** | Siemens | Pre/post for Simcenter & MSC Nastran (Windows) | Commercial | **OLE/COM API** (Python/VB/C#); programmable batch | `.modfem`, Nastran `.bdf`/`.op2` | Lightweight scriptable Nastran pre/post |
| **BETA-CAE ANSA** | BETA CAE | Heavy-duty pre-processing (auto/aero) | Commercial | **Python** scripting; batch mesh (`ansa -b script`) | `.ansa`, Nastran/Abaqus/LS-DYNA decks | Top-tier large-assembly preprocessing |
| **BETA-CAE META** | BETA CAE | Multi-solver post-processing | Commercial | **Python** scripting; batch sessions | `.metadb`, all major result types | High-throughput automated post |
| **Ansys Workbench** | Ansys | Project/parametric orchestration across Ansys solvers | Commercial | **`runwb2 -B -R journal.wbjn`** (IronPython journals); **PyWorkbench** SDK | `.wbpj`, archives `.wbpz` | Parametric/persistent-data backbone |
| **PyAnsys** | Ansys | Python clients across the Ansys stack | **OSS (MIT)** wrappers (need licensed solver) | PyMAPDL, PyMechanical, PyFluent, PyAEDT, PyDPF, PyWorkbench — all support **non-graphical/headless** | per-product | Programmatic glue for entire Ansys ecosystem |

---

## 8. "Which tool for which job" — decision guide

- **Linear/nonlinear structural FEA, broad physics, Python automation** → Ansys Mechanical/MAPDL (PyMAPDL).
- **Nonlinear contact, implicit + explicit, material plasticity** → Abaqus; very large-strain/manufacturing → MSC Marc.
- **Crash / impact / drop / blast (explicit)** → LS-DYNA (or Altair Radioss / ESI PAM-CRASH for auto safety).
- **Structural / topology optimization** → Altair OptiStruct (design), or any solver wrapped in optiSLang/HEEDS.
- **Aerospace certification Nastran workflow** → MSC Nastran; **NX/Simcenter-integrated** → Simcenter Nastran.
- **Arbitrary coupled PDE multiphysics, GUI-first** → COMSOL. **Free/scriptable PDE** → FEniCSx, Elmer, Kratos.
- **General CFD** → Ansys Fluent (or STAR-CCM+ for integrated automation). **Turbomachinery** → CFX / STAR-CCM+.
  **Free/HPC/research CFD** → OpenFOAM; **adjoint design optimization** → SU2; **engine/combustion** → CONVERGE.
- **FE thermal + thermal-stress** → Ansys Thermal. **Electronics cooling** → Icepak / Flotherm / 6SigmaET.
  **Spacecraft thermal (lumped + orbital radiation)** → Thermal Desktop/SINDA-FLUINT; **FE + orbital** → Simcenter TMG.
- **Mechanism / vehicle dynamics** → MSC Adams; **CAD-integrated** → Simcenter Motion; **free** → Project Chrono.
- **High-frequency EM / antennas** → Ansys HFSS or CST; **motors/low-freq magnetics** → Ansys Maxwell / Simcenter MAGNET.
- **Multi-solver meshing/pre** → HyperMesh or ANSA (free → Gmsh/Netgen). **Post** → HyperView/META or ParaView (free).
- **Couple two independent solvers (FSI/CHT)** → preCICE.
- **Free Abaqus-like solver** → CalculiX; **free validated industrial FEA** → Code_Aster (Salome-Meca).
- **Geotechnical / soil-structure (consolidation, slope/foundation/tunnel stability, staged construction)** → PLAXIS (general geo-FEA, Python-scriptable), GeoStudio (modular LEM+FE), OptumG2/G3 (limit analysis); **large-strain/dynamic soil-rock** → Itasca FLAC/FLAC3D (explicit FD, FISH/Python); **jointed/blocky rock** → Itasca 3DEC/UDEC (DEM); **rock engineering FE** → RS2/RS3. General-purpose alternative: Abaqus / Code_Aster geotechnical material library.

---

## 9. Headless-scriptability matrix

| Class | Tools |
|---|---|
| **Fully headless / CLI-native** (solve + script with no GUI ever) | Ansys MAPDL/Mechanical/Fluent/CFX/HFSS/Maxwell (PyAnsys), Abaqus (`cae noGUI`), MSC Nastran, OptiStruct, LS-DYNA, Radioss, MSC Marc, COMSOL (`comsol batch`), STAR-CCM+ (`-batch`), OpenFOAM, SU2, CalculiX, Code_Aster, Elmer, FEniCSx, MFEM, deal.II, Kratos, Gmsh, ParaView (`pvbatch`), preCICE, Project Chrono/PyChrono, MSC Adams (solver) |
| **API/session-driven** (headless solve, programmatic but needs a started server/embedded app) | PyMAPDL/PyMechanical/PyFluent/PyAEDT (gRPC), COMSOL LiveLink (server+MATLAB/Java), Thermal Desktop OpenTD (needs existing `.dwg`), Femap (OLE/COM), CST (Python/VBA control), Itasca FLAC/FLAC3D/3DEC (FISH + Python), PLAXIS (Python remote-scripting server) |
| **GUI-bound for authoring; headless for solve** (the trap) | **Siemens NX CAE / Simcenter 3D** — `.sim`/`.fem` template authoring not reliable in pure batch → pre-seed in GUI, then `run_journal.exe`. Thermal Desktop **geometry** authoring (AutoCAD). Autodesk CFD (mostly GUI). Simcenter Flotherm/Motion authoring. |

**Rule of thumb:** every major commercial CFD/FEA *solver* runs fully headless; the GUI-bound part is almost
always **model authoring in a CAD-coupled pre-processor** (NX CAE, Thermal Desktop AutoCAD), not the solve.

---

## 10. Interoperability — exchange formats & neutral paths

**Geometry (CAD → mesher):**
- **STEP (`.stp`/`.step`)** and **IGES (`.igs`)** — universal neutral CAD; read by Gmsh, ANSA, HyperMesh, Salome, every commercial pre.
- Parasolid (`.x_t`) and ACIS (`.sat`) — common native kernels (Siemens / many).

**Mesh & deck (pre → solver):**
- **Nastran bulk `.bdf`/`.dat`** — MSC/Simcenter Nastran, OptiStruct (`.fem`), exported by HyperMesh/ANSA/Femap; near-universal FE interchange.
- **Abaqus `.inp`** — Abaqus **and** CalculiX (same syntax); exported by most pre-processors.
- **Ansys `.cdb`** — MAPDL archive deck (`CDWRITE`/`CDREAD`).
- **UNV / UFF (`.unv`)** — I-deas/universal mesh+results, widely importable (Gmsh, Salome, Code_Aster via conversion).
- **MED (`.med`, HDF5-based)** — Salome / Code_Aster native mesh+results.
- **`.msh`** — Gmsh native (and OpenFOAM/Elmer/FEniCS import via converters).
- **CGNS** — standard CFD mesh+solution (Fluent, CFX, SU2, STAR-CCM+, OpenFOAM export).

**Results & post (solver → post):**
- **`.op2`/`.f06`/`.h5`** (Nastran), **`.odb`** (Abaqus), **`.rst`/`.rth`** (Ansys), **`d3plot`** (LS-DYNA),
  **`.h3d`** (Altair), **SINDA `.out`** (Thermal Desktop) — each typically read by its vendor post or HyperView/META.
- **VTK / VTU / VTM** — open standard consumed by **ParaView**; written by OpenFOAM, SU2, Elmer, FEniCSx, MFEM, Kratos, Gmsh.
- **EnSight Gold (`.case`)** — neutral CFD/FE results (Fluent, CFX, STAR-CCM+, CONVERGE, OpenFOAM export) → ParaView/EnSight.
- **Exodus, XDMF/HDF5** — large parallel scientific results (MFEM, FEniCSx, ParaView).

**Common neutral bridges between tools:**
- CAD → mesh: **STEP/IGES → Gmsh/ANSA/HyperMesh → solver deck** (`.inp`/`.bdf`/`.cdb`).
- Mesh reuse across solvers: **HyperMesh/ANSA export** to Nastran/Abaqus/LS-DYNA/OptiStruct from one model.
- Any solver → unified post: **export EnSight or VTK → ParaView** (the universal free post path).
- Multiphysics coupling without file swap: **preCICE** maps fields between live solvers at runtime.
- Thermal → structural: temps map by interpolation even on non-matching meshes (Ansys `LDREAD,TEMP`;
  Nastran `TEMPERATURE(LOAD)`), so meshes need not be conformal.

---

## 11. Physics-AI / ML-surrogate tools (the "predict instead of solve" tier)

A distinct, fast-growing tool **class**: a model **trained on prior simulation/test data** that **predicts a field or QoI** for a new design in seconds-to-minutes instead of running the solver — used for design-space exploration, real-time digital twins, and inner optimization loops. This is a tool-**selection** category, not a solver: the strategic question is "should I run the FE/CFD solve at all, or query a trained surrogate / ROM?" Treat the whole class generically; vendor offerings churn.

| Tool class (generic) | Examples (vendor-neutral framing) | Trains on | Output | Speed vs solver | Validity envelope |
|---|---|---|---|---|---|
| **Field-prediction Physics-AI** | Ansys SimAI / GeomAI, Altair physicsAI, Simcenter geometric deep-learning | Prior solved cases (geometry + fields) | Full predicted field (stress/flow/thermal) on new geometry | ~10–100× faster | Geometry/BC/material **inside the training distribution** only |
| **Open / research operator-learning** | NVIDIA Modulus (PINNs, neural operators — FNO/DeepONet) | PDE residual and/or data | Grid-independent PDE surrogate | Fast online; training cost up front | Degrades **out-of-distribution**; needs UQ |
| **ML-built / projection ROMs (digital twin)** | TwinAI-class ROMs, optiSLang / HEEDS AI predictors, CMS/Krylov/POD ROMs (see `advanced-methods.md` §2) | FE/CFD snapshots over a parameter range | Reduced-order response, real-time | Real-time / many-query | Valid over the **parameter band it was reduced on**; verify FRF/transient |
| **Design-copilot NL assistants** | NX Design Copilot-class | Product/usage data | NL setup suggestions, design hints | n/a (assist, not predict) | Author-time aid; not an analysis result |

**Selection rule — solve vs. predict:** a trained ML surrogate / ROM is valid **only inside its training envelope** and for the QoI it was trained on; treat any query outside that envelope as an **extrapolation** (an applicability gap in V&V terms). Use surrogate/ROM/Physics-AI for fast design-space sweeps, real-time twins, and inner optimization loops — then **re-solve the chosen design on full physics before sign-off** (the same "re-solve the optimum on full FE" rule already in `advanced-methods.md` §4.3). **Never report a surrogate / Physics-AI prediction as a SIGNOFF result.** For the methodology — certified/bounded ROMs, POD-NN, neural operators, PINNs and their out-of-distribution caveat — see the surrogate and model-order-reduction treatment in `advanced-methods.md` (§2 MOR, §4.3 DOE→surrogate) and the surrogate-UQ discussion in `vv-uq.md`.

---

## SOURCES

- Abaqus headless (`abaqus cae noGUI=`, `abaqus python`, `abaqus job=`) — Washington Univ. Abaqus docs (high); abqpy docs (med); CAE Assistant / Fidelis FEA / TECHNIA blogs (med). https://classes.engineering.wustl.edu/2009/spring/mase5513/abaqus/docs/v6.5/books/cmd/pt01ch02s02.html , https://caeassistant.com/blog/abaqus-jobs/ , https://www.fidelisfea.com/post/abaqus-and-the-command-window-launch-jobs-monitor-jobs-and-more
- STAR-CCM+ `-batch` Java macros — Siemens Community Java KB (high). https://community.sw.siemens.com/s/article/Simcenter-STAR-CCM-Java-Knowledge-Base-Table-of-contents
- SU2 (`SU2_CFD config.cfg`, LGPL-2.1, CGNS) — primary: su2code.github.io official docs (high); Wikipedia (orientation). https://su2code.github.io/ , https://su2code.github.io/docs/Installation/ , https://en.wikipedia.org/wiki/SU2_code
- COMSOL (`comsol batch`, `comsol compile`, LiveLink/Java API) — COMSOL official docs & learning center (high). https://www.comsol.com/livelink-for-matlab , https://www.comsol.com/support/learning-center/article/overview-of-the-comsol-api-107912 , https://doc.comsol.com/5.5/doc/com.comsol.help.comsol/comsol_ref_running.29.31.html
- Code_Aster (`as_run`, `.comm`, `.med`, GPL-3, Salome-Meca) — official Code-Aster manuals U1.04.00 + code-aster.org forum (high). https://biba1632.gitlab.io/code-aster-manuals/docs/user/u1.04.00.html , https://cofea.readthedocs.io/en/latest/fea_software/code_aster.html
- CalculiX (`ccx -i`, `.inp`, GPL, Abaqus-like) — primary: MIT-hosted CalculiX docs + feacluster (high); Wikipedia (orientation). https://web.mit.edu/calculix_v2.7/CalculiX/ccx_2.7/doc/ccx/node160.html , https://en.wikipedia.org/wiki/Calculix
- PyAEDT / HFSS-Maxwell non-graphical (MIT wrapper, licensed AEDT) — PyAnsys docs + Ansys HFSS scripting help (high). https://aedt.docs.pyansys.com/ , https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/HFSS/Subsystems/HFSS%20Scripting/Content/PyAEDT.htm
- MSC Adams (View command language + Python, batch solve, license) — primary: Hexagon Adams docs + Eng-Tips (high/med); Wikipedia (orientation). https://documentation-be.hexagon.com/bundle/Adams_2023.4.1_Adams_View_Command_User_Guide/raw/resource/enus/Adams_2023.4.1_Adams_View_Command_User_Guide.pdf , https://en.wikipedia.org/wiki/MSC_Adams
- LS-DYNA (`i=`, `ncpu=`, `memory=`, `.k`/`.key`, separate license) — VT/TAMU/OSC HPC docs (high for CLI). https://www.docs.arc.vt.edu/software/lsdyna.html , https://hprc.tamu.edu/kb/Software/LST/ls-dyna/
- OpenFOAM (simpleFoam/pimpleFoam, controlDict, decomposePar, Allrun, GPL) — openfoam.com & openfoam.org docs (high). https://www.openfoam.com/documentation/user-guide/a-reference/a.1-standard-solvers , https://openfoam.org/release/11/
- preCICE (LGPL-3, precice-config.xml, adapters) — precice.org official + v2 paper (high). https://precice.org/docs , https://precice.org/fundamentals-license , https://arxiv.org/abs/2109.14470
- Altair OptiStruct (`optistruct.bat "file.fem"`, command line, Altair Units) — Altair help docs + community (high). https://help.altair.com/hwsolvers/os/topics/solvers/os/run_os_command_line_r.htm , https://altair.com/optistruct
- Remaining tools (Ansys Fluent/CFX TUI & journals, MSC Nastran/Marc, Simcenter Nastran/TMG/Motion/MAGNET/Flotherm, CST, RecurDyn, Project Chrono/PyChrono, Elmer/FEniCSx/MFEM/deal.II/Kratos/Gmsh/Netgen/ParaView, HyperMesh/HyperView, Femap, ANSA/META, Workbench/PyAnsys, Thermal Desktop OpenTD, 6SigmaET, CONVERGE, Radioss, PAM-CRASH) — cross-checked against vendor documentation and the existing fem-cae skill `references/platform-commands.md` (reliability: vendor docs high; skill reference high, already version-validated). Verify exact flags against the installed release.
- Geomechanics / civil-FEM tier (§1b) — PLAXIS Python remote-scripting (Bentley/Seequent docs, high), GeoStudio (Bentley docs, high), OptumG2/G3 (Optum CE docs, med), Itasca FLAC/FLAC3D/3DEC/UDEC FISH + Python (Itasca docs, high), RS2/RS3 (Rocscience docs, high), Abaqus/Code_Aster geotechnical capability (vendor docs, high — see §1/§6). https://communities.bentley.com/products/geotech-analysis/w/wiki/45393/using-plaxis-remote-scripting-with-the-python-wrapper , https://www.itascacg.com/software/flac3d , https://www.rocscience.com/software/rs2 — verify exact scripting entry points and constitutive-model availability against the installed/licensed release.
- Physics-AI / ML-surrogate tier (§11) — treated as a generic tool **class**; named offerings (field-prediction Physics-AI, operator-learning frameworks, ML-built/projection ROMs, design-copilot assistants) are illustrative and churn release-to-release. Cross-checked against vendor product pages and the surrogate/ROM methodology already in this skill (`advanced-methods.md`, `vv-uq.md`). The out-of-distribution / re-solve-before-sign-off caveat is the load-bearing, vendor-neutral content; verify current product names, training-data and validity claims against the installed/licensed release. (reliability: methodology high; specific product capabilities vendor-marketing, corroborate before relying.)
