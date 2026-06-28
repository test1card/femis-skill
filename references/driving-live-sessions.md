# Driving live solver sessions — the inspect → step → re-inspect discipline

When you drive a *stateful* solver session (PyMAPDL, PyMechanical, PyWorkbench, PyFluent, COMSOL via JPype, an
NX journal) rather than submitting a finished deck, the failure mode is different: you can corrupt the model
with a blind sequence of commands and not notice until the solve. This reference ports the **vendor-neutral
discipline** the dedicated driver skills (workbench / mechanical / comsol) use. Those skills carry the
harness-bound, tool-specific depth; lift the *patterns* here, not their runtime.

## Live session vs pure batch — choose deliberately

- **Pure batch / headless** (preferred for the *many* runs): a complete deck or script → `ansys -b`,
  `nastran.exe`, `abaqus job=`, `fluent -g -i jou`, `comsol batch`. No session state to corrupt; reproducible.
- **Live session** (for *authoring, debugging, human-in-the-loop*): a running solver you drive incrementally.
  Use it to build a model, diagnose a failure, or co-drive with a person — then capture the result as a batch
  deck for production. An agent should treat a live session as something to *observe*, not to fire blindly at.

## The core loop (the single most important pattern)

**inspect state → ONE bounded step → re-inspect → confirm → next step.**

Never send a long blind sequence to a stateful session. After each meaningful change (mesh, contact, BC,
material, solve setting), read the state back and confirm it is what you intended *before* the next step. This
is the drivers' central idea and the biggest gap a knowledge-only skill has.

```text
loop:
  state = inspect()            # element/node counts, contact status, BC list, named selections — counts/booleans
  step  = ONE bounded action   # e.g. generate mesh; add ONE contact pair; set cores
  apply(step)
  assert inspect() == expected # did the count/flag change as intended? if not, STOP
```

## On failure: STOP and enter a debug loop (don't push forward)

A broken session does not get better by sending more commands. On any error or unexpected state:
1. **Stop** the forward sequence.
2. **Reproduce minimally** — the smallest action that triggers it.
3. **Read the actual error + current model state** (the solver log / `last_response` / the inspect view), not
   the exit code.
4. **Fix the cause**, re-inspect, then resume.
**Acceptance is physics/observed behavior, not the exit code** (ties to the SMOKE/DEBUG/ENGINEERING/SIGNOFF
modes in SKILL.md): a session that "ran" but left bodies at the initial temperature or a singular peak has not
succeeded. See the Failure-triage table in SKILL.md and `references/ansys-thermal-contact-pitfalls.md`.

## Observing a live session

- **PyMechanical `batch=False`** launches a real desktop Mechanical window bound to the SAME session the SDK
  drives — a screenshot is an always-current view of SDK state, ideal for human-in-the-loop co-driving. Embedded
  `App()` runs like batch (no window); `launch_mechanical(batch=False)` gives the live window.
- **Pure-headless analog:** there is no window, so dump state to JSON and inspect that (counts, statuses), or
  render off-screen (pyvista `Plotter(off_screen=True)`, ParaView `pvbatch`).
- **Return sanitized counts/booleans, never raw names/paths** out of the session — both for context hygiene and
  to avoid leaking model internals.

## Getting data OUT of API sessions (the handoff trap)

Each driver has a quirk that silently returns nothing if you ignore it:
- **PyMechanical `run_python_script` returns only the *last statement's* string.** Returning an ACT object
  (e.g. `ExtAPI.DataModel.Project`) yields an empty string. Serialize explicitly: `json.dumps(...)` inside the
  script → `json.loads(...)` outside, or write a CSV/JSON file and read it back.
- **PyWorkbench / `runwb2 -B -R` IronPython journals: stdout is not piped back.** Write results to a JSON file
  in `%TEMP%`/the working dir and read the file afterward.
- **PyMAPDL** is the clean case: `*GET`/`mapdl.parameters`/PyDPF return values directly, fully headless, no GUI
  promotion of parameters needed.

## Session lifecycle & hygiene

- **Cores** live on the right object — PyMechanical `Analysis.SolveConfigurations[0].SolveProcessSettings`
  (`MaxNumberOfCores`, `DistributeSolution`), NOT `...Settings` (that's QueueSettings → single-core by accident).
- **Don't drive a multi-hour `SOLVE` over live gRPC** — the channel can drop and orphan the solver. Submit a
  batch deck (`ansysNNN -b -i job.dat`) or stream a complete solve block, then **poll** `.mntr`/`.rst`.
- **Clean exit** to release the license and reap stragglers: distributed (`-dis`) MAPDL leaves
  `ANSYS*`/`hydra*`/`mpiexec` and a `*.lock` on Windows; kill them (keep `ansyslmd`) and delete the lock before
  relaunch. Always `mapdl.exit()` / close the session.
- **Resumed DB carries old loads** — `RESUME` restores saved `D,…`/`F,…`; clear with `DDELE,ALL,ALL` /
  `FDELE,ALL,ALL` before applying new BCs (contaminated calibration otherwise).

## Per-tool entry points (vendor-neutral)

| Tool | Live / headless launch | Notes |
|---|---|---|
| **PyMAPDL** | `launch_mapdl(nproc=, additional_switches='-dis')` | fully headless; `*SET` params first-class |
| **PyMechanical** | `App()` (embedded=batch) · `launch_mechanical(batch=False)` (live window) | `run_python_script` returns last statement only |
| **PyWorkbench** | `launch_workbench(show_gui=False)` · `runwb2 -B -R x.wbjn` | promote inputs to `P#` in GUI once; journal writes JSON to temp |
| **PyFluent** | `launch_fluent(show_gui=False, mode='solver')` | TUI journals also work `-g -i jou` |
| **PyDPF** | `dpf.Model('file.rst'/'.rth')` | match `ansys-dpf-core` to server version; scope time/body |
| **Simcenter NX** | `run_journal.exe journal.py` → `OpenActiveDisplay(.sim)+Solution.Solve()` | **seed `.sim` in GUI first** (templates don't resolve in batch) |
| **COMSOL** | JPype/Java API · `comsol batch -inputfile` / `comsolbatch.exe` | see `references/comsol.md` |

## See also

- `references/comsol.md` — COMSOL-specific live/offline recipes (`.mph` introspection, JPype tags-first, batch).
- `references/agent-automation-boundary.md` — which of these operations is agent-headless vs human-GUI.
- `references/pymechanical-headless.md` — PyMechanical/Workbench headless gotchas in depth.
- The author's `workbench` / `mechanical` / `comsol` driver skills — harness-bound, tool-specific live-session depth.
