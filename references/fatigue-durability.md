# Fatigue & durability — practitioner-grade reference

Scope: the **fatigue / durability discipline** — how you turn FE stresses (or a stress PSD from a random-vibration run) into a *life* (cycles or hours to crack initiation) and an acceptance margin. Covers **stress-life (S-N)**, **strain-life (ε-N)**, **notch correction**, **cumulative damage / rainflow**, **multiaxial critical-plane**, **vibration / spectral (frequency-domain) fatigue**, **thermo-mechanical fatigue**, and the **FKM analytical assessment**. Cross-verified against ASTM E466/E606/E1049, SAE fatigue/Neuber technical papers, the FKM Guideline, the Dirlik / Tovo-Benasciutti spectral literature, and standard durability texts. Numbers are industry rules of thumb / standard defaults; confirm against your material data and the governing code. Citations are bracketed `[n]` → SOURCES at end.

The governing rule for the whole topic: **fatigue is a *local* phenomenon driven by a *load history*, not a single peak stress.** A static check asks "does the worst stress exceed an allowable once"; a fatigue check asks "how much damage does the *whole sequence* of stresses do at the *initiation site*". Three things therefore dominate every fatigue result and every fatigue argument: (1) the **material's cyclic** behaviour (an S-N or ε-N curve, *not* the monotonic curve), (2) the **mean stress** of each cycle, and (3) the **counting** of the variable history into discrete cycles before any damage is summed. Get those three right before arguing about the FE mesh.

This file is the **durability post-processing** half of the structural-integrity set. The **constitutive** half (cyclic plasticity / Chaboche, ratcheting fits) lives in `material-modeling.md`; the **crack-propagation** half (Paris / NASGRO da/dN, ΔK, closure) lives in `fracture-mechanics.md`; **weld fatigue** (nominal / hot-spot / effective-notch, IIW FAT classes, t×t mesh, 0.4t/1.0t extrapolation) lives in `mechanical-connections.md` §5.2 — this file **cross-links, it does not duplicate** any of those.

---

## 0. Mental model and the two regimes

A fatigue assessment is a pipeline:

> **FE stress (or stress PSD) → local stress/strain at the hot spot → cycle counting → per-cycle damage from a material curve with a mean-stress correction → damage summation → life & margin.**

Pick the material model by **how much plasticity** the hot spot sees:

| Regime | Driver | Life | Method | Curve |
|---|---|---|---|---|
| **High-cycle fatigue (HCF)** | mostly **elastic**, stress-controlled | ≳10⁴–10⁵ cycles | **Stress-life (S-N)** | σ_a vs N (Basquin) |
| **Low-cycle fatigue (LCF)** | local **plastic** strain, strain-controlled | ≲10⁴ cycles | **Strain-life (ε-N)** | ε_a vs N (Coffin-Manson + Basquin) |

The split is the **transition life** 2N_t where the elastic and plastic strain contributions are equal (§3). Notch roots, weld toes, and thermal-cycled parts yield locally even when the nominal field is elastic → they are **ε-N / notch-correction** problems even at long life. Truly elastic, smooth, vibration-driven parts are **S-N / spectral** problems.

**Time-domain vs frequency-domain.** If you have a load *time history*, count cycles directly (rainflow, §4). If the load is a stationary random *process* given as a PSD (e.g. base-excitation random vibration), use **spectral fatigue** (§6) — it gives the damage from the PSD without ever generating a time series, orders of magnitude cheaper. The two routes converge for the same process; spectral methods *are* statistical models of what rainflow would count.

---

## 1. Stress-life (S-N) — HCF, mainly elastic

### Basquin curve & the endurance limit

The fully-reversed (R = −1) S-N relation is the **Basquin** power law:

> **σ_a = σ′_f · (2N_f)^b**

σ_a = stress amplitude, 2N_f = reversals to failure, **σ′_f** = fatigue strength coefficient (≈ true fracture strength), **b** = fatigue strength exponent (typically **−0.05 … −0.12** for metals). On log-log axes this is a straight line — the basis of every S-N plot. (S-N data is generated per ASTM **E466** for force-controlled constant-amplitude tests.) [1][7]

**Endurance / fatigue limit S_e.** Many **ferritic (BCC) steels** show a true **knee** below which (constant amplitude) life is effectively infinite — historically **S_e ≈ 0.5·S_ut**, capped near **~700 MPa** for high-strength steels (the ratio saturates). **Aluminium, austenitic stainless, copper, most non-ferrous alloys — and many Ti alloys — show *no* sharp endurance limit** — the curve keeps falling, so define a **runout** stress at a reference life (10⁷–5×10⁸ cycles) instead. **Do not assume a knee for Al or Ti** unless your own data shows a clear plateau. Under variable-amplitude loading the knee is also largely *erased* (small cycles below it still damage once larger cycles have started cracks → use Miner-Haibach, §4). [1][8]

### Marin factors — test bar → real component

A polished R.R. Moore test bar S′_e is not a flange. Correct it with **Marin modifying factors**:

> **S_e = k_a·k_b·k_c·k_d·k_e·k_f · S′_e**

| Factor | Meaning | Typical effect |
|---|---|---|
| **k_a** surface finish | as-machined/forged/corroded rougher than polished | k_a = a·S_ut^b (e.g. ground vs hot-rolled vs forged); can be **<0.5** for forged/corroded |
| **k_b** size | larger section → more flawed volume, lower gradient benefit | ~1 for small/axial, **~0.7–0.9** for large rotating-bending |
| **k_c** load type | axial vs bending vs torsion | **~0.85 axial, ~0.59 torsion** (vs bending = 1) |
| **k_d** temperature | strength drift with T | from S_ut(T)/S_ut(20 °C) |
| **k_e** reliability | scatter → design percentile | **0.90 (50 %)… 0.70 (99.9 %)** |
| **k_f** misc | residual stress, plating, fretting, corrosion | case-specific knock-down |

The single biggest real-world knock-down is usually **surface** (k_a) and **mean/residual stress**; shot-peening etc. enter as a beneficial compressive residual (raises effective S_e). [1]

---

## 2. Mean-stress correction (the most error-prone step)

Real cycles have a non-zero **mean stress σ_m** (or load ratio R = σ_min/σ_max); S-N data is usually R = −1. A mean-stress model maps **(σ_a, σ_m)** to an **equivalent fully-reversed amplitude σ_ar** that you then look up on the R = −1 curve. **Tensile mean is damaging; compressive mean is beneficial.** Choosing the wrong model is a routine factor-of-several life error.

| Model | Equation (failure locus / equivalent amplitude) | Character / when |
|---|---|---|
| **Goodman** (line) | σ_a/S_e + σ_m/S_ut = 1 ⇒ σ_ar = σ_a/(1 − σ_m/S_ut) | simple, **conservative** for ductile; default for **brittle/HCF**, cast iron |
| **Gerber** (parabola) | σ_a/S_e + (σ_m/S_ut)² = 1 | **best mean fit for ductile steels**, less conservative; symmetric in σ_m so **must guard against compressive mean** |
| **Soderberg** | σ_a/S_e + σ_m/S_y = 1 | **most conservative** (uses yield S_y); guarantees no yielding but over-designs |
| **Morrow** | σ_a/(σ′_f − σ_m) = (2N)^b ⇒ σ_ar = σ_a/(1 − σ_m/σ′_f) | uses the **true fatigue strength σ′_f**; good for **steels**, strain-life-consistent (pairs with ε-N) |
| **SWT (Smith-Watson-Topper)** | σ_ar = √(σ_max·σ_a) = √(σ_a·(σ_a+σ_m)) | **no extra material constant**; damage parameter σ_max·ε_a; good general metal default, esp. where σ_max governs (tensile/brittle) |
| **Walker** | σ_ar = σ_max^(1−γ)·σ_a^γ = σ_max·((1−R)/2)^γ | **best when a fitted γ is available** (γ ≈ 0.5 ≈ SWT; γ from R-ratio test data); the modern preferred fit |

**Compressive-mean cap (do this).** Gerber and SWT can wrongly predict benefit (or be undefined) for **σ_m < 0**. The standard practical rule: **clip the benefit** — for σ_m ≤ 0 use σ_ar = σ_a (treat as fully-reversed; take no, or limited, credit for compression). Goodman/Morrow already taper toward this. Over-crediting compressive mean is a common non-conservative trap (residual-stress fields flip sign through the section). [1][7]

**Selection heuristic:** brittle / weld / unknown ductility → **Goodman**; ductile steel with good data → **Gerber** or **Walker**; consistency with a strain-life run → **Morrow** or **SWT**; default if you must pick one → **SWT** (no extra constant).

---

## 3. Strain-life (ε-N) — LCF, notch roots, thermal cycling

When the hot spot yields each cycle, *strain* (not stress) is the controlling variable. Total strain amplitude is **elastic (Basquin) + plastic (Coffin-Manson)**:

> **ε_a = (σ′_f/E)·(2N_f)^b + ε′_f·(2N_f)^c**

σ′_f, b as in §1; **ε′_f** = fatigue ductility coefficient (≈ true fracture ductility), **c** = fatigue ductility exponent (typically **−0.5 … −0.7**). (ε-N data per ASTM **E606**, strain-controlled.) [1][2][7]

**Transition life.** The crossover **2N_t** where elastic term = plastic term marks LCF (left, plastic-dominated, ductility wins) vs HCF (right, elastic-dominated, strength wins). Below 2N_t use ε-N; well above it ε-N collapses to Basquin and S-N suffices.

**Cyclic stress-strain curve (CSSC).** Metals **cyclically harden or soften** — the stabilized hysteresis loop differs from the monotonic curve. The CSSC is **σ_a = K′·(ε_pa)^n′** (cyclic strength K′, cyclic hardening exponent n′). **Always use cyclic properties for fatigue**, not the monotonic curve. Soft-annealed metals usually cyclically *harden*; cold-worked metals *soften* (a hazard — they get weaker in service). (See `material-modeling.md` for the Chaboche/cyclic-plasticity constitutive fit and ratcheting.) [7]

**Masing behaviour.** For Masing materials the stable **hysteresis loop is the CSSC scaled ×2** (double stress and strain axes). This lets you build the loop for any reversal pair from the CSSC + the memory rules — the basis of incremental notch/rainflow strain reconstruction. Non-Masing materials need a transient correction.

**Mean stress in ε-N.** Use **Morrow** (subtract σ_m from σ′_f in the elastic term: ε_a = ((σ′_f − σ_m)/E)(2N)^b + ε′_f(2N)^c) or **SWT** (σ_max·ε_a = (σ′_f²/E)(2N)^2b + σ′_f·ε′_f(2N)^(b+c)). SWT is preferred for tensile-mean-sensitive / brittle materials; Morrow for ductile steels. **This ε-N + mean route is how you do weld-toe and notch-root life when local yielding occurs** (with the notch correction below).

---

## 4. Notch correction — elastic FE → local elastic-plastic

The FE elastic stress at a notch overstates the *real* (yield-limited) stress and understates the strain. You must convert the elastic prediction to the true local **(σ, ε)** before entering the ε-N curve. Start from the **elastic stress concentration K_t** (geometry, from the FE field or a chart) or, better, the **fatigue notch factor K_f** which accounts for notch-root stress-gradient support:

> **K_f = 1 + q·(K_t − 1)**, notch sensitivity **q = 1/(1 + a/r)** (**Peterson**) or **q = 1/(1 + √(β/r))** (**Neuber**), r = notch radius, a/β = material length.

Then localize the elastic pseudo-stress S onto the CSSC by one of two energy rules:

| Rule | Statement | Character |
|---|---|---|
| **Neuber** | K_t² = K_σ·K_ε ⇒ **σ·ε = (K_t·S)²/E** (rectangular-hyperbola ∩ CSSC) | the classic; **more conservative**; best for plane-stress / thin / surface notches |
| **Glinka (ESED)** | equal **strain-energy density** at the notch root: ∫σ dε (local) = (K_t·S)²/2E | **less conservative than Neuber**; better for **plane-strain / bulk yielding / blunter notches** |

Solve the chosen rule simultaneously with the CSSC (and the Masing loop for unloading) to get the local σ, ε **per reversal**; apply for every cycle of a variable history. Substituting K_f for K_t folds in the gradient support. **Use the local strain amplitude (with mean) in the ε-N equation**, not the elastic FE stress. [4][7]

> **Why this matters:** a peak FE stress at a fillet that reads "above ultimate" is *not* a static failure and *not* a usable fatigue stress — it is an elastic artifact that Neuber/Glinka redistributes into a finite local strain. Feeding the raw elastic peak into S-N is a classic over-conservative blunder; feeding it without notch correction into ε-N is meaningless.

---

## 5. Cumulative damage — rainflow + Miner

### Rainflow counting (ASTM E1049)

A variable-amplitude history must be decomposed into **closed hysteresis loops** = discrete cycles before any damage law applies. The standard is **rainflow counting** (ASTM **E1049**), implemented as the **4-point algorithm** (or the equivalent **reservoir** method). [3][6]

- First **extract peaks/valleys** (turning points) — discard non-reversal points.
- **4-point rule:** examine four consecutive points (S1,S2,S3,S4); the inner range |S2−S3| is counted as a **closed cycle** if it is **≤** both adjacent ranges (|S1−S2| and |S3−S4|); remove S2,S3 and continue. Leftover un-closed swings form the **residue**, counted as **half-cycles** (or closed by repeating the history / hysteresis-memory closure).
- Each counted cycle yields a **(range, mean)** or **(σ_a, σ_m)** pair → mean-correct (§2) → look up N_i.
- **Order independence** is the point: rainflow recovers the same closed loops the material would actually trace (material memory), regardless of sequence — *but* it discards sequence/load-interaction effects (Miner is therefore order-blind; see limits below).

**Rainflow matrices.** Output a **from-to (Markov) or range-mean matrix** for spectral comparison and for damage editing. **Never sum damage without counting first** — summing instantaneous stresses or using max-min range only is wrong.

### Palmgren-Miner damage summation

> **D = Σ (n_i / N_i)**, failure at **D = 1**.

n_i = applied cycles at level i, N_i = allowable cycles (from S-N/ε-N at that mean-corrected amplitude). [1][5]

- **Scatter / design value.** Linear Miner ignores sequence and load-interaction → real failures scatter; design to **D_crit = 0.2–0.5** (automotive/ground vehicle often 0.5; aerospace/critical lower). Test correlation routinely lands D anywhere ~0.3–3.
- **Miner-Haibach (modified slope) — important under broadband loading.** Standard Miner gives **zero** damage to cycles below the endurance knee, but once cracks initiate those small cycles *do* propagate damage. **Haibach** extends the S-N line below the knee with a **shallower slope k′ = 2k − 1** (k = slope above the knee) instead of a flat cutoff. Use it (or "elementary Miner" = single slope all the way down, even more conservative) whenever the spectrum has many small cycles below S_e — the usual case for random vibration. Choosing flat-cutoff Miner there is a classic non-conservative error. [1][8]
- **Damage editing.** Remove small, non-damaging cycles (below a fraction of the endurance limit) to shorten test/sim histories — but only *after* checking they are below the Haibach-extended line, not the flat knee.

---

## 6. Vibration / spectral (frequency-domain) fatigue — the random-vibration bridge

**This section is the explicit bridge from a random-vibration FE run to a fatigue life.** When the loading is a **stationary, ergodic, Gaussian random process** (broadband base excitation, acoustic, road, flow-induced), generating and rainflow-counting long time histories is wasteful. Instead, run a **random-vibration (PSD) analysis** (see `dynamics-nvh-acoustics.md` §6) to get the **stress response PSD G(f)** at the hot spot, then a **spectral fatigue method** returns the rainflow-range PDF and the damage **directly from the PSD** — typically orders of magnitude cheaper than time-domain, and the only practical route for long-duration random loads. [9][10][11]

### From stress PSD to spectral moments

The whole method rests on the **spectral moments** of the one-sided stress PSD G(f) (f in Hz, or use ω = 2πf):

> **m_k = ∫₀^∞ f^k · G(f) df**, for **k = 0, 1, 2, 4**.

From these:
- **m_0** = variance of stress ⇒ **RMS stress σ_rms = √m_0** (zero-mean process).
- **Rate of zero up-crossings (≈ mean frequency):** **ν_0 = √(m_2/m_0)** (Hz).
- **Rate of peaks:** **ν_p = √(m_4/m_2)** (Hz).
- **Irregularity factor:** **γ = ν_0/ν_p = m_2/√(m_0·m_4)**, with **0 < γ ≤ 1**. **γ → 1 = narrow-band** (one peak per zero-crossing, sinusoid-like); **γ → 0 = wide-band** (many small peaks between crossings). γ (and the bandwidth parameter **α_2 = γ**, or **ε = √(1−γ²)**) selects the method. [10][11]

**Verification first:** the process must be **stationary and Gaussian** (check kurtosis ≈ 3; non-Gaussian / non-stationary loads need a kurtosis correction or time-domain). The PSD must **capture all participating modes** — confirm the modal **effective mass ≥ 80–90 %** in the excited direction and the PSD upper frequency covers the modes that respond (the effective-mass gate from `solver-numerics.md` §2 / `dynamics-nvh-acoustics.md` §6). A missed mode = missed damage.

### Methods — pick by bandwidth

For each method the **probability density of rainflow stress ranges p(S)** (or directly the m-th moment of ranges) feeds the damage integral below.

| Method | Best for | Note |
|---|---|---|
| **Narrow-band (Rayleigh)** | γ ≈ 1 | Ranges are **Rayleigh-distributed**; peak rate = ν_0. **Conservative upper bound** for wide-band (over-counts large ranges) — the safe first cut. [10] |
| **Steinberg 3-band** | quick electronics / Gaussian | Approximates by **3 stress bins at 1σ/2σ/3σ occurring 68.3 % / 27.1 % / 4.33 %** of the time; clips at 3σ. Simple hand/spreadsheet check; can be unconservative if energy beyond 3σ matters. [11] |
| **Wirsching-Light** | wide-band | Empirical **rainflow-correction factor λ(α,m)** applied to the narrow-band damage (λ ≤ 1) — removes narrow-band conservatism cheaply. [10] |
| **α_0.75 (Ortiz-Chen / bandwidth)** | wide-band | Correction based on the **α_0.75 = m_1.5/√(m_0·m_3)** bandwidth parameter. [10] |
| **Dirlik** | **general wide-band — the de-facto standard** | Empirical closed-form **p(S)** = one exponential + two Rayleigh terms, fitted to extensive simulation; uses m_0,m_1,m_2,m_4. **Very accurate across bandwidths**; the default production choice. [9][10] |
| **Tovo-Benasciutti** | wide-band | Damage = a **weighted blend** of narrow-band and range-counting bounds, weight b(α_1,α_2) from spectral moments; **accuracy comparable to Dirlik**, theoretically cleaner. [9][10] |
| **Zhao-Baker, Lalanne, Petrucci-Zuccarello** | alternatives | Other fitted PDFs / bandwidth models; use if validated for your spectra. [10] |

(Open-source `FLife` and most commercial durability tools implement Dirlik / Tovo-Benasciutti / NB / Wirsching-Light / α_0.75 / Zhao-Baker — useful for cross-checking a hand calc.) [12]

### Spectral damage rate

With a Basquin S-N curve **N·S^m = C** (slope m, intercept C) and a method's range PDF p(S), the **expected damage per unit time** is:

> **E[D]/T = (ν_p / C) · ∫₀^∞ S^m · p(S) dS = (ν_p / C) · E[S^m]**

i.e. damage rate = (peak rate)/(curve intercept) × the **m-th moment of the rainflow-range distribution**. Multiply by exposure time T for total D; failure at D = D_crit. For **narrow-band** this has a closed form via the Gamma function: **E[D]/T = ν_0·(2√2·σ_rms)^m·Γ(1+m/2)/C**. **Dirlik / Tovo-Benasciutti** replace the Rayleigh moment with their wide-band p(S), giving far less conservative (more accurate) life. Combine multiple load cases / mission segments by **summing damage** (Miner across blocks). [9][10][11]

> **The bridge, stated plainly:** *produce the stress PSD in the random-vibration analysis (dynamics §6); fatigue it here.* The dynamics reference stops at the response PSD / 3σ stress; this section converts that PSD into cycles and a life. Quoting only a "3σ stress < allowable" margin (common in spec work) is a **static** check on a random load — it is not a fatigue life and can be badly non-conservative for long exposures or low-cycle-fraction-but-high-σ tails.

---

## 7. Multiaxial fatigue — critical-plane methods

Real hot spots see **multiaxial** stress (combined bending+torsion, biaxial weld toes, contact). A scalar equivalent (von Mises / Tresca) **fails for fatigue under non-proportional loading** — see below — so durability uses **critical-plane** criteria: search over candidate material planes for the one that **maximizes a damage parameter**; that plane's parameter drives the life and predicts the crack-plane orientation.

| Criterion | Damage parameter (on the critical plane) | Best for |
|---|---|---|
| **Findley** | **(τ_a + k·σ_n,max)** maximized over planes | **HCF**, normal-stress-sensitive metals; endurance assessment |
| **Brown-Miller** | **(Δγ_max/2 + S·Δε_n)** (shear + normal strain on max-shear plane) | **LCF ductile** metals; classic critical-plane ε-N |
| **Fatemi-Socie** | **(Δγ_max/2)·(1 + k·σ_n,max/σ_y)** | **shear-dominated LCF**, captures non-proportional hardening via σ_n,max; widely used for ductile metals |
| **SWT (critical-plane)** | **σ_n,max·Δε_n/2** on the max-normal-strain plane | **tensile / brittle** crack initiation (Mode I) |
| **Dang Van** | mesoscopic **τ(t) + a·σ_h(t) ≤ b** (instantaneous shear + hydrostatic) | **HCF endurance / infinite-life** screening; whole load path, not a counted cycle |

**Proportional vs non-proportional (NP).** Under **proportional** loading the principal-stress *directions are fixed* — a scalar equivalent stress with a sign convention can work, and the critical plane is stationary. Under **non-proportional** loading (e.g. bending and torsion out of phase) the **principal axes rotate during the cycle**, which (a) activates more slip systems → **additional cyclic hardening** (extra damage not in the uniaxial curve), and (b) makes any single equivalent-stress amplitude ambiguous. **Von-Mises-equivalent fatigue is invalid for NP loading** — it can be non-conservative by large factors. **Prove proportionality before using an equivalent-stress shortcut**; if NP, use a critical-plane criterion (Fatemi-Socie / Brown-Miller capture NP hardening through the normal-stress term). Detect NP via the rotation of the principal directions or a non-proportionality factor over the cycle. [4]

---

## 8. Thermo-mechanical fatigue (TMF) & creep-fatigue

When **temperature cycles together with mechanical strain** (turbine blades/disks, exhaust, power electronics, brakes), life is governed by coupled **fatigue + creep + oxidation** — far below isothermal LCF life.

- **In-phase (IP):** maximum temperature coincides with **maximum (tensile) strain** → **creep-dominated**, intergranular cavitation/cracking; tensile hold at high T relaxes and accumulates creep damage.
- **Out-of-phase (OP):** maximum temperature at **minimum (compressive) strain** (typical for externally heated, internally constrained parts) → **oxidation/cracking-dominated**; compressive yielding hot then tensile cold cracks the oxide. **OP is usually the more damaging / life-limiting** case for many superalloys — assess both.
- **Constitutive needs:** temperature-dependent cyclic plasticity (visco-plastic Chaboche, `material-modeling.md`) + creep + an oxidation/damage model (Sehitoglu / Neu-Sehitoglu damage partitioning).
- **Creep-fatigue damage summation:** total damage **D = D_fatigue + D_creep ≤ D_allow**, with D_fatigue = Σn/N_f (ε-N) and D_creep = Σt/t_r (time-fraction, Robinson) or ductility-exhaustion / strain-range partitioning. Codes give the interaction envelope (the **bilinear D_f–D_c diagram** in **ASME III Div 1 Subsection NH / RCC-MR**); the allowable corner is well below (1,1). Sequence and hold time matter (load-then-hold). (Cross-ref creep in `material-modeling.md`; relaxation in `specialized-analyses.md`.) [13]

---

## 9. FKM Guideline — analytical component assessment

The **FKM Guideline "Analytical Strength Assessment of Components"** (German FKM/VDMA, machinery/automotive certification) is a structured, code-like procedure to take **FE (or nominal) stresses to a static and a fatigue degree-of-utilization** with **traceable, component-specific factors** — a defensible alternative to an ad-hoc S-N calc. Outline: [14]

1. **Material strength** from standardized values (with technological size factor, temperature factor).
2. **Design factors:** **stress-gradient / support factor n_χ** (notch support — high gradient is less damaging, the rational counterpart of K_f), **surface roughness K_R**, surface-treatment, protective-layer factors.
3. **Mean-stress sensitivity M** (material-dependent slope of the Haigh diagram) sets the mean-stress correction by load case and mean-stress regime (4 regimes by stress ratio).
4. **Cyclic strength / component S-N** built from the above; variable amplitude via a spectrum and Miner (with the guideline's consequence rules).
5. **Safety factors j** scaled by **failure consequence and inspectability** (and load uncertainty).
6. **Degree of utilization a = stress / (strength / j) ≤ 1** for both static and fatigue.

Use FKM when you need a **standardized, auditable** component fatigue assessment (machine frames, pressure parts, automotive structures) rather than a research-grade ε-N/critical-plane study; it is the European industry default for general machinery. [14]

---

## 10. Verification gates (do these every fatigue run)

- **Right curve, cyclic properties.** S-N for HCF/elastic, ε-N for LCF/notch/thermal; use the **cyclic** stress-strain curve, never the monotonic; confirm R-ratio / mean basis of the data.
- **Mesh converged for the *stress that feeds the correction*** — converge the **elastic notch stress** (or use a fixed, mesh-insensitive extraction: weld **hot-spot** 0.4t/1.0t per connections §5.2, or a structural stress) — **never** the singular peak at a re-entrant corner (it never converges; like a crack tip).
- **Mean-stress model justified** by material ductility and sign of mean; **compressive-mean credit capped**.
- **Count before you sum** — rainflow (E1049) the history into cycles *before* Miner; use **Miner-Haibach** when small sub-knee cycles are present (broadband / random).
- **Multiaxial:** prove **proportionality** before any equivalent-stress shortcut; if non-proportional, use a **critical-plane** criterion (Mises-equivalent is invalid for NP).
- **Spectral:** confirm the process is **stationary & Gaussian** (kurtosis ≈ 3); confirm the PSD **captured all participating modes** (effective mass ≥ 80–90 %, dynamics §6); report which spectral method and why (narrow-band as a conservative sanity bound, Dirlik/TB for the real number).
- **Design D_crit, not D = 1** — apply the scatter/consequence margin (0.2–0.5 typical) and state it; cross-check life against any available test/field data.
- **TMF/creep-fatigue:** assess **both IP and OP**; use the code interaction diagram, not simple linear summation to (1,1).

**Top mistakes:** feeding the raw singular FE peak stress straight into S-N (gross over-conservatism) — or into ε-N without Neuber/Glinka (meaningless); assuming an endurance limit for aluminium (there isn't one); flat-cutoff Miner under broadband loading (misses sub-knee damage → non-conservative — use Haibach); summing damage without rainflow counting; over-crediting a compressive mean (sign flips through the section); using von-Mises-equivalent fatigue under non-proportional multiaxial loading; quoting a "3σ stress < allowable" margin from a random-vibration run and calling it a fatigue life (it is a static check — do the spectral-damage integral); using the monotonic instead of the cyclic stress-strain curve.

---

## 11. Condensed quick-reference

- **Regime:** elastic/HCF → **S-N** (Basquin σ_a=σ′_f(2N)^b); plastic/LCF/notch → **ε-N** (+Coffin-Manson). Split at transition life 2N_t.
- **Endurance limit:** steels/Ti have one (~0.5 S_ut, cap ~700 MPa); **Al & most non-ferrous do not** — use a runout.
- **Mean stress:** map (σ_a,σ_m)→σ_ar via **Goodman** (conservative/brittle) / **Gerber** (ductile) / **Soderberg** (yield) / **Morrow** / **SWT** (no extra constant) / **Walker** (best fit). **Cap compressive-mean credit.**
- **Notch:** elastic FE → local σ,ε via **Neuber** (K_t²=K_σK_ε, conservative) or **Glinka** (ESED, less conservative); use K_f for gradient support; feed local strain to ε-N.
- **Damage:** **rainflow (ASTM E1049, 4-point)** → cycles → mean-correct → **Miner D=Σn/N (D_crit 0.2–0.5)**; **Miner-Haibach** (slope 2k−1) for sub-knee cycles.
- **Multiaxial:** **critical-plane** (Findley HCF / Brown-Miller / Fatemi-Socie LCF / SWT-plane / Dang Van endurance); **Mises-equivalent invalid for non-proportional** loading.
- **Spectral (random vibration):** stress PSD → moments **m_0,m_1,m_2,m_4** → **ν_0=√(m_2/m_0)**, **ν_p=√(m_4/m_2)**, irregularity **γ=m_2/√(m_0 m_4)** → method (**narrow-band**=conservative, **Dirlik**=default, **Tovo-Benasciutti**, Steinberg 3-band, Wirsching-Light) → **E[D]/T=(ν_p/C)E[S^m]**. **PSD comes from dynamics §6.**
- **TMF:** IP (creep) vs OP (oxidation, often worse); **D_f+D_c≤D_allow** per ASME-NH/RCC-MR interaction diagram.
- **FKM:** standardized analytical component assessment (gradient/surface/mean-sensitivity factors, consequence-scaled safety, utilization ≤1).

---

## See also

- `dynamics-nvh-acoustics.md` §6 (**random vibration / PSD** — produces the stress PSD this file fatigues; §7 SRS; §2 prestress/effective mass) and §1 (modal completeness for spectral coverage).
- `mechanical-connections.md` §5.2 (**weld fatigue** — nominal / hot-spot / effective-notch, IIW FAT classes, t×t mesh, 0.4t/1.0t extrapolation; this file cross-links, does not duplicate it) and §4.3 (preload protects bolt fatigue).
- `material-modeling.md` (**cyclic plasticity / Chaboche**, ratcheting fits, creep models — the constitutive half of ε-N, TMF, creep-fatigue).
- `fracture-mechanics.md` (**crack *propagation*** — Paris/Forman/NASGRO da/dN=C·ΔKᵐ, ΔK_th, R-ratio/closure, EIFS/damage-tolerance — the life *after* initiation; this file covers initiation).
- `solver-numerics.md` §2 (eigensolver completeness / Sturm / effective-mass gate behind any spectral run) and §4 (transient time integration if doing time-domain durability).
- `specialized-analyses.md` (plasticity/creep relaxation; the stub this file expands).

---

## SOURCES

Reliability key: **H** = primary standard / peer-reviewed / authoritative text; **M** = reputable practitioner reference / encyclopedic, cross-checked; **L** = secondary/forum (corroborative only).

1. Standard fatigue-design texts — Basquin/Coffin-Manson, Marin factors, Goodman/Gerber/Soderberg/Morrow/SWT, Miner & Miner-Haibach (Dowling, *Mechanical Behavior of Materials*; Stephens et al., *Metal Fatigue in Engineering*; Shigley, *Mechanical Engineering Design* for Marin factors). — **H**.
2. Coffin-Manson / strain-life lineage (Coffin 1954; Manson 1953/NACA) and SAE strain-life methodology. — **H**.
3. ASTM **E1049** "Standard Practices for Cycle Counting in Fatigue Analysis" (rainflow / 4-point / reservoir). https://www.astm.org/e1049-85r17.html — **H**.
4. Multiaxial / Neuber notch correction — SAE Technical Paper **950705** (multiaxial Neuber); SAE Fatigue Design Handbook; *Multiaxial Notch Fatigue* (Susmel/ed., Woodhead). https://www.sae.org/publications/technical-papers/content/950705/ — **H**.
5. Palmgren-Miner rule (Palmgren 1924; Miner 1945, *J. Appl. Mech.*) — linear cumulative damage. — **H**.
6. Halfpenny & Kihm — "Rainflow counting & vibration/acoustic fatigue" (rainflow algorithm, spectral methods). http://www.vibrationdata.com/tutorials2/Paper_RASD2010_005_Halfpenny_Kihm.pdf — **M**.
7. ASTM **E466** (force-controlled constant-amplitude S-N test) and **E606** (strain-controlled ε-N test) — the test standards the curves key to. https://www.astm.org/e0466-21.html ; https://www.astm.org/e0606_e0606m-21.html — **H**.
8. Endurance-limit & Haibach modified-Miner (no true limit for Al/non-ferrous; Haibach slope 2k−1 below knee) — Haibach, *Betriebsfestigkeit*; FKM Guideline background. — **H**.
9. Dirlik & Tovo-Benasciutti spectral-fatigue review (history + formulae; wide-band accuracy comparison) — MDPI *Metals* 11(9):1333, 2021. https://www.mdpi.com/2075-4701/11/9/1333 — **H**.
10. Spectral / frequency-domain fatigue methods (spectral moments, irregularity factor, narrow-band/Rayleigh, Wirsching-Light, α_0.75, Dirlik, Tovo-Benasciutti) — Bishop & Sherratt, *Finite Element Based Fatigue Calculations* (NAFEMS); Dirlik (1985) PhD thesis (Univ. Warwick); nCode/MSC frequency-domain fatigue theory manuals. Orientation: Wikipedia — Vibration fatigue, https://en.wikipedia.org/wiki/Vibration_fatigue — **M**.
11. Steinberg 3-band (1σ/2σ/3σ at 68.3/27.1/4.33 %) and electronics vibration fatigue — Steinberg, *Vibration Analysis for Electronic Equipment*. — **H**.
12. **FLife** open-source spectral-fatigue library (implements Dirlik / Tovo-Benasciutti / narrow-band / Wirsching-Light / α_0.75 / Zhao-Baker / Rainflow) — LADISK. https://github.com/ladisk/FLife — **M**.
13. Creep-fatigue interaction & TMF — **ASME BPVC III Div 1 NH** / **RCC-MR** bilinear damage-interaction diagram; Sehitoglu & Neu thermomechanical-fatigue damage. — **H**.
14. **FKM Guideline** "Analytical Strength Assessment of Components in Mechanical Engineering" (FKM/VDMA) — static + fatigue assessment with stress-gradient/support, surface, mean-stress-sensitivity, and consequence-scaled safety factors. — **H**.
