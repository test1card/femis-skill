# ML Surrogates, Data-Driven ROM & Digital Twins

Scope: the **data-driven / learned** layer that sits on top of classical FEM/CAE — projection-based reduced-order models (POD-Galerkin, PODI, DMD, operator inference) and the **hyper-reduction** that makes nonlinear ROM affordable; **certified reduced-basis** reduction with rigorous error bounds; **ML surrogates** (Gaussian-process/Kriging, polynomial chaos, neural operators, PINNs, graph-network simulators), each maturity-tagged honestly; **digital twins** (executable/hybrid, FMI/FMU, calibration-to-sensor); and the governing **validity-envelope / solve-vs-predict** discipline that keeps all of it honest.

This file is the **data-driven counterpart** to `advanced-methods.md`. The *classical, structure-preserving* reduction methods (Component Mode Synthesis / Craig–Bampton, Guyan static condensation, Krylov moment-matching, modal truncation, intrusive POD-Galerkin) live there and are **not duplicated here** — see `advanced-methods.md` §1–2 and cross-link freely. The single rule that ties both files together: **a reduced or learned model is an approximation over a band — state the band and verify against the full FE before any engineering decision.**

Maturity tags used throughout: **`PRODUCTION`** (shipping in commercial CAE, used in industry) · **`EMERGING`** (productized but early / narrow / vendor-pilot) · **`RESEARCH`** (papers only, not yet trustworthy for ENGINEERING/SIGNOFF). Confidence tags: **[ESTABLISHED]** = settled method with a textbook/standard · **[ACTIVE]** = mature method, active refinement · **[FRONTIER]** = moving fast, treat specifics as dated-on-arrival.

> **The one rule, stated up front.** Every method in this file *predicts* rather than *solves*. A prediction is only valid **inside the training / parameter envelope** it was built from; outside it, error is **silent and unbounded**. Use surrogates and ROMs to **search, screen, and explore**; **re-solve the down-selected optimum / critical point on the full FE (or full CFD) model before any engineering, certification, or sign-off claim.** This is the same discipline `advanced-methods.md` (re-solve the topology/optimization result) and `optimization-calibration.md` (re-solve the surrogate optimum; calibration ≠ validation) already enforce — extended to the learned layer.

---

## 1. Projection-based ROM (data-driven branch)

Classical ROM reduces a model by a *physically structured* subspace (constraint + normal modes, Krylov vectors). The data-driven branch instead builds the subspace **from snapshots of solved cases** (a "snapshot matrix"), then projects. The split that matters operationally:

- **Intrusive** ROM needs access to the solver's operators/residual (assemble the reduced system by Galerkin/Petrov–Galerkin projection of the governing equations). Highest fidelity and the only branch with clean stability theory, but **unavailable behind a black-box commercial solver**.
- **Non-intrusive** ROM needs **only input→output data** (snapshots, parameters). It treats the solver as a black box and learns either a reduced *operator* or a reduced *response map*. **This is the branch that matters for the skill's headless / vendor-locked reality** — it works with any solver you can script to dump fields.

### 1.1 POD / SVD basis from snapshots [ESTABLISHED] `PRODUCTION` (method)

The workhorse. **Recipe:** (1) collect snapshots — solve the full model at a spread of parameters / time steps and stack the state vectors as columns of `S`; (2) **SVD** `S = UΣVᵀ`; the left singular vectors `U` are the POD (a.k.a. PCA / KL / empirical-eigenfunction) basis, ordered by captured energy `σᵢ²`; (3) **truncate** at the smallest `r` such that cumulative energy `Σσᵢ² (i≤r) / Σσᵢ²` ≥ a threshold — **99–99.9%** is typical, but the energy criterion is a *guide, not a guarantee* of QoI accuracy (see honesty gates). The reduced state is `x ≈ U_r a`, with `r ≪ N`.

- **Galerkin projection (intrusive):** substitute `x = U_r a` into the FE residual and project with `U_rᵀ` → an `r×r` reduced system. Cheap *if* the operators are linear/affine in parameters; nonlinear terms re-introduce full-order cost unless hyper-reduced (§2).
- **PODI — POD with Interpolation (non-intrusive):** build a POD basis from snapshots, then **interpolate the reduced coefficients** `a(μ)` across the parameter space (RBF / spline / Kriging on the coefficient vectors, often with interpolation on the Grassmann manifold for the basis itself). No solver operators needed — pure data. Excellent for **parametric design sweeps over a fixed geometry family**; the limitation is that interpolation, not physics, governs between samples → respect the convex hull of the training parameters.

### 1.2 DMD — Dynamic Mode Decomposition [ACTIVE] `PRODUCTION` (method) / `EMERGING` (forecasting)

Purely **data-driven, equation-free** spatiotemporal modal decomposition: from a sequence of snapshots, DMD fits a best-fit linear operator `A` such that `x_{k+1} ≈ A x_k`, and returns **modes** (spatial structures) each with a **complex eigenvalue** (growth/decay rate + oscillation frequency). Use for **identifying** coherent structures, dominant frequencies, and transient/flow dynamics, and for **short-horizon forecasting**. Caveats: it assumes (locally) linear dynamics, so **forecasting beyond the sampled regime drifts**; strongly nonlinear or chaotic systems need extensions (extended/Hankel DMD, with delay embeddings). Variants worth knowing: **exact DMD**, **optimized/total-least-squares DMD** (measurement-noise robust), **DMD with control** (separates actuation), **parametric DMD**.

### 1.3 Operator Inference (OpInf) [FRONTIER] `EMERGING`

The **non-intrusive way to recover a *physics-structured* reduced model** — the bridge between pure data fitting and intrusive projection. Postulate a reduced model of known *form* (e.g. linear + quadratic operators, as polynomial nonlinearities admit) `ȧ = c + A a + H (a⊗a) + B u`, then **learn the reduced operators by least-squares regression** against projected snapshot data — *without ever touching the full-order operators or solver source* (Peherstorfer & Willcox). Because it recovers operators (not just a response map), it **extrapolates in time / inputs better than pure regression** and yields a model you can analyze. 2024–2025 work adds **structure/physics constraints** — Hamiltonian-preserving, gradient/energy-preserving, state-constrained, and **streaming** (online-updating) variants — which materially improve **stability** (the recurring OpInf failure mode). Treat as `EMERGING`: powerful, real tooling exists, but stability and regularization choices still need expert care and held-out verification.

### 1.4 Nonlinear-manifold ROM (autoencoder latent ROM) [FRONTIER] `RESEARCH`

POD is a *linear* subspace; for advection-dominated / sharp-front problems the Kolmogorov n-width decays slowly and linear ROM needs an impractically large `r`. **Nonlinear-manifold ROM** replaces `U_r` with a **learned nonlinear decoder** (autoencoder) `x ≈ g(a)` and projects the dynamics onto the manifold. Can reach far smaller latent dimension on transport problems, but training cost, stability, and verification are open — keep at `RESEARCH` for engineering use.

---

## 2. Hyper-reduction (the efficiency enabler for *nonlinear* ROM) [ACTIVE]

**Why it is non-optional.** A POD-Galerkin ROM of a *nonlinear* model still has to **evaluate the nonlinear term (and its Jacobian) at every full-order point** each step, then project — so the online cost stays `O(N)`, defeating the reduction. **Hyper-reduction** breaks this by evaluating the nonlinear term at **only a small, cleverly selected subset** of points/elements and reconstructing the rest. Without it, a nonlinear ROM is not actually reduced in cost.

| Method | Idea | Selects | Strength | Caveat | Tag |
|---|---|---|---|---|---|
| **(D)EIM** — (Discrete) Empirical Interpolation [Chaturantabut & Sorensen 2010] | Build a POD basis for the *nonlinear term*; greedily pick interpolation indices; evaluate the nonlinearity only at those indices | a small set of **sample points/DOF** | General, well-understood, the standard for nonlinear POD-Galerkin | Can lose stability/accuracy if sample points are poorly placed; matrix-DEIM / Q-DEIM improve conditioning | `PRODUCTION` (method) |
| **gappy POD** | Reconstruct a full field from sparse samples by least-squares in the POD basis | sensor/sample locations | Field reconstruction, flow estimation from sparse sensors, the parent idea behind DEIM | Reconstruction quality ∝ sample placement & basis coverage | `ESTABLISHED` |
| **ECSW** — Energy-Conserving Sampling & Weighting [Farhat et al. 2014/2015] | Select a **reduced set of elements** with positive **weights** so the reduced internal-force *virtual work* matches the full model | a sparse **element subset + weights** | **Preserves Lagrangian structure / stability**; excellent for structural FE nonlinear dynamics; mesh-consistent | Training (NNLS weight solve) is an offline cost; weights are basis-specific | `PRODUCTION` (auto crash/NVH ROM) / `EMERGING` (at large scale) |

**Practitioner rule.** If you are reducing a **nonlinear** model and the online run is *not* dramatically faster than the FOM, you have not hyper-reduced — check that the nonlinear-term evaluation is sampled (DEIM) or the quadrature is reduced (ECSW), not full. For structural/contact nonlinearity prefer **ECSW** (structure-preserving); for general nonlinear PDE terms **DEIM** is the default. Always overlay hyper-reduced ROM vs FOM on a **held-out** parameter/time point — hyper-reduction adds a *second* approximation layer on top of the projection error.

See also: classical intrusive ROM, Krylov, CMS — `advanced-methods.md` §1–2.

---

## 3. Certified / bounded ROM — reduced-basis with a-posteriori error bounds [ESTABLISHED] `EMERGING` (in commercial CAE)

The rigorous answer to "**how wrong is my ROM at this parameter?**" — the GCI-analog for model reduction. For **parametrized** problems that must be re-evaluated across a parameter space (geometry, material, BC, load — the many-query / real-time / digital-twin case), the **certified reduced-basis (RB) method** (Patera, Rozza, Hesthaven, Stamm) builds the basis with a **provable, cheaply computable a-posteriori error bound** in the loop:

- **Offline greedy sampling.** Start with one basis vector; repeatedly evaluate a **rigorous error bound** `Δ_N(μ) ≥ ‖u(μ) − u_N(μ)‖` over a training parameter sample, **add the snapshot at the worst-bound parameter**, re-orthonormalize, repeat until `max Δ_N(μ) < tol`. The greedy makes the basis **provably near-optimal** without solving the FOM everywhere — the bound *steers* the sampling, which is what makes it both rigorous and cheap.
- **Offline–online split.** The error bound (and the reduced output) is computed online in cost **independent of the full-model size** `N` — the expensive, `N`-dependent quantities (residual norms, stability/coercivity-constant estimates via the **successive-constraint method**) are precomputed offline. Online you get *both* the reduced output *and* its certified error bar in `O(N_basis)`.
- **Output bounds.** A separate, often tighter, a-posteriori bound on a **linear output functional** `s(μ)` (the QoI) — the rigorous embodiment of "converge the QoI, not the field."
- **POD also admits bounds.** Residual-based a-posteriori error indicators exist for POD-Galerkin ROMs too (less tight than RB's certified bounds, but the same idea).

**The generalizable takeaway for *any* ROM — CMS, Krylov, POD included:** a reduced model should carry a **computable error estimate**, not merely a validity band asserted by a single FRF/transient overlay. When the tool exposes a certified bound or residual indicator (research stacks like **pyMOR / RBniCS**, and increasingly vendor digital-twin/ROM features), **drive basis construction and trust by the bound**. When it doesn't, the FRF/transient verification against the FOM is the **weaker substitute — state that explicitly** in the deliverable.

**Honest maturity.** The *theory* is `ESTABLISHED` (textbook: Hesthaven–Rozza–Stamm 2015). In *day-to-day commercial CAE* the certified-RB machinery is rarely exposed in the big GUI solvers, so its practical maturity there is `EMERGING`; it is `PRODUCTION` in the reduced-basis research/open-source ecosystem. Cross-link: the certified-ROM bullet in `advanced-methods.md` §2.

---

## 4. ML surrogates — families, with honest maturity tags

A **surrogate** (metamodel / emulator) replaces an expensive solver call with a cheap learned approximation `ŷ = f̂(x)`. The classical, well-understood surrogates (Kriging/GP, RSM, RBF, PCE) live in the DOE→surrogate→optimize workflow of `optimization-calibration.md` §4.3 — summarized here with the newer learned families and a maturity verdict for each. **Read this table as "what is it trustworthy for *today*," not "what is exciting."**

| Family | What it learns | Data need | Generalization | Gives uncertainty? | Maturity | Best fit |
|---|---|---|---|---|---|---|
| **Gaussian Process / Kriging** | Smooth response map `x→y` over a modest # of scalar inputs | Low (10s–100s of points) | Interpolatory; degrades far from samples but **error bar grows there** | **Yes — native, calibrated** posterior variance | **`PRODUCTION`** | DOE, design optimization, calibration, active learning. The default surrogate. |
| **Polynomial Chaos Expansion (PCE)** | Spectral expansion of `y` in orthogonal polynomials of the random inputs | Low–moderate (curse of dimension) | Excellent for **smooth, low-D** stochastic response; analytic mean/variance/Sobol | **Yes** (moments analytic) | **`PRODUCTION`** (UQ) | Forward UQ, variance decomposition; see `vv-uq.md` §6. |
| **RBF / response-surface (RSM)** | Low-order or radial interpolant | Low | Local; cheap | No (basic forms) | **`PRODUCTION`** | Quick metamodels, low-D screening. |
| **Neural operators (FNO, DeepONet, Geo-FNO)** | The **solution operator** — a map between *function spaces* (BC/forcing/geometry field → solution field) | **High** (100s–1000s of solved cases) | Generalizes across BCs/forcings/(some) geometries; **mesh/discretization-independent inference**; 10²–10⁵× faster than the solver online | Not natively (needs ensembling / Bayesian wrappers) | **`EMERGING`** (productized via vendor AI; narrow per-family) | Many-query over a geometry/parameter family; the engine behind commercial "AI surrogate" products. |
| **PINNs — Physics-Informed Neural Networks** | A field that minimizes **PDE residual + BC/IC** as a loss (labeled data optional) | Low–none for the physics loss; sparse data for inverse | Per-problem; usually **retrain for new geometry/BC** | No (needs Bayesian/ensemble PINN) | **`EMERGING`** (inverse / assimilation) / **`RESEARCH`** (as a forward solver) | **Inverse problems, data assimilation, parameter ID, sparse-data** — *not* a general forward FEM replacement. |
| **Graph-network simulators (MeshGraphNets / GNS)** | Next-state update via message passing **directly on the mesh** | High | Natural for unstructured meshes, Lagrangian/contact; struggles to scale | No (natively) | **`RESEARCH`→`EMERGING`** | Research; industrial million-cell meshes still hard (cost ∝ nodes+edges). |

### 4.1 Gaussian process / Kriging — the production default [ESTABLISHED] `PRODUCTION`
The surrogate to reach for first. Cheap to fit, **interpolates the training data exactly**, and — uniquely among common surrogates — returns a **calibrated predictive variance** that *grows away from samples*. That error bar is what powers **active learning / Bayesian optimization** (place the next expensive run where variance × improvement is highest) and **surrogate reliability** (U-function / AK-MCS). Caveats: scales poorly past ~10³–10⁴ points (dense covariance) and a few dozen input dimensions; the variance is **only as good as the kernel/stationarity assumptions** — verify, don't trust blindly. See `vv-uq.md` §6 and `optimization-calibration.md` §4.3.

### 4.2 Polynomial-chaos surrogate [ESTABLISHED] `PRODUCTION` (UQ)
A surrogate *and* a UQ tool in one: the PCE coefficients give the **mean, variance, and Sobol sensitivity indices analytically**, no extra sampling. Non-intrusive (regression / pseudo-spectral) PCE treats the solver as a black box. Strong for **smooth, low-dimensional** stochastic responses; suffers the curse of dimensionality and struggles with discontinuous/bifurcating responses. Detailed treatment in `vv-uq.md` §6.

### 4.3 Neural operators (FNO / DeepONet) [FRONTIER] `EMERGING`
The family behind the commercial "train on your simulation data, predict on geometry you haven't solved" products. They learn the **solution operator** between function spaces, so one trained model serves a *whole family* of BCs/forcings (and, with Geo-FNO / geometry-aware variants, a range of shapes), inferring in milliseconds. **DeepONet** (Lu et al.) uses a branch net (input function) × trunk net (query location); **FNO** (Li et al.) parameterizes the operator with learned spectral (Fourier) convolutions, giving discretization-independence. Honest framing: the **speedup is *inference* speed after a large upfront training-data cost** (hundreds–thousands of full solves); accuracy is **bounded by training-set coverage** and collapses out-of-distribution. `EMERGING` — real and shipping, but per-application and not a certified solver.

### 4.4 PINNs [FRONTIER] `EMERGING` (inverse) / `RESEARCH` (forward)
A neural net trained so its output satisfies the **governing PDE residual + boundary/initial conditions** (Raissi, Perdikaris & Karniadakis), so it can train with **little or no labeled data**. **Where they genuinely shine: inverse problems, parameter identification, data assimilation, and sparse/scattered-data** settings — the physics loss regularizes the ill-posed inverse, which is exactly the calibration/`optimization-calibration.md` use case. **Where they are oversold: as a general forward solver.** Documented failure modes: slow training; **competing loss-gradient terms** (PDE vs BC vs data) drive convergence to bad minima; **stiff / multiscale** problems are hard; and each new geometry/BC usually means **retraining** — so a PINN rarely beats a mature FEM solver on a one-off forward solve. Treat forward-PINN claims with skepticism; treat inverse/assimilation PINNs as a real `EMERGING` tool.

### 4.5 Graph-network simulators [FRONTIER] `RESEARCH`→`EMERGING`
Message-passing GNNs (MeshGraphNets / GNS) that learn next-state updates **directly on the FE/FV mesh** — natural for unstructured meshes and Lagrangian/contact dynamics. The blocker is **scalability**: memory and cost scale with nodes + edges, so industrial million-cell meshes remain hard (hence 2024–2025 hierarchical / multiscale GNN research). Promising, not yet trustworthy for engineering sign-off.

### 4.6 Commercial AI-surrogate products (vendor-neutral, examples not endorsements)
By 2025 most major CAE vendors ship an **AI/ML surrogate** as a first-class offering, and a separate open framework lets you build your own. Named generically as examples, not recommendations:
- **Turnkey vendor AI surrogates** — train on your *existing simulation data* (often solver-agnostic, even cross-vendor), learn the shape→performance map, predict 10×–1000× faster for design exploration. Examples in the market: solver-vendor AI add-ons to flagship CFD/structural suites (e.g. SimAI-class, PhysicsAI-class products).
- **Open / build-your-own frameworks** — e.g. **NVIDIA Modulus / PhysicsNeMo**-class libraries (PyTorch-based, Apache-licensed) to build PINNs, neural operators, and GNNs with GPU-distributed training. You own the model but need ML skill, GPUs, and a training corpus.

**Honest framing (say this to any stakeholder):** these are **design-exploration accelerators, not certified solvers.** The 10×–1000× numbers are **inference** speed *after* an upfront training-data cost (hundreds–thousands of solved cases); accuracy is bounded by training-set coverage. Use for screening/optimization; **re-solve down-selected designs on the full solver before sign-off** (§7).

---

## 5. Digital twins (executable & hybrid)

A digital twin is the **deployed consumer** of this skill's ROM (§1–3) and calibration (`optimization-calibration.md`) layers — a model running *alongside* a physical asset, fed by its sensors. It is genuinely `PRODUCTION` (with caveats), and is mostly a *systems-integration* of methods you already have.

### 5.1 Taxonomy (get the noun right) [ESTABLISHED]
| Term | Data flow | What it is |
|---|---|---|
| Digital **model** | none (manual) | A simulation model of the asset; no live coupling. |
| Digital **shadow** | sensor → model (one-way) | Model updated *from* the asset, but does not act back. |
| Digital **twin** | sensor ↔ model (two-way) | Bidirectional: model informs decisions/control on the asset. |
| **Executable digital twin (xDT)** | self-contained, real-time | A deployable, self-contained real-time model (ROM/FMU) that runs in the field beside the asset. |

Don't call a one-way monitoring dashboard a "twin" — it's a shadow. The distinction is the bidirectional, decision-closing loop.

### 5.2 The hybrid twin [ACTIVE] `EMERGING`→`PRODUCTION`
The robust production pattern: **physics ROM + data-driven correction**. A physics-based ROM (POD / CMS / Krylov state-space — `advanced-methods.md` §2) provides **causality and extrapolation**; a **data-driven residual model** (GP / NN) learns the **un-modeled discrepancy** between ROM and measured reality. This is exactly the **Kennedy–O'Hagan model-discrepancy term** (`vv-uq.md` §6) made operational — the principled way to combine "physics where we trust it, data where we don't." Pure-ML twins lose the physics extrapolation safety net; pure-physics twins carry the un-modeled discrepancy uncorrected.

### 5.3 Deployment path: FE/CFD → ROM → FMU → runtime [ACTIVE] `PRODUCTION`
1. Build/verify the full FE or CFD model.
2. **Reduce** to a ROM (§1–3; or CMS/Krylov state-space per `advanced-methods.md` §2) sized to the operating band / controller bandwidth.
3. **Export as an FMU** via **FMI** (Functional Mock-up Interface) — Co-Simulation mode for a self-contained real-time component. **FMI 3.0** adds **clocks / event handling** for multi-rate and hybrid (continuous + discrete) twins and explicitly targets digital-twin / virtual-ECU / hybrid-simulation use cases; the ecosystem is broad (hundreds of FMI-compatible tools). 
4. Run in a real-time runtime alongside the asset. **Reuse the FMI co-simulation discipline already documented in `advanced-methods.md` §3.3** — communication/macro-step size is the key accuracy knob; reduce the *communication* step (not the output interval) if the coupling is inaccurate; watch for algebraic-loop / coupling instability.

### 5.4 Continuous calibration-to-sensor [ACTIVE] `EMERGING`
A live twin is the skill's **inverse-ID / model-updating machinery run online** against streaming sensor data (`optimization-calibration.md` §4.4). **Carry every calibration gate into the online loop:** fit the **QoI-bearing observable** (not a convenient aggregate); reject **edge-pinned knobs** (an optimum at a corridor edge is a structural error being absorbed by a knob — `optimization-calibration.md` calibration-objective gate); flag **unsensored bodies** that drive the QoI and carry an explicit error band; audit material assignments. Online, add **drift detection**: a twin that wanders **outside its training/reduction envelope must flag, not silently extrapolate** (§7).

---

## 6. When a surrogate / ROM pays — vs when to just solve

The decision is about **amortization and credibility**, not novelty. Use this table; the default for a one-off, novel, or sign-off-bound analysis is **just solve**.

| Situation | Surrogate / ROM? | Why |
|---|---|---|
| One-off high-fidelity analysis; novel geometry; certification deliverable | **No — use the full solver** | No training corpus; no credibility path; the upfront data cost never amortizes. |
| Many similar designs (DOE, optimization, design sweep) over a *fixed geometry family* | **Yes — neural operator / GP / parametric ROM** | Train/reduce once, infer 10²–10⁵× faster; cost amortizes over the sweep. |
| Real-time / embedded prediction, control, digital twin | **Yes — ROM (certified if available) / operator** | ms inference; physics ROM for causality (§5). |
| Inverse problem / parameter ID / sparse-sensor assimilation | **Yes — PINN or GP/Bayesian** | Physics/Bayes prior regularizes the ill-posed inverse. |
| Forward solve of a stiff/multiscale PDE, one geometry, high accuracy needed | **No — solve** | PINN/operator training cost & accuracy rarely beat a mature solver here. |
| Query **outside** the training/parameter envelope | **No — solve (or retrain)** | Surrogates do **not** extrapolate; OOD error is silent and unbounded. |

**Break-even intuition.** A surrogate pays only when `N_queries × (cost_solve − cost_infer) > cost_training_corpus + cost_fit + cost_verify`. For 3 designs, just solve. For 3,000, train a surrogate. In between, a **parametric / certified ROM** (lower training cost than a deep net, carries an error bound) is often the sweet spot.

---

## 7. Honesty gates (apply to every surrogate, ROM, and twin)

These mirror — and extend to the learned layer — the discipline already in `advanced-methods.md`, `optimization-calibration.md`, and `vv-uq.md`. Enforce all of them before reporting a learned/reduced result.

1. **Validity-envelope rule.** A surrogate/ROM is an **interpolator over its training/parameter envelope**. **State the envelope explicitly** — geometry family, parameter ranges, BC/load types, mesh/discretization family, time window — and **flag every query outside it**. Out-of-distribution error is *silent*: the model returns a confident, wrong number. For GP/Bayesian models, monitor the predictive variance; for others, monitor distance-to-training-set and a drift metric.
2. **Solve-vs-predict.** A surrogate/ROM **predicts**; the solver **solves**. **Never ship a surrogate-predicted result as ENGINEERING / SIGNOFF without a confirming full-FE (or full-CFD) solve** at the operating point. Identical to "re-solve the optimum on full FE" (`optimization-calibration.md` §4.3, `advanced-methods.md` §4.2). Re-solve the optimum, the critical point, *and* any point the search pushed near an envelope edge.
3. **Held-out test error is mandatory.** Report accuracy on cases **not used in training**, as a **distribution** (P50 / P95 relative error **per QoI**), not a single best-case number. Overlay ROM-vs-FOM (or surrogate-vs-solve) on a held-out parameter/time point.
4. **Carry a computable error estimate where one exists.** Prefer a **certified bound** (§3) or residual indicator over an asserted validity band; where none exists, say so and use the held-out distribution as the (weaker) substitute.
5. **Calibration ≠ validation still applies.** A surrogate or hybrid-twin correction fit to data is *calibrated*; **validation requires independent data** (`vv-uq.md`). Carry the calibration-objective gate (fit the QoI observable; reject edge-pinned knobs; flag unsensored bodies).
6. **ROM stability is not inherited.** A Galerkin POD-ROM **can be unstable even when the FOM is stable** — verify stability, use closure models / structure-preserving projection (ECSW, structure-constrained OpInf) where needed.
7. **VVUQ for SciML is an open problem — be honest about it.** There is **no MMS / GCI equivalent yet** for a trained neural net. Treat learned-surrogate numerical error as an **explicit epistemic term** and carry it; do not present a SciML prediction as a verified result, and never let it cross into SIGNOFF without a full-model confirmation. (For classical-method verification — MMS, GCI, a-posteriori estimators — see `meshing-convergence.md` and `vv-uq.md`.)
8. **Agent / autonomy note.** Training, inference, ROM construction, and the online calibration loop are **AGENT-HEADLESS** (scriptable Python). **Accepting a surrogate/twin result for sign-off remains HUMAN-JUDGMENT** — idealization, envelope adequacy, accepting edge-pinned knobs, and the final engineering decision are not delegated to the surrogate.

---

## See also

- `advanced-methods.md` §1–2 — **classical** ROM: CMS / Craig–Bampton, Guyan, Krylov moment-matching, modal truncation, intrusive POD-Galerkin, state-space export; **§2 certified/bounded-ROM bullet**; §3.3 FMI/FMU co-simulation discipline (reused by digital twins).
- `optimization-calibration.md` — DOE→surrogate→optimize (Kriging/GP/PCE), inverse parameter ID / model updating, the **calibration-objective gate**, and the **re-solve-the-optimum** rule extended here to ML surrogates.
- `vv-uq.md` §6 — forward UQ (PCE/Sobol), Kennedy–O'Hagan model-discrepancy (the principled hybrid-twin correction), identifiability / FIM, and the SciML-VVUQ open-problem framing.
- `meshing-convergence.md` — GCI and a-posteriori error estimation (the discretization-error analogs of §3's ROM error bounds).
- `software-landscape.md` — where commercial AI-surrogate / SPDM / digital-twin tooling sits in the platform map.

## SOURCES

Projection ROM, POD/PODI, DMD, operator inference
- Benner, Gugercin & Willcox, "A Survey of Projection-Based MOR for Parametric Dynamical Systems," *SIAM Review* 57(4):483–531 (2015).
- Hijazi et al., "Data-Driven POD-Galerkin ROM for Turbulent Flows," *J. Comput. Phys.* — https://www.sciencedirect.com/science/article/abs/pii/S0021999120302874
- Schmid, "Dynamic Mode Decomposition of numerical and experimental data," *J. Fluid Mech.* 656:5–28 (2010); Kutz, Brunton, Brunton & Proctor, *Dynamic Mode Decomposition* (SIAM, 2016).
- Peherstorfer & Willcox, "Data-driven operator inference for nonintrusive projection-based model reduction," *CMAME* 306:196–215 (2016); structure-preserving / streaming OpInf, arXiv 2304.06262, 2502.03672, 2601.12161 (2023–2025).

Hyper-reduction
- Chaturantabut & Sorensen, "Nonlinear Model Reduction via Discrete Empirical Interpolation (DEIM)," *SIAM J. Sci. Comput.* 32(5):2737–2764 (2010).
- Everson & Sirovich, "Karhunen–Loève procedure for gappy data," *J. Opt. Soc. Am. A* 12(8):1657 (1995) (gappy POD).
- Farhat, Avery, Chapman & Cortial, "Dimensional reduction of nonlinear FE dynamic models with finite rotations and energy-conserving mesh sampling and weighting (ECSW)," *IJNME* 98(9):625–662 (2014); Farhat et al., *IJNME* 102(5) (2015).

Certified reduced-basis ROM
- Hesthaven, Rozza & Stamm, *Certified Reduced Basis Methods for Parametrized PDEs* (Springer, 2015).
- Rozza, Huynh & Patera, "Reduced basis approximation and a posteriori error estimation for affinely parametrized elliptic coercive PDEs," *Arch. Comput. Methods Eng.* 15:229–275 (2007).
- Quarteroni, Rozza & Manzoni, "Certified reduced basis approximation for parametrized PDEs and applications," *J. Math. in Industry* 1:3 (2011). Tooling: pyMOR, RBniCS.

ML surrogates / neural operators / PINNs / GNN
- Lu, Jin, Pang, Zhang & Karniadakis, "Learning nonlinear operators via DeepONet," *Nature Machine Intelligence* 3:218–229 (2021).
- Li, Kovachki, Azizzadenesheli et al., "Fourier Neural Operator for Parametric PDEs," ICLR 2021; Geo-FNO, NeurIPS 2024.
- Raissi, Perdikaris & Karniadakis, "Physics-Informed Neural Networks," *J. Comput. Phys.* 378:686–707 (2019); PINN review, *Appl. Sci.* 15(14):8092 (2025); loss-landscape / stiffness failure modes, *Mathematics* 13(20):3289 (2025).
- Pfaff, Fortunato, Sanchez-Gonzalez & Battaglia, "Learning Mesh-Based Simulation with Graph Networks (MeshGraphNets)," ICLR 2021; GNS scaling work (2024–2025).
- Hesthaven & Ubbiali, "Non-intrusive ROM of nonlinear problems using neural networks (POD-NN)," *J. Comput. Phys.* 363:55–78 (2018).
- VVUQ-for-SciML necessity — see the ASME V&V 10/20/40 verification & validation standards and Oberkampf & Roy, *Verification and Validation in Scientific Computing* (Cambridge, 2010); applied to data-driven / SciML surrogates this remains an open methodological problem. [UNVERIFIED — no single canonical SciML-specific reference; grounded in the general V&V literature above]

Digital twins / FMI
- "The Executable Digital Twin: merging the digital and the physical worlds," arXiv 2210.17402.
- FMI 3.0 standard (clocks / event handling; digital-twin & hybrid-simulation use cases) — https://fmi-standard.org
- Kennedy & O'Hagan, "Bayesian calibration of computer models," *J. Royal Stat. Soc. B* 63(3):425–464 (2001) (the model-discrepancy basis for hybrid twins).
