# Structural Dynamics, NVH & Acoustics — Practitioner Best-Practices Brief

Scope: practitioner-grade, generalizable best practices for FEM/CAE structural dynamics, NVH, and vibro-acoustics. Numbers are rules-of-thumb cross-verified against vendor theory (Ansys/MAPDL, Simcenter/Nastran, MSC), recognized practitioners (Tom Irvine / vibrationdata, W.P. Rodden), and spacecraft standards (NASA-STD/HDBK, ECSS). Treat every number as a default to be confirmed against the governing spec for your program, not a law of nature.

---

## 0. Mental model and workflow order

Almost every dynamics result is built on a **modal solve**, so a wrong modal basis silently poisons everything downstream (harmonic, random, transient, SRS, flutter). The canonical chain:

1. **Modal** (free or prestressed) → natural frequencies, mode shapes, effective mass.
2. Check **cumulative effective mass** and **frequency-range coverage**; add **residual vectors** if force/stress outputs matter.
3. Choose response analysis: **harmonic (frequency response)**, **random (PSD)**, **transient**, or **SRS/shock**.
4. Apply correct **damping** model and **base-excitation** technique.
5. Post-process to engineering quantities (stress, GRMS, RMS displacement, SPL, sound power, TL, flutter speed).

Top systemic mistake: trusting a response analysis whose underlying modal basis is truncated or under-resolved. Second: applying damping inconsistently between model and test.

---

## 1. Modal analysis

**Mode count — effective mass criterion.** Include enough modes so the **cumulative effective modal mass reaches ≥ 80–90 %** of total mass in *each* excitation direction (translational and, for base/rotational excitation, rotational). 90 % is the common acceptance gate; 80 % is a frequently used minimum. A mode contributing < ~1–2 % of effective mass can usually be ignored for response, but not necessarily for local stress.

**Mode count — frequency-range criterion.** Extract modes up to **~1.5× (commonly 1.5–2×) the maximum excitation frequency**. The factor gives the modal basis enough "headroom" so modes just above the band still contribute correctly to in-band response. For pyroshock / high-frequency localized excitation you typically need far more modes (the spectrum is broadband to kHz).

**Modal participation factor vs effective mass.** The participation factor Γ measures how strongly a unit base motion excites a mode; **effective mass = Γ²** (for mass-normalized modes) and sums to the rigid-body mass — this is why effective mass, not the participation factor itself, is the convergence metric.

**Residual vectors / modal truncation augmentation.** Mode-superposition truncates high-frequency modes; this is fine for displacement but produces **errors in force and stress** because the missing modes carry static (residual) flexibility. Fix by augmenting the modal basis with **residual vectors** (static shapes from the applied/enforced loads, orthogonalized against the retained modes and discarded if not independent): MSC/NX Nastran `PARAM,RESVEC,YES` / `RESVEC` case control; this is the modern replacement for the older **missing-mass / mode-acceleration** correction. Always enable residual vectors for base-excitation, frequency-response, and any analysis where interface forces or stresses are deliverables.

**Common mistakes:** judging convergence by frequency-range alone while effective mass is still < 80 %; forgetting rotational effective mass; omitting residual vectors and then reporting truncated (non-conservative) stresses; mass-normalization confusion between codes.

---

## 2. Prestressed, stress-stiffened, and spin-softened modal

**Prestress (stress stiffening).** Run a static (or nonlinear) preload first, pass the resulting **geometric/stress-stiffness matrix [Kσ]** into the eigensolve. **Tension raises frequencies; compression lowers them** (a guitar string, a spinning blade, a pressurized membrane). Required for cables, membranes, thin pressurized shells, tensioned/bolt-preloaded joints, and turbomachinery blades. Workflow (Ansys/Mechanical, Nastran): linear/nonlinear static → prestressed modal reusing the stressed stiffness.

**Spin softening.** For rotating bodies, the **centrifugal load softens** radial stiffness (the rotating-frame "follower" effect) — it *lowers* frequencies and opposes stress stiffening. **Activate stress stiffening whenever spin softening is on**; using one without the other gives large errors at high speed. Both are required for accurate rotor natural frequencies.

**Mistake:** modeling a spinning part with ordinary modal (no [Kσ], no spin softening) — frequencies can be off by tens of percent at speed.

---

## 3. Damping models

| Model | Form | Where valid | Notes |
|---|---|---|---|
| **Modal (critical) damping ratio ζ** | per-mode ζ | mode-superposition | Cleanest; assign per mode or per band. |
| **Rayleigh (proportional) α, β** | C = αM + βK | full or modal transient/harmonic | α damps low freq, β damps high freq; only **exactly matches a target ζ at two frequencies** — pick the two to bracket the band of interest, accept the bathtub-shaped error between/outside. |
| **Structural / hysteretic (loss factor η)** | rate-independent, complex stiffness K(1+iη) | **frequency domain only** | Energy loss per cycle independent of frequency; physically realistic for many materials. **η ≈ 2ζ at resonance**, exact only at that frequency. Cannot be used directly in transient. |
| **Viscous (dashpot c)** | force ∝ velocity | transient & harmonic | Energy loss per cycle ∝ frequency. |

**Q (quality / amplification factor) = 1 / (2ζ) = transmissibility at resonance.** Memorize the map:

- ζ = 5 % → **Q = 10** (default for **pyroshock / SRS**).
- ζ = 2 % → **Q = 25**.
- ζ = 1 % → **Q = 50**.
- Spacecraft payload modes are often assigned **ζ = 0.5–1.5 %** (Q ≈ 33–100) — lightly damped, so resonant amplification is severe and notching usually needed.

**Mistakes:** using structural/hysteretic damping in a transient solve (invalid — it is a frequency-domain construct); assuming Rayleigh damping is flat across the band; double-counting damping (material + global + element); using an optimistic Q that under-predicts test response.

---

## 4. Harmonic / frequency-response analysis (steady-state sinusoidal)

**Mode-superposition vs full:**
- **Mode-superposition** — fast, smooths the response by clustering output frequencies near each fn, supports modal/Rayleigh damping. Default for most linear FRF work. **Requires a converged modal basis + residual vectors.**
- **Full (direct)** — solves the full complex system at each frequency; exact, no modal truncation, **mandatory if you need frequency-dependent (structural/hysteretic) damping, damping elements, or frequency-dependent material**. Slower; no automatic resonance clustering.

**Frequency resolution.** Resolve each resonance with enough spectral lines across the **half-power (−3 dB) bandwidth**; for a peak of width Δf ≈ fn/Q you want several points inside Δf. Lightly damped peaks (high Q) demand fine, **clustered** stepping around each fn — uniform coarse stepping will miss/under-predict peaks. Mode-superposition's "cluster about natural frequencies" option does this automatically.

**Mistakes:** uniform frequency stepping that straddles a sharp peak; using full method but then expecting modal-style smoothing; ignoring residual vectors so anti-resonances/forces are wrong.

---

## 5. Transient dynamic analysis

**Time step.** Resolve the **highest mode that contributes** to the response: **~20 points per cycle of the highest frequency of interest → Δt = 1/(20·f_max)**. ~20 pts/cycle keeps period elongation < ~1 %. **Use a smaller Δt if accelerations** (not just displacements) are deliverables, and for contact/impact.

**Integration.** Implicit **Newmark / HHT-α** (generalized-α) is the workhorse for structural transient — unconditionally stable for linear problems; HHT-α adds controllable numerical damping to kill spurious high-frequency content without polluting the band of interest. **Explicit** (central difference) only for very short, highly nonlinear, wave/impact events (conditionally stable: Δt bounded by the **CFL / smallest-element transit time**).

**Mode-superposition transient** is efficient for linear problems but again **cannot use structural/hysteretic damping** (use modal or Rayleigh) and needs residual vectors for accurate forces.

**Mistakes:** time step set by output-plot cadence instead of by f_max; using mode-superposition transient with structural damping; explicit run with Δt above the CFL limit (instant blow-up); too few modes so high-frequency content is silently absent.

---

## 6. Random vibration (PSD) — the spacecraft workhorse

**Inputs/outputs.** Excitation is an **acceleration spectral density (ASD/PSD)** in g²/Hz; response PSDs are integrated to **RMS** quantities. Solved by **mode-superposition frequency response** with the PSD applied as base excitation.

**GRMS (overall RMS acceleration)** = √(area under the response PSD) = √(∫ ASD df).

**Miles' equation** (SDOF, single dominant mode, *flat/white* input PSD across the resonance):

> **GRMS ≈ √( (π/2) · f_n · Q · ASD(f_n) )**, with **Q = 1/(2ζ)**.

Use Miles for quick sizing of a component dominated by one mode on a flat input; it **over/under-predicts when the input is not flat at fn, when multiple modes participate, or when the base is not rigid** — then use the full modal random solve.

**Design to 3σ.** Random response is Gaussian, so peaks are statistical. **Design/qualify to 3σ = 3 × RMS** (covers 99.73 % of instantaneous values); this is the standard conservative load multiplier for stress and interface forces. (Some programs check higher sigma for fatigue / high-cycle; 3σ is the default static-equivalent.)

**Equivalent static load** from random = (3σ acceleration) × mass, applied as an inertial load per direction.

**Mistakes:** applying Miles when the input PSD is shaped (not flat) at the resonance; forgetting the (π/2) factor; designing to 1σ; ignoring cross-correlation between modes; not enabling residual vectors so RMS *forces/stresses* are truncated.

---

## 7. Shock response spectrum (SRS) & shock transient

**Definition.** SRS = plot of the **peak acceleration response of a bank of SDOF oscillators** (each tuned to a frequency, common **damping ζ = 5 %, Q = 10**) all driven by the same base transient. It characterizes shock *severity vs frequency* for qualification; it is **not** a unique time history (many transients share one SRS).

**FEM use.** Either (a) run a **transient** with the measured/derived shock pulse as base input and post-process peaks, or (b) drive a **modal/transient** model with the SRS as an enveloping input. Match the **SDOF damping to the spec (5 % typical)**. For pyroshock the spectrum is broadband to several kHz → extract **many modes** and use Q = 10.

**Mistakes:** under-extracting modes (shock is broadband); wrong SDOF damping; treating SRS as a literal time history.

---

## 8. Base excitation / enforced motion

Two standard ways to impose support acceleration/displacement:

- **Large-mass method.** Attach a **large mass ≈ 10⁶ × structure mass** at the driven DOF(s), apply **force = large_mass × target_acceleration**; the huge inertia makes the resulting motion ≈ the enforced acceleration. Constrain the driven node in all but the excitation direction. Classic, robust, but **can corrupt bolt-preload models** and slightly perturbs eigenvalues — pick the factor large enough (10⁶) that the perturbation is negligible.
- **Direct enforced motion (SPCD / enforced acceleration).** Modern solvers impose the motion directly (cleaner, preferred when available, compatible with preload). NX/Nastran auto-derives the needed static loads and **needs residual vectors** to be accurate.

**Mistakes:** large mass too small (motion not enforced) or absurdly large (numerical conditioning); forgetting to free only the excitation DOF; enforced motion without residual vectors → wrong interface forces.

---

## 9. Rotordynamics

- **Gyroscopic effects** make natural frequencies **speed-dependent**, splitting each mode into **forward- and backward-whirl** branches.
- **Campbell diagram:** plot natural frequency vs spin speed; overlay **excitation order lines (1×, 2×, … N× rpm)**. Each **intersection of an order line with a frequency branch = a critical speed** for that mode/excitation. Goal: keep operating speeds away from criticals (often ±10–20 % margin per program spec).
- Include **gyroscopic matrix [G]**, and (per §2) **stress stiffening + spin softening**; bearings/seals add speed- and load-dependent stiffness/damping (cross-coupled terms can drive instability/whirl).
- Solve as a **speed-swept complex/QR-damped modal** (damped eigenvalues give whirl + stability).

**Mistakes:** omitting gyroscopics (no whirl split, criticals wrong); using undamped modal so instabilities are invisible; ignoring bearing cross-coupling.

### 9.1 Depth: unbalance, bearings, stability, torsional

The note above is the eigen-side (gyroscopics, Campbell, whirl split, QR-damped). The practice of turbomachinery design adds forced-response, bearings, stability, and torsional — governed by the **API rotordynamics standards** (**API 617** for centrifugal compressors, **API 684** the rotordynamics tutorial / acceptance bible).

**Two families — keep them separate.** A real machine needs **both**:
- **Lateral rotordynamics** — bending/whirl: gyroscopic, criticals, oil-film instability. This is the speed-dependent, gyroscopically-coupled problem of §9.
- **Torsional rotordynamics** — shaft twist along the drivetrain. **No gyroscopic coupling** (the modes don't split with speed the way lateral modes do), excited by torque ripple — gear mesh, motor harmonics, VFD orders. Modeled as lumped inertia-shaft chains (**Holzer** historically) or torsional FE; build a Campbell of torsional modes vs excitation **orders** (gear-mesh = #teeth × rpm, **2× line frequency** for synchronous motors, VFD switching harmonics) and keep torsional criticals out of the operating range with margin. Coupling and gearbox torsional stiffness dominate the low modes. Critical for reciprocating drives and large electric machines.

**Unbalance (synchronous, 1×) response.** Residual unbalance is a rotating force that grows as **m·e·Ω²** and rotates at shaft speed → pure **1×** synchronous excitation. Sweep speed and plot **response amplitude and phase**; peaks occur at the criticals with amplification ≈ **Q = 1/(2ζ)** at that mode (lightly damped rotor → high peak → tight clearance/seal-rub risk). Acceptance:
- **ISO 1940** sets permissible residual unbalance via **balance-quality grades G** (e.g. **G 2.5** for machine-tool spindles / turbines, **G 6.3** for general rotating machinery, **G 1.0** for precision) — grade × (mass / speed) gives the allowable unbalance.
- **ISO 7919** (shaft-relative) and **ISO 10816** (bearing-housing) set vibration evaluation **limits / alarm-trip zones** for the operating machine.

**Bearings — the controlling element (8 linearized dynamic coefficients).** A fluid-film or rolling bearing is represented in the rotor model by a **linearized stiffness and damping matrix**, i.e. **8 coefficients** about the running eccentricity: stiffness **k_xx, k_xy, k_yx, k_yy** and damping **c_xx, c_xy, c_yx, c_yy**. They are **speed- and load-dependent** → recompute (or re-interpolate) the set at each speed before the eigen/forced solve.
- **Hydrodynamic journal (oil-film) bearings** introduce **cross-coupled stiffness (k_xy, k_yx)** from the converging oil wedge. Cross-coupling pumps energy into **forward whirl**: at roughly **half speed (~0.43–0.48× shaft speed)** the journal centre orbits → **oil whirl** (sub-synchronous). When rotor speed rises so that the whirl frequency locks onto a lateral critical, the whirl amplitude runs away → **oil whip** — a self-excited instability that does not track speed. The speed at which this onset occurs is the **threshold speed of instability**, the hard design limit for fluid-film rotors.
- **Mitigation:** **tilting-pad journal bearings** have near-zero cross-coupling (pads pivot to kill the destabilizing term) and raise the threshold dramatically; **squeeze-film dampers** add external damping to push the onset above the operating range. **Rolling-element bearings** are stiff (nonlinear Hertzian) with very little damping — high criticals, little stability margin from the bearing itself.

**Stability (damped complex eigen / log decrement).** Solve the **damped (complex) eigenproblem** (the QR-damped / UNSYM machinery of §9 and solver-numerics) at each speed including the bearing/seal cross-coupling. Each mode's decay is reported as the **logarithmic decrement δ** (= 2πζ for light damping): **δ > 0 = stable** (whirl decays), **δ < 0 = self-excited instability**. **API 617 / API 684** define the acceptance: a **Level I** screening (energy / stability margin) and, if it fails or for high-pressure service, a **Level II** analysis that adds the destabilizing forces and sweeps the **cross-coupling sensitivity** (apply increasing destabilizing cross-coupled stiffness Q_A at the rotor mid-span, find the Q that drives δ→0 — the margin to instability). Required positive log-dec with margin across that sweep is the gate.

**Seal & aerodynamic cross-coupling (destabilizing).** Labyrinth / annular liquid seals and **aerodynamic cross-coupling (Alford forces** — tip-clearance variation in turbines/compressors) add **destabilizing cross-coupled stiffness**, just like the oil film. Include them in the stability budget for high-pressure compressors and turbines; they are often *the* reason a machine fails the Level II stability check.

**Transient run-up / coast-down.** Integrate through the criticals (Newmark / HHT with rotating-load and gyroscopic terms active, §5) to capture **peak transient amplitude while sweeping through a resonance** and any dwell — the acceleration rate sets how high the response actually climbs (fast traverse limits the peak vs a slow soak at the critical).

**Gates (rotordynamics):** gyroscopics ON for lateral (else criticals are wrong, §9); bearing coefficients evaluated **at the right speed**; enough modes extracted through the operating range × margin; **log-dec positive with API margin across the cross-coupling sensitivity sweep** (stability proven, not assumed); separation margin from criticals per spec; **lateral AND torsional both assessed** (torsional is silent in a lateral-only model).

---

## 10. Vibro-acoustics

**Domain decomposition:**
- **Interior / cavity (enclosed fluid):** **acoustic FEM** (fluid Helmholtz elements) — efficient for bounded cavities (vehicle interior, duct, casing).
- **Exterior / radiation (unbounded):** **BEM** (only the surface is meshed; radiation condition automatic) **or** FEM truncated with **PML / infinite elements** to absorb outgoing waves without reflection. **Hybrid FEM (structure/cavity) + BEM (radiation)** is the standard for radiated noise from a vibrating structure.

**Acoustic mesh density — the governing rule.** Mesh the **shortest wavelength** (highest frequency): λ = c / f_max (c ≈ 343 m/s in air).
- **≥ 6 linear elements per wavelength** (h ≤ λ/6) is the universal rule of thumb; some practitioners use λ/5; "six per wavelength" is a *minimum*, more is safer (pollution/dispersion error grows with frequency·distance).
- **≥ 5–6 quadratic (2nd-order) elements per wavelength** (h ≤ λ/5) — quadratic elements are far more efficient per DOF for waves and are preferred for acoustics.
- Same ≥ 6/λ guidance applies to **BEM** surface meshes.

**Coupled ("wet") modes.** Strong fluid-structure coupling (e.g., light panel on a stiff cavity, fuel tanks, water-loaded structures) shifts and adds modes vs the in-vacuo ("dry") modes — solve the **coupled structural-acoustic eigenproblem** (unsymmetric) to get wet modes when the fluid mass-loads or stiffens the structure.

**NVH outputs & diagnostics:**
- **SPL** (sound pressure level at field points), **sound power** (radiated, source-independent of receiver location), **transmission loss (TL)** for partitions/panels.
- **Acoustic Transfer Vector (ATV):** precomputed transfer between surface normal velocity and pressure at a field point — enables fast **multi-rpm / multi-order** sweeps (compute ATV once, reuse for every operating point). **Modal ATV (MATV)** combines with structural modes.
- **Panel (acoustic) contribution analysis (PACA/MATV):** ranks which panels/surfaces dominate the noise at a target point — the key NVH design lever (tells you *where* to add damping/stiffness/trim).
- **Trim/absorption** modeled via Biot (poro-elastic) for seats, blankets, liners.

**Mistakes:** meshing for f_min not f_max (under-resolved at the top of the band → dispersion error); using dry modes where coupling is strong; running full coupled solves per rpm instead of ATV; neglecting PML/infinite-element/radiation BC on exterior problems (spurious reflections).

---

## 11. Aeroelasticity / flutter (note)

- **Flutter** = dynamic instability where aerodynamic, inertial, and elastic forces couple and extract energy from the flow → growing oscillation above the **flutter speed**. Found by tracking **modal damping vs airspeed**; flutter onset = damping crosses zero (mode goes unstable).
- Standard subsonic industrial method: structural **modal basis (FEM mass/stiffness)** + unsteady aero from the **Doublet-Lattice Method (DLM)** panels; solve with the **p-k ("British") method** (e.g., **Nastran SOL 145**) sweeping density/Mach/velocity. SOL 200 flutter optimization also uses p-k.
- **DLM meshing:** chordwise box size must shrink as **reduced frequency k** rises (boxes must resolve the unsteady pressure wave along the chord). Older guidance of a few boxes per chord has been revised sharply upward (modern refinements call for on the order of tens of boxes per aerodynamic wavelength at high k); keep box **aspect ratios** within the solver's validated range and align boxes spanwise with structural modes. Always do a **box-density convergence study** on flutter speed.

**Mistakes:** too-coarse DLM mesh at high reduced frequency; mismatched aero/structural spline; reading flutter off frequency coalescence alone instead of the damping-vs-speed crossing.

---

## 12. Spacecraft test correlation (sine / random / acoustic) & force limiting

- **Sine vibration** — low-frequency mechanically-transmitted launch loads / final dynamic qualification (per **NASA-STD-7002**, launch-vehicle ICDs, **ECSS-E-ST-10-03**). Random vibration (energy mostly < ~100 Hz from the mount, plus higher-frequency) may substitute for system sine on some programs.
- **Random vibration** — broadband mechanically-/acoustically-induced environment; design/qualify to **3σ** (§6).
- **Acoustic / vibroacoustic** — high-level diffuse acoustic field exciting large lightweight surfaces (solar arrays, panels, antennas); governed by **NASA-STD-7001**. Predict with vibro-acoustic FEM/BEM or statistical methods.
- **Model correlation:** match analysis to modal-survey/test — targets typically **frequency error within a few % (≈ ≤ 3–5 %) on major modes** and **MAC (Modal Assurance Criterion) ≥ ~0.9** for the dominant modes (program-specific). Update via §0 chain, not by ad-hoc stiffness fudging.

**Force-limited vibration testing (FLVT)** — the key anti-**overtest** technique:
- A shaker is near-infinite impedance vs the real flight mount, so a pure acceleration-controlled (base-shake) test **overdrives the article at its resonances** (the real interface force would notch there). FLVT adds a **force limit** so the test **notches** the input acceleration at resonances to flight-realistic interface force.
- **Semi-empirical method (Scharton)** is the most-used: force-limit spec **S_FF = C² · M² · S_AA** (C = nondimensional dynamic amplification constant, M = total mass, S_AA = input ASD); **C² ≈ 2 (often 1–5)** as a starting point, refined by coupled-loads/impedance data. Documented in **NASA-HDBK-7004** (and handbook **NASA-RP/HDBK** lineage).
- **Notching** (manual or force-limited) protects the article but must be **justified** so qualification margins are not eroded; NASA and ESA differ on system-level notch acceptance criteria.

**Mistakes:** acceleration-control-only base shake (overtest, can fail flight-good hardware); unjustified manual notching (undertest); picking C² without impedance/CLA support; correlating to test by tweaking damping instead of mass/stiffness.

---

## Quick-reference cheat sheet

| Quantity | Default rule |
|---|---|
| Modal mode count (effective mass) | cumulative ≥ **80–90 %** each direction |
| Modal mode count (frequency) | up to **1.5–2 × f_excite,max** |
| Residual vectors | **ON** for force/stress, base-excitation, FRF |
| Q ↔ ζ | **Q = 1/(2ζ)**; 5 %→Q10, 2 %→Q25, 1 %→Q50 |
| Structural damping η | **η ≈ 2ζ** (resonance only); **frequency-domain only** |
| Rayleigh α,β | matches ζ exactly at **two** frequencies only |
| Transient Δt | **1/(20·f_max)** (smaller for accel/contact) |
| Miles' GRMS | **√((π/2)·f_n·Q·ASD(f_n))**, flat-PSD SDOF |
| Random design load | **3σ = 3 × RMS** |
| SRS / pyroshock damping | **ζ = 5 %, Q = 10** |
| Large-mass factor | **≈ 10⁶ × model mass** |
| Acoustic mesh | **≥ 6 linear / ≥ 5–6 quadratic elements per wavelength** at f_max (λ = c/f) |
| Rotordynamics | gyroscopics + stress-stiffening + spin-softening; Campbell criticals |
| Rotor unbalance / vibration limits | 1× synchronous response; **ISO 1940** balance grade G; **ISO 7919/10816** limits |
| Bearings | **8 dynamic coefficients** (k_xx..c_yy, speed/load-dependent); oil whirl ~0.43–0.48× → oil whip |
| Rotor stability | damped complex eigen → **log-dec δ > 0**; **API 617/684** Level I/II + cross-coupling sweep |
| Force-limit C² | **≈ 2** (range 1–5) semi-empirical (Scharton) |
| Test correlation | freq error ≤ ~3–5 %, **MAC ≥ ~0.9** on major modes |

---

## SOURCES

Modal mass / mode count / residual vectors:
- Tom Irvine, "Effective Modal Mass & Modal Participation Factors," vibrationdata.com — https://vibrationdata.com/tutorials2/ModalMass.pdf
- Altair SimSolid, Modal Participation Factors — https://help.altair.com/ss/en_us/topics/simsolid/results/modal_participation_factors_r.htm
- CATI, "Understanding Mass Participation Factor Results in Frequency Studies" — https://www.cati.com/blog/understanding-mass-participation-factor-results-in-frequency-studies/
- Siemens NX/Simcenter Nastran, "Using Residual Vectors (Modal Augmentation)" — http://www2.me.rochester.edu/courses/ME204/nx_help/en_US/tdocExt/content/1/id502001.xml
- MSC, "SimAcademy — Residual Vectors in Modal Solutions" — https://simulatemore.mscsoftware.com/simacademy-residual-vectors-in-modal-solutions-msc-nastran-video/

Prestress / stress stiffening / spin softening:
- Ansys Theory, 3.5 Spin Softening — https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_thry/thy_geo4.html
- Springer, "Prestressed Modal Analysis Using FE Package ANSYS" — https://link.springer.com/chapter/10.1007/978-3-540-31852-1_19

Damping / harmonic / Q-factor:
- Ansys, Damping Controls (16.1.14) — https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/wb_sim/ds_damping_controls.html
- Ansys Theory, 14.3 Damping Matrices — https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_thry/thy_tool3.html
- COMSOL, "Damping in Structural Dynamics: Theory and Sources" — https://www.comsol.com/blogs/damping-in-structural-dynamics-theory-and-sources
- Strand7, Special Topics: Damping — https://www.strand7.com/strand7r3help/Content/Topics/SpecialTopics/SpecialDamping.htm
- MDPI Appl. Sci., "Comparative Analysis of Viscous Damping Model and Hysteretic Damping Model" — https://www.mdpi.com/2076-3417/12/23/12107
- Vibration Research, "How to Use the Q-factor" — https://vibrationresearch.com/resources/how-to-use-q-factor/
- Ansys, Mode Superposition Harmonic Analysis (Innovation Courses) — https://courses.ansys.com/index.php/courses/harmonic-response-analysis-in-ansys-mechanical/lessons/performing-mode-superposition-harmonic-analysis-lesson-1/

Transient / time integration:
- Ansys Theory, 15.2 Transient Analysis (Newmark, 20 pts/cycle) — https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_thry/thy_anproc2.html
- Ansys, 5.6 Transient Dynamic Analysis Options — https://ansyshelp.ansys.com/public//Views/Secured/corp/v252/en/ans_str/Hlp_G_STR5_12.html

Random vibration / Miles / 3σ:
- EngineerExcel, "Miles' Equation: Equivalent Acceleration for Random Vibrations" — https://engineerexcel.com/miles-equation/
- Tom Irvine, "Equivalent Static Loads for Random Vibration" (vibrationdata) — https://www.vibrationdata.com/tutorials2/eqstatic.pdf
- Simmons, "Miles' Equation" (vibrationdata) — https://www.vibrationdata.com/tutorials_alt/Simmons_MilesEquation.pdf
- INCAS Bulletin, "Comparative study between random vibration and linear static" — https://bulletin.incas.ro/files/dima__moisei__coman__nastase__liliceanu__petre__vo.pdf

SRS / shock:
- caeflow, "Shock Response Spectrum (SRS): The Comprehensive Guide" — https://caeflow.com/vibration_and_acoustics/shock-response-spectrum-srs/
- Siemens Community, "Shock Response Spectrum (SRS)" — https://community.sw.siemens.com/s/article/shock-response-spectrum-srs
- Fidelis FEA, "What Is SRS Analysis in FEA" — https://www.fidelisfea.com/post/what-is-shock-response-spectrum-srs-analysis-in-fea-and-how-is-it-calculated

Base excitation / large mass:
- Ansys Theory, 14.18 Enforced Motion in Structural Analysis — https://www.mm.bme.hu/~gyebro/files/ans_help_v182/ans_thry/str_EnMoinStAn.html
- Eng-Tips, "Large Mass Method" — https://www.eng-tips.com/threads/large-mass-method.30457/
- Siemens NX, "Enforced Acceleration" — http://www2.me.rochester.edu/courses/ME204/nx_help/en_US/tdocExt/content/6/id623306.xml

Rotordynamics / Campbell / unbalance / bearings / stability / torsional:
- vibromera, "Campbell Diagram: Critical Speed Analysis Guide" — https://vibromera.eu/glossary/campbell-diagram/
- Ansys, 19.5.22 Campbell Diagram Chart Results — https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/wb_sim/ds_campbell_diagram_results.html
- Siemens Simcenter blog, rotor dynamics simulation — https://blogs.sw.siemens.com/simcenter/say-your-prayers-or-get-a-rotor-dynamics-simulation-engineer-how-simulation-ensures-engines-can-survive-vibrations/
- API STD 617, *Axial and Centrifugal Compressors and Expander-compressors* (lateral/torsional rotordynamics & stability acceptance) — American Petroleum Institute.
- API STD 684, *API Standard Paragraphs Rotordynamic Tutorial: Lateral Critical Speeds, Unbalance Response, Stability, Train Torsionals, and Rotor Balancing* — the practitioner reference for log-dec / Level I & II stability.
- ISO 1940-1, *Mechanical vibration — Balance quality requirements for rotors in a constant (rigid) state — Part 1: Specification and verification of balance tolerances* (grades G).
- ISO 7919 / ISO 20816 (supersedes ISO 10816), *Mechanical vibration — Evaluation of machine vibration* (shaft-relative / bearing-housing limit zones).
- Oil whirl / oil whip & threshold speed of instability; tilting-pad & squeeze-film dynamic coefficients — Muszynska; Vance, Childs, Friswell rotordynamics texts.

Duct acoustics / muffler TMM / absorption / IE vs PML / acoustics FEM mistakes (deep reference):
- `references/acoustics-fem.md` — 4-pole transfer matrix method with full matrix entries and TL formula, cut-on frequencies for circular/rectangular/elliptical ducts, Sabine/impedance/locally-vs-extended-reacting absorption, IE vs PML decision table (Astley/Burnett formulation, COMSOL 6.3 official meshing rules), aeolian tone / Strouhal number, and 14 documented acoustics FEM mistakes with fixes.

Vibro-acoustics / mesh-per-wavelength / ATV / panel contribution / TL:
- COMSOL, "How to Use the Boundary Element Method in Acoustics Modeling" — https://www.comsol.com/blogs/how-to-use-the-boundary-element-method-in-acoustics-modeling
- COMSOL, "How to Automate Meshing in Frequency Bands for Acoustic Simulations" — https://www.comsol.com/blogs/how-to-automate-meshing-in-frequency-bands-for-acoustic-simulations
- Marburg, "Six boundary elements per wavelength: Is that enough?" — *J. Comput. Acoust.* 10(1):25–51 (2002): https://doi.org/10.1142/S0218396X02001401
- "More Than Six Elements Per Wavelength" — Langer, Maeder et al., *J. Comput. Acoust.* 25(4):1750025 (2017): https://doi.org/10.1142/S0218396X17500254
- Simcenter blog, "Efficient and Accurate Broadband FEM-based Vibro-acoustics (Part 1)" — https://blogs.sw.siemens.com/simcenter/efficient-and-accurate-broadband-fem-based-vibro-acoustics-part-1/
- Simcenter blog, "Simcenter 3D Acoustics 2506: what's new" (ATV ROM, multi-rpm) — https://blogs.sw.siemens.com/simcenter/simcenter-3d-acoustics-2506-discover-whats-new/
- Siemens Community, "Sound Transmission Loss" — https://community.sw.siemens.com/s/article/sound-transmission-loss
- Liu et al., Complexity (Wiley), "Optimization of Noise Transfer Path Based on Composite Panel Acoustic and Modal Contribution Analysis" — https://www.hindawi.com/journals/complexity/2021/3059865/
- Atalla & Sgard, "Finite Element and Boundary Methods in Structural Acoustics and Vibration" (Routledge) — https://www.routledge.com/Finite-Element-and-Boundary-Methods-in-Structural-Acoustics-and-Vibration/Atalla-Sgard/p/book/9781138749177

Aeroelasticity / flutter / DLM:
- SDA Software, Nastran Aerodynamic Flutter (SOL 145, p-k) — https://sdasoftware.com/software/nastran/features/aerodynamic-flutter/
- Siemens NX, "Introduction to Aeroelastic Analysis and Design" — http://www2.me.rochester.edu/courses/ME204/nx_help/en_US/tdocExt/content/1/id483121.xml
- Rodden et al., "Further Refinement of the Subsonic Doublet-Lattice Method," J. Aircraft 35(5) — https://www.odonata-research.com/references/aerodynamics/dlm/Journal-of-Aircraft-Vol-35-No-5-p720.pdf
- Rodden, "Improvements to the Doublet-Lattice Method in MSC/NASTRAN" — https://web.mscsoftware.com/support/library/conf/auc99/p03799.pdf

Spacecraft standards / test correlation / force limiting:
- NASA-STD-7001A, Payload Vibroacoustic Test Criteria — https://standards.nasa.gov/sites/default/files/standards/NASA/B/0/Historical/nasa-std-7001a.pdf
- NASA-STD-7002B, Payload Test Requirements — https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7002B-w-Change-1.pdf
- Vibration Research, "Understanding NASA-STD-7001 Test Parameters" — https://vibrationresearch.com/blog/understanding-nasa-std-7001-test-parameters/
- NASA NESC, "Best Practices for Use of Sine Vibration Testing" — https://www.nasa.gov/centers-and-facilities/nesc/the-nesc-publishes-best-practices-for-use-of-sine-vibration-testing/
- NASA-HDBK-7004C, Force Limited Vibration Testing — https://experiorlabs.com/wp-content/uploads/2019/10/NASA-HDBK-7004C-Force-Limited-Vibration-Testing.pdf
- NASA NTRS, "Application of the Semi-Empirical Force-Limiting Approach" — https://ntrs.nasa.gov/api/citations/20120014221/downloads/20120014221.pdf
- S3VI / Instar, "Vibration Testing of Small Satellites" — https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/Instar_Vibration_Testing_of_Small_Satellites_Part_1.pdf
