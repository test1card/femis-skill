# Agent-Headless vs Human-GUI Boundary — FEM/CAE Automation Contract

**Scope.** What an AI/automation **agent** can drive end-to-end with no human, what needs a **live licensed session/API**, what a **human must do once in a GUI** (and why), what is an **engineering judgment** the agent must not own, and what is **license-gated**. Covers Ansys (PyMAPDL / PyMechanical / PyWorkbench / Workbench batch / optiSLang, plus the wider PyAnsys family: PyAEDT, PyPrimeMesh, PyAdditive, PySherlock, PyEnSight, PyHPS), Siemens NX Open / Simcenter 3D / Simcenter Nastran / TMG / HEEDS, Ansys Thermal Desktop + SINDA/FLUINT (OpenTD), and Abaqus, plus cloud/HPC job submission.

**Verification note.** Every row is cross-checked against ≥2 authoritative sources (vendor docs, vendor KB/community, recognized practitioners). Where the originating brief was stale or overstated, this document corrects it and flags the correction. See SOURCES at the end with a reliability rating.

---

## Classification buckets

| Bucket | Meaning |
|---|---|
| **AGENT-HEADLESS** | Fully scriptable/batch. No GUI process, no live interactive session beyond what the solver itself needs. Driven by a text deck, a `subprocess` call, or a batch journal. |
| **AGENT-VIA-API** | Scriptable, but needs a **running session + checked-out license** for the duration (Python/journal API attached to a live app process — possibly invisible). |
| **HUMAN-GUI-REQUIRED** | Must be done interactively at least once. The capability is missing, unreliable, or unsupported in pure batch — usually because templates/registry/visual picking aren't initialized headless. |
| **HUMAN-JUDGMENT** | An engineering decision the agent must surface, not make alone (idealization, accepting a calibration, sign-off). |
| **LICENSE-GATED** | Needs a specific feature/seat/SKU; each parallel solver instance burns its own seat. |

Most rows carry **two** tags (e.g., *AGENT-VIA-API + LICENSE-GATED*): the first is the automation mode, the second a hard constraint.

---

## Per-operation table

### Ansys (MAPDL / Mechanical / Workbench)

| Operation | Classification | How (command / API) | Hard limit / note |
|---|---|---|---|
| CAD import | AGENT-VIA-API | PyMechanical `app.open()` / Workbench `GeometryImport`; SpaceClaim/Discovery scripting | Native-CAD readers (Creo/NX/SW plugin-based import) may need the CAD-reader license; STEP/IGES are clean headless. |
| Geometry cleanup / defeature | AGENT-VIA-API + HUMAN-JUDGMENT | SpaceClaim/Discovery script API; Mechanical defeaturing via ACT/Python | Scriptable, but *which* features to suppress and how much to simplify is HUMAN-JUDGMENT — over-defeaturing changes the physics. |
| Meshing | AGENT-VIA-API | PyMechanical mesh object; PyPrimeMesh (`ansys-meshing-prime`) is headless; MAPDL native mesher via PyMAPDL | Mesh *adequacy* (refinement, mesh-independence/GCI) is HUMAN-JUDGMENT — see V&V row. |
| Material creation & assignment | AGENT-HEADLESS (MAPDL) / AGENT-VIA-API (Mechanical) | PyMAPDL `MP`,`MPDATA`,`TB` (pure APDL, zero GUI); Mechanical via `Engineering Data` script / XML import | Fully scriptable. Temperature-dependent tables, hyperelastic fits etc. are data — agent owns them once the data is given. |
| Contacts / connections / joints | AGENT-VIA-API + HUMAN-JUDGMENT | PyMAPDL contact pairs (`CONTA`/`TARGE`, `CNCH`); Mechanical auto-contact + scripted contact objects | Auto-detection is scriptable; **contact type, stiffness, thermal contact conductance, and whether a joint is bonded/frictional is HUMAN-JUDGMENT**. |
| BCs & loads | AGENT-HEADLESS (MAPDL) / AGENT-VIA-API (Mechanical) | PyMAPDL `D`,`F`,`SF`,`BF`,`ACEL`,tables; Mechanical scripted loads | Fully scriptable including transient load tables. |
| Parameter / expression exposure for optimization | **split — see note** | **PyMAPDL: AGENT-HEADLESS** — `mapdl.parameters['x']=...`, `*SET`, `*GET` are first-class, no GUI. **Workbench/Mechanical/DesignXplorer: HUMAN-GUI-REQUIRED (one-time)** | To drive DesignXplorer/optiSLang through Workbench, a quantity must be **promoted to a `P#` project parameter**. In a Mechanical *Command (APDL)* object, inputs are `ARG1–ARG9` and outputs are auto-promoted only if named with the **Output Search Prefix** (`my_` by default). Raw PyMAPDL bypasses all of this. |
| Solve — steady / transient / nonlinear | AGENT-HEADLESS | PyMAPDL `SOLVE`/`/SOLU`; Mechanical embedded `App` (`app.solve()`); `mapdl` runs in batch; MAPDL `-b` batch | Embedded PyMechanical `App(globals=globals())` **always runs in batch mode** — same path Mechanical uses for batch, no GUI. PyMAPDL holds a license for the life of the instance. |
| Optimization / DOE / calibration / model-updating | AGENT-HEADLESS / AGENT-VIA-API + LICENSE-GATED | **PyMAPDL + SciPy** (`scipy.optimize`, fully headless); **optiSLang Core Headless** / PyOptiSLang for scripted overnight runs; DesignXplorer (needs Workbench P# params) | optiSLang ships an explicit **Core Headless** install for automated/embedded use. DesignXplorer route inherits the GUI-promote-to-`P#` requirement above. |
| Results extraction — field & history | AGENT-HEADLESS | **DPF** (`ansys-dpf-core`) reads `.rst`/`.rth` license-free on the client side; PyMAPDL `*GET`/`PRNSOL`; Mechanical scripted result objects | DPF is the headless workhorse — no live solver session needed to post a result file. |
| Post-processing images / plots | AGENT-HEADLESS | DPF + PyVista off-screen render; PyMAPDL `mapdl.post_processing` plots (off-screen) | Off-screen rendering works on headless servers (xvfb on Linux). |
| Correlation & model updating (test↔analysis, MAC, node pairing) | AGENT-VIA-API (math) / HUMAN-JUDGMENT (pairing accept) | DPF/NumPy MAC computation is scriptable; SOL-200/optiSLang updating headless | **Computing MAC and updating parameters is scriptable; accepting a mode pairing / sensor-to-node map is judgment.** (Ansys has no first-class interactive correlation node-pairing GUI like Simcenter's — see NX rows.) |
| Template / project / plugin authoring | AGENT-VIA-API / HUMAN-GUI-REQUIRED | ACT extensions, Workbench journals, `.wbjn`; Mechanical `.mechdb` seed | A reusable `.mechdb`/`.wbpj` seed is commonly built **once in the GUI** then driven headless — analogous to the NX seed-`.sim` pattern. |

#### Wider PyAnsys family (electromagnetics, meshing, additive, reliability, post, HPC)

These extend the agent-headless surface beyond the core MAPDL/Mechanical/Workbench stack. PyPI versions/Python ranges below were confirmed on PyPI (recorded inline); **verify the exact build against your installed Ansys release** since the PyAnsys ↔ solver version coupling moves each release.

| Operation | Classification | How (command / API) | Hard limit / note |
|---|---|---|---|
| Electromagnetics / electronics-cooling (HFSS / Maxwell / Icepak / Q3D / SIwave) | AGENT-HEADLESS + LICENSE-GATED | **PyAEDT** — `pip install pyaedt` (pulls `ansys-aedt-core` ≥1.x); `from ansys.aedt.core import Hfss; hfss = Hfss(non_graphical=True, new_desktop=True, version="2026.1")` → solve → `hfss.post` for fields | `non_graphical=True` runs AEDT with **no GUI**. Needs a local **AEDT install** (the `non_graphical` flag has been available since ~2022 R1 — verify your release) + an EM license. `import pyaedt` is a back-compat shim for `import ansys.aedt.core` (renamed at v1.0; new code should use the `ansys.aedt.core` path). **Icepak gives an agent-headless electronics-cooling thermal path** the core stack otherwise lacks. (`pyaedt` 1.1.0, Python 3.10–3.13; `ansys-aedt-core` exact version "1.x" — verify per release.) |
| Meshing (standalone, headless) | AGENT-HEADLESS + LICENSE-GATED | **PyPrimeMesh** — `pip install ansys-meshing-prime`; `from ansys.meshing import prime; client = prime.launch_prime(); model = client.model` → size controls, surface/volume mesh, diagnostics, export | Headless client to **Ansys Prime Server** — no GUI required. Mesh *adequacy* (refinement, GCI) remains HUMAN-JUDGMENT (see V&V). (`ansys-meshing-prime` 0.10.4, Python 3.10–3.13; verify the Prime Server version it targets against your install.) |
| Additive manufacturing (thermal/mechanical build sim) | AGENT-HEADLESS + LICENSE-GATED | **PyAdditive** — `pip install ansys-additive-core`; `from ansys.additive.core import Additive; additive = Additive()` → submit single-bead / porosity / microstructure / thermal-history simulations → pull results | **Service/cloud client — inherently headless, no GUI.** Connects to a local or remote Additive server; each simulation consumes an Additive license. (`ansys-additive-core` 0.20.1, Python 3.10–3.13; verify the server endpoint/version per deployment.) |
| Reliability physics (board/component, PoF) | AGENT-HEADLESS + LICENSE-GATED | **PySherlock** — `pip install ansys-sherlock-core`; `from ansys.sherlock.core import launcher; sherlock = launcher.launch_sherlock()` (gRPC) → import ODB++/project, run thermal-mechanical / vibration / solder-fatigue analyses | gRPC client drives Sherlock **headless** (no GUI). Needs a Sherlock install + license. (`ansys-sherlock-core` 1.0.2, Python 3.10–3.13; verify the matching Sherlock release.) |
| Post-processing / rendering (large CFD/EM/structural) | AGENT-HEADLESS + LICENSE-GATED | **PyEnSight** — `pip install ansys-pyensight-core`; `from ansys.pyensight.core import LocalLauncher; session = LocalLauncher().start()` → load datasets, build views, render images/animations | Supports **off-screen rendering headless** (no display needed). Needs an EnSight install + license. Complements DPF for very large or multi-solver result sets. (`ansys-pyensight-core` 0.11.12, Python 3.10–3.14; verify the EnSight release.) |

### Siemens NX / Simcenter 3D / Simcenter Nastran / TMG / HEEDS

| Operation | Classification | How | Hard limit / note |
|---|---|---|---|
| CAD import / geometry cleanup / defeature | AGENT-VIA-API + HUMAN-JUDGMENT | NX Open (Python/.NET/C++) via `run_journal.exe` (invisible NX session) or NX Batch | Scriptable; simplification extent is judgment. |
| Meshing | AGENT-VIA-API | NX Open CAE meshing API on a `.fem`, driven via `run_journal.exe` | **Requires a pre-existing `.fem`** — see the template boundary below. |
| Material creation & assignment | AGENT-VIA-API | NX Open `PhysicalMaterial`/`MaterialManager` on the `.fem` | Scriptable once the `.fem` exists. |
| Contacts / connections / joints | AGENT-VIA-API + HUMAN-JUDGMENT | NX Open simulation object API; TMG thermal couplings | Same judgment caveat as Ansys for contact/TCC choice. |
| BCs & loads | AGENT-VIA-API | NX Open load/constraint API on the `.sim` | Scriptable once the `.sim` exists. |
| **New `.fem` / `.sim` creation in pure batch** | **HUMAN-GUI-REQUIRED (one-time seed)** | GUI: create a seed `.sim` (+`.fem`) once; then headless `run_journal.exe` → `OpenActiveDisplay(seed.sim)` → edit → `Solution.Solve()` | **`Parts.FileNew` for `.fem`/`.sim` does not reliably resolve in pure batch — the CAE template registry (`UGII_TEMPLATE_DIR`/`.pax`) is not initialized in a headless session.** Standard workaround is the pre-created seed file. (Verified: vendor KB "no templates available" + UGII_TEMPLATE_DIR community threads + "how to run NX headless".) |
| Parameter/expression exposure | AGENT-VIA-API | NX expressions via NX Open; HEEDS tags variables in its own study | Driven through HEEDS/expressions, not a `P#` system. |
| Solve — Simcenter Nastran (incl. SOL 159 transient, SOL 200 opt) | AGENT-HEADLESS | Standalone `nastran.exe model.dat scr=y old=n` via `subprocess`; SOL 200 = `DESVAR`/`DRESP`/`DVPREL` bulk deck | **Fully headless** — Simcenter Nastran ships as a standalone solver; the deck is plain text. Parse `.f06`/`.op2`. |
| Solve — TMG thermal / flow | AGENT-HEADLESS | TMG solver invoked on the exported deck; or via the `.sim` solve through NX Batch | TMG solve itself is headless once the deck/`.sim` exists. (TMG authoring still needs the seed `.sim`.) |
| Optimization / DOE / calibration | AGENT-VIA-API (HEEDS) / AGENT-HEADLESS (SOL 200) + LICENSE-GATED | **HEEDS: study authored in GUI, solver runs CLI/HPC via HEEDS Distributed Execution**; SOL 200 deck is headless | HEEDS study setup (workflow canvas, variable/response wiring) is GUI work; execution fans out to CLI/HPC/cloud. |
| Results extraction | AGENT-HEADLESS / AGENT-VIA-API | Parse `.f06`/`.op2`/`.mntr` directly (headless); or NX Open post API on `.sim` | Text/binary result parsing is fully headless. |
| Post images/plots | AGENT-VIA-API | NX Open post + screenshot via `run_journal.exe` (invisible session can still render to file) | |
| **Correlation & model updating (test↔analysis, MAC, node pairing)** | **HUMAN-GUI-REQUIRED** | Simcenter 3D / TMG **Correlation** node: alignment node-pair picking, sensor→node mapping by proximity+tolerance, mode-pairing edit (right-click → Edit) | **Node pairing, sensor mapping, and mode-pairing acceptance are interactive GUI workflows.** MAC math is computable headless, but the *pairing* (which test node ↔ which FE node, alignment) is interactive. |
| Template / project / plugin authoring | HUMAN-GUI-REQUIRED (seed) / AGENT-VIA-API | Build `.pax`/template + seed `.sim` in GUI; author NX Open plugins as code | Template registry is GUI/registry-bound (see seed boundary). |

### Ansys Thermal Desktop + SINDA/FLUINT (OpenTD)

| Operation | Classification | How | Hard limit / note |
|---|---|---|---|
| Geometry authoring (surfaces, nodes, conductors) | HUMAN-GUI-REQUIRED (practically) / AGENT-VIA-API (limited) | Thermal Desktop runs **inside AutoCAD**; OpenTD can start AutoCAD **invisible** (`ThermalDesktop.ConnectConfig`) | The AutoCAD process is **mandatory** and is launched even for scripting. OpenTD can drive it invisibly, but interactive geometry *authoring* is AutoCAD-GUI work in practice. AutoCAD **standard** required (LT not supported). |
| Material / property assignment | AGENT-VIA-API | OpenTD property API (pythonnet → `clr` → OpenTD assembly) | Needs the running (possibly invisible) TD/AutoCAD session. |
| BCs / heat loads / orbital | AGENT-VIA-API | OpenTD API | Same session requirement. |
| Parameter / symbol exposure | AGENT-VIA-API | OpenTD symbols/registers; SINDA/FLUINT registers in the deck | |
| Solve (SINDA/FLUINT steady/transient) | AGENT-HEADLESS | TD builds the node/conductor network and launches SINDA/FLUINT; deck-level run is batchable | SINDA/FLUINT build needs **Intel Fortran + VS Build Tools** present (compiler-gated environment). |
| DOE / sweep / calibration | AGENT-VIA-API | OpenTD sweep/scripted runs (pythonnet) | |
| Results extraction & post | AGENT-VIA-API / AGENT-HEADLESS | OpenTD result API; or parse SINDA `.out`/save files directly | Direct deck-output parsing is headless. |
| **Python runtime for OpenTD** | constraint (corrected) | pythonnet bridge | **Correction to brief:** current **pythonnet 3.1.0 supports CPython 3.10–3.14**, so 3.14 is *not* categorically broken. The "use 3.11/3.12" rule was true for older pythonnet builds; pin pythonnet + Python to a tested pair for the installed TD version rather than assuming 3.14 fails. Verify against the TD release's appendix. |

### Abaqus

| Operation | Classification | How | Hard limit / note |
|---|---|---|---|
| Model build / geometry / mesh / materials / BCs | AGENT-HEADLESS | `abaqus cae noGUI=script.py` (full CAE kernel, no GUI) — `from abaqus import *; executeOnCaeStartup()` | `noGUI` runs the whole CAE package headless; `abaqus python` alone lacks the CAE modules. **Interpreter:** older Abaqus shipped a Python 2 kernel; recent releases (Abaqus **2024+**, exact minor not pinned) move the kernel toward Python 3 — **verify the scripting interpreter per install** before assuming Py2-vs-Py3 syntax. |
| Solve | AGENT-HEADLESS | `abaqus job=myjob input=model.inp interactive` (or background) | `.inp` is plain text; can be hand-written or CAE-generated. |
| Optimization / DOE / calibration | AGENT-HEADLESS / AGENT-VIA-API | Python scripts + Isight (Isight study often GUI-authored), or scripted parameter sweeps over `.inp` | Tosca/optimization may be a separate license. |
| Results extraction & post | AGENT-HEADLESS | `abaqus python` + `odbAccess` on the `.odb`; scripted Viewport image dump | `.odb` reading is fully scriptable headless. |

---

## Hard-boundary list (the contract)

**Fully agent-headless (no GUI, no live interactive session beyond the solve):**
1. **PyMAPDL** is the gold standard: `*SET`/`*GET`, `mapdl.parameters[...]`, mesh, materials (`MP`/`TB`), BCs, `SOLVE` — all zero-GUI. Parameters are first-class; **no GUI promotion needed**.
2. **Embedded PyMechanical** `App(globals=globals())` **always runs in batch mode**, the same way Mechanical runs batch — no GUI window.
3. **DPF** (`ansys-dpf-core`) reads `.rst`/`.rth` on the client **license-free** — the headless post-processing workhorse. Temperatures from `.rth` are in °C internally; add 273.15 for K.
4. **Simcenter Nastran** standalone solver: `nastran.exe deck.dat scr=y old=n` — SOL 153/159 thermal and SOL 200 optimization run fully headless from a text deck. Parse `.f06`/`.op2`/`.mntr`.
5. **TMG and SINDA/FLUINT solves** are headless once the deck/network exists.
6. **Abaqus**: `abaqus cae noGUI=script.py` + `abaqus job=` are headless end-to-end; `.odb` post via `odbAccess`.
7. **optiSLang Core Headless** + PyOptiSLang for scripted/overnight optimization.

**Needs a running session + license (agent-via-API, possibly invisible):**
8. **Workbench batch**: `runwb2 -B -R journal.wbjn` (`-B`=batch/no-GUI, `-R`=replay journal). PyWorkbench `launch_workbench(show_gui=False)`.
9. **NX Open** via `run_journal.exe` starts an **invisible NX session with no UI** but still **requires a valid NX license** for whatever the journal does.
10. **OpenTD** drives Thermal Desktop through pythonnet; AutoCAD can be made **invisible** but the AutoCAD process is mandatory and is launched.

**Must be done in the GUI at least once (and why):**
11. **Workbench/DesignXplorer parameter promotion** — a quantity is only optimizable once **promoted to a `P#` project parameter**; in Mechanical *Command (APDL)* objects, inputs are `ARG1–ARG9` and outputs need the **Output Search Prefix** (`my_`). *Why:* the parameter manager is a project-GUI construct. **Exception: raw PyMAPDL needs none of this.**
12. **Siemens NX CAE `.fem`/`.sim` creation in pure batch fails** — `Parts.FileNew` for CAE templates does not resolve because the **template registry (`UGII_TEMPLATE_DIR`/`.pax`) is not initialized headless**. *Workaround:* pre-create a seed `.sim` in the GUI once, then headless `run_journal.exe` → `OpenActiveDisplay(seed.sim)` → `Solution.Solve()`. (Same pattern recommended for Ansys reusable `.mechdb` seeds.)
13. **Simcenter/TMG Correlation node-pairing & MAC mapping** — alignment node-pair selection, sensor→node proximity mapping, and mode-pairing acceptance are **interactive GUI** operations. The MAC *number* is computable headless; the *pairing decision* is not a batch operation.
14. **HEEDS study authoring** — the workflow canvas / variable-response wiring is built in the GUI; only **execution** fans out to CLI/HPC/cloud.
15. **Thermal Desktop geometry authoring** is AutoCAD-GUI-bound in practice (OpenTD can solve/sweep/post invisibly, but drawing the model is interactive).

**License / environment gating:**
16. **Every parallel solver instance consumes its own license seat.** PyMAPDL `LocalMapdlPool` of 3 = 3 licenses; HPC parametric variations need HPC increments / an **HPC Parametric Pack** (post-2020 R2: each variation after the first = 8 HPC increments or 1 Pack increment, 4 cores/variation included).
17. **NX Batch (headless NX on Linux) is a separate product SKU (NX30182)** — must be licensed in addition to NX.
18. **SINDA/FLUINT build environment** requires Intel Fortran + Visual Studio Build Tools present.
19. **OpenTD/pythonnet runtime** must be a tested Python+pythonnet pair for the TD release (pythonnet ≥3.1 covers 3.10–3.14; do not assume 3.14 fails — verify per TD version).
20. **Native-CAD import** (Creo/NX/SolidWorks geometry into Ansys) can require a CAD-reader license seat beyond the base solver.

**Cloud / HPC job submission (no single "PyAnsys → cloud" call):**

There is **no one first-class PyAnsys method that submits a job to a cluster or to the cloud**. The realistic agent paths are:

- **PyHPS** (`ansys-hps-client`) — Python client for **Ansys HPC Platform Services (HPS)**. `from ansys.hps.client import Client; from ansys.hps.client.jms import JmsApi, Project, ...` → define a project/job-definition → submit jobs to an HPS evaluator pool. Use this against an HPS endpoint, or call the **HPS REST API** directly. (`ansys-hps-client` 0.12.1, Python 3.10–3.13; verify the HPS server version.)
- **Direct-to-scheduler** — submit the solver's own batch command (`ansysXXX -b`, `nastran …`, `abaqus job=…`, `fluent … -g`) inside a **SLURM `sbatch`** / PBS / LSF script. PyMAPDL propagates env vars (including license) into the job and exposes a `scheduler_options` dict; multi-node MAPDL needs `ANS_MULTIPLE_NODES=1` + `HYDRA_BOOTSTRAP=slurm`. This is the most portable route and needs no extra SDK.
- **Ansys Gateway (on AWS/Azure) / Ansys Access** — these exist for cloud submission, but a clean first-class "PyAnsys → Gateway job submit" SDK path is **not** clearly documented; treat cloud submission as **via PyHPS / HPS REST or direct-to-scheduler**, not as a single PyAnsys call. *Verify against your release/subscription.*

License from a container/cluster job: pass `ANSYSLMD_LICENSE_FILE=PORT@HOST` (FlexNet needs **both** the `lmgrd` port, typically 1055, **and** the vendor-daemon port, typically 2325, reachable — the vendor port is the recurring firewall gotcha). For the DPF Docker server add `ANSYS_DPF_ACCEPT_LA=Y`. Official container images are **access-gated** for the major Ansys solvers (MAPDL/Fluent/DPF on `ghcr.io/ansys`, customer-gated); HPC clusters commonly run rootless via **Apptainer/Singularity** (`srun apptainer exec --bind $PWD solver.sif …`), where the MPI must be host-ABI-compatible. *Image availability and gating change — verify against your entitlement.*

**What the agent must NEVER auto-do (HUMAN-JUDGMENT / governance):**
21. **Make idealization decisions alone** — solid-vs-shell, what to defeature, contact type, thermal contact conductance, bonded-vs-frictional, lumped-vs-resolved. Propose and flag; do not silently choose.
22. **Accept a calibration pinned at a parameter bound** (edge-pinned optimum) — surface it; an at-bound result means the bound, not the physics, is driving the answer.
23. **Trust a singular/degenerate result** — a rank-deficient FIM, a singular optimization peak, or a result that depends on an unconverged mesh must be flagged, not reported as fact.
24. **Claim verification/sign-off** — "validated", "passes", "mesh-independent", "settled transient" require evidence (GCI study, converged `.rth`/`.rst` to full time, V&V); never assert without the run output.
25. **Irreversible pushes / merges / overwrites** — committing, pushing to a shared branch, or overwriting a baseline model are outward-facing actions that need explicit human authorization, not inferred approval.

---

## SOURCES

Reliability: ★★★ = official vendor docs / KB; ★★ = vendor community / recognized practitioner blog; ★ = general practitioner/forum corroboration.

**Ansys — PyMAPDL / PyMechanical / PyWorkbench / Workbench / optiSLang / DPF**
- ★★★ PyMAPDL user guide & language/usage — https://mapdl.docs.pyansys.com/version/stable/user_guide/mapdl.html
- ★★★ PyMAPDL FAQ (license held for life of instance; non-GUI command caveats) — https://mapdl.docs.pyansys.com/version/stable/getting_started/faq.html
- ★★★ `launch_mapdl` API — https://mapdl.docs.pyansys.com/version/stable/api/_autosummary/ansys.mapdl.core.launcher.launch_mapdl.html
- ★★★ PyMAPDL on HPC clusters (per-instance licensing, MapdlPool) — https://mapdl.docs.pyansys.com/version/stable/user_guide/hpc/pymapdl.html
- ★★ PyMAPDL Discussion #2829 "LocalMapdlPool and number of licenses" (3 parallel = 3 licenses) — https://github.com/ansys/pymapdl/discussions/2829
- ★★★ PyMechanical overview — embedded App vs remote, embedded always batch — https://mechanical.docs.pyansys.com/version/stable/user_guide/howto/overview.html
- ★★★ PyMechanical FAQ — https://mechanical.docs.pyansys.com/version/stable/faq.html
- ★★ PyMechanical cheat sheet (`App(globals=globals())`) — https://developer.ansys.com/blog/pymechanical-cheat-sheet
- ★★★ PyWorkbench user guide / `launch_workbench(show_gui=False)` — https://workbench.docs.pyansys.com/version/stable/user-guide.html
- ★★★ PyWorkbench Launcher API — https://workbench.docs.pyansys.com/version/stable/api/ansys/workbench/core/workbench_launcher/Launcher.html
- ★★★ Workbench User's Guide 2025 R2 (`runwb2 -B -R`, parameters/design points) — https://ansyshelp.ansys.com/public/Views/Secured/corp/v252/en/pdf/Workbench_Users_Guide.pdf
- ★★ batch-ansys-workbench README (`-B`=batch, `-R`=replay journal) — https://github.com/solab-ntu/batch-ansys-workbench/blob/master/README.md
- ★★★ DesignXplorer User's Guide (parameters must be in Parameter Set) — https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/pdf/DesignXplorer_Users_Guide.pdf
- ★★ PADT — "Making APDL Parameters Available in Parameter Manager / DesignXplorer" (`ARG1–ARG9` inputs, `my_` Output Search Prefix) — https://www.padtinc.com/2013/10/02/making-apdl-parameters-available-in-the-ansys-parameter-manager-or-designxplorer-prep-solve-and-post/
- ★★★ PyOptiSLang `Optislang` API (batch mode, `no_run`) — https://optislang.docs.pyansys.com/version/stable/api/_autosummary/ansys.optislang.core.optislang.Optislang.html
- ★★★ Ansys optiSLang 2026 R1 What's New — **Core Headless** option — https://www.ansys.com/blog/ansys-2026-r1-whats-new-ansys-optislang-software

**Wider PyAnsys family + cloud/HPC submission** (PyPI versions/Python ranges confirmed on PyPI; verify the solver-coupling per release)
- ★★★ PyAEDT docs (`non_graphical=True`, `ansys.aedt.core`) — https://aedt.docs.pyansys.com/version/stable/ ; PyPI `pyaedt` 1.1.0 — https://pypi.org/pypi/pyaedt/json
- ★★★ PyPrimeMesh docs — https://prime.docs.pyansys.com/version/stable/ ; PyPI `ansys-meshing-prime` 0.10.4 — https://pypi.org/pypi/ansys-meshing-prime/json
- ★★★ PyAdditive docs (service client) — https://additive.docs.pyansys.com/version/stable/ ; PyPI `ansys-additive-core` 0.20.1 — https://pypi.org/pypi/ansys-additive-core/json
- ★★★ PySherlock docs (gRPC launcher) — https://sherlock.docs.pyansys.com/version/stable/ ; PyPI `ansys-sherlock-core` 1.0.2 — https://pypi.org/pypi/ansys-sherlock-core/json
- ★★★ PyEnSight docs (off-screen rendering) — https://ensight.docs.pyansys.com/version/stable/ ; PyPI `ansys-pyensight-core` 0.11.12 — https://pypi.org/pypi/ansys-pyensight-core/json
- ★★★ PyHPS docs (HPC Platform Services client) — https://hps.docs.pyansys.com/version/stable/ ; PyPI `ansys-hps-client` 0.12.1 — https://pypi.org/pypi/ansys-hps-client/json
- ★★★ PyMAPDL on HPC / SLURM (`scheduler_options`, `ANS_MULTIPLE_NODES`, `HYDRA_BOOTSTRAP=slurm`) — https://mapdl.docs.pyansys.com/version/stable/user_guide/hpc/

**Siemens NX / Simcenter 3D / Simcenter Nastran / TMG / HEEDS**
- ★★ NX Journaling — "Using/Batch file to run recorded journal" (`run_journal.exe` = batch, no GUI) — https://nxjournaling.com/content/using-batch-file-run-recorded-journal
- ★★★ Siemens community — "How to run NX headless?" (NX Batch headless, driven by NX Open; SKU NX30182) — https://community.sw.siemens.com/s/question/0D5Vb00000GuzG1KAJ/how-to-run-nx-headless
- ★★★ Siemens KB — "Possible Solutions to 'There are no templates available…'" (CAE template/`.pax` resolution) — https://community.sw.siemens.com/s/article/Possible-Solutions-to-the-error-There-are-not-templates-available-to-support-the-operation-you-are-trying
- ★★ Siemens community — "NX customized worksheets — UGII_TEMPLATE_DIR not work" / fem-sim template thread (template-dir must be set; restart NX) — https://community.sw.siemens.com/s/question/0D54O00007i559ASAQ/nx-customized-worksheets-ugiitemplatedir-not-work and https://community.sw.siemens.com/s/question/0D54O000061xlMQSAY/whats-the-best-way-to-make-a-fem-and-sim-template-in-nx-thermalflow
- ★★ "how to launch batch cases on NX Nastran" / "Running Nastran outside of NX Pre/Post" (standalone `nastran.exe` batch) — https://community.sw.siemens.com/s/question/0D54O000061xkp5SAA/how-to-launch-batch-cases-on-nx-nastran
- ★★★ Simcenter Nastran QRG 2020.1 (command-line options) — https://docs.plm.automation.siemens.com/data_services/resources/scnastran/2020_1/help/tdoc/en_US/pdf/qrg.pdf
- ★★ Simcenter Nastran product page (standalone solver; thermal from same solver) — https://plm.sw.siemens.com/en-US/simcenter/mechanical-simulation/nastran/
- ★★ ATA Engineering — "Design Sensitivity and Optimization with Simcenter Nastran" (SOL 200 DESVAR/DRESP/DVPREL; run BDF via subprocess, read sensitivities from `.f06`) — https://www.ata-e.com/wp-content/uploads/2024/11/Webinar-Design-Sensitivity-and-Optimization-with-Simcenter-Nastran.pdf
- ★★★ Siemens KB — "Correlating Simulation & Modal Test Results with Simcenter 3D" (interactive alignment node-pairing, MAC, mode-pairing edit) — https://community.sw.siemens.com/articles/en_US/Knowledge/correlating-simulation-modal-test-results-with-simcenter-3d
- ★★ Maya HTT mirror of the same correlation workflow — https://www.mayahtt.com/blog/correlating-simulation-modal-test-results-simcenter-3d/
- ★★ Simcenter HEEDS product page (desktop study app, SHERPA, Distributed Execution to HPC/cloud) — https://www.siemens.com/en-us/products/simcenter/integration-solutions/heeds/
- ★★ Volupe — Simcenter HEEDS overview — https://volupe.com/products-simcenter/simcenter-heeds/

**Ansys Thermal Desktop / SINDA/FLUINT / OpenTD**
- ★★★ Ansys Developer Portal — "Appendix B: Using OpenTD with Python" (pythonnet/`clr` to load OpenTD assembly) — https://developer.ansys.com/docs/opentd-2025-r2/getting-started/appendix-B-using-opentd-with-python.md
- ★★ C&R Technologies — OpenTD API page & brochure (AutoCAD invisible via ConnectConfig; TD launches SINDA/FLUINT) — https://www.crtech.com/opentd-thermal-desktop-api and https://www.crtech.com/sites/default/files/files/Brochures/OpenTD.pdf
- ★★★ Ansys Thermal Desktop System Requirements (AutoCAD standard required, LT not supported; Intel Fortran + VS Build Tools for SINDA/FLUINT) — https://www.ansys.com/support/thermal-desktop-system-requirements
- ★★★ pythonnet PyPI / releases (3.1.0 supports CPython 3.10–3.14) — https://pypi.org/project/pythonnet/ and https://github.com/pythonnet/pythonnet/releases

**Abaqus**
- ★★ Abaqus Scripting Interface — "How does the ASI interact with Abaqus/CAE" (`abaqus cae noGUI=` runs full package headless) — https://classes.engineering.wustl.edu/2009/spring/mase5513/abaqus/docs/v6.5/books/cmd/pt01ch02s02.html
- ★★ abqpy getting-started (`abaqus cae script=` / `noGUI=`; required imports + `executeOnCaeStartup()`) — https://abqpy.readthedocs.io/projects/pyabaqus/en/stable/getting_started.html
- ★ `abaqus python` lacks the CAE modules; run GUI-authored scripts headless via `abaqus cae noGUI=<script>` (kernel-only interpreter: `abaqus python`) — Abaqus Scripting User's Guide / Execution procedures (Dassault Systèmes SIMULIA).

**Corrections to the originating brief (flagged for transparency):**
- *OpenTD/pythonnet:* brief said "fails on Python 3.14 → use 3.11/3.12". **Corrected:** pythonnet 3.1.0 supports CPython 3.10–3.14; the failure was version-specific to older pythonnet. Pin a tested pair per TD release; do not assume 3.14 is broken.
- *NX seed-`.sim`:* brief's mechanism confirmed (template registry not initialized headless → `Parts.FileNew` fails) and **augmented** with the NX Batch SKU (NX30182) gating fact.
- *APDL→DesignXplorer:* brief's "parameters must be GUI-promoted to P# (except PyMAPDL)" confirmed and **made precise** (`ARG1–ARG9` inputs, `my_`/Output Search Prefix outputs in Command(APDL) objects).
