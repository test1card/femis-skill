# CAE Platform Cheat-Sheet: Practice → Command/API

Conventions: MAPDL commands UPPERCASE; PyMAPDL = `mapdl.<cmd>(...)` snake-case mirror. Nastran = case-control / bulk-data entries. Defaults stated where confirmed against official references. Verify version-specific API names against your release's docs.

---

## A. Ansys MAPDL / PyMAPDL

### A.1 Launch / parallel
| Practice | Knob |
|---|---|
| Batch run (no GUI) | `ansys251 -b -i input.dat -o out.out -j jobname` (`-b` batch, `-i/-o` in/out, `-j` jobname) |
| Shared-memory cores | `-np N` |
| Distributed (DMP, MPI) | `-dis -np N` (preferred for large; SPARSE & PCG run fully distributed) |
| GPU | `-acc nvidia -na 1` |
| PyMAPDL launch | `from ansys.mapdl.core import launch_mapdl; mapdl = launch_mapdl(nproc=8, additional_switches='-dis')` |

### A.2 Equation solver — `EQSLV, Lab, TOLER, MULT`
- `EQSLV,SPARSE` direct (default; robust, ill-conditioned OK). `EQSLV,PCG,1e-6` iterative for large solids. Also `JCG`, `ICCG`, `QMR`.
- PCG `TOLER` default 1e-8 (1e-6 saves CPU). `MULT` default 2.5 nonlinear / 1.0 linear (raise <3.0 on "PCG error level 1").
- Solver settable only in first load step. DMP: SPARSE/PCG fully distributed; ICCG/QMR not.

### A.3 Mesh & quality
| Practice | Knob |
|---|---|
| Global size | `ESIZE, SIZE, NDIV` |
| Smart sizing | `SMRTSIZE, SIZLVL` (1 fine … 10 coarse) |
| Line divisions / bias | `LESIZE, NL1, SIZE, , NDIV, SPACE` |
| Local refinement | `EREFINE`/`NREFINE`/`KREFINE`/`LREFINE`/`AREFINE` |
| Mesh | `AMESH`, `VMESH`, `VSWEEP`; `MSHAPE,0/1` (hex/tet), `MSHKEY,0/1` (free/mapped) |
| Quality check | `SHPP,ON`+`SHPP,SUMMARY`; `CHECK`; warning limits `SHPP,MODIFY` |
| Merge coincident nodes | `NUMMRG,NODE` (default tol **1e-4**, higher-numbered node deleted) → bonds **coincident-node** interfaces perfectly (zero resistance, conformal — for *touching* bodies; use LINK33/contact for gaps). **Merge NODE before KP** (else orphaned nodes); **avoid if avoidable** — too-large tol collapses small lines/areas → meshing failure |

### A.4 Nonlinear static/transient
| Practice | Knob |
|---|---|
| Large deflection | `NLGEOM,ON` |
| Auto time stepping | `AUTOTS,ON` (with bisection) |
| Substeps | `NSUBST, NSBSTP, NSBMX, NSBMN, Carry` |
| Time-step (alt.) | `DELTIM, DTIME, DTMIN, DTMAX, Carry` |
| Convergence | `CNVTOL, Lab, VALUE, TOLER, NORM, MINREF` — struct `F`/`U`/`M`/`ROT`; thermal `HEAT`/`TEMP` |
| Max equilibrium iters | `NEQIT, NEQIT, FORCEkey` (auto 15–26 by physics) |
| Newton-Raphson | `NROPT,FULL/MODI/INIT/UNSYM` |
| Line search / predictor | `LNSRCH,ON`; `PRED,ON` |
| Real-time monitor | `NLHIST,...` → `Jobname.nlh`; live `.mntr` |
| Load / time step | `TIME, TIME`; `LSWRITE`/`LSSOLVE` |
| Restart | enable `RESCONTROL,DEFINE,...`; resume `ANTYPE,,REST,LDSTEP,SUBSTEP,Action` (type cannot change) |

### A.5 Thermal & thermal→structural coupling
| Practice | Knob |
|---|---|
| Steady-state thermal | `ANTYPE,STATIC` (+ `TUNIF`) |
| Transient thermal | `ANTYPE,TRANS`; `TIMINT,ON`; init `IC`/`TUNIF`; results → `.rth`. **`OUTRES,ALL,ALL`** to write every substep (default writes only *some* → missing intermediate times in `.rth`); for big models throttle with `OUTRES,,<freq>` or a time-table to bound `.rth` size |
| Element switch | `ETCHG,TTS` (thermal→struct) / `STT` |
| Map temps to structure | `LDREAD, TEMP, LSTEP, SBSTEP, TIME, KIMG, Fname, Ext` → reads `.rth`, applies as `BF` body load (interpolates between sets; `LAST` = last set) |
| Transient 1-way loop | structural `ANTYPE,TRANS` substeps + `LDREAD,TEMP,,,time,,jobname,rth` per thermal time |
| Reference temp / CTE | `TREF`; `MP,ALPX`/`MP,CTEX`; offset `TOFFST`; `STEF` |
| Convection / radiation BC | **SURF151/152** surface-effect elements (`ESURF` on faces): convection `SF,,CONV` (temp-dependent film via table); **radiation to a space/extra node** via `MP,EMIS` + form factor `FORMF` + `STEF`/`SBCONST` (KEYOPT extra/space-node); link FLUID116 for bulk T |
| Thermal loads (APDL) | surface: `SF`/`SFE` (convection `CONV`, heat flux `HFLUX`); body: `BF`/`BFE` (heat-gen `HGEN`); time/temp-dependent via `%TABLE%` (e.g. `SFE,ALL,,HFLUX,,%HFLUX_TAB%`). Apply on a selected set (`NSEL`/`ESEL`) then `ALLSEL` |
| T-dependent props (APDL) | `MPTEMP` (temp table, ≤100 pts) → `MPDATA,KXX`/`C`/`DENS,…` per temp; or `TB,THERM`. **Beyond the table ends ANSYS uses CONSTANT (flat) extrapolation** → extend the table through the full T-range (critical for cryogenic `k(T)`/`cp(T)`) |

### A.6 Postprocessing & result files
- Files: `.rst` (struct), `.rth` (thermal), `.nlh` (nonlinear hist), `.mntr` (monitor).
- Reactions `PRRSOL,Lab` / summed `FSUM` / `NFORCE`; element `PRESOL`/`ETABLE`; energy `PRENERGY`; error `PRERR`.
- **Heat through a surface/junction** (decisive thermal-path diagnostic): at a fixed-T node the **reaction heat** `PRRSOL,HEAT` = heat the model extracts (steady: Σin = Σout). For an *internal* surface with no BC: `NSEL` the surface nodes → `ESLN` → `FSUM` → `*GET,q,FSUM,0,ITEM,HEAT`. **Requires Nodal-Forces output ON** (`OUTRES,NLOAD,ALL` / Output Controls "Nodal Forces = Yes") before solving, else it returns zero.
- `/POST1` (`SET,LSTEP,SBSTEP`), time-history `/POST26`. Averaged `PLNSOL`/`PRNSOL`; unaveraged `PLESOL`/`PRESOL`.
- PyDPF: `from ansys.dpf import core as dpf; model = dpf.Model('file.rst'); model.results.displacement().eval()`; thermal `dpf.Model('file.rth')` → `temperature()`. PyMAPDL: `mapdl.post_processing.nodal_temperature()/.nodal_displacement()`.
  - **Scope + time** (transient/by-body): `ms = model.metadata.meshed_region.named_selection('FLANGE')`; `t = model.results.temperature.on_all_time_freqs.on_mesh_scoping(ms).eval()`. **Default = last time-step only** → always set the time scoping for transients.
  - Averaging: stress/strain are **ElementalNodal**; convert with `to_nodal` / `nodal_to_elemental` / `elemental_mean`; reduce with the `min_max` operator. PyMAPDL `post_processing` **respects the current `NSEL`/`ESEL` selection** — select the body/component first; `element_temperature` = min/max/avg of each element's nodes.
  - **Units & names (silent traps):** check the unit system via `model.metadata.result_info` and per-field `field.unit` — **temperature often returns in °C (MKS), not K** → convert and record in `qoi.csv` (a "stays at 290" vs "17" confusion is usually this). **List `meshed_region.available_named_selections` FIRST** — Workbench names are **UPPERCASE** (+ auto `_CONTACT`/`_TARGET`/`CM_n`); a wrong-case or not-sent-to-solver name returns an **empty scoping silently** (no error), so you extract nothing.
  - **Probe at a sensor coordinate** (not a node — for test-vs-FEM correlation): PyDPF `ops.mapping.on_coordinates(fields, coordinates, mesh)` interpolates via element shape functions — **a point OUTSIDE the mesh returns EMPTY silently**, so snap sensor coords onto the body first. APDL/PyMAPDL: `n = mapdl.queries.node(x,y,z)` (nearest node — there is **no `*GET` by coordinate**), then `TEMP(n)`. Map each sensor's (x,y,z)→node/interp once and reuse.
- **Export arrays to CSV (APDL-native):** `*CFOPEN,file,csv` → `*VWRITE,a(1),b(1)` + a FORTRAN format line on the next line `(F12.5,',',F12.5)` → `*CFCLOSE`. `*VWRITE` is limited to **19 columns** → use `*MWRITE` for wider arrays. A headless alternative to DPF / `run_python_script` for pulling out tables.

---

## B. Ansys Mechanical (PyMechanical / ACT)

Embedded `from ansys.mechanical.core import App; app = App()`. Remote `launch_mechanical()` + `mechanical.run_python_script(...)`. API root `Ansys.ACT.Automation.Mechanical`.

| Practice | API |
|---|---|
| Mesh global size | `mesh = Model.Mesh; mesh.ElementSize = Quantity('5 [mm]')` |
| Mesh method | MeshControls → `Method.Method = MethodType.Tetrahedrons/Sweep/MultiZone` |
| Local sizing | `mesh.AddSizing()` → `.Location`, `.ElementSize` |
| Quality | `mesh.MeshMetric = MeshMetricType.SkewnessMetric/AspectRatio`; `mesh.ElementQuality` |
| Generate | `mesh.GenerateMesh()` |
| Named selections | `Model.AddNamedSelection()` (sent UPPERCASE to solver) |
| Analysis settings | `analysis.AnalysisSettings` → `.NumberOfSteps`, `.SetAutomaticTimeStepping(...)`, `.SetInitialTimeStep/.SetMinimumTimeStep/.SetMaximumTimeStep`, `.SetNumberOfSubSteps` |
| Large deflection | `.LargeDeflection = True` |
| Solver type | `.SolverType = SolverType.Direct/Iterative` |
| Convergence | `NonlinearAdaptiveRegion`; `.NewtonRaphsonOption` |
| Solve | `analysis.Solve(True)` |
| Results | `solution.AddTotalDeformation()/AddEquivalentStress()/AddForceReaction()/AddTemperature()`; `.Location = ns`; `result.Maximum/.Minimum/.PlotData` |
| Convergence object | result → Convergence (Allowable Change %, max loops) automates h-refinement |
| Thermal→struct | `Model.AddImportedLoad()` / Imported Body Temperature; or upstream thermal system link |

---

## C. Simcenter Nastran

### C.1 Solution sequences
| SOL | Use |
|---|---|
| 101 | Linear statics (+ linear contact) |
| 103 | Normal modes |
| 105 | Linear buckling |
| 106 | Nonlinear statics (legacy single-step) |
| 153 | Steady-state heat transfer (nonlinear allowed) |
| 159 | Transient heat transfer |
| 401 | Multistep nonlinear (static/dynamic/preload/modal; thermal coupling) |
| 402 | Multistep nonlinear w/ large rotation |

### C.2 Parallel
- SMP: `nastran job.dat parallel=8`
- DMP: `nastran job.dat dmparallel=4` (`numseg` subdomains); hybrid `parallel=`×`dmparallel=`.
- GPU: `gpgpu=any|nvidia|amd`.

### C.3 Nonlinear / time-step control
| Practice | Entry |
|---|---|
| SOL 106 increments/convergence | `NLPARM` (NINC, KMETHOD, KSTEP, MAXITER, CONV=UPW, EPSU/EPSP/EPSW, INTOUT) via `NLPARM=id` |
| SOL 106/129 transient nonlinear | `TSTEPNL` |
| SOL 401 control | `NLCNTL=id`; time step `TSTEP1` |
| SOL 402 control | `NLCNTL2` |
| Linear transient step | `TSTEP` (N×dt blocks) |
| Large displacement | `PARAM,LGDISP,1` (SOL 106); built-in 401/402 |

### C.4 Thermal & mapping
- Steady `SOL 153`, transient `SOL 159` (init `TEMPD`/`IC`, `TSTEP`, radiation `RADBC`/`VIEW`/`RADCAV`, convection `CONV`/`PCONV`). SOL 153 steady result can seed SOL 159 initial conditions.
- **Thermal contact (conduction across a joint) = GLUE, not friction contact** `[DOCS-ONLY]`: surfaces `BSURF` (shells) / `BSURFS` (solids), paired in **`BGSET`** (glue set) + **`BGPARM`** (glue params); in SOL 153/159 a glue connection is treated as a **conductance** link. (`BCTSET`+`BCTPARM` = friction *structural* contact, NOT the thermal conductor. Ansys analog = bonded thermal contact + TCC.)
- **Simcenter 3D Thermal Coupling** (GUI-level TMG analog of TCC) `[DOCS-ONLY]`: coupling types **conductive / radiative / convective / interface**; source → Primary Region, target → Secondary Region; **Total Conductance** magnitude → contactor (Absolute value), supports **constant / time-dependent / ΔT-dependent** values.
- Temps → structural: `TEMPERATURE(LOAD)=sid` referencing `TEMP`/`TEMPF`; `TEMPERATURE(INITIAL)`; `PARAM,TABS`; CTE `A` on `MATi`. SOL 401/402 direct coupling with Simcenter 3D Thermal.

### C.5 Output & parsing
- Case control: `DISPLACEMENT`, `STRESS(CORNER)`, `SPCFORCES` (reactions), `FORCE`, `OLOAD`, `THERMAL`, `FLUX`; `…(PLOT/PRINT/PUNCH)`; `PARAM,POST,-1` → `.op2`.
- Files: `.f06` (text), `.op2` (binary), `.pch`, `.h5`.
- **f06 error triage (headless):** a fatal message → Nastran exits early (don't trust a clean shell exit code). Grep the `.f06` for **UFM** (User Fatal Message), **SFM** (System Fatal Message), and **UWM** (User Warning Message); the message number + text gives the cause (e.g. UFM 1126 datablock, SFM 2199 with ASET/OMIT and no linear-material elements).
- pyNastran: `from pyNastran.bdf.bdf import BDF` / `from pyNastran.op2.op2 import OP2` → `op2.displacements`, `op2.spc_forces`, `op2.temperatures`.
- **Heat-balance gate (thermal V&V, Nastran equivalent of the reaction check):** request `OLOAD` (applied-heat resultant) + `SPCFORCES` (constraint/reaction heat at fixed-T nodes); at steady state Σ applied = Σ reaction. `[DOCS-ONLY]` (pre-NX12 `OLOAD` was wrong for an `SLOAD` in a nodal coordinate system — check version).

### C.6 Connections
RBE2 (rigid), RBE3 (distributed), RBAR, MPC, CBUSH (6-DOF), CELAS, CWELD (spot), CFAST (fastener), CGAP (gap). Contact/glue: **`BCTSET`+`BCTPARM`** (friction contact, PENN/PENT/search), **`BGSET`+`BGPARM`** (glue — and the thermal conductor in SOL 153/159), surfaces **`BSURF`** (shell)/**`BSURFS`** (solid).

### C.7 Run-time performance / scratch / memory
- Command form: `nastran job.dat key=value …`. **Scratch** `sdir=D:\scratch` (or `SDIRECTORY` in `nastran.rcf`) — put on a **fast local SSD / RAID-0, never a network drive**; disk-full in scratch is the usual large-run failure.
- Memory `mem=`; **`buffsize` 8192 → 32769** for models > ~400k DOF (more efficient I/O). `scr=yes` for scratch DBs you don't need to keep.

---

## D. Thermal Desktop / OpenTD / SINDA-FLUINT

OpenTD = .NET (Net4.8/Net8) API; engine SINDA/FLUINT (a **batch-style solution engine**); radiation RadCAD (Monte-Carlo ray trace). Drive via Python+pythonnet, C# (recommended), VB, or MATLAB.

**Headless reality `[DOCS-ONLY]`:** the GUI block is **geometry *authoring*** (AutoCAD-based) — **solving, parametric sweeps, and post are scriptable** via OpenTD on an **existing `.dwg`** (create/query/modify/**run**/control). So the practical pattern is: author the `.dwg` once in the GUI, then drive solves/symbol-sweeps/post headlessly. `OpenTD.CoSolver` links a running SINDA solution to other software (live co-solve). pythonnet must match the CPython version: **pythonnet ≥3.1 supports CPython 3.10–3.14** — do *not* assume 3.14 fails; pin a tested pythonnet+Python pair per TD release (older pythonnet builds were the source of the "use 3.11/3.12" rule), or host from C#. See `references/agent-automation-boundary.md` (§ "Python runtime for OpenTD").

### D.1 Connect / load (Python)
```python
import clr
clr.AddReference("OpenTDv251")          # version-specific
from OpenTDv251 import ThermalDesktop
td = ThermalDesktop()
td.ConnectConfig.DwgPathname = r"C:\model\sat.dwg"
td.Connect()
```

### D.2 Symbols (parametric)
```python
sym = td.GetSymbol("emiss_panel")
sym.Value = "0.85"; sym.Update()
td.UpdateSymbols()
```

### D.3 Cases / run / solver control
```python
csm = td.GetCaseSetManager()
cs  = csm.GetCaseSet("Hot")
cs.Run()
```
SINDA control constants on the CaseSet: `NLOOPS` (max steady iters), `DRLXCA`/`ARLXCA` (max ΔT/iter ~1e-2), energy balance `EBALSA`/`BALENG`, transient `TIMEND`, `DTIMEI` (initial step), `DTIMEH/DTIMEL` (max/min step), `DTMPCA` (max ΔT/step). Steady = `STEADY`/`FASTIC`; transient = `FWDBCK`/`FORWRD`.

### D.4 RadCAD radiation
Radiation task → set optical props (`emiss`, `absor`), `RaysPerNode`, `CalculateRadks()`/`CalculateHeatRates()` → RADKs + orbital heating; `OrbitManager` for orbit/heating cases. Verify enclosure row-sums → 1.

### D.5 Reading output
ASCII `.out` (nodal T, Q, energy balance); query post-run via OpenTD model objects (`td.GetThermalNodes()` → `.Temperature`). **Binary save files** (`SAVE`/`RESAVE`-restart/`CRASH` routines) hold nodes/conductors per time/record for headless post (colorize/extract by time or record number). **Energy-balance registers** `[DOCS-ONLY]`: `EBALSA`/`EBALSC` (steady arithmetic/diffusion), `EBALNA`/`EBALNC` (transient) — assert imbalance ≪ throughput; `OUTPUT`/`OPEITR` control output frequency.

---

## E. Open-source solver headless one-liners

All of these run **fully headless** (no GUI) from a text input file — the agent-headless open-source counterpart to the commercial solvers above. Exact flags/module names are **version-dependent**; verify against your build's docs. `[VERIFIED-web]` for the canonical invocation form; `[DOCS-ONLY]` where the Python-module API is release-specific.

| Solver | Headless invocation | Notes |
|---|---|---|
| **code_aster** | `bin/run_aster file.export` (the `.export` lists mesh/command/result files); modern Python API `import code_aster` `[DOCS-ONLY]` | `run_aster` (and the older `as_run`) drive the study from the `.export`. The `import code_aster` module API is the modern replacement for `as_run` scripting — **verify it exists in your release**. Primary distribution is now Salome-Meca **Apptainer `.sif`**. |
| **Elmer** | `ElmerSolver case.sif` (single); `ElmerSolver_mpi` + `mpirun -np N` for parallel | The `.sif` (Solver Input File) is the plain-text case. Mesh first with `ElmerGrid`. `ElmerGUI` is optional/GUI-only. |
| **CalculiX** | solver `ccx jobname` (**no `.inp` extension** — it appends it); pre/post `cgx -b f.fbd` (batch) | `ccx jobname` reads `jobname.inp`, writes `jobname.frd`/`.dat`. `cgx -b file.fbd` runs CGX in **batch** against an FBD command file (use `-bg` for a background/no-window variant — verify per build). |
| **SU2** | `SU2_CFD config.cfg`; parallel `mpirun -np N SU2_CFD config.cfg`; Python `import pysu2` `[DOCS-ONLY]` | `config.cfg` is the case. `pysu2` is the in-memory Python wrapper (built with the `-Denable-pywrapper=true` Meson option) for co-simulation/control — **verify it was compiled into your build**. |
| **FEniCSx** | `import dolfinx` (pure Python — run with `python script.py`, parallel `mpirun -np N python script.py`) | No CLI solver; the model **is** the Python script. Legacy FEniCS used `import dolfin`; FEniCSx is `import dolfinx` — confirm which generation is installed. |
| **MOOSE** | `./<app>-opt -i input.i`; parallel `mpiexec -n N ./<app>-opt -i input.i` | Each MOOSE app is a compiled executable (`-opt` = optimized build; `-dbg` = debug). `input.i` is the HIT/GetPot input. Add `--n-threads=N` for hybrid MPI+threads. |

### E.1 Version-dependent batch flags (verify exact spelling against your release)

The **direction** below is confirmed, but the **exact flag/option spelling is release-specific** — these tools have renamed or reworked their headless switches between versions. Confirm against your installed release's docs before scripting:

- **Siemens NX Check-Mate** — runs validation/Check-Mate checks in batch via NX Open / `run_journal.exe`; the exact batch one-liner and check-profile arguments vary by NX version. *Verify against your release.*
- **LS-PrePost** — headless/batch playback of command files exists, but the switch differs by build (`-nographics` vs `-batch`, plus `c=command.cfile`). *Verify against your release.*
- **LS-OPT** — batch/queued invocation against a `.lsopt` project file; the CLI form and queuing options are version-dependent. *Verify against your release.*
- **Altair (HyperWorks)** — Tcl/Python batch via `hmbatch` (HyperMesh) and `hwbatch` (HyperView/HyperGraph), also `acc` for compute; exact executable names and flags shift across HyperWorks releases. *Verify against your release.*
- **Simcenter STAR-CCM+** — Java macros are the canonical batch path (`starccm+ -batch macro.java case.sim -np N`); **native Python `.py` macros are supported only from a recent release** — confirm your version supports `-batch macro.py` before relying on it.

---

## Thermal practice (cross-platform quick map)

| Practice | Guidance |
|---|---|
| Steady vs transient | Steady = end-state, static BC. Transient = time-varying BC / thermal-mass response. |
| Lumped vs distributed | Biot `Bi=hL_c/k`<0.1 → lumped; ≥0.1 → mesh gradient. L_c=V/A_s. |
| Time step | Fourier `Fo=αΔt/L²≤0.5` at steepest gradient; small Δt₀≈L_min²/(4α) then auto-grow. |
| Radiation | T⁴ nonlinear; set abs-temp offset; α(solar) ≠ ε(IR). |
| View factors | raise rays/hemicube until Σ F_ij=1 per surface & ΔF<tol. |
| Interface conductance | MAPDL `TCC`; Nastran `PCONV`/`BCTPARM`; TD contactor conductance. |
| Energy balance | Σ Q_in = Σ Q_out (steady) / ΔU/Δt (transient); imbalance ≪1%. |
| Initial conditions | dominate transient until ~3–5 τ; always set correctly. |
