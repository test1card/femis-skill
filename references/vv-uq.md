# Verification, Validation, Uncertainty Quantification & Simulation Governance — Practitioner Brief

**Scope.** A dense, generalizable best-practices reference for a public FEM/CAE Agent Skill. Covers the V&V vocabulary, code verification, solution verification (mesh/time-step convergence + GCI), validation, the ASME V&V 10 / 20 / 40 standards, NAFEMS quality and benchmarks, uncertainty quantification, robust/reliability design, reporting/traceability, and the top mistakes. Every normative claim is anchored to ASME, NAFEMS, Sandia (Oberkampf/Roy/Trucano), or Roache. See SOURCES at the end.

---

## 1. Vocabulary — get the words right or the rest collapses

The single most consequential idea in this whole field, repeated by every standard and every Sandia author:

- **Verification = "solving the equations right."** Are the mathematical equations being solved correctly? It is a *mathematics* question, judged against exact/known solutions and against the discretization theory. No experimental data is involved. (ASME V&V 10; Roache; Oberkampf & Trucano.)
- **Validation = "solving the right equations."** Does the model represent reality with sufficient accuracy for its intended use? It is a *physics* question, judged by comparison to physical experiment. (ASME V&V 10/20; Oberkampf & Roy.)
- **Verification precedes validation.** A model that does not solve its equations correctly cannot be meaningfully compared to experiment — you would be comparing experimental error against an unknown mixture of numerical error and model-form error. Always verify (code, then solution) before you validate.
- **Calibration ≠ Validation.** Calibration (a.k.a. model updating / parameter tuning / inverse identification) adjusts model parameters so output matches data. **Tuning a model to a dataset and then reporting agreement with that same dataset is not validation — it is circular.** Validation requires comparison against *independent* data not used in calibration. Oberkampf, Trucano, and Roy strictly separate **calibration → validation → prediction**, and produce a *quantitative measure of model-form uncertainty* that survives into prediction. This is the most common single act of self-deception in industrial CAE.
- **Prediction** is the use of the model *outside* the validation domain (different geometry, loads, regime). Predictive capability requires V&V **plus** an explicit accounting of how far you are extrapolating beyond validated conditions (the *applicability* / *domain-of-validation* gap).
- **UQ (Uncertainty Quantification)** is the characterization and propagation of all uncertainties (numerical, parametric, model-form, experimental) so that results carry **error bars, not point values**. Modern ASME usage is **VVUQ** — UQ is not optional decoration; it is the third pillar.

> Mnemonic for the Skill: *Verification asks "is my math right?", Validation asks "is my physics right?", Calibration asks "what parameters make it fit?" — and only the first two earn trust.*

---

## 2. Code Verification — is the solver implemented correctly?

Code verification is performed **once per code/version/feature**, by the developer or a rigorous user, and is independent of any particular engineering problem. The deliverable is evidence that the discretization converges to the exact solution at the **theoretical order of accuracy**.

### 2.1 Method of Manufactured Solutions (MMS) — the gold standard
The most powerful, general code-verification technique (term coined by Oberkampf; technique from Roache & Steinberg; standard reference Roy et al., *J. Comp. Phys.* 2004; Salari & Knupp, Sandia).

Procedure:
1. **Choose** a smooth, non-trivial analytic "manufactured" solution (e.g. products of trig/exponential functions) — it need not be physically realistic, only smooth and exercising all terms.
2. **Substitute** it into the governing PDE/operator to obtain an analytic **source term** (forcing function) that makes the manufactured function the *exact* solution of the modified equations.
3. **Apply** that source term and the corresponding boundary conditions to the code.
4. **Refine** systematically and measure the global discretization error norm (the code's answer vs. the known manufactured solution).
5. **Acceptance test = observed order of accuracy.** Compute the *observed* (a.k.a. apparent/effective) order p and confirm it matches the **formal/theoretical** order. *This is the recommended rigorous acceptance criterion* — not merely "error is small," but "error decreases at the theoretically correct rate."

MMS with systematic refinement is *remarkably sensitive*: it catches order-reducing bugs (wrong stencil, boundary-condition implementation errors, mismatched operators) that a single benchmark comparison hides. It gives code verification a "theorem-like quality with a clearly defined completion point" (Roache).

### 2.2 Benchmark / analytic-solution library (the practical complement)
When MMS is not available, verify against **exact** or **highly accurate reference** solutions:
- **Closed-form references:** Timoshenko (elasticity, plates, beams), Roark's *Formulas for Stress and Strain*, classical heat-conduction solutions (Carslaw & Jaeger).
- **NAFEMS standard benchmarks:** the canonical curated FE verification suite. **LE-series** = Linear Elastic tests (e.g. **LE1** elliptic membrane / plane stress; **LE11** solid cylinder–taper–sphere under a temperature field = a thermo-mechanical benchmark). **T-series** = thermal/heat-transfer benchmarks. Also vibration/dynamics and geometric/material nonlinear sets. *The Standard NAFEMS Benchmarks* (Rev. 3, 1990 and later) supplies target values; quality solvers reproduce them to within ~1–3 % with documented discretization error (e.g. ESRD StressCheck reports <1 % discretization error, <3 % vs. NAFEMS reference, **with the target extraction shown converged before any comparison** — a Simulation Governance requirement).
- **Manufactured/analytic dynamic, contact, and nonlinear references** as available.

**Pitfall:** matching one benchmark at one mesh is *not* code verification — it can pass by luck/cancellation. Code verification requires the *order test under refinement*.

---

## 3. Solution (Calculation) Verification — is *this* run numerically accurate?

Performed **per analysis**, by the user, to estimate the **numerical error of the specific result you will report**. Three error sources, all must be controlled:

> **Acknowledged vs. unacknowledged errors (AIAA G-077 taxonomy).** The three sources below are **acknowledged errors** — discretization, iterative/algebraic, round-off — known in kind and **quantifiable / bounded by GCI and UQ**. They are not the whole picture. **Unacknowledged errors** (coding bugs, wrong BCs, unit slips, mislabeled materials, user blunders) are **not captured by any error band** — a perfectly converged mesh of the wrong problem yields a tight, confident, *wrong* number. They are caught only by **independent checking, benchmark reproduction, and the sanity gates** (free-free/RBM, mass/CoG, SPC-reaction, thermoelastic checks — §7.2), never by tightening tolerances.

### 3.1 Discretization error — mesh & time-step convergence (the dominant one)
Never trust a single mesh. Demonstrate the reported quantity of interest (QoI) is **mesh-independent** (and, for transient problems, **time-step-independent**) via systematic refinement.

**Grid Convergence Index (GCI)** — the ASME V&V 20 / *J. Fluids Eng.* publication-standard method (Roache 1994; Celik et al. 2008). Requires **≥ 3 systematically refined grids** (coarse h₃, medium h₂, fine h₁):

1. **Refinement ratio** `r = h_coarse / h_fine`; keep `r ≥ 1.3` (recommended) and as uniform as possible across levels.
2. **Observed order of accuracy** from three solutions φ₁, φ₂, φ₃:
   `p = ln( (φ₃ − φ₂) / (φ₂ − φ₁) ) / ln(r)`
   (general unequal-ratio form solved iteratively per Celik/Roache). Compare p to the formal order; a wildly off p signals you are **not in the asymptotic range**.
3. **Richardson extrapolation** to estimate the grid-independent value:
   `φ_exact ≈ φ₁ + (φ₁ − φ₂)/(r^p − 1)`.
4. **GCI** (reported as a percentage error band on the fine grid):
   `GCI = (F_s · |e|) / (r^p − 1)`, with relative error `e = (φ₂ − φ₁)/φ₁`.
   **Safety factor F_s = 1.25 when using 3+ grids** (the recommended, calibrated value); **F_s = 3.0 when only 2 grids are available** (much more conservative — and a sign you should add a third).
5. **Asymptotic-range check:** the solution is in the asymptotic range when `GCI₂₃ / (r^p · GCI₁₂) ≈ 1`. If not, refine further — your error estimate is unreliable.

**Reporting rule:** state the QoI **with its GCI band** (e.g. "σ_max = 102 ± 2 MPa, GCI = 1.9 %"), not a bare number. Different QoIs converge at different rates — *higher-order/local quantities (peak stress, wall flux) converge slower than integral quantities (total reaction, drag, total heat).* Verify the specific quantity you will report.

**Practical convergence acceptance (engineering rule-of-thumb, weaker than full GCI):** QoI change **< ~2–5 % across three successive refinements**; displacement converges faster than stress (displacements are primary DOFs, stresses are derived). For stress concentrations, aim for several (≥3–5) elements through the gradient/thickness and use quadratic (p≥2) elements.

### 3.2 Iterative / algebraic convergence error
For nonlinear or iterative solvers, residuals must be driven low enough that **iterative error ≪ discretization error**. Tighten residual tolerances and confirm the QoI is stationary in the residual; a loosely converged nonlinear solve corrupts the mesh study.

### 3.3 Round-off / finite-precision error
Usually negligible in double precision but can dominate on very fine grids, ill-conditioned systems, or differences of nearly-equal large numbers. Watch conditioning; switch to higher precision if a refinement study stops converging at small h.

---

## 4. Validation — is the model the right physics?

Validation compares the (already-verified) simulation to **physical experiment**, with quantified uncertainty on *both* sides.

### 4.1 Validation hierarchy ("validation pyramid")
Build a tiered hierarchy (Oberkampf & Trucano; ASME V&V 10): **unit/separate-effects → subassembly/benchmark → subsystem → full system**. Lower tiers isolate single physics with controllable, well-instrumented experiments; the top tier is the integrated application (often impossible to test fully). Validation evidence flows *up* the pyramid; predictive confidence at the top is built from validated pieces below. Use a **PIRT (Phenomena Identification and Ranking Table)** to rank which phenomena matter most and steer V&V effort there.

### 4.2 Validation metrics — quantify the (dis)agreement
Do not "eyeball" overlaid curves. Use a **validation metric** — a quantitative measure of the difference between prediction and data that **accounts for uncertainty in both**:
- **Comparison error** `E = S − D` (simulation − experimental data).
- **Area metric / probability-box metric** (Oberkampf & Barone, Ferson): integrate the difference between the predicted and empirical **cumulative distribution functions** — gives a metric with the *units of the QoI* and a built-in penalty for distribution mismatch, valid when prediction and/or data are distributions.
- Report the metric **with its confidence interval**, across the validation domain, not at a single point.

### 4.3 ASME V&V 20 validation approach (CFD & heat transfer — the quantitative engine)
V&V 20 turns validation into experimental-uncertainty accounting. It defines the **validation comparison error** `E = S − D` and a **validation uncertainty** `u_val` that combines the independent uncertainty sources:

`u_val² = u_num² + u_input² + u_D²`

where `u_num` = numerical (solution-verification / GCI) uncertainty, `u_input` = uncertainty from input parameters/BCs propagated through the model, and `u_D` = experimental-data uncertainty. The **model-form error δ_model is then bounded**: `δ_model = E ± u_val`. Interpretation: if `|E| ≤ u_val`, model-form error is *within the noise* — you cannot distinguish it from uncertainty, i.e. the model is validated **at that accuracy level**. If `|E| > u_val`, you have detected a real model-form deficiency of magnitude ≈ `E`. **The validation result is an accuracy level you have earned, not a binary pass/fail and not "the model is correct."**

### 4.4 Model-form error & extrapolation
Validation only certifies the model *within the tested domain*. Using it outside that domain (prediction) requires either (a) extending the validation hierarchy, or (b) explicitly carrying the validated **model-form uncertainty** into the prediction and widening it for the extrapolation distance. State the validation domain boundaries; flag every prediction that lies outside them.

---

## 5. The ASME V&V standards family

| Standard | Domain | Core contribution |
|---|---|---|
| **ASME V&V 10** (2006 Guide; 2019/R2025 Standard) + **V&V 10.1** | Computational **Solid Mechanics** | Common vocabulary, conceptual VVUQ framework, validation hierarchy, roles of verification vs. validation; **10.1** is a fully worked illustrative example. |
| **ASME V&V 20** (2009) | Computational **Fluid Dynamics & Heat Transfer** | The quantitative validation methodology: `E = S − D`, `u_val² = u_num² + u_input² + u_D²`, GCI-based numerical uncertainty. The go-to *numbers* standard. |
| **ASME V&V 40** (2018) | Computational modeling for **Medical Devices** | **Risk-informed credibility** framework — scale V&V rigor to model risk. FDA-recognized. |
| **ASME V&V 50** | **Advanced / additive manufacturing** process modeling | Same VVUQ philosophy applied to coupled **thermal–mechanical–metallurgical process simulations** (e.g. additive, forming, heat-treat), where the "experiment" is a manufactured part and the QoIs are residual stress, distortion, microstructure. |
| (related) **V&V 60/70** energy/nuclear — same philosophy, other domains. |
| **ASME V&V 50** scope line: it extends the family from *product* analysis to *process* analysis — useful when the same FE thermal/structural stack is reused to predict as-built state rather than in-service response. |

### ASME V&V 40 — risk-informed credibility (generalizable far beyond medical)
The most transferable idea in the family: **"scale the rigor of V&V to the consequence of being wrong."** Mechanics:
- **Context of Use (COU):** a precise statement of *what specific decision the model informs and how its output is used.* Everything is judged relative to the COU.
- **Model Risk = Model Influence × Decision Consequence.**
  - *Model influence* = how much the decision relies on the model vs. other evidence (tests, prior art).
  - *Decision consequence* = severity of harm if the model-based decision is wrong.
- **Credibility goals** are set proportional to model risk: high risk → high required rigor in each **credibility factor**.
- **Credibility factors** are grouped under **Verification** (code verification; calculation/solution verification — discretization, numerical, solver), **Validation** (model-form assessment; validation experiments comparing computation to test; quantity & quality of comparison data), and **Applicability** (the relevance of the validation evidence to the COU — i.e. the gap between *where you validated* and *where you are using* the model).
- **Applicability / credibility gap analysis:** if you validated under conditions A but apply under conditions B, you must explicitly justify why the model remains credible across the gap.
- **Deliverable: a Credibility Assessment Report** stating COU, model risk, credibility goals, and the evidence each goal was met. The FDA's 2023 guidance *"Assessing the Credibility of Computational Modeling and Simulation in Medical Device Submissions"* is aligned with V&V 40.

> For a *general* CAE skill, adopt the V&V 40 mindset even outside medical devices: define the COU, rate model influence × consequence, and **scale V&V depth to risk** — a screening study and a safety-critical certification deserve very different rigor, and saying so explicitly is good governance.

---

## 5b. Model-credibility scales — operationalizing "scale rigor to risk"

V&V 40 says scale rigor to consequence; it stops at *principle*. Two standard, mutually consistent **credibility scales** let you turn that principle into a **factor-by-factor score** an analyst reports with the result — the operational bridge from "how trustworthy is this model?" to a defensible, auditable answer. The governing discipline in both is to expose each factor explicitly rather than collapse evidence into a vague adjective. **NASA CAS uses a weakest-factor/minimum rollup; Sandia PCMM reports the element scores and summary statistics rather than forcing a single governing score.** A brilliant validation hung on anonymous, un-traceable inputs is not a credible result; a single radar/score table that exposes the weak dimension is worth more than any one-word adjective.

### NASA-STD-7009 Credibility Assessment Scale (CAS) — 8 factors, levels 0–4
Rate each factor on **0–4** (low → high), set a **required level per factor from the decision's consequence**, and govern the result by the lowest factor:

| # | Factor | What it scores |
|---|---|---|
| 1 | **Verification** | Is the math solved right? (code + solution verification — §2, §3) |
| 2 | **Validation** | Is the physics right vs. independent experiment? (§4) |
| 3 | **Input Pedigree** | Traceability/quality of inputs — material data, loads, BCs, geometry source |
| 4 | **Results Uncertainty** | Are uncertainties characterized and propagated to error bars? (§6) |
| 5 | **Results Robustness** | Sensitivity — how the result responds to input/assumption perturbation |
| 6 | **Use History** | Track record of this model/approach on comparable problems |
| 7 | **M&S Management** | Process control, configuration management, documentation discipline |
| 8 | **People Qualifications** | Analyst competency and independent-checker qualification |

Report the **score table**, the **required vs. achieved level per factor**, and **call out the weakest factor explicitly** — it is the single most useful statement in a credibility report.

### Sandia PCMM (Predictive Capability Maturity Model) — 6 elements, levels 0–3
Same idea, more PDE/M&S-centric; rate each element on **maturity 0–3**, with target maturity set by application risk:

| Element | What it scores |
|---|---|
| **Representation & Geometric Fidelity** | How faithfully geometry/idealizations capture the real article |
| **Physics & Material Model Fidelity** | Adequacy of the governing physics and constitutive models |
| **Code Verification** | Solver correctness (MMS/benchmarks, order test — §2) |
| **Solution Verification** | This-run numerical error (mesh/time-step, GCI — §3) |
| **Model Validation** | Quantified comparison to experiment (§4) |
| **UQ & Sensitivity Analysis** | Uncertainty characterization, propagation, and sensitivity (§6) |

### How to use these in this skill
Map the **execution mode** to a **target credibility level** (set the per-factor targets from the COU's consequence):
- **SMOKE / DEBUG** ≈ low — pipeline or diagnostic run only; do **not** score it for credibility, and do not let it leak into a deliverable as if it were.
- **ENGINEERING** ≈ mid — verification done, at least sanity-level validation, uncertainty noted; most factors at a moderate, stated level.
- **SIGNOFF** ≈ high — every factor at its risk-required level, with the **run manifest carrying the CAS/PCMM scores** as part of provenance (§7).

Surfacing the **weakest factor / weakest element** is the deliverable's most useful single statement even when the method does not formally roll up by the minimum. These scores are exactly what a credibility report records, so they slot directly into the manifest/SIGNOFF machinery rather than living in a separate document.

---

## 6. Uncertainty Quantification (UQ)

### 6.1 Classify uncertainty first
- **Aleatory (irreducible, "variability"):** inherent randomness — material scatter, load variability, manufacturing tolerances, geometry variation. Modeled as **probability distributions**; reduced only by changing the system, not by more knowledge.
- **Epistemic (reducible, "lack of knowledge"):** unknown parameters, model-form uncertainty, sparse data, boundary-condition ignorance. Modeled as **intervals / probability boxes (p-boxes)** or via Bayesian priors; reducible with more data or better models.
- **Mixed aleatory–epistemic** problems (the realistic case) use nested/second-order sampling, p-boxes, or Dempster–Shafer evidence theory; conflating the two (treating an unknown-but-fixed parameter as random) understates true uncertainty.

### 6.2 Sensitivity analysis — find what matters before propagating
- **Local SA:** derivatives/one-at-a-time around a nominal point. Cheap, but misses interactions and is only valid locally.
- **Global SA (preferred):**
  - **Morris elementary effects ("screening"):** cheap, O(k) runs, ranks which of many inputs are influential / have nonlinear or interaction effects. Use first to **cull** the input set.
  - **Sobol' indices (variance-based):** apportion output variance to each input and to interactions (first-order Sᵢ and total-effect S_Tᵢ). Rigorous but sample-hungry — pair with a surrogate.

### 6.3 Propagation methods
- **Monte Carlo (MC):** gold-standard, distribution-free, embarrassingly parallel, but `O(1/√N)` convergence ⇒ many runs. Latin Hypercube Sampling improves coverage per sample.
- **Polynomial Chaos Expansion (PCE):** build a spectral surrogate in the random inputs; for smooth responses converges far faster than MC. **Sobol' indices come *analytically* from the PCE coefficients** — one expansion yields both the output PDF and global sensitivities. Sparse/adaptive PCE handles moderate dimensions; "arbitrary" PCE handles non-standard input distributions.
- **Surrogate / response-surface models** (Kriging/Gaussian-process, RBF, neural nets) replace the expensive FE model for propagation, optimization, and reliability — standard in **Ansys optiSLang / DesignXplorer** and **Siemens HEEDS**.
- **Bayesian calibration & model updating:** infer uncertain parameters *with posterior distributions* from data (Kennedy–O'Hagan framework adds a **model-discrepancy term** so calibration does not silently absorb model-form error into parameters — critical to keep calibration honest and distinct from validation).

### 6.4 Robust & reliability-based design
- **Reliability analysis:** estimate probability of failure `P_f = P(g(X) ≤ 0)` for a limit state g via FORM/SORM (fast, gradient-based) or sampling; report the **reliability index β**.
- **RBDO (Reliability-Based Design Optimization):** optimize subject to probabilistic constraints (`P_f ≤ target`).
- **Robust design / Design for Six Sigma (DFSS):** minimize output *variance* (insensitivity to scatter), often targeting ±6σ margin; trade nominal performance for robustness against tolerance/load scatter. optiSLang's "robustness & reliability" and HEEDS/SHERPA workflows implement these.

### 6.5 Bayesian model selection & parameter identifiability
Two questions sit *above* a single calibration (§6.3 Kennedy–O'Hagan) and decide whether its results mean anything: *which model does the data prefer?* and *can the data pin down the parameters at all?*

- **Bayesian model selection (evidence / Bayes factor).** When competing model forms are plausible (e.g. isotropic vs. orthotropic material, with vs. without a contact-resistance term, linear vs. nonlinear hardening), do **not** pick by best fit alone — a more flexible model always fits the calibration data at least as well (overfitting). Compare models by their **marginal likelihood (Bayesian evidence)** `Z = ∫ p(data│θ,M) p(θ│M) dθ`, the probability the model assigns to the observed data *averaged over its prior parameter space*. The **Bayes factor** `B₁₂ = Z₁/Z₂` is the evidence ratio between two models; it has a built-in **Occam penalty** — extra parameters cost prior volume, so a needlessly complex model is penalized unless the data demand it. Rough reading (Jeffreys): |ln B| < 1 inconclusive, 1–3 positive, >3 strong, >5 decisive. Practical estimators: nested sampling, thermodynamic integration, or information criteria as cheap proxies (**WAIC / DIC** for Bayesian fits; **AIC / BIC** for point estimates — BIC approximates ln Z). Use model selection to choose the *model form* before crediting a calibration; it complements, not replaces, held-out **validation** (§4) — evidence ranks models on *this* data, validation tests the winner on *independent* data.

- **Parameter identifiability (can the data even constrain θ?).** A parameter is **non-identifiable** when the data cannot distinguish it from others — different θ give indistinguishable model output. Two flavors: **structural** non-identifiability (a model symmetry/aliasing makes a parameter combination unconstrained *regardless of data quantity* — e.g. only a product or ratio of two parameters appears in the response) and **practical** non-identifiability (the parameter *is* in principle constrained, but the available data are too sparse/noisy to pin it). Symptoms and diagnostics:
  - A **flat or ridged likelihood/posterior** along a parameter (or parameter combination); posterior ≈ prior for that parameter means the data added nothing.
  - **Strong posterior correlations** between parameters (a near-degenerate ridge) — they trade off, only their combination is identified.
  - **Rank-deficient or ill-conditioned Fisher Information Matrix (FIM)** `F = Jᵀ Σ⁻¹ J` (J = sensitivity of outputs to parameters): a (near-)zero eigenvalue marks an unconstrained direction; the Cramér–Rao bound `cov(θ̂) ⪰ F⁻¹` gives the best achievable parameter uncertainty *before* you run the inversion. **Profile likelihoods** confirm which individual parameters are bounded.
  - **Practical fixes:** fix/strongly-prior the unidentifiable parameter to an independent value; reparameterize to the identified combination; or — best — design the experiment/measurement set to break the degeneracy (more/different sensors, additional load cases, a richer transient). This is exactly **optimal experimental design**: maximize a scalar of the FIM (D-optimal = max det F; A-optimal = min trace F⁻¹; E-optimal = max min-eigenvalue) so the calibration is well-posed *before* spending the test.
  - **Discipline:** a calibrated parameter value reported without an identifiability check is suspect — a tidy point estimate can be an arbitrary point on a flat ridge. Report which parameters the data actually constrained, and treat the rest as fixed assumptions, not results.

---

## 7. Reporting, Traceability & Simulation Governance

NAFEMS frames the management wrapper around all of the above:
- **R0033 / "How To Manage Finite Element Analysis"** — the management-and-quality view: FEA is a **design-process tool**, planning, competency, checking, and documentation matter as much as the solve. NAFEMS quality publications (incl. the Quality System Supplement to ISO 9001 for FEA) require documented procedures, analyst competency, and independent checking.
- **Simulation Governance** (Szabó & Babuška; promoted by NAFEMS/ESRD): the exercise of command and control over simulation — verified solver, verified target extraction, hierarchical models, documented error estimates. *Rule observed in benchmark practice:* **confirm the target QoI extraction has converged before reporting or comparing anything.**
- **Model provenance & traceability:** record solver name/version, element types & formulation, mesh metrics, material data and its source, BC/load assumptions and idealizations, contact/connection settings, solver/convergence settings, the mesh-convergence (GCI) evidence, and the validation evidence + domain. A result without this metadata is not auditable and not reusable.
- **Scale rigor to consequence** (the V&V 40 principle, generalized): a concept screening study needs a documented sanity check; a safety-critical or certification analysis needs full code verification reference, GCI bands, validation against independent test, and a credibility report.

> Single-mesh error estimation & adaptivity (recovery-based ZZ/SPR a-posteriori estimators, effectivity index, h-/p-/hp-refinement) → `references/meshing-convergence.md`.

### 7.1 From per-run provenance to lifecycle governance (SPDM / QSS)
The run manifest + runs-index above govern *one* analysis; an organization must govern *all* of them. The per-run record is the **unit**; the items below are the **library** that holds, versions, and connects those units.

- **Quality system — NAFEMS QSS / ESQMS.** The **Quality System Supplement (QSS / Engineering Simulation Quality Management System, ESQMS)** specializes **ISO 9001** for engineering simulation: documented procedures, **recorded analyst competency** (cf. NAFEMS PSE — Professional Simulation Engineer), and **independent checking of every credited result**. It is the named, citable answer to "what does ISO 9001 look like for FEA/CFD?"
- **SPDM (Simulation Process & Data Management).** The lifecycle/data layer:
  - **Version-control** models, inputs, and results — not just the geometry, but mesh, material cards, BC/load sets, and solver version.
  - Maintain a **digital-thread / traceability link from each result to the engineering decision or requirement it informed** — a result with no decision it supports is orphaned; a decision with no traceable result behind it is unverified.
  - Keep an **audit trail** for reproducibility and **reuse**; apply **configuration management** to model versions. A result is only auditable if you can recover the exact model, mesh, materials, and solver version that produced it.
- **Discipline for an agent:** never leave two "final" results without a `superseded_by` pointer (already required for the per-run manifest). Additionally, tag each manifest with the **model version / configuration ID** and the **decision or requirement it supports**, so the run is reusable and auditable rather than orphaned — and carry the §5b credibility scores (CAS/PCMM) in the manifest so the credibility assessment travels with the data, not in a separate document.

### 7.2 Structural margins & FE-model verification (apply the governing standard's numbers — don't invent margins)
For load-bearing and especially spacecraft/aerospace structures, the credible result is not "max stress < allowable" but "max stress < allowable **after** the mandated factors, on a model that passed the standard's FE-verification checks." *(Thermal-prediction margins and thermal-model test-correlation are covered separately — see `references/thermal-and-coupling.md`.)*

- **Keep the factors separate and traceable (ECSS-E-ST-32-10C; NASA-STD-5001/-5002 are analogous).** Design verification multiplies limit/applied loads by, as distinct multipliers:
  - a **Factor of Safety (FoS)** / **Design Factor** — covers manufacturing, material-property, and load uncertainties; and
  - a **Model Uncertainty Factor (MUF / "model factor")** — covers the *analysis method's* own uncertainty. Analysis-only (untested) load paths carry a **higher** MUF; **test-correlated** models earn a **lower** one.
  Do not fold these into a single fudge number — keep FoS, design factor, and MUF as separate, named, traceable multipliers so a reviewer can see what each one is buying.
- **FE-model verification checklist (ECSS-E-ST-32-03C, *Structural finite element models* — generalizable).** These are the **space-standard names for the sanity gates** a credible FE deliverable already runs; cite them when working to ECSS:
  - **Free-free (unconstrained) run → the dimensionality-correct rigid-body-mode count at ≈ 0 Hz** (6 for a full 3D model; fewer for 2D/axisymmetric/shell idealizations) **and no spurious mechanisms** — checks connectivity and constraint integrity.
  - **Total mass & centre-of-gravity** vs. the mass budget — catches density/units/missing-mass errors.
  - **Strain-energy / "epsilon" error norms** — flags under-integrated or distorted regions and poorly converged load paths.
  - **Unconnected-node / orphan checks** — no nodes silently disconnected from the load path.
  - **Single-point-constraint (SPC) reaction-force check ≈ 0** where no reaction is expected — catches over-constraint and grounding errors.
  - **Thermoelastic check:** a uniform ΔT on a free, single-material body must produce **≈ 0 stress** (it should expand freely) — a non-zero result exposes spurious constraint or CTE/connection errors.

**Minimum credible-report checklist for a CAE deliverable:**
1. Objective, QoI(s), and **Context of Use** (what decision this informs).
2. Idealizations & assumptions (geometry defeaturing, element choice, connections, BCs, materials + sources).
3. **Code verification** basis (solver verified / NAFEMS-benchmark / MMS evidence).
4. **Solution verification:** mesh (and time-step) convergence study with **GCI / % error band** on each reported QoI; asymptotic-range confirmation.
5. Iterative & round-off error controlled (residual levels).
6. **Validation** (if claimed): independent experimental comparison, `E` vs `u_val`, validation domain — and explicit note if results are used outside it (prediction/extrapolation).
7. **UQ:** uncertainty sources classified (aleatory/epistemic), sensitivities, propagated **error bars** on the QoI.
8. Provenance metadata (versions, mesh, materials, settings) and independent review sign-off.

---

## 8. Top mistakes (and the fix)

1. **Single-mesh trust.** Reporting stress/flux from one mesh with no convergence study. *Fix:* ≥3 systematically refined grids + GCI; report the error band. Without it you have **no idea** of your numerical error.
2. **Calibrate-then-claim-validation.** Tuning parameters to data and reporting the match as "validated." *Fix:* validate against **independent** data; keep calibration / validation / prediction strictly separate; carry model-form uncertainty forward (Kennedy–O'Hagan discrepancy term).
3. **Trusting peak singular stress.** Reading the max nodal stress at a re-entrant corner, point load, point constraint, or crack tip — where the exact stress is **infinite** (σ → ∞). The peak *rises without bound* under refinement and **never converges**, unlike a real stress concentration (fillet/hole) which converges to a finite value. *Fix:* distinguish singularity from concentration via the convergence behavior; invoke **St. Venant's principle** (local disturbance, stresses correct away from it) to ignore irrelevant singularities; for relevant ones add a real fillet radius, use stress **linearization** or **averaged/extrapolated** stresses, or switch to fracture-mechanics (K, J) treatment. *Never quote a raw singular peak as a design stress.*
4. **No error bounds / point-value reporting.** Headline numbers with no numerical, parametric, or experimental uncertainty. *Fix:* every reported QoI carries a band (GCI for numerical, UQ propagation for parametric/aleatory).
5. **Verifying with one benchmark instead of an order test.** A single benchmark match can pass by cancellation. *Fix:* MMS/benchmark **order-of-accuracy test under refinement.**
6. **Validating the wrong quantity / wrong tier.** Comparing an integral while reporting a local QoI, or "validating" only at the full-system level. *Fix:* validation hierarchy + PIRT; validate the *specific* QoI you will report.
7. **Skipping verification before validation.** Comparing to experiment with unquantified numerical error — model-form and discretization error become indistinguishable. *Fix:* code → solution verification first, then validation; in V&V 20 terms, `u_num` is an explicit term in `u_val`.
8. **Extrapolating beyond the validation domain silently.** Using a model far outside tested conditions and presenting it as validated. *Fix:* state the validation domain; flag predictions outside it; widen uncertainty for extrapolation (the **applicability gap**).
9. **Loose iterative/nonlinear convergence under a mesh study.** Residuals not low enough, so "mesh effects" are really solver noise. *Fix:* iterative error ≪ discretization error before refining.
10. **Confusing aleatory and epistemic uncertainty.** Treating unknown-but-fixed parameters as random (or vice-versa), mis-stating total uncertainty. *Fix:* classify first; use intervals/p-boxes for epistemic, distributions for aleatory, nested sampling for mixed.
11. **Effort not scaled to risk.** Same (or no) rigor regardless of consequence. *Fix:* V&V 40 mindset — COU, model risk = influence × consequence, credibility goals proportional to risk.
12. **No provenance / un-auditable model.** Results without solver version, mesh metrics, material sources, BC assumptions. *Fix:* the §7 traceability record + independent checking (NAFEMS quality / Simulation Governance).

---

## SOURCES

ASME standards & overviews
- ASME, *V&V 10 — Standard for Verification and Validation in Computational Solid Mechanics* (2006 Guide; 2019 / R2025). https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-solid-mechanics ; https://webstore.ansi.org/standards/asme/asme102019
- ASME, *V&V 10.1 — An Illustration of the Concepts of V&V in Computational Solid Mechanics* (2012, R2022). https://webstore.ansi.org/standards/asme/asme102012r2022
- "An Overview of the ASME V&V-10 Guide" (NCSU repository). https://repository.lib.ncsu.edu/bitstreams/a45e16f4-5cce-44f4-b2bd-fa760019c8aa/download
- ASME, *V&V 20 — Standard for V&V in Computational Fluid Dynamics and Heat Transfer* (2009). https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-fluid-dynamics-and-heat-transfer
- "Overview of ASME V&V 20-2009" (Coleman/Stern, OSTI). https://www.osti.gov/servlets/purl/1368927
- "On the Interpretation and Scope of the V&V 20 Standard" (ASME VVS2020). https://asmedigitalcollection.asme.org/VVS/proceedings/VVS2020/83594/V001T02A001/1085872
- ASME, *V&V 40 — Assessing Credibility of Computational Modeling through V&V: Application to Medical Devices* (2018). https://www.asme.org/codes-standards/find-codes-standards/assessing-credibility-of-computational-modeling-through-verification-and-validation-application-to-medical-devices
- ASME V&V 40 model/simulation standard summary (NIH IMAG). https://www.imagwiki.nibib.nih.gov/sites/default/files/asme_vv_40_model_simulation_standard.pdf
- "Credibility in Computational Modeling for Medical Devices: A Closer Look at ASME V&V40" (BIOMEDER). https://company.biomeder.com/en/credibility-in-computational-modeling-for-medical-devices-asme-vv40/
- FDA, *Assessing the Credibility of Computational Modeling and Simulation in Medical Device Submissions* (2023). https://www.fda.gov/media/154985/download
- Credibility application (Bologna BCT, ScienceDirect). https://www.sciencedirect.com/science/article/pii/S0169260723003930 ; Hemolysis/blood-pump risk-based application (PMC). https://pmc.ncbi.nlm.nih.gov/articles/PMC6493688/
- ASME V&V 50 — V&V in computational modeling for advanced manufacturing (ASME V&V committee family). https://www.asme.org/codes-standards/publications-information/verification-validation-uncertainty

Model-credibility scales (NASA CAS / Sandia PCMM)
- NASA-STD-7009B, *Standard for Models and Simulations* (2024) — 8-factor Credibility Assessment Scale. https://standards.nasa.gov/standard/NASA/NASA-STD-7009 ; PDF https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf ; 8-factor CAS deployment paper https://ntrs.nasa.gov/citations/20200003344
- Pilch, Oberkampf & Trucano, *Predictive Capability Maturity Model for Computational Modeling and Simulation*, SAND2007-5948 (6 elements, levels 0–3). https://www.osti.gov/biblio/976951 ; PCMM credibility-assessment paper https://www.osti.gov/servlets/purl/1480395

Structural margins & FE-model verification (ECSS)
- ECSS-E-ST-32-10C Rev.2, *Structural factors of safety for spaceflight hardware* (2019) — FoS / design factor / model uncertainty. https://ecss.nl/standard/ecss-e-st-32-10c-rev-2-structural-factors-of-safety-for-spaceflight-hardware-15-may-2019/
- ECSS-E-ST-32-03C, *Structural finite element models* (FE-model verification checklist). https://standards.globalspec.com/standards/detail?docId=1271946
- NASA-STD-5001 / -5002 (analogous structural design & verification factors). https://standards.nasa.gov/

Error taxonomy
- AIAA G-077-1998, *Guide for the Verification and Validation of CFD Simulations* — acknowledged vs. unacknowledged errors. https://www.nafems.org/downloads/edocs/aiaa_guide_review.pdf ; https://arc.aiaa.org/doi/book/10.2514/4.472855

Bayesian model selection & parameter identifiability
- Jeffreys / Kass & Raftery, *Bayes Factors* (J. Am. Stat. Assoc. 1995) — evidence ratio interpretation scale. https://www.tandfonline.com/doi/abs/10.1080/01621459.1995.10476572
- MacKay, *Information Theory, Inference, and Learning Algorithms* (Bayesian evidence / Occam factor). https://www.inference.org.uk/mackay/itila/
- Raue et al., *Structural and practical identifiability via the profile likelihood* (Bioinformatics 2009). https://doi.org/10.1093/bioinformatics/btp358
- Optimal experimental design / Fisher-information criteria (D/A/E-optimality) — Atkinson, Donev & Tobias, *Optimum Experimental Designs, with SAS* (Oxford, 2007); Pukelsheim, *Optimal Design of Experiments* (SIAM Classics, 2006). Orientation: Wikipedia — Optimal experimental design, https://en.wikipedia.org/wiki/Optimal_experimental_design

Roache / Oberkampf / Roy / Trucano (foundational V&V literature)
- P. J. Roache, *Fundamentals of Verification and Validation* (2009 chapter PDF). https://fenix.tecnico.ulisboa.pt/downloadFile/2815368242400390/FVV_Roache_2009.pdf
- W. L. Oberkampf, *Concepts and Practice of Verification, Validation, and Uncertainty Quantification.* https://woodruffscientific.com/wiki/lib/exe/fetch.php?media=oberkampf.pdf
- W. L. Oberkampf, *Verification, Validation, and Predictive Capability — What's What?* (webinar). https://geodynamics.org/resources/301/download/Oberkampf_Webinar_CIG-2016.pdf
- Oberkampf & Trucano, *Verification, Validation, and Predictive Capability in Computational Engineering and Physics* (Sandia). https://www.sandia.gov/research/publications/details/verification-validation-and-predictive-capability-in-computational-engineer-2004-01-01/ ; https://www.osti.gov/biblio/918370
- Roy et al., *Review of Code and Solution Verification Procedures for Computational Simulation* (J. Comp. Phys. 2004). https://www.sciencedirect.com/science/article/abs/pii/S0021999104004619
- Knupp/Salari & Roy, *Code Verification by the Method of Manufactured Solutions* (ASME J. Fluids Eng.). https://asmedigitalcollection.asme.org/fluidsengineering/article/124/1/4/462791/
- MMS code verification of elastostatic solid mechanics in a commercial FE solver (ScienceDirect). https://www.sciencedirect.com/science/article/abs/pii/S0045794919301968
- Model validation & predictive capability — thermal challenge problem (ScienceDirect). https://www.sciencedirect.com/science/article/abs/pii/S0045782507005105

GCI / mesh convergence
- "Establishing Grid Convergence" — GCI procedure, F_s=1.25 (3 grids), Richardson extrapolation, asymptotic range (curiosityFluids). https://curiosityfluids.com/2016/09/09/establishing-grid-convergence/
- Celik et al. GCI calculator / standard (Volupe). https://volupe.com/support/grid-convergence-index-calculator/
- "Convergence in FEA Analysis: How to Perform a Reliable FEA Convergence Study." https://ideametricsglobalengineering.com/convergence-in-fea-analysis-validation-guide/

NAFEMS — benchmarks & quality management
- NAFEMS Publications guide. https://www.nafems.org/publications/pubguide/list/
- *How To Manage Finite Element Analysis* (R0033 lineage). https://www.nafems.org/publications/resource_center/ht31/
- *The Standard NAFEMS Benchmarks* (resource center). https://www.nafems.org/publications/resource_center/p18/
- ESRD StressCheck results for the Standard NAFEMS Benchmarks: Linear Elastic Tests (LE1, etc.) + Simulation Governance. https://www.esrd.com/stresscheck-results-standard-nafems-benchmarks-linear-elastic-tests-available/
- NAFEMS LE11 thermo-mechanical validation case (OnScale). https://onscale.com/help/solve/validation/validation-case-thermomechanical-nafems/

Stress singularities & St. Venant
- "Stress singularities, stress concentrations and mesh convergence" (Acín). http://www.acin.net/2015/06/02/stress-singularities-stress-concentrations-and-mesh-convergence/
- "Stress singularity — an honest discussion" (Enterfea). https://enterfea.com/stress-singularity-an-honest-discussion/
- "Dealing with Stress Concentration and Singularities" (Digital Engineering 24/7). https://www.digitalengineering247.com/article/dealing-stress-concentrations-singularities

Uncertainty quantification & sensitivity
- Mixed aleatory-epistemic uncertainty in structures — Jiang, Zheng & Han, "Probability-interval hybrid uncertainty analysis … a review," *Struct. Multidisc. Optim.* (2017): https://doi.org/10.1007/s00158-017-1864-4
- "Global sensitivity analysis in the context of imprecise probabilities (p-boxes) using sparse PCE" (ETH RSUQ). https://ethz.ch/content/dam/ethz/special-interest/baug/ibk/risk-safety-and-uncertainty-dam/publications/reports/RSUQ-2017-007.pdf
- "Arbitrary polynomial chaos expansion for UQ and global sensitivity analysis in structural dynamics" (ScienceDirect). https://www.sciencedirect.com/science/article/abs/pii/S0888327020301187
- Ansys optiSLang robustness/reliability/calibration workflow overview (EDRMedeso). https://edrmedeso.com/article/optislang-explained-from-one-off-simulations-to-automated-data-driven-product-optimisation/
