# Solver numerics — practitioner-grade best-practices brief

Scope: the numerical machinery beneath every FE solve — **linear equation solvers, eigensolvers, nonlinear solution, time integration, parallelization, and residual/diagnostic decoding.** Cross-verified against Ansys theory/command docs, the Abaqus Analysis User's Manual, LS-DYNA/DynaSupport, Simcenter/MSC Nastran guides, NAFEMS, and numerical-analysis references. Numbers given are vendor defaults / industry rules of thumb; always confirm against your installed version. Citations are bracketed `[n]` → SOURCES at end.

The governing rule for the whole topic: **defaults are tuned for the average model, not yours.** Pick the solver to match the matrix (conditioning, size, symmetry, definiteness), then read the residual history rather than trusting the exit code.

---

## 1. Linear equation solvers (the inner `Kx = f`)

Every static, every Newton iteration, every implicit time step, and every eigen-shift ultimately solves a sparse linear system. Two families:

### Direct (sparse / multifrontal / frontal)

Factorizes `K = LDLᵀ` (Cholesky-type for symmetric positive-definite) by Gaussian elimination, reordered to limit fill-in. The **frontal** method (Irons, 1970) assembles and eliminates element-by-element so the full matrix never resides in memory at once; the **multifrontal** method (Duff & Reid) generalizes this to multiple independent fronts driven by an elimination tree, which exposes parallelism and is the basis of modern sparse direct solvers (Ansys SPARSE, Nastran's default decomposition). [1][2][8]

- **Robust** — gives an answer regardless of conditioning (within round-off); handles indefinite matrices (buckling, mixed u–P, contact), negative pivots (instability detection), and multiple/repeated right-hand sides cheaply (factor once, back-substitute many — ideal for modal/load-stepping). [3][8]
- **Cost** — factorization is the bottleneck: memory and flops scale super-linearly with bandwidth/front size. For 3-D solids RAM and time grow far faster than the DOF count. Direct typically needs **~5–10× the RAM** of an iterative solve on the same model. [3]
- **In-core vs out-of-core** — keep the factor in RAM. An **out-of-core** direct solve spills the factor to disk and is commonly **~10× slower** (disk-bandwidth bound). Size RAM *before* launching: if the factor won't fit, switch to iterative or DMP-partition rather than thrash. [3]

### Iterative (PCG / JCG / ICCG)

Krylov-subspace methods (Preconditioned Conjugate Gradient and its symmetric variants) that never form the factor — only sparse mat-vec products, so memory is roughly **O(N)** and far lower than direct. Convergence is governed by the **condition number κ(K)**: iterations to a fixed tolerance scale like `√κ` for CG, so preconditioning (the "P") is essential. [4][9][10]

- **Best on** large, **well-conditioned**, bulky **3-D solid** models (chunky parts, soil, large castings) where direct RAM is prohibitive. [3][4]
- **Fails / stalls on ill-conditioning** — thin shells/beams (huge bending-vs-membrane stiffness ratio), near-rigid contact/bonded MPC, near-incompressible materials, vastly different element sizes or material moduli, and near-singular (under-constrained) systems. The cure is **a better/stronger preconditioner or switching to direct**, NOT loosening the convergence tolerance (that hides, not fixes, the problem). [3][4][9]
- **Preconditioners** transform the system to a clustered spectrum so CG converges in far fewer iterations: Jacobi/diagonal (cheap, weak), incomplete Cholesky (ICCG, stronger), and multilevel/multigrid (strongest, near mesh-independent). A perfect preconditioner `P⁻¹≈K⁻¹` converges in one step; the trade is setup/apply cost vs iteration count. [10]
- **Level-of-difficulty knob** — Ansys PCG `Lev_Diff` 1–5: higher levels use stronger (more memory-hungry) preconditioning; `Lev_Diff 5` approaches direct-solver robustness at a memory cost between PCG and SPARSE. Raise it when PCG stalls before reverting to direct. [3]

### Conditioning — the unifying concept

`κ(K) = ‖K‖·‖K⁻¹‖` (ratio of largest/smallest singular value for SPD). Practical impact and the rule every analyst should know:

> **You lose ≈ log₁₀(κ) significant decimal digits to round-off.** IEEE double has ~16 digits; κ=10¹⁰ ⇒ only ~6 trustworthy digits; κ→10¹⁵–10¹⁶ ⇒ results are numerical noise and the solver reports near-singularity. [11]

High κ in FEM comes from: thin/slender features (shells, beams), enormous stiffness contrasts (rigid links bonded to soft parts, penalty/contact `FKN` too high), under-constraint (rigid-body DOF), and degenerate/sliver elements. Fix the *model* (constraints, connection stiffness, mesh quality) — a re-solve on a different solver only masks it.

### Selection cheat-sheet

| Situation | Solver |
|---|---|
| Shells/beams, contact, nonlinear, buckling, modal block, multiple RHS, indefinite | **Direct sparse** (in-core) |
| Large well-conditioned 3-D solid, RAM-limited | **PCG** (raise `Lev_Diff` if it stalls) |
| Thermal (SPD, well-conditioned) steady/transient | **JCG / ICCG** (cheap) |
| Iterative won't converge | Strengthen preconditioner → else **switch to direct** |

**Top mistakes:** running a huge direct solve out-of-core by accident (silent 10× slowdown — check the in-core/out-of-core message); using iterative on a shell/contact model and blaming "FEA inaccuracy" for non-convergence; loosening iterative tolerance to force convergence on an ill-conditioned (often under-constrained) system. [3][4][11]

---

## 2. Eigensolvers (modal, buckling, dynamics)

Solve the generalized eigenproblem `K φ = λ M φ` (modal: λ=ω²) or `K φ = λ K_g φ` (linear buckling: λ=load factor). Method choice is driven by **how many modes**, **model size**, and **symmetry/damping**.

### Methods and when to use each

| Method (Ansys `MODOPT` / Nastran) | Use when | Notes |
|---|---|---|
| **Block Lanczos** (`LANB`, Nastran `READ`/Lanczos default) | **Default** for natural frequencies & mode shapes; a few–few-hundred modes | Block-shifted Lanczos (Grimes et al.) with automated **shift strategy**; uses the **sparse direct** factorization internally → robust, handles rigid-body modes. [5][6][12] |
| **PCG Lanczos** (`LANPCG`) | Large models, modes concentrated in low range, RAM-limited | Lanczos driven by the **PCG iterative** solver instead of direct; trades memory for setup. Not for buckling. [5][12] |
| **Subspace** (`SUBSP`) | Moderate mode count on large models, distributed (DMP) runs | Subspace iteration with auto-shift; good DMP scaling. [5][12] |
| **Supernode** (`SNODE`) | **Many modes (>~200, up to 10 000+)** in one shot | **Approximate** node-grouping + reduced Lanczos; **faster than Block/PCG Lanczos when >~200 modes**. Accuracy controlled by `SNOPTION`; pre-computes supernode modes to `FREQE×RangeFact` (default 2.0). [5][6] |
| **AMLS / ACMS** (Nastran ACMS, Abaqus AMS, CDH/AMLS) | **NVH-scale**: thousands of modes on million-DOF auto-body/powertrain models | Automated multi-level substructuring: splits the model into ~10 000 substructures over ~20 levels, solves on substructure eigenvectors. **Approximate**, **~10–25× faster than Lanczos** for large mode counts; the NVH industry standard. [7][13] |
| **Damped** (`DAMP`) / **QR Damped** (`QRDAMP`) | Systems with a damping matrix `C`; complex eigenvalues | `DAMP` = full Lanczos+QR on `[K,C,M]`; `QRDAMP` reduces to a modal subspace first (faster, assumes modal damping adequate). Gives whirl/decay (complex λ). [5][12] |
| **Unsymmetric** (`UNSYM`) | Gyroscopic/rotordynamics, follower loads, contact/friction stiffness asymmetry | Lanczos+QR on unsymmetric `[K*,M*]`. Required when `K` or `M` is non-symmetric. [5][12] |

### Quality gates (do these every modal run)

- **Sturm sequence check** — counts negative pivots of `(K − σM)` over the captured range; the count must equal the number of converged modes, else modes were **missed**. In Block Lanczos it is **off by default** (the internal shift logic is usually reliable) but **turn it on whenever completeness matters** (response spectrum, mode superposition, fatigue). It reports the number of missing eigenvalues. [6]
- **Rigid-body modes** — a free-free structure must show **6 near-zero modes** (3 translation + 3 rotation, ω≈0). More than 6 zeros ⇒ a mechanism / missing connection / under-constraint; fewer ⇒ over-constraint. [user-domain canon, consistent with 1]
- **Effective mass / mass participation** — request enough modes that the **cumulative effective mass reaches ≥ 80–90 % per excited direction** (≥0.9 is the standard acceptance for response-spectrum/base-excitation work). Check the participation-factor table (Nastran `PARAM,MEFFMASS`); residual/missing mass beyond the cutoff needs a residual-vector / missing-mass correction. [14]
- **Frequency shift** — use a shift (`FREQB`/`SHIFT`) to capture modes near a target frequency, step past rigid-body singularities (shift K so `K−σM` is non-singular), or zoom a band. Essential for pre-stressed and free-free runs. [5][6]
- **Prestressed (stress-stiffened) modal** — run the static load first and carry stress stiffening (`PSTRES`/`STATSUB`); tensioned cables, spinning disks, and thin pressurized shells change frequency markedly. [5]

**Top mistakes:** too few modes ⇒ <90 % effective mass ⇒ unconservative dynamic response; using Supernode/AMLS (approximate) when exact low-mode accuracy is required; ignoring a Sturm warning; forgetting the 6-rigid-body sanity check on free-free models; using a symmetric solver on a rotordynamic (unsymmetric/gyroscopic) model and missing whirl split.

---

## 3. Nonlinear solution methods (`R(u) = F_ext − F_int(u) = 0`)

### Newton family

- **Full Newton-Raphson** (default) — re-forms and re-factorizes the tangent stiffness `Kᵀ = ∂F_int/∂u` **every iteration**. Near the solution it converges **quadratically** (the error roughly squares each iteration — number of correct digits doubles), which is why a healthy NR residual drops 1–2+ orders per iteration. Cost: a factorization per iteration. [15][16]
- **Modified Newton** — holds `Kᵀ` fixed for several iterations (re-form occasionally). Cheaper iterations, only **linear** convergence (more iterations). Good when the tangent is expensive or noisy. [15][16]
- **Initial-stiffness** — uses the elastic `K₀` throughout: very cheap and robust per iteration, slowest convergence; a fallback for badly-behaved tangents. [15]
- **Quasi-Newton (BFGS-type)** — builds a secant approximation to `Kᵀ` from successive residuals; Abaqus enables **line search by default with quasi-Newton**. Good middle ground for smooth large problems. [16]

### Path-following for instabilities

- **Arc-length (Riks / Crisfield / modified Riks)** — **mandatory for snap-through (limit point in load control) and snap-back (limit point in displacement control)**, i.e. softening/post-buckling where the load–displacement curve has negative stiffness and the structure must shed strain energy. Treats the **load magnitude as an extra unknown (load proportionality factor λ)** and constrains the step along an arc in (u, λ) space, so it traces past limit points where pure load- or displacement-control diverge. Abaqus *RIKS uses 1 % strain-increment extrapolation and solves loads + displacements simultaneously; you set the initial arc increment, not the load. MAPDL `ARCLEN,ON`; Nastran SOL 106/400 arc-length. **Caveat:** classic Riks fails on **post-buckling with loss of contact** — use dynamics or viscous stabilization there instead. [17][18]
- **Energy stabilization (`STABILIZE` / `STABILIZE,ENERGY`)** — adds artificial volume-proportional viscous damping to dissipate the released energy and walk through *local* instabilities (chatter, local buckling) without arc-length. Abaqus automatic stabilization defaults to a **dissipated-energy fraction ≈ 2.0×10⁻⁴**; MAPDL `STABILIZE` uses a dissipation/energy ratio (~1e-4 typical). **Always verify the stabilization/damping energy is ≪ strain energy** (a few % at most) or it corrupts the result. [17][18]
- **Load vs displacement control** — displacement (or arc-length) control can pass simple limit points that load control cannot. Prefer displacement/arc-length when a reaction force decreases while displacement increases. [17]

### Stepping, ramping, and auto-incrementation

- **Auto time stepping + bisection** — let the solver size substeps (Ansys `AUTOTS,ON`; Abaqus automatic incrementation). On non-convergence it **cuts back** the increment and retries. Abaqus default cut-back factors: **0.25 after divergence, 0.5 for too-slow convergence, 0.75 after too many equilibrium iterations**, with **max 5 cut-backs per increment** and **16 equilibrium iterations** before cutting back. [19]
- **Ramp vs step loads** — ramp loads (`KBC,0`; Abaqus default for quasi-static) for smooth nonlinearity so the increment scales with the time increment (more robust); step (`KBC,1`) only when the load is genuinely instantaneous.

### Convergence criteria — read the residual, never the exit code

Multiple criteria, **all active ones must pass**:

- **Abaqus/Standard defaults:** residual force ratio **Rⁿα = 0.005 (0.5 %)** of the time-averaged force; displacement-correction ratio **Cⁿα = 0.01 (1 %)** of the largest incremental displacement (residual moment 0.02, rotation 0.02). Optional half-increment residual for dynamics. [19]
- **MAPDL defaults:** force/moment tolerance **0.5 %**, displacement **5 %** (`CNVTOL`), optional energy. Force/moment is primary; displacement secondary. [user-domain canon]
- **Nastran SOL 106/400 `NLPARM`:** load `EPSP`≈1e-2, work `EPSW`≈1e-2, displacement `EPSU`≈1e-3 (defaults context-dependent).
- **Healthy** residual history: drops 1–2 orders of magnitude over ≤~10–15 iterations (quadratic tail with full Newton). **Sick:** residual flat/oscillating/rising; repeated bisection to vanishing steps; hitting `NEQIT`/16-iteration limit every increment; "severe discontinuities" looping (contact chatter). Diagnose the physics (lost contact, material instability, under-constraint) — don't just loosen tolerances or raise iteration limits. [16][19]

**Top mistakes:** using load control through a limit point (diverges) instead of arc-length; over-stabilizing (`STABILIZE` energy comparable to strain energy → fake stiffness, wrong answer); raising iteration count / loosening tolerance to "converge" a physically unstable model; ramping when the response is genuinely dynamic (or vice-versa); declaring success on the exit code while the result file is from the last *converged* increment, not the target load.

---

## 4. Time integration (transient dynamics & transient thermal)

### Implicit (unconditionally stable) vs explicit (conditionally stable)

| Scheme | Type | Stability | Use |
|---|---|---|---|
| **Newmark-β** (β=¼, γ=½ "average acceleration"/trapezoidal) | implicit | **unconditional**, 2nd-order, no algorithmic damping | structural dynamics default [20] |
| **HHT-α (α-method)** / **generalized-α** | implicit | unconditional, **tunable numerical damping** | damp spurious high-frequency content without killing the resolved response [18][21] |
| **Central difference** | explicit | **conditional: Δt ≤ Δt_crit (CFL)** | short, high-rate events: impact, crash, blast, drop, explosive forming [22][23] |
| **Backward-Euler** | implicit | unconditional | transient **thermal** default (monotone, no overshoot) |
| **Crank-Nicolson (θ=½)** | implicit | unconditional but can **oscillate** on coarse Δt | more accurate thermal; watch ringing at sharp fronts |

**Newmark stability:** unconditional iff `2β ≥ γ ≥ ½`; `γ=½` gives no algorithmic damping (2nd-order accurate); `γ>½` adds damping but drops to 1st-order accuracy. [20] **HHT-α** (Abaqus `*DYNAMIC, ALPHA`): `α=0` recovers the trapezoidal rule (Newmark β=¼,γ=½, energy-preserving); **negative α adds high-frequency numerical damping**; `α=−1/3` is **maximum damping** (~6 % damping ratio when Δt ≈ 40 % of the mode period); typical practical range **α ≈ −0.05 … −0.1**. [18][21]

**Implicit accuracy rule:** resolve the highest mode of interest with **≥ ~10–20 time steps per period**; coarser misses the dynamics, and even unconditional stability ≠ accuracy. Add a touch of HHT damping to kill numerical ringing from contact/sudden loads. [18]

#### HHT-α / Newmark numerical-damping parameters (dialing high-frequency dissipation)

The whole point of HHT-α is to remove **spurious high-frequency** content (ringing from contact chatter, sudden loads, stiff penalty springs) **without** corrupting the low (resolved) modes — something plain Newmark cannot do at 2nd-order accuracy. The control is one knob; everything else follows from it.

**Newmark (β, γ).** Unconditionally stable iff `2β ≥ γ ≥ ½`. The default **β = ¼, γ = ½** ("average-acceleration" / trapezoidal rule) is unconditionally stable, **2nd-order accurate, and has zero algorithmic damping**. Adding damping the Newmark way means **γ > ½** — but that **drops the scheme to 1st-order accuracy** and damps low modes too, so it is the *wrong* tool for high-frequency dissipation. (β = 0, γ = ½ is the explicit central-difference scheme — conditionally stable.) [20]

**HHT-α (Hilber–Hughes–Taylor 1977).** Introduces one extra parameter **α** that shifts where equilibrium is evaluated within the step, then ties Newmark's parameters to it:

> **β = (1−α)² / 4,  γ = ½ − α,  with α ∈ [−⅓, 0]** (original-paper sign convention; α negative ⇒ γ > ½). [18][21]

This keeps **2nd-order accuracy and unconditional stability** while adding **high-frequency** numerical dissipation only. `α = 0` recovers the trapezoidal rule (no damping); more-negative α = more high-frequency damping; **α = −⅓ is the maximum**.

**The single knob is the asymptotic spectral radius ρ∞** — the amplification factor applied to the highest frequencies each step (ρ∞ = 1 ⇒ no high-frequency damping; ρ∞ = 0 ⇒ those modes annihilated in one step). For HHT-α the exact relation (confidence: **high** — algebraically and numerically verified, original-paper convention) is:

> **ρ∞ = (1 + α) / (1 − α)  ⟺  α = (ρ∞ − 1) / (ρ∞ + 1)**,  valid for **ρ∞ ∈ [½, 1]**.

(HHT-α can only reach ρ∞ = ½ at α = −⅓; pushing dissipation harder — ρ∞ < ½ — requires generalized-α, below.)

| Target ρ∞ | α | β = (1−α)²/4 | γ = ½−α | Effect |
|---|---|---|---|---|
| **1.0** | 0 | 0.2500 | 0.5000 | No numerical damping (= trapezoidal Newmark) |
| **0.9** | −0.05263 | 0.2770 | 0.5526 | Light HF damping — typical "clean up ringing" setting |
| **0.8** | −0.11111 | 0.3086 | 0.6111 | Moderate HF damping |
| **0.5** | −⅓ (−0.33333) | 4/9 (0.4444) | 5/6 (0.8333) | Maximum HHT-α damping |

A common practical band is **α ≈ −0.05 … −0.1** (ρ∞ ≈ 0.9–0.8): enough to suppress contact/impact ringing, little effect on the modes you care about. At α = −⅓, the maximum-damping point corresponds to roughly a **6 % damping ratio when Δt ≈ 40 % of the mode period** — i.e. it bites hardest exactly on modes resolved by only ~2–3 steps/period, leaving well-resolved modes nearly untouched. [18][21]

**Generalized-α (Chung–Hulbert 1993) — the modern generalization.** Splits the single time-shift into two (**α_f** on the stiffness/force term, **α_m** on the inertia term), giving **optimal** high-frequency dissipation for a chosen ρ∞ with minimal low-frequency damping — and it can reach the full **ρ∞ ∈ [0, 1]** range (HHT-α is the special case α_m = 0). For a target ρ∞ ∈ [0, 1]: [21]

> **α_m = (2ρ∞ − 1)/(ρ∞ + 1),  α_f = ρ∞/(ρ∞ + 1),  γ = ½ − α_m + α_f,  β = ¼(1 − α_m + α_f)².**

Most modern implicit dynamics solvers expose generalized-α (sometimes under a single "spectral radius" / "numerical damping" input that hides the four parameters). **Sign-convention caveat:** vendors differ — Abaqus `*DYNAMIC, ALPHA` and the original paper use **negative α** as above; some codes (e.g. OpenSees) redefine `α_code = 1 + α_paper` so the input runs **0.67 … 1.0** for the same physical range. Always check the manual for which convention the input box wants before typing a number.

### Explicit — the CFL stable time step

The critical step is the time for a stress wave to cross the **smallest element**:

> **Δt_crit = L_min / c**, with dilatational wave speed **c = √(E/ρ)** (1-D; `√(E(1−ν)/((1+ν)(1−2ν)ρ))` in 3-D). [22][23]

Practical points:
- A safety/scale factor (**TSSF**, default ~0.9 in LS-DYNA) multiplies Δt_crit. The whole model marches at the **single smallest** element's Δt — **one sliver element throttles the entire run**. Mesh quality at small features is a *cost* lever, not just accuracy. [22][23]
- **Mass scaling** raises Δt by **adding non-physical mass** to the time-step-controlling elements (LS-DYNA `DT2MS`; the recommended `DT2MS<0` form adds mass only to elements below `TSSF·|DT2MS|`). Because `F=ma`, added mass changes inertia/results. **Limits:** keep added mass small (rule of thumb **< ~1–5 % of model mass**, monitored in `glstat`/`d3hsp`), and **only where it doesn't matter** (a few small noncritical elements, or quasi-static runs where velocity/KE is low). Always run a second pass with reduced/zero scaling to gauge sensitivity. [23][24][25][26]
- **Quasi-static via explicit:** apply loads slowly (prescribed displacement/velocity, smooth ramp), and verify **kinetic energy ≪ internal energy** throughout — that is the definition of quasi-static and the check that mass scaling didn't introduce spurious dynamics. [25]

### Energy balance (explicit) — the integrity check

Reduced-integration elements can develop zero-energy **hourglass** modes; control them (LS-DYNA viscous/stiffness hourglass `*CONTROL_HOURGLASS`, default type 1; stiffness type 4/5 for coarse meshes; type 6 for accuracy-critical). The acceptance criterion:

> **Hourglass (artificial) energy < ~5–10 % of internal energy** (≤5 % preferred, 10 % the upper limit). Likewise **sliding-interface (contact) energy** should stay small/positive; large negative contact energy ⇒ initial penetrations/bad contact. Check the global energy balance: **total energy ≈ constant** (a few % drift max). [24][26]

**Top mistakes:** explicit Δt strangled by a single bad element (didn't check the smallest-element/Δt report); mass scaling that quietly adds 20 %+ mass and changes the physics; hourglass energy >10 % (spurious deformation, soft response) left uncontrolled; using explicit for a long, slow event (millions of tiny steps) where implicit is far cheaper; coarse implicit Δt missing the response frequency.

---

## 5. Parallelization (SMP vs DMP, scaling, GPU)

- **SMP (shared-memory parallel)** — one process, multiple threads, one address space. Easy, no decomposition, but **efficiency saturates early — ~4–8 cores** (memory-bandwidth bound; LS-DYNA SMP "maybe 8 cores give or take"). [24]
- **DMP / DDM (distributed-memory parallel, MPI)** — partitions the model into subdomains solved on separate ranks (different machines/sockets), communicating at interfaces. **Better scaling** to many cores; the way to use a cluster. MAPDL `-dis -np N`; Nastran `dmparallel=N`/`DOMAINSOLVER`; Abaqus `mp_mode=mpi`. [27]
- **Nastran DMP decomposition flavors** — **geometric** (partition the mesh; works best on shell-dominant models with small interface boundaries; "chunky" solids create large interface DOF and scale worse), **frequency** (split the eigen range into independent bands, e.g. 0–120 Hz / 120–200 Hz, auto-balanced by modal density), and **load/RHS** domains — combinable. [27]
- **Scaling reality** — efficiency plateaus around **~16–32 cores** for typical models; small or bandwidth-bound models saturate by **~4–8**. **Verify empirically:** time@N vs time@2N — stop adding cores when speedup-per-doubling drops below **~1.3×**. Decomposition quality matters: load-balanced partitions, minimal interface DOF; **contact spanning many subdomains kills scaling.** [24][27]
- **GPU** — offloads the dense frontal/multifrontal kernels of the **direct** solver on **large factorizations** (MAPDL `-acc nvidia` / `ACCOPTION`; Nastran `gpgpu=`). Helps big direct solves; sparse triangular solves and incomplete factorizations are hard to accelerate, so iterative-solver GPU speedups are model-dependent. [27]
- **Licensing** — beyond ~4 cores usually needs HPC packs/tokens; budget licenses before scaling.

**Top mistakes:** throwing 64 cores at a model that saturates at 8 (wasted licenses, possible slowdown from comms); DMP on a contact model with contact straddling every partition; expecting linear speedup; geometric DMP on a chunky solid where frequency DMP (for modal) would scale far better.

---

## 6. Reading residuals & decoding solver messages

The single highest-value skill: **never trust the exit code — read the history and the message file.**

- **Negative / zero pivot (`NEGATIVE PIVOT`, MAXRATIO warning, "numerically singular")** = the stiffness matrix is **singular or indefinite**. In a *static* run almost always **under-constraint** (rigid-body DOF, lost/insufficient contact, a part connected to nothing, hinge/mechanism, zero-stiffness from bad properties). In **buckling/post-limit** runs a negative pivot is *expected and physical* (it signals the instability). **Diagnose the DOF/node reported — do not blindly re-mesh.** [3][29]
- **Nastran singularity controls:** `PARAM,MAXRATIO` (default **1e7**) flags matrix-diagonal-to-factor-diagonal ratios above it (mechanism/ill-conditioning indicator); `PARAM,AUTOSPC,YES` auto-constrains singularities with ratio below `EPZERO` (**1e-8**); `EPPRT` (**1e-8**) lists potential singularities; grid-point singularities are reported in the GPST table. A **high MAXRATIO (≫1e7) is a red flag for a real modeling defect**, not a nuisance to suppress. [28][30]
- **Distortion / negative Jacobian** = a degenerate or excessively-deformed element (often in nonlinear/large-strain or remap) — fix mesh quality or use adaptive remeshing; in explicit, eroding/inverted elements need element deletion or remap.
- **Non-convergence patterns** (§3) — flat/rising residual, runaway bisection, severe-discontinuity loops (contact), hitting the iteration cap every increment. Map the pattern to a cause: chatter→contact stabilization/FKN; sudden divergence→line search/load step; gradual stall→material instability/limit point→arc-length.
- **Energy/mass diagnostics** (explicit) — `glstat`/`matsum`: watch hourglass %, contact energy sign, added-mass %, and total-energy drift (§4).
- **Eigen diagnostics** — Sturm "modes missed" warning, fewer/more than 6 rigid-body modes, effective mass < 90 % (§2).

**Golden rule:** confirm **(a)** a result file was written **and (b)** the target load/time step actually converged, *before* reading any QoI. Batch non-convergence silently leaves you reading a stale or partial increment.

---

## 7. Condensed quick-reference

- **Linear:** direct=robust+RAM-hungry (in-core!), iterative=cheap+needs good conditioning. Lose log₁₀(κ) digits.
- **Modal:** Block Lanczos default; Supernode/AMLS for many/NVH modes (approximate, 10–25×); Sturm check; ≥90 % effective mass; 6 rigid-body modes; QRDAMP/UNSYM for damped/rotating.
- **Nonlinear:** full Newton (quadratic); arc-length/Riks for snap-through/back; line search + auto-step+bisection; residual must fall 1–2 orders; Abaqus 0.5 %/1 % force/disp defaults; stabilization energy ≪ strain energy.
- **Transient:** implicit Newmark (β=¼,γ=½, no damping) / HHT-α (β=(1−α)²/4, γ=½−α, α∈[−⅓,0]; ρ∞=(1+α)/(1−α), dial ρ∞≈0.9–0.8 for HF damping) / generalized-α (ρ∞∈[0,1]) unconditional (≥10–20 steps/period); explicit central-difference Δt=L_min/√(E/ρ) (CFL); mass-scaling added mass <1–5 %; hourglass energy <5–10 %.
- **Parallel:** SMP saturates ~8, DMP scales further (~16–32), verify time@N vs @2N (stop <1.3×/doubling), GPU for big direct factorizations.
- **Diagnostics:** negative pivot=singular/under-constrained (or physical in buckling); MAXRATIO>1e7=defect; read residual history, not exit code.

---

## SOURCES

Reliability key: **H** = primary vendor theory/user manual or peer-reviewed/standards body (highest); **M** = vendor knowledge-base / reputable practitioner / encyclopedic reference cross-checked; **L** = forum/secondary (used only corroboratively).

1. NAFEMS — "What is the Difference Between Direct and Iterative Solvers" (resource WT03 / benchmark guidance). https://www.nafems.org/publications/resource_center/wt03/ — **H** (standards/education body; landing requires login but topic canon).
2. Frontal / multifrontal direct solvers (Irons frontal; Duff–Reid multifrontal) — Duff, Erisman & Reid, *Direct Methods for Sparse Matrices*, 2nd ed. (Oxford, 2017); Irons (1970) *Int. J. Numer. Methods Eng.* 2:5. Orientation: Wikipedia — Frontal solver, https://en.wikipedia.org/wiki/Frontal_solver — **M**.
3. Ansys Mechanical/MAPDL solver theory & practice (SPARSE vs PCG, in-core/out-of-core ~10×, `Lev_Diff`, RAM ~5–10×) — corroborated via Ansys help & practitioner summaries; SolidWorks Simulation "Direct vs Iterative" help. https://help.solidworks.com/2021/english/SolidWorks/cworks/c_direct_iterative_solvers.htm — **M**.
4. Conjugate-gradient / PCG (κ-dependent convergence, ≈√κ iteration bound) — Saad, *Iterative Methods for Sparse Linear Systems*, 2nd ed. (SIAM, 2003); Golub & Van Loan, *Matrix Computations*, 4th ed. (Johns Hopkins). Orientation: Wikipedia — Conjugate gradient method, https://en.wikipedia.org/wiki/Conjugate_gradient_method — **M**.
5. Ansys `MODOPT` command reference (LANB/LANPCG/SNODE/SUBSP/UNSYM/DAMP/QRDAMP). https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_cmd/Hlp_C_MODOPT.html — **H** (mirror of Ansys docs).
6. Ansys Theory Reference §14.13 "Eigenvalue and Eigenvector Extraction" (Block Lanczos shift strategy + Sturm check off-by-default; Supernode approximate, >200 modes faster, SNOPTION RangeFact 2.0). https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_thry/thy_tool13.html — **H** (mirror).
7. CDH/AMLS & AMLS literature — automated multi-level substructuring (~10 000 substructures/~20 levels; 10–25× faster than Lanczos; Volvo NVH order-of-magnitude). https://cdh-ag.com/en/software/cdh-software/cdh-amls/ and Abaqus AMS release note https://classes.engineering.wustl.edu/2009/spring/mase5513/abaqus/docs/v6.6/books/rnb/abc06aqs14.html — **M/H**.
8. Sparse direct (factor-once / multi-RHS) — Davis, *Direct Methods for Sparse Linear Systems* (SIAM, 2006); Duff, Erisman & Reid (as [2]). Orientation: Wikipedia — Frontal solver, https://en.wikipedia.org/wiki/Frontal_solver — **M**.
9. Condition number (sensitivity, ill-conditioning sources) — Golub & Van Loan, *Matrix Computations*, 4th ed.; Trefethen & Bau, *Numerical Linear Algebra* (SIAM). Orientation: Wikipedia — Condition number, https://en.wikipedia.org/wiki/Condition_number — **M**.
10. Preconditioning (Jacobi / incomplete-Cholesky / multigrid; ideal preconditioner = 1 step) — Saad, *Iterative Methods for Sparse Linear Systems*, 2nd ed. (SIAM, 2003). Orientation: Wikipedia — Preconditioner, https://en.wikipedia.org/wiki/Preconditioner — **M**.
11. Numerical-analysis rule of thumb — lose log₁₀(κ) digits; double≈16 digits (Driscoll, *Fundamentals of Numerical Computation*; Northwestern reliable-computations notes). https://tobydriscoll.net/fnc-julia/intro/floating-point.html — **H** (university text).
12. Ansys "Comparing Mode-Extraction Methods" + Theory §14.13 table (applicability matrix). https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_thry/thy_tool13.html — **H** (mirror).
13. Altair OptiStruct AMLS reference & ScienceDirect AMLS FRF synthesis. https://2025.help.altair.com/2025/hwdesktop/altair_help/topics/solvers/os/solvers_amls_os_r.htm — **M/H**.
14. Ansys modal best practice — extract modes to ≥90 % effective mass participation (Ansys help / response-spectrum guidance; Nastran `PARAM,MEFFMASS`). https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/ans_str/Hlp_G_STR3_15.html — **H** (Ansys docs).
15. Newton / modified-Newton iteration in nonlinear FEA (full vs modified NR, initial stiffness, quadratic convergence) — Bathe, *Finite Element Procedures* (Prentice-Hall); Crisfield, *Non-linear Finite Element Analysis of Solids and Structures* (Wiley). Orientation: Wikipedia — Newton's method, https://en.wikipedia.org/wiki/Newton%27s_method — **M**.
16. Abaqus Analysis User's Manual §2.2.1 / §7.2.3 "Nonlinear solution methods / Convergence criteria" (full Newton, quasi-Newton, line search default with quasi-Newton). https://classes.engineering.wustl.edu/2009/spring/mase5513/abaqus/docs/v6.6/books/stm/ch02s02ath14.html — **H**.
17. Abaqus Analysis User's Manual §6.2.4 "Unstable collapse and postbuckling analysis" (Riks: load magnitude as unknown, 1 % extrapolation, fails on contact-loss; STABILIZE volume-proportional damping vs Riks). http://abaqusdocs.eait.uq.edu.au/v6.11/books/usb/pt03ch06s02at03.html — **H** (mirror).
18. Abaqus Analysis User's Manual §6.3.2 "Implicit dynamic analysis using direct integration" (HHT-α: α=0 trapezoidal, α=−1/3 max damping ≈6 % at Δt=40 % period, allowable α/β/γ). http://abaqusdocs.eait.uq.edu.au/v6.11/books/usb/pt03ch06s03at07.html — **H** (mirror).
19. Abaqus Analysis User's Manual §7.2.2 "Commonly used control parameters" (Rⁿα=0.005, Cⁿα=0.01, cut-back 0.25/0.5/0.75, max 5 cut-backs, 16 equilibrium iterations, line-search default). http://abaqusdocs.eait.uq.edu.au/v6.9ef/books/usb/pt03ch07s02aus43.html — **H** (mirror).
20. Newmark-β time integration (β=¼,γ=½ unconditional average-acceleration; 2β≥γ≥½ stability; γ>½ adds numerical damping at first-order) — Newmark, N.M. (1959) *A method of computation for structural dynamics*, J. Eng. Mech. Div. ASCE 85(EM3):67–94 (primary); Hughes, *The Finite Element Method: Linear Static and Dynamic Finite Element Analysis* (Dover) ch. 9; Bathe, *Finite Element Procedures*. Orientation: Wikipedia — Newmark-beta method, https://en.wikipedia.org/wiki/Newmark-beta_method — **M**.
21. Abaqus §6.3.2 HHT-α numerical-damping table (transient-fidelity defaults; negative α → damping). http://abaqusdocs.eait.uq.edu.au/v6.11/books/usb/pt03ch06s03at07.html — **H** (mirror). HHT-α↔ρ∞ relation `ρ∞=(1+α)/(1−α)` and generalized-α (Chung–Hulbert) parameters `α_m=(2ρ∞−1)/(ρ∞+1)`, `α_f=ρ∞/(ρ∞+1)` corroborated by: Hilber, Hughes & Taylor (1977) *Improved numerical dissipation for time integration algorithms in structural dynamics*, Earthquake Eng. Struct. Dyn. 5:283–292 (**H**, primary); Chung & Hulbert (1993) J. Appl. Mech. 60:371–375 (**H**, primary); Exudyn generalized-α solver docs https://exudyn.readthedocs.io/en/stable/docs/RST/ImplicitTrapezoidalRulebasedNewmarkAndGeneralizedalphaSolver.html (**M**); OpenSees HHT (sign-convention `α_code=1+α_paper`, range 0.67–1.0) https://opensees.berkeley.edu/wiki/index.php/Hilber-Hughes-Taylor_Method (**M**). The β/γ table values were algebraically/numerically verified (spectral radius of the amplification matrix).
22. Courant–Friedrichs–Lewy condition (numerical domain of dependence must contain the physical one; Δt shrinks with grid) — Courant, Friedrichs & Lewy (1928) *Über die partiellen Differenzengleichungen der mathematischen Physik*, Math. Ann. 100:32–74 (primary); LeVeque, *Finite Volume Methods for Hyperbolic Problems* (Cambridge). Orientation: Wikipedia — Courant–Friedrichs–Lewy condition, https://en.wikipedia.org/wiki/Courant%E2%80%93Friedrichs%E2%80%93Lewy_condition — **M**.
23. LS-DYNA Mass Scaling FAQ / Theory "Time Step Control" (Δt ∝ element size / sound speed; c ∝ √(E/ρ)). https://ftp.lstc.com/anonymous/outgoing/support/FAQ/mass_scaling — **H** (LSTC official FAQ).
24. Ansys Knowledge "Guidelines for reducing runtime of an explicit analysis in LS-DYNA" (DT2MS<0 recommended; mass shown in glstat/d3hsp; SMP ~8-core limit; default reduced-int elements; contact choice). https://innovationspace.ansys.com/knowledge/forums/topic/some-basic-guidelines-for-reducing-the-runtime-of-an-explicit-analysis-in-ls-dyna/ — **M** (Ansys KB).
25. EDR Medeso "Making Quasi-Static Simulations Simple with Ansys LS-DYNA" (apply loads slowly, KE≪IE, smooth ramp; mass scaling valid when KE small). https://edrmedeso.com/article/making-quasi-static-simulations-simple-with-ansys-ls-dyna/ — **M** (Ansys channel partner).
26. LS-DYNA hourglass / energy-balance best practice — hourglass energy ≤10 % (≤5 % preferred) of internal energy; LS-DYNA Explicit Technical Guide v1.5. https://lsdyna.ansys.com/wp-content/uploads/2025/03/LSDYNA_Explicit_Technical_Guide_v1.5.pdf — **H** (Ansys/LST guide).
27. Simcenter/NX & MSC Nastran Parallel Processing / HPC guides (SMP vs DMP; geometric vs frequency vs load decomposition; geometric best on shells; GPU `gpgpu=`). https://www.smart-fem.de/media/dmp.pdf and MSC Nastran 2022.2 HPC User's Guide https://documentation-be.hexagon.com/bundle/MSC_Nastran_2022.2_High_Performance_Computing_User_Guide/raw/resource/enus/MSC_Nastran_2022.2_High_Performance_Computing_User_Guide.pdf — **H** (vendor guides).
28. MSC/NX Nastran singularity parameters (MAXRATIO default 1e7, AUTOSPC, EPZERO/EPPRT 1e-8). https://www.numeric-gmbh.ch/posts/investigating-excessive-pivot-ratios-in-matrix-kll-22.html (corroborated) + Nastran QRG. — **M**.
29. Ansys/CAE solver diagnostics — negative/zero pivot = singular/under-constrained (physical in buckling). Cross-checked across Ansys help & practitioner notes. — **M**.
30. Eng-Tips / MSC community on PARAM cards (AUTOSPC behavior, MAXRATIO meaning) — corroborative only. https://www.eng-tips.com/threads/param-cards-in-nastran.348205/ — **L**.
