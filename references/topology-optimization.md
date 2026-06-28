# Topology Optimization — Practitioner Reference

Scope: structural **topology optimization** (TO) — finding the *material layout* in a design space that best meets an objective under constraints. Covers the three structural-optimization types and when each applies; **density methods** (SIMP, RAMP) and the canonical compliance-minimization problem plus other objectives; **adjoint sensitivities** and the two production optimizers (OC, MMA); the **numerical pathologies** (checkerboarding, mesh-dependence, gray) and their **filtering / projection / length-scale** cures; **manufacturing constraints** (member size, symmetry, draw/extrusion, AM overhang, frozen regions); the **advanced formulations** (stress-constrained, buckling, eigenfrequency, multi-material, robust/multi-load, level-set & phase-field, homogenization / lattice / AM-aware); the **tool landscape** (vendor-neutral); and — above all — **the discipline**: a topology result is a **concept, not a part**. Vendor specifics are flagged; numbers and rules are sourced (see SOURCES). Confidence tags: **[VERIFIED-web]** = corroborated against external sources during authoring · **[DOCS-ONLY]** = from method/vendor documentation, not independently re-derived here.

This file is the **deep dive** behind the topology pointer in `advanced-methods.md` §4.1–4.2 (which gives the one-paragraph version and the instability-control checklist). The shape-optimization treatment (stress-concentration relief, fillet/notch reshaping) lives in `advanced-methods.md` §4.1 and is **cross-linked, not duplicated**. The single rule that ties this file to the rest of the skill: **a topology result *predicts* a load path; it does not *solve* a verified part — re-interpret it to clean geometry and re-solve on a validated mesh before any engineering claim** (`ml-surrogates-and-rom.md` §7 solve-vs-predict, extended to the generative layer).

---

## 1. The three structural-optimization types (pick by what you let change)

| Type | Design variables | What changes | Topology fixed? | Typical use | Cost |
|---|---|---|---|---|---|
| **Sizing** | Discrete dimensions — shell thickness, beam cross-section, spring/material parameters (continuous scalars) | Magnitudes only; mesh & connectivity unchanged | **Yes** | Tune a known layout: gauge a panel, size a truss, set a beam section | Cheapest; analytic sensitivities, smooth |
| **Shape** | Boundary positions — CAD parameters, control points, morph/free-form-deformation fields | Boundaries move; **no holes created/destroyed** | **Yes** (genus fixed) | Stress-concentration relief: reshape a **fillet, notch, hole, re-entrant corner** to flatten the boundary stress | Moderate; needs remeshing/morphing |
| **Topology** | A material-distribution field (density ρ(x) per element, or a level-set/phase field) | **Connectivity itself** — members, holes, branches appear/vanish | **No — it decides the layout** | Conceptual design from a blank design space: where should material *be*? | Most expensive; most freedom |

**Decision rule.** Use **topology** *early* (concept stage, blank-sheet, "where does the load path want to go?"). Use **shape** to refine a sound topology's local detail — the canonical payoff is **stress-concentration relief** at fixed envelope/mass, where flattening the tangential boundary stress to a near-uniform "fully-stressed" contour is the optimum signature (full treatment + the minimum-radius/mesh-converged-hotspot caveats in **`advanced-methods.md` §4.1**). Use **sizing** *last*, to tune magnitudes once layout and shape are frozen. The three are a **sequence**, not alternatives: TO gives a concept → CAD reconstruction → shape/sizing polish → verification solve. **[VERIFIED-web]**

> The crucial mental model: **sizing and shape optimize *within* a topology; topology optimizes *across* topologies.** That extra freedom is why TO finds non-intuitive, organic, load-path-following structures — and why its raw output is never a manufacturable part (§9).

---

## 2. Density (material-distribution) methods

The dominant industrial approach discretizes the design domain into FE and assigns each element a **continuous "density" design variable** ρ_e ∈ [0,1] (0 = void, 1 = solid). The optimizer drives each ρ_e toward 0 or 1; the trouble is that continuous variables admit **intermediate ("gray") densities** with no physical meaning, so the material-interpolation law is built to **penalize** them.

### 2.1 SIMP — Solid Isotropic Material with Penalization [VERIFIED-web]

The workhorse (Bendsøe 1989; Rozvany; Bendsøe & Sigmund). The element Young's modulus interpolates as a **power law** of density:

> **E(ρ_e) = E_min + ρ_e^p · (E_0 − E_min)**,  with penalization exponent **p > 1** (canonically **p = 3**)

where **E_0** is the solid material's modulus and **E_min** is a tiny non-zero floor (e.g. 10⁻⁹·E_0) that keeps void elements in the model **without making the stiffness matrix singular** (a pure-zero modulus de-couples those DOF). (The original SIMP wrote E = ρ^p·E_0; the modified/positive form with E_min is the numerically robust version used in the 88-line code and most solvers.)

**Why the power law penalizes gray.** For p > 1 the modulus gained per unit *mass* is **disproportionately low at intermediate density**: an element at ρ = 0.5 with p = 3 contributes only 0.5³ = **0.125** of the stiffness but costs 0.5 of the **volume** budget. So intermediate material is a *bad deal* — the optimizer is economically driven to spend its volume on solid (ρ→1) elements and leave the rest void (ρ→0), yielding a near-**0/1 (black-and-white)** design. Higher p sharpens this but too-high p (≳4–5 from the start) creates many local minima; **continuation** (start p≈1, ramp toward 3) helps reach a better optimum. The choice **p ≥ 3** is also tied to the **Hashin–Shtrikman** bounds — at p ≥ 3 (in 2D, ν = 1/3) the SIMP "material" is physically realizable as a composite microstructure, which is the theoretical justification for p = 3, not mere convenience. **[VERIFIED-web]**

### 2.2 RAMP — Rational Approximation of Material Properties [VERIFIED-web]

The main alternative interpolation (Stolpe & Svanberg 2001):

> **E(ρ_e) = E_min + [ ρ_e / (1 + q·(1 − ρ_e)) ] · (E_0 − E_min)**,  with penalization parameter **q > 0** (e.g. q ≈ 8)

**Why it exists — the SIMP gap RAMP closes.** SIMP's power law has **zero slope at ρ = 0** (dE/dρ → 0 as ρ → 0 for p > 1). That makes void elements "sticky": their sensitivity vanishes, so an element that *should* re-enter the design can't easily be revived — and it complicates problems where void-region sensitivity matters (notably some **dynamic / eigenfrequency** and self-weight problems, where SIMP can produce **artificial localized "modes"** in near-void regions). RAMP has a **non-zero slope at ρ = 0**, giving void elements a finite sensitivity and a cleaner concave-in-the-right-way interpolation. **Practitioner rule: SIMP is the default for compliance/stiffness; reach for RAMP for eigenfrequency, self-weight, or when SIMP gray/local-mode artifacts appear.** **[VERIFIED-web]**

### 2.3 The canonical problem — minimum compliance under a volume constraint [VERIFIED-web]

The reference problem (the one the 99-line and 88-line codes solve):

```
min_ρ   c(ρ) = Uᵀ K(ρ) U = Σ_e (ρ_e)^p u_eᵀ k_0 u_e        (compliance = strain energy)
s.t.    K(ρ) U = F                                         (equilibrium / FE state equation)
        V(ρ)/V_0 = Σ_e ρ_e v_e / V_0  ≤  f                 (volume fraction ≤ target f, e.g. 0.3–0.5)
        0 < ρ_min ≤ ρ_e ≤ 1                                (box bounds; ρ_min keeps K non-singular)
```

**Compliance** c = UᵀKU is the structure's total strain energy under the applied load — **minimizing compliance = maximizing stiffness** (minimizing deflection at the load). The **volume-fraction constraint** f is what makes it interesting: with unlimited material the answer is "fill everything," so TO is fundamentally **"the stiffest structure using at most f of the design volume."** The constraint is active at the optimum (the optimizer spends its whole budget). **[VERIFIED-web]**

### 2.4 Other objectives (same machinery, different functional)

| Objective | Minimize / maximize | Notes & cautions |
|---|---|---|
| **Min compliance / max stiffness** | min UᵀKU at fixed volume | The canonical, best-behaved problem; self-adjoint (free sensitivities, §3). |
| **Min volume / mass** s.t. performance | min Σρ_e v_e s.t. stress/compliance/displacement limits | The "design-for-constraints" inverse of compliance; needs the constraint to be well-posed (stress → §6). |
| **Stress-constrained / min-stress** | limit/min peak stress (p-norm aggregate) | Hard: stress is **local, singular, and non-self-adjoint** — see §6.1. |
| **Max fundamental frequency / frequency gap** | max λ₁ (or a target band) | Use **RAMP** or careful interpolation to avoid spurious near-void modes; objective non-smooth at **mode-crossing/repeated eigenvalues** → use bound formulation / sub-gradient. §6.3. |
| **Compliant mechanism** | maximize output displacement / mechanical advantage for a given input | Multi-load (input port + dummy output load); needs **adjoint** (non-self-adjoint); prone to **one-node hinges** → length-scale control essential. |
| **Thermal** | min thermal compliance (max heat dissipation), or min peak temperature, or tailor an effective CTE | Heat-conduction analog of stiffness; thermo-elastic/coupled and **thermal-actuator** mechanisms are common multiphysics TO targets. |
| **Multi-load / robust** | min worst-case or weighted-sum compliance over load cases | Single-load TO is **fragile** off-design — almost always run multi-load (§6.5). |

---

## 3. Sensitivity analysis (adjoint) + the two optimizers

TO has **many design variables** (one per element — 10⁴–10⁷) and **few constraints**, so you need the gradient of the objective (and each constraint) w.r.t. *every* ρ_e. The efficient route is the **adjoint method**.

### 3.1 Adjoint sensitivities [VERIFIED-web]

For a response g(ρ, U) constrained by the state equation K(ρ)U = F, the adjoint method gives dg/dρ_e at a cost **independent of the number of design variables** — one extra (adjoint) linear solve per *response*, reused for all elements (vs. finite differences, which need one full solve **per design variable** — utterly infeasible at 10⁶ variables).

- **Compliance is *self-adjoint*** — the adjoint vector equals the displacement (λ = U), so the sensitivity is **free** (no extra solve):
  > **∂c/∂ρ_e = −p · ρ_e^(p−1) · u_eᵀ k_0 u_e**  (always **≤ 0**: adding material always reduces compliance).
- **Non-self-adjoint responses** (stress, compliant-mechanism output, most non-compliance objectives) need a **separate adjoint solve** per response. For *aggregated* constraints (a single p-norm stress measure, §6.1) that is **one** adjoint solve, which is exactly why aggregation is used.
- **Get the chain rule right.** Sensitivities are computed on the *physical* density, then propagated **back through the filter and projection** (§5) to the design variable. A classic bug is filtering the field but **not** the sensitivities (or double-filtering) → wrong gradients, stalled or oscillating convergence. **[VERIFIED-web]**

### 3.2 Optimality Criteria (OC) [VERIFIED-web]

The simple, fast updater in the 99-/88-line codes. Derived from the KKT conditions: at the optimum, the ratio of (objective sensitivity) to (volume sensitivity) — the **B_e** value — is uniform across all non-bound elements. OC is a **fixed-point/heuristic multiplicative update** with a per-element clamp:

```
ρ_e^new = clamp( ρ_e · B_e^η ,  [ max(ρ_min, ρ_e − m) ,  min(1, ρ_e + m) ] )

         (−∂c/∂ρ_e)                       p · ρ_e^(p−1) · u_eᵀ k_0 u_e
   B_e = ───────────   (compliance form:  ───────────────────────────  ,  ∂V/∂ρ_e = v_e)
          λ · ∂V/∂ρ_e                              λ · v_e
```

**B_e** is the ratio of the (negated) compliance sensitivity to the volume-constraint sensitivity ∂V/∂ρ_e = v_e (the element volume): at the KKT optimum B_e = 1 for every interior element, so each step multiplicatively nudges ρ_e toward where that holds. The pieces:
- **Damping exponent η ≈ 0.5** — softens the multiplicative step (the raw B_e ratio can be large); η = 1/2 is the canonical value in the 99-/88-line codes.
- **Move limit m ≈ 0.2** — the per-iteration box `[ρ_e − m, ρ_e + m]` (further clipped to `[ρ_min, 1]`) caps how far any element may swing in one step, preventing overshoot/oscillation.
- **Lagrange multiplier λ by bisection** — λ is *not* known a priori; it is found each iteration by **bisection** so the volume constraint **Σ_e v_e ρ_e = V\*** (V\* = f·V_0) is satisfied exactly. Larger λ shrinks every B_e (less material added), so the constrained volume Σ v_e ρ_e is monotone in λ — bisection on λ converges quickly to the target.

**Strengths:** trivially cheap, very robust for **single-constraint** compliance problems, scales to millions of elements. **Limitation:** it is essentially **single-constraint** (the one volume constraint is what the bisection on λ enforces) — it does **not** generalize cleanly to multiple/general constraints (multiple stress limits, displacement + frequency + volume together). For those, use **MMA** (§3.3), which handles multiple nonlinear constraints by construction. **[VERIFIED-web]**

### 3.3 MMA — Method of Moving Asymptotes (Svanberg 1987) [VERIFIED-web]

The de-facto **general-purpose** TO optimizer. MMA is a **sequential convex programming** method: at each iteration it builds a **separable convex approximation** of the objective and constraints using **moving asymptotes** (lower L_j and upper U_j bounds per variable that adapt each step to control conservativeness/oscillation), then solves that cheap convex sub-problem. **Why it dominates:** it handles **many design variables AND multiple general (nonlinear) constraints** at once — which OC cannot — making it the standard for stress-constrained, multi-load, frequency, and multiphysics TO. **GCMMA** (globally convergent MMA, Svanberg 2002) adds an inner conservative-approximation loop for guaranteed convergence. **Tuning knobs:** asymptote initialization and the move/adaptation parameters control stability vs. speed; over-aggressive asymptotes oscillate, over-conservative ones crawl. **Practitioner rule: OC for plain compliance-vs-volume; MMA (or GCMMA) the moment you have more than one nontrivial constraint.** **[VERIFIED-web]**

---

## 4. The reference codes (read these to *understand* TO)

| Code | Lines | What it is | Why it matters |
|---|---|---|---|
| **`top.m`** — Sigmund 99-line | 99 | MATLAB minimum-compliance SIMP + OC + sensitivity filter, on a structured 2D mesh | The canonical pedagogical TO; the paper everyone cites for "how TO actually works." (Sigmund 2001) |
| **`top88.m`** — 88-line | 88 | Vectorized, **much faster** rewrite; adds the **density filter** option and cleaner FE assembly | The modern teaching/baseline reference; ~100× faster than the 99-line. (Andreassen et al. 2011) |
| **`top3d`** / `top3d125` | ~125 | 3D extension | Standard 3D baseline. |
| **`topX` / 88-line variants** | — | PETSc/large-scale, level-set, stress, MMA-driven ports | Bridges to industrial scale & advanced formulations. |
| **ToPy** (Python) | — | Open-source SIMP TO (2D/3D), reads a problem-definition file | A free, scriptable TO engine — **AGENT-HEADLESS** for automation. |

Use these to **validate your understanding and your own loops** before trusting any black-box result. **[VERIFIED-web]**

---

## 5. Numerical pathologies & their fixes (the must-knows)

Raw density TO is plagued by three coupled artifacts. **Regularization (filtering + length scale + projection) is not optional** — it is what makes TO well-posed, mesh-independent, and manufacturable. (Sigmund & Petersson 1998 is the canonical survey; cross-link `advanced-methods.md` §4.2.)

### 5.1 Checkerboarding [VERIFIED-web]
**Symptom:** regions of alternating solid/void elements in a checkerboard pattern. **Cause:** a **numerical artifact**, not physics — low-order (bilinear Q4 / first-order) elements **overestimate** the stiffness of a checkerboard layout, so the optimizer is fooled into thinking it's efficient. **Fixes:** **filtering** (sensitivity or density, §5.4) — the standard cure; or **higher-order elements** / patch recovery (more expensive); or explicit checkerboard-control / perimeter constraints. Filtering is near-universal because it fixes checkerboarding *and* mesh-dependence at once.

### 5.2 Mesh-dependence (non-uniqueness) [VERIFIED-web]
**Symptom:** refine the mesh and you don't get the *same* structure resolved better — you get a **different, finer structure with more, thinner members**. **Cause:** the continuous problem is **ill-posed** — finer meshes admit ever-finer microstructure, so there is no mesh-convergent solution without a **length scale**. **Fix:** impose a **minimum length scale** via a **filter of fixed physical radius r_min** (§5.4/§5.5). With r_min the topology becomes **mesh-independent** (same layout across mesh sizes, just better-resolved boundaries) — *this is the property you must demonstrate.* Note: r_min must be a **physical length**, held fixed as you refine, not a fixed number of elements.

### 5.3 Local minima [VERIFIED-web]
TO is **non-convex** — different starts / parameters give different local optima. Mitigations: **continuation** (gradually ramp the SIMP penalty p from ~1 to 3, and/or sharpen the projection β slowly — §5.6); sensible **move limits**; multi-start for important problems. There is **no guarantee of the global optimum**; report the result as "a good design," not "the optimum."

### 5.4 Filtering — the core regularizer [VERIFIED-web]
Two classic variants, both convolving over the neighborhood N_e of elements within physical radius **r_min** with a weight w (typically a linear "hat" decaying to zero at r_min):

- **Sensitivity filter** (Sigmund 1994/1997): replace each element's sensitivity by a **weighted average of neighbors' sensitivities**. Heuristic (modifies the gradient, not the model) but **extremely robust and cheap** — it's what the 99-line uses, and still a great default.
- **Density filter** (Bruns & Tortorelli; Bourdin 2001): define a **physical density** ρ̃_e as the **weighted average of design densities** in N_e, and build the FE model from ρ̃. Has a clean variational interpretation and a **consistent chain rule** for sensitivities (§3.1) — preferred when you need rigorous gradients or want to compose with projection. Its side effect is **blurred (gray) boundaries**, which §5.6 projection then sharpens.

Both impose a **minimum member size ≈ r_min** and kill checkerboarding. **r_min is the single most important TO knob** — it sets the smallest feature and directly trades resolution against manufacturability.

### 5.5 Minimum length scale = the filter radius [VERIFIED-web]
The **filter radius r_min sets the minimum member (and, with the right formulation, minimum-void/hole) size.** This is how you (a) make the result mesh-independent and (b) honor a manufacturing floor (you can't machine/print a feature thinner than your tool/printer resolution, so set r_min accordingly). **Rule of thumb:** r_min ≳ a few element sizes (so the filter actually averages over a neighborhood) — meaning **mesh fineness sets your *resolution*, r_min sets your *feature size*, and they are independent design choices.** The **robust formulation** (§6.6) is what lets you impose minimum size on **both** solid and void rigorously.

### 5.6 Grayscale → projection / Heaviside [VERIFIED-web]
Density filtering leaves a band of **intermediate (gray) elements** at member boundaries — physically meaningless and not manufacturable. **Projection** pushes the filtered density toward **0/1** with a **smoothed Heaviside** around a threshold η (typ. 0.5), sharpness controlled by **β**:

> ρ̄_e = [ tanh(β·η) + tanh(β·(ρ̃_e − η)) ] / [ tanh(β·η) + tanh(β·(1 − η)) ]

- **β → 0** ≈ no projection (linear, gray); **β → ∞** ≈ a true step (crisp 0/1 but non-differentiable/unstable if applied abruptly).
- **β-continuation is essential:** start small (β ≈ 1), **double β periodically** (1→2→4→…→~16–64) so the optimizer first finds a smooth layout, then crisps it — jumping straight to high β traps you in a bad local minimum.
- **Threshold-projection (η)** is also the lever for the **robust / eroded-dilated** formulation (§6.6): η < 0.5 dilates, η > 0.5 erodes, modeling manufacturing over/under-etch and enforcing length scale on both phases.

### 5.7 The fix-it checklist
Checkerboard or mesh-dependent? → **add a filter (fixed physical r_min).** Boundaries gray? → **add β-continuation projection.** Stuck in a poor design? → **continuation on p and β, move limits, multistart.** Members too thin/void too small to make? → **raise r_min / use robust eroded-dilated.** None of these is a luxury; a TO result produced *without* a length scale is not a valid result.

---

## 6. Advanced formulations

### 6.1 Stress-constrained TO — the hard one [VERIFIED-web]
Three coupled difficulties, each with a standard remedy:

1. **The singularity phenomenon.** The true feasible set has **degenerate, lower-dimensional regions** at ρ → 0: as an element vanishes its stress does *not* go to zero (stress is intensive), so the optimum often sits on a "singular" sliver that gradient methods **cannot reach**. **Fix: stress relaxation** — **ε-relaxation** (Cheng & Guo) or **qp-relaxation** (relax the stress-density coupling so the constraint smoothly vanishes with the material), which "fills in" the degenerate subspace and restores a reachable optimum.
2. **Stress is *local* — millions of constraints.** One stress limit *per element* is intractable (one adjoint solve per constraint). **Fix: constraint aggregation** into a **single (or few, block-wise) differentiable global measure** — the **p-norm** or **KS (Kreisselmeier–Steinhauser)** function approximates the max stress:
   > σ_PN = ( Σ_e σ_e^P )^(1/P) → max_e σ_e as P → ∞
   One aggregate = **one adjoint solve.** The catch: low P **underestimates** the true peak (unsafe) and smooths it; high P approximates the max tightly but is **numerically stiff/oscillatory**. Use **P-continuation** and/or **adaptive normalization / clustering** (aggregate per region, not globally) to recover the local peak without instability.
3. **Highly nonlinear & non-self-adjoint.** Stress sensitivities need a real adjoint solve and are far less smooth than compliance → **MMA/GCMMA** (not OC), tight move limits, continuation.

**The honesty trap:** an *aggregated* stress constraint controls an *approximation* of the peak — the **true local peak stress in the final design must be checked on the re-solved, verified mesh** (§9). Aggregation is an optimizer device, **not** a stress-verification.

### 6.2 Buckling-constrained TO [VERIFIED-web]
Adds a **linear-buckling eigenvalue constraint** (critical load factor λ_crit ≥ target) — essential because minimum-compliance designs are often **slender and buckling-prone** (compliance ignores stability entirely). Difficulties: the **geometric stiffness matrix** depends on the stress state (extra adjoint terms); **mode switching and repeated/clustered buckling eigenvalues** make the constraint non-differentiable (bound formulation / aggregation over the lowest modes); and **spurious buckling modes in low-density regions** (the void-element artifact again) must be filtered/penalized. Computationally heavy but increasingly available in commercial TO. Pair with stress for a "stiff, strong, **and** stable" design.

### 6.3 Eigenfrequency / dynamic TO [VERIFIED-web]
**Maximize the fundamental frequency**, a **frequency gap/band**, or **minimize dynamic compliance / frequency response** at a drive frequency. Issues: **repeated eigenvalues** (e.g. symmetric designs) make λ non-differentiable → **bound (max-min) formulation** with sub-gradient/aggregation over the degenerate set; **localized spurious modes** in near-void regions (use **RAMP** §2.2 or modified mass interpolation, e.g. drop/penalize mass below a density threshold); and **mode-tracking** so the objective follows the right mode across iterations rather than swapping.

### 6.4 Multi-material TO [DOCS-ONLY]
Distribute **two or more solid phases** (plus void) — e.g. stiff+compliant, or different metals. Extends SIMP/RAMP via **multi-phase interpolation** (recursive/ordered SIMP, or a DMO — Discrete Material Optimization — interpolation), or a multi-phase **level-set/phase-field**. More design variables and a tendency to gray *between materials*; needs phase-wise volume/cost constraints. Useful for **multi-functional** (stiffness + thermal + damping) and **AM multi-material** parts.

### 6.5 Robust & multi-load TO [VERIFIED-web]
- **Multi-load:** a structure optimized for a **single** load case is **brittle** off-design (a member perfectly placed for one load is useless or harmful for another). Use a **weighted-sum** or, better, a **worst-case (min-max)** objective over all credible load cases. This is a near-mandatory default, not an "advanced" extra.
- **Robust formulation (manufacturing uncertainty):** optimize the **worst of an eroded / nominal / dilated** trio of designs simultaneously (via the projection threshold η, §5.6). This (a) makes performance insensitive to uniform **over/under-etch / printer-line offset** and (b) **rigorously enforces minimum length scale on both solid and void** — the single most reliable route to a length-scale-controlled, manufacturable result (Wang, Lazarov & Sigmund 2011).
- **Uncertainty in loads/material** → stochastic/robust (mean+std objective) or reliability-based TO (RBTO, probabilistic constraints).

### 6.6 The robust eroded/dilated trio — why it earns its keep [VERIFIED-web]
Restating §5.6 + §6.5 as the production recommendation: run **three projections of one design** — **eroded** (η > 0.5, thinner), **nominal** (η = 0.5), **dilated** (η < 0.5, thicker) — and optimize the **worst-performing**. Because the eroded design caps **minimum solid** size and the dilated caps **minimum void/hole** size, you get **two-sided length-scale control for free**, plus immunity to fabrication offset. It is the standard answer to "give me a manufacturable, mesh-independent topology."

### 6.7 Level-set & phase-field methods [VERIFIED-web]
The main **alternative to density methods** — represent the structure **implicitly** and evolve its **boundary**:

- **Level-set TO** (Sethian–Wendt; **Allaire, Jouve & Toader 2004**; **Wang, Wang & Guo 2003**): the structure is the zero-level-set of a higher-dimensional function φ(x); the boundary moves by solving a **Hamilton–Jacobi PDE** driven by **shape-derivative** sensitivities (often with a **topological derivative** to *nucleate new holes*, since classic level-set only moves existing boundaries). **Strengths:** **crisp, gray-free boundaries** at every iteration (no SIMP penalization, no projection needed) and clean CAD-friendly geometry. **Weaknesses:** strongly **dependent on the initial hole layout** (without hole-nucleation it can't create topology that wasn't seeded), needs re-initialization/velocity-extension care, and is generally **less plug-and-play** than SIMP.
- **Phase-field TO** (Allen–Cahn / Cahn–Hilliard): an interface with a diffuse but controlled width evolves by gradient flow; the **interfacial-energy term gives an intrinsic perimeter/length-scale control** (a built-in regularizer) and handles topology changes (merging/splitting) naturally. Smoother, often slower; attractive when you want intrinsic length-scale and clean interfaces.

**When to prefer them:** crisp boundary / direct CAD output, problems where SIMP gray is troublesome, or research workflows. **When SIMP still wins:** general-purpose, robust, well-tooled, easiest multi-constraint via MMA.

### 6.8 Homogenization, lattice & AM-aware design [VERIFIED-web]
- **Homogenization** is the *origin* of TO (Bendsøe & Kikuchi 1988): represent each element by a **periodic microstructure** with analytically/numerically **homogenized effective properties**, and optimize microstructure parameters + orientation. Modern revival: **multiscale / "de-homogenization"** TO produces **graded lattice infill** that approaches the theoretical stiffness bound while being **manufacturable by AM**.
- **Lattice / infill TO:** optimize a **variable-density lattice** (cell type + local relative density/orientation) instead of (or inside) a solid layout — natural for **additive manufacturing**, gives lightweight, multi-functional (thermal/energy-absorbing), buckling-tolerant parts, and avoids large solid masses. Often combined: solid TO for the load-bearing skeleton + optimized lattice infill.
- **AM-aware TO** folds the AM process into the optimization itself — see §7 overhang constraints; the broader point is that lattice + homogenization + overhang control together are why **TO and metal/polymer AM co-evolved**: AM can *build* the organic, lattice-filled geometry TO wants, and TO needs AM (or casting) to realize non-machinable shapes.

---

## 7. Manufacturing constraints (turn a concept into something buildable)

Unconstrained TO produces shapes you often **cannot make**. Modern TO bakes manufacturing into the formulation so the result is buildable, not just optimal-on-paper. **[VERIFIED-web]**

| Constraint | What it enforces | How it's imposed |
|---|---|---|
| **Minimum member size** | No feature thinner than tool/printer resolution | Filter radius **r_min** (§5.5) / eroded-dilated robust (§6.6) |
| **Maximum member size** | No thick blobs (cooling, residual stress, mass) — forces ribs/lattice instead of bulk | Local-volume constraint over each neighborhood; max-size projection |
| **Minimum hole / void size** | Holes large enough to clear powder, machine, or cast | Dilated projection in the robust trio (§6.6) |
| **Symmetry** | Mirror / planar / cyclic symmetry of the result | Map/average design variables across symmetry planes (or filter symmetrically); also tames non-uniqueness |
| **Extrusion** | Constant cross-section along an axis (extruded/profiled parts) | Force ρ constant along the extrusion direction (group variables along the axis) |
| **Casting / draw direction (mold release)** | **No internal voids or undercuts** that trap the mold → die must release along the draw direction(s) | Draw/cast constraint: void must connect monotonically to the parting line along the draw axis; single- or two-sided draw |
| **AM overhang / self-support** | No down-facing surface below the **critical self-support angle** (≈ **45°** typical for metal PBF) without support; minimize/avoid sacrificial supports | **Overhang constraint** (AM-filter / additive front-propagation projection that builds layer-by-layer feasibility into ρ); print-direction-aware |
| **Frozen / no-go (non-design) regions** | Keep mounting bosses, bearing seats, interfaces solid; keep clearance/keep-out volumes void | Tag elements as **non-design** (fixed ρ = 1 solid or ρ = 0 void), excluded from the design variable set |

**Practitioner rules.** (1) Decide the **process first** — the relevant constraints (draw direction for casting vs. overhang for AM) are mutually exclusive design drivers. (2) **Frozen regions are mandatory**, not optional: load-introduction and interface volumes must be declared non-design or TO will eat them. (3) Manufacturing constraints **cost performance** — the optimum-on-paper compliance always degrades once you add draw/overhang/min-size; that gap is real and should be reported. (4) Even with overhang constraints, AM TO results still usually need a final **build-orientation + support study** in the AM-prep tool. **[VERIFIED-web]**

---

## 8. Tools (vendor-neutral)

| Tool | Class | TO scope (high level) | Headless / automation |
|---|---|---|---|
| **Ansys Mechanical — Topology Optimization** | Commercial FE-integrated | SIMP/level-set; compliance, mass, frequency, displacement, global-stress; manufacturing (min/max member, symmetry, pull-out/extrusion, AM overhang); STL export + validation system | Scriptable (ACT/PyMechanical/Mechanical APDL) — **AGENT-HEADLESS** |
| **Ansys optiSLang** | Process integration / RDO | Parametric & robust-design optimization, DOE-surrogate-optimize wrapping (also drives sizing/shape) | Scriptable |
| **Altair OptiStruct** | Commercial solver | The long-time TO benchmark: SIMP density, comprehensive responses, manufacturing constraints, lattice; OptiStruct is the reference industrial TO solver | Batch / scriptable |
| **Altair Inspire** | Designer-facing TO | Fast concept TO + geometry reconstruction (PolyNURBS) + re-analysis in one GUI | GUI-led |
| **Abaqus / Tosca (Topology & Shape)** | Commercial (SIMCENTER/Dassault) | Tosca Structure: density (SIMP) topology + shape/sizing; non-design regions, member size, symmetry, casting/AM constraints; couples to Abaqus solver | Batch / scriptable |
| **Simcenter (Siemens) TO** | Commercial FE-integrated | Topology/lattice within Simcenter 3D / NX; generative + AM workflow | GUI + scripting |
| **nTop (nTopology)** | Implicit-modeling / field-driven | Lattice & implicit TO, field-driven design, AM-native; excels at lattices and large-scale implicit geometry | Strong API / **headless** |
| **MSC Apex Generative Design** | Generative / AM | Topology-driven generative design oriented to AM | GUI-led |
| **ToPy** (open-source, Python) | Open-source engine | SIMP 2D/3D minimum-compliance + variants from a problem file | **Fully headless / scriptable** |
| **Sigmund 99-line / `top88.m` (88-line) / `top3d`** | Open-source reference | The canonical MATLAB SIMP+OC (and density-filter) baselines | Scriptable |
| **`topopt` family / PETSc large-scale / FEniCS-based** | Open-source / research | Large-scale (millions of elements), level-set, stress, MMA-driven research codes | Headless |

**Vendor-neutral framing.** All major FE suites now ship integrated TO with manufacturing constraints and a reconstruct→re-analyze loop; the open-source 88-line / ToPy stack is the right way to *learn* and to *automate* without a license. **No tool removes the §9 discipline** — every one of them outputs a concept that must be re-interpreted and re-verified. **[VERIFIED-web]**

---

## 9. THE DISCIPLINE — a topology result is a concept, not a part

This is the section that matters most, and it is the same **solve-vs-predict** rule the rest of the skill enforces, specialized to TO.

**A raw TO result is not a validated structure.** It is a **density field on the design mesh** with three properties that *disqualify it from any engineering claim as-is*:
1. **It carries the modeling artifacts of the optimization** — residual gray elements, jagged/staircased "boundaries" that are mesh-faceted not real surfaces, possibly thin one-node hinges, and (with aggregation) only an **approximate** stress measure (§6.1).
2. **The SIMP/RAMP "material" is an interpolation, not a real constitutive model** — the penalized intermediate-density stiffness is a mathematical device; stresses/strains read off the density field are **not** trustworthy engineering values.
3. **It was solved on the design mesh for the optimization objective**, not meshed or converged for accurate stress/displacement of the *actual* geometry.

**The mandatory workflow:**

```
TO run  →  INTERPRET (extract/threshold the layout, read the load path)
        →  RECONSTRUCT clean CAD (smooth surfaces / PolyNURBS / implicit / hand-CAD;
              honor manufacturing & restore frozen interfaces)
        →  RE-MESH the reconstructed geometry to a proper analysis mesh
        →  RE-SOLVE the real BCs/loads on that mesh
        →  MESH-CONVERGENCE study (the part now has real geometry → real
              stress concentrations at fillets/holes that the design mesh never had)
        →  VERIFY against requirements (stress, displacement, frequency, buckling,
              fatigue) — only NOW is an ENGINEERING/SIGNOFF claim admissible.
```

**Why re-solve is non-negotiable.** Reconstruction **changes the geometry** (you smoothed staircases, added fillets, restored interfaces, applied draw/overhang) — so the reconstructed part is a **different structure** from the density field. Its real stress field, especially **stress concentrations at the new fillets and holes**, simply **did not exist** in the TO model and **must be re-computed and mesh-converged** (a true re-entrant corner is a singularity — see `meshing-convergence.md`). A reconstructed TO part routinely shows peak stresses well above what the aggregated TO constraint implied. **Treat the TO compliance/stress numbers as a *design indicator*, never as the verified result.**

**Honesty gates for any TO deliverable** (mirrors `ml-surrogates-and-rom.md` §7):
- **Concept-not-part gate:** never present the raw TO image/field as the analyzed part; the deliverable is the **re-solved, mesh-converged reconstruction**.
- **Length-scale gate:** state r_min (and the projection β schedule); a result produced without a length scale is **mesh-dependent and invalid** — show the mesh-independence (§5.2).
- **Constraint-fidelity gate:** an *aggregated* stress/buckling constraint controls an **approximation** — report the **true local peak** from the verified solve, not the aggregate.
- **Manufacturing gate:** state the assumed **process and its constraints** (draw vs. overhang, min/max size, frozen regions) and the **performance cost** they imposed; if none were applied, say the result may be unbuildable.
- **Load-case gate:** state every load case optimized; flag single-load designs as **fragile off-design** (§6.5).
- **Local-minimum honesty:** report the result as "a good design from this start/parameters," not "the global optimum" (§5.3).
- **Agent/autonomy note:** the TO run, reconstruction scripting, re-mesh, and re-solve are **AGENT-HEADLESS** (scriptable). **Accepting the reconstructed design and the engineering sign-off remain HUMAN-JUDGMENT** — idealization adequacy, manufacturing choice, accepting the local optimum, and the final claim are not delegated to the optimizer.

---

## See also

- `advanced-methods.md` §4.1 — the three optimization types and the **shape-optimization** deep-cut (stress-concentration relief: fillet/notch/hole reshaping, minimum-radius & mesh-converged-hotspot rules); §4.2 — the topology **instability-control checklist** (this file is its expansion); §4.3 — **DOE→surrogate→optimize** (the metamodel route used to make many-evaluation TO/shape loops affordable); §4.4 — model updating / inverse ID.
- `ml-surrogates-and-rom.md` §7 — the **solve-vs-predict / validity-envelope honesty gates** that §9 here specializes; **generative-design** AI surrogates that propose layouts (still concepts, still re-solved).
- `meshing-convergence.md` — the **mesh-convergence / GCI** study and the **sharp-corner singularity** caveat that the §9 re-solve depends on.
- `vv-uq.md` — verification & validation discipline behind "calibration/optimization ≠ validation."

## SOURCES

Foundational books & surveys
- M.P. Bendsøe & O. Sigmund, *Topology Optimization: Theory, Methods, and Applications* (Springer, 2nd ed. 2003) — the standard reference.
- M.P. Bendsøe & N. Kikuchi, "Generating optimal topologies in structural design using a homogenization method," *CMAME* 71(2):197–224 (1988) — the homogenization origin of TO.
- M.P. Bendsøe, "Optimal shape design as a material distribution problem," *Struct. Optim.* 1:193–202 (1989) — SIMP density approach.
- O. Sigmund & J. Petersson, "Numerical instabilities in topology optimization: a survey on procedures dealing with checkerboards, mesh-dependencies and local minima," *Struct. Optim.* 16:68–75 (1998). https://link.springer.com/article/10.1007/BF01214002

The reference codes
- O. Sigmund, "A 99 line topology optimization code written in Matlab," *Struct. Multidisc. Optim.* 21:120–127 (2001). https://www.topopt.mek.dtu.dk/Apps-and-software/A-99-line-topology-optimization-code-written-in-MATLAB
- E. Andreassen, A. Clausen, M. Schevenels, B.S. Lazarov & O. Sigmund, "Efficient topology optimization in MATLAB using 88 lines of code," *Struct. Multidisc. Optim.* 43:1–16 (2011). https://www.topopt.mek.dtu.dk/Apps-and-software/Efficient-topology-optimization-in-MATLAB
- ToPy — open-source SIMP topology optimization (Python). https://github.com/williamhunter/topy

Interpolation: SIMP vs RAMP
- M. Stolpe & K. Svanberg, "An alternative interpolation scheme for minimum compliance topology optimization (RAMP)," *Struct. Multidisc. Optim.* 22:116–124 (2001). https://link.springer.com/article/10.1007/s001580100129
- G.I.N. Rozvany, "A critical review of established methods of structural topology optimization," *Struct. Multidisc. Optim.* 37:217–237 (2009).

Optimizers: OC & MMA
- K. Svanberg, "The method of moving asymptotes — a new method for structural optimization," *IJNME* 24:359–373 (1987). https://onlinelibrary.wiley.com/doi/10.1002/nme.1620240207
- K. Svanberg, "A class of globally convergent optimization methods based on conservative convex separable approximations (GCMMA)," *SIAM J. Optim.* 12(2):555–573 (2002).
- (Optimality Criteria as used in the 99-/88-line codes; see Bendsøe & Sigmund book, Ch. 1.)

Filtering, length scale, projection, robust
- O. Sigmund, "Morphology-based black and white filters for topology optimization," *Struct. Multidisc. Optim.* 33:401–424 (2007).
- B. Bourdin, "Filters in topology optimization," *IJNME* 50:2143–2158 (2001).
- T.E. Bruns & D.A. Tortorelli, "Topology optimization of non-linear elastic structures and compliant mechanisms," *CMAME* 190:3443–3459 (2001) (density filter).
- J.K. Guest, J.H. Prévost & T. Belytschko, "Achieving minimum length scale in topology optimization using nodal design variables and projection functions," *IJNME* 61:238–254 (2004) (Heaviside projection).
- F. Wang, B.S. Lazarov & O. Sigmund, "On projection methods, convergence and robust formulations in topology optimization," *Struct. Multidisc. Optim.* 43:767–784 (2011) (robust eroded/dilated, two-sided length scale).

Stress, buckling, frequency
- P. Duysinx & M.P. Bendsøe, "Topology optimization of continuum structures with local stress constraints," *IJNME* 43:1453–1478 (1998).
- G. Cheng & X. Guo, "ε-relaxed approach in structural topology optimization," *Struct. Optim.* 13:258–266 (1997) (singularity / relaxation).
- C. Le, J. Norato, T. Bruns, C. Ha & D. Tortorelli, "Stress-based topology optimization for continua," *Struct. Multidisc. Optim.* 41:605–620 (2010) (p-norm / regional aggregation).
- N.L. Pedersen, "Maximization of eigenvalues using topology optimization," *Struct. Multidisc. Optim.* 20:2–11 (2000) (repeated eigenvalues / localized modes).
- X. Gao & H. Ma, "Topology optimization of continuum structures under buckling constraints," *Comput. Struct.* 157:142–152 (2015).

Level-set, phase-field, multiscale/lattice
- G. Allaire, F. Jouve & A.-M. Toader, "Structural optimization using sensitivity analysis and a level-set method," *J. Comput. Phys.* 194:363–393 (2004). https://www.sciencedirect.com/science/article/pii/S0021999103004873
- M.Y. Wang, X. Wang & D. Guo, "A level set method for structural topology optimization," *CMAME* 192:227–246 (2003).
- B. Bourdin & A. Chambolle, "Design-dependent loads in topology optimization" / phase-field approaches, *ESAIM:COCV* 9:19–48 (2003).
- J.P. Groen & O. Sigmund, "Homogenization-based topology optimization for high-resolution manufacturable microstructures (de-homogenization)," *IJNME* 113:1148–1163 (2018).

Manufacturing & AM constraints
- M. Langelaar, "An additive manufacturing filter for topology optimization of print-ready designs," *Struct. Multidisc. Optim.* 55:871–883 (2017) (overhang / self-support, ≈45° angle).
- J.K. Guest & M. Zhou, casting/extrusion/symmetry manufacturing-constraint formulations; Altair OptiStruct & Abaqus Tosca manufacturing-constraint documentation (min/max member, draw direction, symmetry, extrusion) [DOCS-ONLY].
- A.T. Gaynor & J.K. Guest, "Topology optimization considering overhang constraints," *Struct. Multidisc. Optim.* 54:1157–1172 (2016).

Tools (vendor documentation [DOCS-ONLY])
- Ansys Mechanical Topology Optimization; Altair OptiStruct / Inspire; Dassault/SIMULIA Abaqus Topology Optimization Module (Tosca Structure); Siemens Simcenter / NX topology & generative; nTopology (nTop) implicit/lattice; MSC Apex Generative Design — vendor product documentation.
