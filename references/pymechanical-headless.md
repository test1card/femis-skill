# PyMechanical / Workbench headless automation — debugged gotchas

Hard-won from a real headless Ansys Mechanical thermal run on a real model. Each item cost real
debugging time; verify against your driver scripts and release.

## 0. Embedded App vs remote session (pick the mode)

- **Embedded `App()`** — Mechanical runs **in your Python process**; full object-model (read/create/update/
  delete); best for scripts/Jupyter. `app = App(); app.update_globals(globals())`; reuse with `app.new()`.
  **Linux: launch under the shipped `mechanical-env`** (sets env vars before Python starts) or embedding fails.
- **Remote `launch_mechanical()`** — Mechanical as a **separate server process**; best for CI/CD, Docker,
  multiple simultaneous instances; drive via `mechanical.run_python_script(...)`.
- Both need **Mechanical 2024 R2+** installed and licensed; PyMechanical supports **Python 3.10–3.13**.
  The license level (Pro/Premium/Enterprise) follows the analysis features used.

## 1. Solver core count lives on `SolveProcessSettings` (NOT `...Settings`)

The cores/parallel knobs are on **`Analysis.SolveConfigurations[0].SolveProcessSettings`**:

```python
sps = analysis.SolveConfigurations[0].SolveProcessSettings
sps.MaxNumberOfCores  = 16        # physical cores
sps.DistributeSolution = True     # DMP (distributed) — big speedup vs SMP
sps.ThreadsPerProcess  = 1
```

**Trap:** `SolveConfigurations[0].Settings` is **`QueueSettings`** and has **no core
fields** — setting cores there silently does nothing. Getting this wrong cost a
**9-minute vs 70-second** solve (ran single-core by default).

## 2. Injecting tabular temperature-dependent material properties (Granta / EngineeringData XML)

For T-dependent k(T), cp(T) etc. into Workbench Engineering Data:
- Put the **dependent values** in `<ParameterValue parameter="paN">/<Data>` (in the production
  model: `pr9/pa14` = conductivity, `pr8/pa13` = specific heat); the **independent**
  Temperature parameter is in **°C**.
- **★ Every per-point Qualifier** (Variable Type / Offset / Scale / Units) under a data
  parameter **must be an N-value comma list matching the `<Data>` count**, or
  project-open fails: *"Qualifier count does not match Data count."* Metadata-only
  qualifiers stay scalar.
- Edit `EngineeringData.xml`, then **copy** the table into `material.engd` + `SYS.engd`
  — but the `.engd` files use a **different parameter-id scheme**, so **don't regex the
  same ids in place** in them. Mech-side, load with `Materials.Import(xml)`.

## 3. Headless solve monitoring (the live log is in a private scratch dir)

The Mechanical server writes `solve.out` / `.mntr` to a **private working directory
that is cleaned up on session exit**. To monitor/keep them:
- **Before** solving, report `analysis.WorkingDir` to a status file the driver controls.
- Tail the live **`.mntr`** during the solve: current *solution time* ÷ *end time* = % done.
- Capture `solve.out` **before the session closes** (copy it out), or it's gone.

## 4. Workbench system-share journaling — geometry share ≠ defeature share

```python
template.CreateSystem(
    ComponentsToShare=[geometryComponent],   # shares GEOMETRY into a new system
    Position="Right", RelativeTo=system1)
```
**Caveats:** sharing **geometry** does **not** carry the **defeature/suppression** (that
lives in the source **Model**, not the geometry) — the new system gets the **full body
count** and needs **re-defeature**; and the new system's **Model cell needs an Update**
before its analysis branch populates. (To carry contacts/mesh, share the **Model** cell
instead — see `ansys-thermal-contact-pitfalls.md` §2.)

## 5. Step-0 tooling reality checks

- **Thermal Desktop** (CRTech) ships inside ANSYS v261 at `…/v261/CRTech/Thermal Desktop/`
  but is **AutoCAD-based** (GUI authoring via `TdDwgLauncher`) — **not trivially
  headless**. **OpenTD** automation needs **pythonnet**, which **fails on Python 3.14**
  ("Failed to initialize Python.Runtime.dll"). pythonnet's supported CPython ceiling
  lags the latest release — **use a Python 3.11/3.12 (or 3.13) env** for OpenTD, or host
  OpenTD from **C#/.NET** or **MATLAB** instead.
- The Claude Code harness **auto-backgrounds long shell solves** — **poll result/status
  files**, don't rely on a completion notification.

## 6. Workbench batch & archive

- **Batch run:** `runwb2 -B -R project.wbjn` (`-B` batch/no-GUI, `-R` run the journal). Add `--archive`
  to write a `_completed.wbpz` when done.
- **`.wbpz`** = the whole project (`.wbpj` + `_files/`) zipped — the portable unit; restore via **File ▸ Open**
  (2019R1+) or *Restore Archive*. You can check an archive's version **without** restoring it. **Archive right
  after a run** to capture the solved state before private scratch dirs are cleaned (pairs with §3 monitoring).
- **Parametric (DesignPoints) headless:** `runwb2 -B -R study.wbjn` (or `-I -E` to start a control server);
  update inputs with `DesignPoint.SetParameterExpression(param, expr)` → `Parameters.Update`, retrieve outputs via
  `ExportAllDesignPointsData()`. **Trap: output params silently don't update unless result files are saved in the
  expected location** (external-run results must sit with the originals).

## 7. PyDPF result-reading version pitfalls

- Match **`ansys-dpf-core`** to the **DPF server / Ansys-install** version. A mismatch → `DPFServerException`
  or **zero/empty results from a valid `.rst`** the native software reads fine.
- Use a recent `ansys-dpf-core`: **≥0.10** integrates the gate/grpc deps (no more sync issues); **≥0.3.2**
  silences the InvalidProtobuf UTF-8 warning. Always verify a non-empty mesh + valid time scoping before trusting an extract.

## 8. PyMAPDL run hygiene (distributed stragglers, lock, resume) — from the live run

- **`-dis` leaves MPI stragglers + a lock that blocks relaunch.** After
  `launch_mapdl(additional_switches='-dis', nproc=12)` + `mapdl.exit()`, Windows often leaves ~N `ANSYS.exe` /
  `ANSYS261.exe` + `hydra_bstrap_proxy` / `hydra_pmi_proxy` / `mpiexec` processes, and the next launch dies with
  `LockFileException: Unable to remove lock file …\file.lock`. **Between headless runs:** kill all
  `ANSYS|MAPDL|hydra|mpiexec|aisol` processes (**keep `ansyslmd`**, the license daemon), then delete
  `<run_location>\*.lock`. `mapdl.exit()` does **not** reliably reap the MPI workers on Windows.
- **`mapdl.resume(db)` restores the saved BC/load state.** A db saved after an anchored solve still carries its
  `D,…,TEMP` constraints → a "fresh" single-anchor re-solve silently has TWO anchors (wrong connectivity read /
  contaminated calibration). **Clear loads after a resume** (`DDELE,ALL,ALL` / `FDELE,ALL,ALL`, or rebuild from
  the deck) before applying new BCs.

## 9. Embedded `.mechdb` save / lock / recovery hygiene

- Save with **`app.save_as(path, overwrite=True, remove_lock=True)`** — `remove_lock` clears a stale lock before saving.
- `launch_gui()` works on a **temp copy** of the active `.mechdb`; `cleanup_gui()` removes it afterward.
- **Opening multiple `.mechdb` in sequence in one embedded process is buggy** — use a **fresh `App` / process per project** rather than reusing one instance across projects.
- After a Workbench/Mechanical crash, the project is **recoverable from the `.mechdb`** file.

## Cross-references
- Thermally-inert structural contacts, mesh-rebuild-after-contact-change, connectivity
  union-find gate, MAPDL escape hatch: `ansys-thermal-contact-pitfalls.md`.
- Full per-platform command cheat-sheet: `platform-commands.md`.
