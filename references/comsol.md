# COMSOL Multiphysics — automation & recipes

COMSOL's differentiator is **unified multiphysics** (structural, thermal, CFD, electromagnetics, acoustics,
chemical/electrochemical) with **built-in couplings** (thermal expansion, Joule/induction heating, FSI,
electromagnetic heating) and **unit-aware, equation-based** modeling. This reference gives the automation
patterns; the author's `comsol` driver skill carries live JPype-session depth.

## Automation paths

| Path | Use | Entry |
|---|---|---|
| **Java API ("Model Java")** | the native model API; record any GUI action as Java | drive from Python via **JPype**, or compile/run Java, or MATLAB |
| **Python via JPype** | scripting from Python against the Java API | `jpype.startJVM(classpath=COMSOL plugins)`, then `com.comsol.model.util.ModelUtil` |
| **MATLAB LiveLink** | MATLAB scripting | `mphstart`, `mphload`, `mphint`, `mpheval` |
| **Application Builder / Method editor** | Java methods inside an app | for packaged apps |
| **Batch (headless)** | run a finished `.mph` | `comsol batch -inputfile in.mph -outputfile out.mph -study std1` · Windows `comsolbatch.exe` · client-server `comsol mphserver` + JPype client · cluster `comsol batch -mpibootstrap` |

Batch and live sessions both **consume a license seat**. `mphserver` gives a persistent licensed server you
attach to from Python (good for the inspect→step→re-inspect loop in `references/driving-live-sessions.md`).

## Model tree is tags-first

Everything is addressed by a **tag**, and you **set properties before building/solving**:
```python
m = ModelUtil.create("Model")
m.component().create("comp1", True)
m.component("comp1").geom().create("geom1", 3)
# ... create features, then SET props, then build/solve:
m.component("comp1").physics().create("solid", "SolidMechanics", "geom1")
m.study().create("std1"); m.study("std1").create("stat", "Stationary")
m.study("std1").run()
```
Tags must be unique; build geometry/mesh before referencing them downstream; check
`m.sol("sol1").getLastComputationInfo()` / the log rather than assuming success.

## `.mph` = a ZIP archive (offline introspection, no license)

An `.mph` is a ZIP. You can **inspect a model without a license or a running COMSOL**: unzip and read the XML
model tree to enumerate node tags, types, physics, parameters, and study setup. This is the agent-friendly way
to understand a model you cannot (or should not) open live — classify node types, list parameters, confirm the
study before committing a licensed run. (The `comsol` driver skill ships an `inspect_mph`/`nodeType` recipe.)

## Results extraction (headless caveat)

**Image/plot export is often flaky or blocked headless.** Prefer **numeric** results:
- LiveLink/Java: `mphint`/`mphmean`/`mpheval` (integrate/average/evaluate), `mphinterp` (field at points),
  **table export** to CSV.
- Define **probes / derived values / evaluation groups** in the model and export their tables.
- For fields, export to VTK/`.txt` and post in ParaView rather than rendering inside COMSOL.

## Practical notes

- **Units:** COMSOL is unit-aware (enter `7850[kg/m^3]`, `200[GPa]`) and converts internally — still sanity-check
  a natural frequency / reaction after setup.
- **Study types:** Stationary, Time Dependent, Eigenfrequency, Frequency Domain, Parametric Sweep, plus the
  Optimization Module (gradient/derivative-free) for calibration/inverse problems.
- **Meshing:** physics-controlled (quick) vs user-controlled (needed for CFD boundary layers / stress
  concentrations); the default mesh is usually too coarse for the physics — run a mesh-independence study (GCI,
  `references/meshing-convergence.md`).
- **Multiphysics couplings** are the reason to choose COMSOL — use the built-in coupling nodes (Thermal
  Expansion, Fluid-Structure Interaction, Electromagnetic Heating) rather than hand-rolling field transfer.
- **Convergence:** equation-based/strongly-coupled problems need good initial values, ramping (continuation /
  auxiliary sweep), and a fully-coupled vs segregated solver choice — read the solver log, not just the green check.

## See also

- `references/driving-live-sessions.md` — the inspect→step→re-inspect discipline for live JPype sessions.
- `references/software-landscape.md` — where COMSOL sits among the CAE tools.
- `references/agent-automation-boundary.md` — which COMSOL operations are agent-headless vs human-GUI.
- The author's `comsol` driver skill — live JPype/Java-Shell session control, `.mph` introspection, shared-desktop co-driving.
