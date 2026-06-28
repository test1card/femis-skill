#!/usr/bin/env python3
"""
Grid Convergence Index (GCI) — Roache / ASME V&V 20 / Celik et al. 2008.

Quantifies discretization uncertainty from >=3 systematically refined meshes (or
time steps) tracking ONE scalar QoI. Use it as the SIGNOFF mesh/time-step gate:
accept ONLY when the refinement is monotonically CONVERGING (Roache convergence
ratio 0 < R < 1), the observed order p is sane (p>0, near the formal order), the
fine-grid GCI is small (~1-3%), and the solution is in the asymptotic range
(asymptotic ratio ~ 1).

REJECTED, never PASSED:
  * R <= 0  -> oscillatory (the QoI swings either side of the limit).
  * R >= 1  -> DIVERGING: the QoI change GROWS as the mesh refines, so it is not
              approaching a limit. A small/positive GCI here is meaningless.
A negative/garbage uncertainty is never a PASS.

Handles UNEQUAL refinement ratios via the Celik (2008) fixed-point solve for p
(reduces exactly to the closed form ln|e32/e21|/ln(r) when r21 == r32).

Stdlib only. Usage:
    python gci.py h1 f1 h2 f2 h3 f3
where (h1,f1) is the FINEST grid. h = representative cell size (or time step);
f = the QoI on that grid. h1 < h2 < h3 (need not be a constant ratio).

Example (peak temperature, K), r ~ 2 refinement:
    python gci.py  1.0 305.20  2.0 306.10  4.0 308.50
"""
from __future__ import annotations

import sys
from math import copysign, log


def _solve_order(r21, r32, e21, e32, tol=1e-10, itmax=200):
    """Observed order p via the Celik (2008) fixed-point iteration, valid for
    unequal ratios:  p = |ln|e32/e21| + q(p)| / ln(r21),
        q(p) = ln((r21**p - s)/(r32**p - s)),  s = sign(e32/e21).
    For r21 == r32, q == 0 and p reduces to the closed form. Returns (p, s,
    converged). p is reported as a magnitude (Celik convention); the CALLER must
    gate on the convergence ratio R, not on p alone (a diverging series also has
    a positive p).
    """
    ratio = e32 / e21
    s = copysign(1.0, ratio)  # +1 monotone, -1 oscillatory
    a = abs(ratio)
    if a == 0.0:
        return 0.0, s, True
    lnr21 = log(r21)
    p = abs(log(a)) / lnr21  # initial guess (closed form)
    converged = False
    for _ in range(itmax):
        try:
            q = log((r21 ** p - s) / (r32 ** p - s))
        except (ValueError, ZeroDivisionError):
            break  # argument went non-positive -> can't continue the fixed point
        p_new = abs(log(a) + q) / lnr21
        p_new = 0.5 * (p_new + p)  # light damping to tame fixed-point oscillation
        if abs(p_new - p) < tol:
            p = p_new
            converged = True
            break
        p = p_new
    return p, s, converged


def gci(h1, f1, h2, f2, h3, f3, Fs=1.25):
    """Return a dict with the Roache convergence ratio R, observed order p,
    Richardson extrapolate, the two GCIs, the asymptotic-range ratio, and
    validity flags. Grids ordered fine->coarse.

    Key flags the verdict honours:
      convergence_ratio_R : e21/e32. 0<R<1 converging; R<=0 oscillatory; R>=1 diverging.
      converging          : 0 < R < 1.
      order_converged     : the p fixed-point converged.
      valid               : converging AND p>0 AND GCIs finite & positive -> GCI meaningful.
    """
    if not (h1 < h2 < h3):
        raise ValueError("Need h1 < h2 < h3 (finest first).")
    r21 = h2 / h1
    r32 = h3 / h2
    e21 = f2 - f1
    e32 = f3 - f2
    if e21 == 0.0:
        raise ValueError("f1 == f2: QoI already mesh-independent (or duplicate grids).")

    # Roache convergence ratio: the single most important diagnostic.
    R = float("inf") if e32 == 0.0 else e21 / e32
    converging = 0.0 < R < 1.0
    p, _s, order_converged = _solve_order(r21, r32, e21, e32)

    rp = r21 ** p
    f_exact = (rp * f1 - f2) / (rp - 1.0) if rp != 1.0 else float("nan")
    eps21 = abs(e21 / f1) if f1 else float("inf")
    eps32 = abs(e32 / f2) if f2 else float("inf")
    gci_fine = Fs * eps21 / (rp - 1.0) if rp > 1.0 else float("nan")
    rp32 = r32 ** p
    gci_coarse = Fs * eps32 / (rp32 - 1.0) if rp32 > 1.0 else float("nan")
    denom = rp * gci_fine
    asymptotic_ratio = (gci_coarse / denom) if (denom and denom == denom) else float("nan")

    valid = (
        converging
        and p > 0.0
        and gci_fine == gci_fine          # not NaN
        and gci_fine > 0.0
        and gci_coarse == gci_coarse
        and gci_coarse > 0.0
    )
    return {
        "convergence_ratio_R": R,
        "converging": converging,
        "observed_order_p": p,
        "order_converged": order_converged,
        "richardson_f_exact": f_exact,
        "gci_fine_pct": 100.0 * gci_fine,
        "gci_coarse_pct": 100.0 * gci_coarse,
        "asymptotic_ratio": asymptotic_ratio,
        "monotonic": R > 0.0,
        "valid": valid,
        "qoi_change_21_pct": 100.0 * eps21,
        "r21": r21,
        "r32": r32,
    }


def _verdict(res):
    R = res["convergence_ratio_R"]
    # Reject non-converging data FIRST — a small/positive GCI is meaningless there.
    if R <= 0.0:
        return ("REJECT - non-monotone (oscillatory) refinement (R<=0); the QoI swings either side of the "
                "limit. GCI invalid; add a finer grid / fix the model.")
    if R >= 1.0:
        return (f"REJECT - DIVERGING under refinement (convergence ratio R={R:.3f} >= 1): the QoI change GROWS "
                "as the mesh refines, so it is not approaching a limit. Do NOT report a GCI; fix the model / add grids.")
    if not res["valid"] or res["observed_order_p"] <= 0.0:
        return (f"REJECT - not in the asymptotic range (p={res['observed_order_p']:.3f}); GCI not meaningful.")
    if not res["order_converged"]:
        return "MARGINAL - order-of-accuracy iteration did not converge; treat p (and the GCI) with caution."
    ok_band = res["gci_fine_pct"] <= 3.0 and res["qoi_change_21_pct"] <= 2.0
    ok_asym = 0.9 <= res["asymptotic_ratio"] <= 1.1
    if ok_band and ok_asym:
        return "PASS - converging (0<R<1), p>0, fine-grid GCI small, and in the asymptotic range."
    if ok_band and not ok_asym:
        return "MARGINAL - small GCI but asymptotic ratio off 1.0; add a grid to confirm."
    return "FAIL - refine further; QoI not yet mesh-independent."


def main(argv):
    if len(argv) != 6:
        print(__doc__)
        return 2
    h1, f1, h2, f2, h3, f3 = map(float, argv)
    res = gci(h1, f1, h2, f2, h3, f3)
    print(f"refinement ratios     = r21 {res['r21']:.3f}, r32 {res['r32']:.3f}")
    print(f"convergence ratio R   = {res['convergence_ratio_R']:.3f}  (0<R<1 converging)")
    print(f"observed order p      = {res['observed_order_p']:.3f}"
          f"{'' if res['order_converged'] else '  (iteration NOT converged)'}")
    print(f"Richardson f_exact    = {res['richardson_f_exact']:.5g}")
    print(f"GCI_fine              = {res['gci_fine_pct']:.3f} %")
    print(f"GCI_coarse            = {res['gci_coarse_pct']:.3f} %")
    print(f"asymptotic ratio      = {res['asymptotic_ratio']:.4f}  (want ~1.0)")
    print(f"QoI change (fine pair)= {res['qoi_change_21_pct']:.3f} %")
    print(f"verdict               = {_verdict(res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
