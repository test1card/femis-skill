# Optimization, Calibration & Model Updating

Turn a parametric FE model into a **design-exploration / inverse-problem engine**: sensitivity → metamodel →
optimize, or *calibrate* model parameters until predictions match measurements. Contact-conductance / cryo
contact-calibration is one narrow instance of general parameter identification — the same machinery does
material-curve fitting, modal model-updating, lightweighting, robust design.

Status tags: **[VERIFIED-web]** = stated in vendor/official docs; **[DOCS-ONLY]** = from docs/forums, not run;
**[NEEDS-HW-TEST]** = reproduce on the licensed install before trusting in ENGINEERING/SIGNOFF.

## Tool map

| Tool | Platform | Own surrogate? | Steady/scalar | **Transient T(t) curve** | Optimizer | Launch |
|---|---|---|---|---|---|---|
| **optiSLang** | Ansys | **Yes** — MOP (auto metamodel competition, picks best by CoP) | Yes | **YES — native signal/curve MOP** (temperature fields, FRFs, force–disp); recent releases add **Damped Least Squares** for noisy measured signals | NLPQL/EA/DLS/adaptive | GUI wizard; **batch `optislang.exe -b --python`** / PyOptiSLang |
| **DesignXplorer** | Ansys (Workbench) | Yes — response surfaces (CCD/Box-Behnken/LHS → Kriging/genetic-aggregation) | Yes (scalar params) | **No native curve fit** — reduce T(t) to scalars (peak, value-at-time, time-to-threshold) | Goal-Driven Opt, Six Sigma | GUI; DP update headless via `runwb2 -B -R` |
| **PyMAPDL + SciPy** | Ansys | No (bring your own) | Yes | **YES — by construction**: solve transient → PyDPF extract T(t) → custom RMS misfit → `scipy.optimize(..., bounds=)` | any (scipy/scikit/BoTorch) | **Pure Python, zero-GUI** |
| **HEEDS / SHERPA** | Siemens (also NX **Design Space Exploration**) | Optional (surrogates / AI Predictor); baseline SHERPA needs none | Yes | **YES — by construction**: solver-neutral black box; tag inputs in the solver's text input file, scrape responses (incl. a time-history column) from the output file, define a residual objective | SHERPA (auto hybrid global+local), MO-SHERPA | Study built in Modeler GUI; **HEEDS Solver runs from CLI / HPC** |
| **Simcenter 3D Correlation & Model Updating** | Siemens (structural) | No — sensitivity-based | Yes (modal) | **NO — modal/FRF only** (freqs, mode shapes/MAC/CoMAC, FRF/FRAC); test data via UNV/UFF | Least-Squares or Genetic | GUI; NXOpen-scriptable |
| **TMG Correlation** (Maya HTT, Simcenter 3D **Thermal**) | Siemens | No — error-minimization | **Yes** | **YES — calibrates steady AND transient temperature curves** vs reference/test temps (the thermal analog of structural Correlation) | built-in | GUI in Simcenter 3D Pre/Post |
| **NX / Simcenter Nastran SOL 200** | Siemens | No — gradient-based (analytic design sensitivities) | Yes | **Responses exist** (DRESP1 TDISP/TVELO/TACCL/TSTRE) **but model-matching-to-test is demonstrated in freq/modal**; no documented thermal-cooldown-T(t) update workflow | gradient (DESVAR, DCONSTR) | Batch deck (SOL 200) |

## The transient-calibration question — answered

- **Native T(t)-curve calibration lives in exactly two productized places:** Ansys **optiSLang** (signal/curve MOP, DLS) for any platform's signal, and **TMG Correlation** for Simcenter 3D **thermal** (steady+transient). [VERIFIED-web]
- **Dedicated *structural* model-updating is steady/modal/FRF-only** — Simcenter 3D Correlation and the practical SOL 200 "Model Matching" target frequencies / mode shapes / FRF, not a time-history thermal curve. [VERIFIED-web]
- **Everywhere else, transient calibration = wrap the solver in a general optimizer with a hand-built time-series objective.** The mechanism is identical across **HEEDS/SHERPA**, **PyMAPDL+SciPy**, and (in principle) **SOL 200 DRESP2/3**: perturb bounded params → run the transient solve → extract T(t) → compute RMS/least-squares misfit vs the measured curve → minimize. The PyMAPDL+SciPy loop (transient + conductance/`ks` knobs + custom cooldown-RMS objective) is the validated reference pattern; optiSLang / TMG Correlation are the productized alternatives, not a missing capability.
- **DesignXplorer is scalar-only** — not for curve targets without reducing T(t) to scalars. [DOCS-ONLY]

## Calibration-objective gate (enforce before any model-updating run)

A calibration is only as good as its objective. Enforce these — they are how a calibration silently hides a structural error:

1. **Fit the downstream observable, not a convenient aggregate sensor-RMS.** The metric must be the temperature of the **bodies that carry the QoI + their spatial gradient at the measurement epoch(s)**, not an aggregate transient RMS over incidental thermometers. A good fit of the wrong target is not validation.
2. **One global scalar can't reproduce a spatial gradient.** A single global conductance multiplier fits the aggregate cooldown rate while **mis-distributing** the gradient — it's a *fudge, not a knob*. Prefer a per-member section/mesh fix **bounded by CAD** (as-built ∫(A/L) per member) over a free global scalar.
3. **Unsensored-body warning.** If a body that drives the QoI has **no sensor**, the fit can't validate it — flag it, carry an explicit error band, and make **predicting that body's temperature** the headline deliverable.
4. **Material-assignment audit.** Every body whose material property drives the QoI must have its real T-dependent props verified *before* trusting a coupled result (a mis-assigned CTE/k/cp poisons the whole systematic).
5. **Knob-corridor + edge check.** Require each calibrated knob to land **inside its physical corridor** (e.g. a pressed metal–metal contact within its measured h_c band). An optimum **pinned at a corridor edge** is a tell that a structural term (wrong BC, wrong area, missing body, wrong radiative neighbor) is being absorbed by the knob — **reject the fit even if the target curve matches**, and cross-check every auxiliary node's settled temperature against the physical stage it is tied to.

## Application domains (these are general inverse/exploration engines, not single-purpose calibrators)

Structural shape/sizing/**topology** optimization & lightweighting · steady+transient **thermal** correlation ·
**modal/dynamics** model updating (MAC/FRF) · flow/CFD optimization (HEEDS↔STAR-CCM+ Design Manager) · MDO /
multi-physics co-sim · sensitivity / DOE / screening · robust design & reliability (Six Sigma, RBDO) ·
material / inverse parameter ID · digital-twin / test-data correlation.

**Pattern across all of them: GUI to author the process, headless/HPC to execute the many runs.**

## ML surrogates for search — fine, but re-solve the optimum (validity-envelope warning)

The DOE→surrogate→optimize workflow (Kriging/GP/PCE/RBF) is **production-standard for *search*** — fit a cheap metamodel, optimize on it, add infill points where it matters. Beyond the classical surrogates, a fast-growing **ML-surrogate** layer (neural operators FNO/DeepONet, POD + neural-net non-intrusive ROM, PINNs for inverse/parameter-ID, graph-network simulators) can be dramatically faster online and is now shipping in vendor "AI predictor / AI surrogate" features. Use them for **screening, optimization, and many-query exploration** — with three non-negotiable caveats:

1. **Validity envelope.** A surrogate is an **interpolator over its training/parameter envelope**; accuracy **collapses out-of-distribution** and the error is **silent** (a confident, wrong number). State the envelope (geometry family, parameter ranges, BC types) and flag any query outside it.
2. **Re-solve the optimum on full FE.** Identical to the rule the classical surrogate workflow already enforces (`advanced-methods.md` §4.3): **never present a surrogate-predicted optimum/critical point as a verified result** — confirm it with a full-FE (or full-CFD) solve before any ENGINEERING/SIGNOFF claim. Also re-solve any point the search pushed near an envelope edge.
3. **Carry UQ + held-out error.** Prefer surrogates that give a calibrated error bar (GP/Bayesian) or wrap an ensemble; report held-out test error as a **distribution per QoI** (P50/P95), not a single number. Calibration ≠ validation still applies.

For the full data-driven / ML-surrogate / digital-twin treatment — families with honest maturity tags, hyper-reduction, certified-ROM error bounds, the **when-a-surrogate-pays-vs-just-solve** decision note, and the continuous calibration-to-sensor (digital-twin) loop that extends the calibration-objective gate online — see **`ml-surrogates-and-rom.md`**.

## Minimizing GUI interaction — recipes

The irreducible manual step everywhere except pure PyMAPDL is **parameter exposure**; after that the
parametrize→calibrate→verify loop is scriptable.

- **PyMAPDL (zero-GUI, preferred when the model is APDL-expressible):** fully parametric deck with `*SET`; from Python `mapdl.parameters["X"]=val` → solve → `*GET`/PyDPF extract → RMS misfit → `scipy.optimize.minimize(..., bounds=)`. No GUI at all.
- **Workbench / DesignXplorer / PyWorkbench:** *GUI once* — click-promote each input/result to a `P#` parameter, save `.wbpj`. *Then headless* — `runwb2 -B -R script.wbjn` or `launch_workbench(show_gui=False)` → `SetParameterExpression` → `UpdateAllDesignPoints` → read outputs; wrap with scipy.
- **optiSLang:** *GUI once* — Solver→Sensitivity→Optimization wizards wire the parametric system + responses/criteria. *Then* re-run via PyOptiSLang/batch as data changes.
- **NX / Simcenter (the GUI-bound platform):** *GUI once* — build the `.prt`/`.fem`/`.sim`, expose driving quantities as **Expressions**, record a solve journal. *Then headless* — `run_journal.exe journal.py -args …` edits expressions / writes the Nastran field, solves, parses `.f06`/`.op2`; loop via an external optimizer. (NX FileNew CAE templates don't resolve in pure batch — see the headless-vs-GUI note in SKILL.md.)
- **HEEDS:** *GUI once* — load a baseline run, **tag** input vars in the solver input file + output responses in the result file, set the run command. *Then* HEEDS runs the whole DOE/optimization automatically, solver as a black box.

## Run note

Treat all rows tagged `[DOCS-ONLY]`/`[NEEDS-HW-TEST]` as hypotheses — run a SMOKE reproducer on the actual
licensed install before relying on them in ENGINEERING/SIGNOFF. The exact `HeedsSolver` CLI flag string and the
literal PyOptiSLang batch-calibration signature are install-specific; confirm them from the tool's own help/logs.
