#!/usr/bin/env python3
"""y+ first-cell-height estimator for wall-bounded CFD meshing.

Given a target y+ and the flow conditions, estimate the wall-normal size of the
first cell so the near-wall mesh lands in the intended region:
  * y+ < 1            wall-resolved   (resolve the viscous sublayer; low-Re k-omega SST, LES/DES/DDES)
  * 30 <= y+ <= 300   wall-function   (standard / scalable wall functions, high-Re k-epsilon)
  * 1 < y+ < 30       BUFFER LAYER -- AVOID (neither modelling assumption holds)

Method -- flat-plate turbulent boundary-layer estimate (the standard a-priori
sizing; Schlichting):
    Re_L  = rho*U*L/mu
    Cf    = 0.058 * Re_L**-0.2          (turbulent flat plate, ~1e5 < Re < 1e7)
    tau_w = 0.5 * Cf * rho * U**2
    u_tau = sqrt(tau_w/rho)             (friction velocity)
    y     = yplus * mu / (rho*u_tau)    (wall-normal distance of the first node)

`y` is the distance from the wall to the first NODE. For CELL-CENTRED solvers
(Fluent, OpenFOAM, STAR-CCM+) the first cell *centroid* sits at y, so the first
cell HEIGHT is ~2*y; for node/vertex solvers the first-cell height ~ y.

This is an ESTIMATE for initial meshing only. The achieved y+ scales with the
LOCAL wall shear, which varies over the body -- size for the high-shear region,
then CONFIRM the achieved y+ from the converged solution and re-mesh if off.
See references/cfd.md and references/meshing-convergence.md.

Vendor-neutral; no project data. Run `python yplus.py` for a self-test.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class YPlusResult:
    first_node_distance: float          # y   [length] wall -> first node
    first_cell_height_cellcentred: float  # ~2y [length] for cell-centred codes
    Re_L: float
    Cf: float
    tau_w: float                        # wall shear stress [force/length^2]
    u_tau: float                        # friction velocity [length/time]
    regime: str


def estimate_first_cell(yplus_target: float, U: float, L: float,
                        rho: float, mu: float) -> YPlusResult:
    """Estimate first-cell wall-normal size for a target y+.

    Use ONE consistent unit system (SI shown):
      yplus_target : desired y+ (e.g. 1 wall-resolved, 50 wall functions)
      U   : reference (freestream / bulk) velocity   [m/s]
      L   : characteristic length for Re (plate length / chord / hydraulic dia) [m]
      rho : density            [kg/m^3]
      mu  : dynamic viscosity  [Pa.s]

    Example -- air at 20 C over a 1 m plate at 50 m/s, target y+ = 1:
    >>> r = estimate_first_cell(1.0, 50.0, 1.0, 1.225, 1.81e-5)
    >>> round(r.first_node_distance * 1e6, 1)   # microns
    7.8
    """
    if min(yplus_target, U, L, rho, mu) <= 0:
        raise ValueError("all inputs must be positive")
    Re_L = rho * U * L / mu
    Cf = 0.058 * Re_L ** -0.2
    tau_w = 0.5 * Cf * rho * U * U
    u_tau = math.sqrt(tau_w / rho)
    y = yplus_target * mu / (rho * u_tau)

    if yplus_target <= 1:
        regime = "wall-resolved (viscous sublayer; low-Re / LES / DES)"
    elif yplus_target <= 5:
        regime = "wall-resolved edge (sublayer; aim y+<=1 for margin)"
    elif yplus_target < 30:
        regime = "BUFFER LAYER (1<y+<30) -- AVOID: neither wall-resolved nor wall-function"
    elif yplus_target <= 300:
        regime = "wall-function range (30<=y+<=300)"
    else:
        regime = "y+>300 -- too coarse; wall functions degrade"
    if not (1e5 <= Re_L <= 1e7):
        regime += (" | NOTE: Re_L outside the Cf-correlation range [1e5, 1e7] "
                   "-- estimate degraded (use a Cf valid for this Re)")
    return YPlusResult(y, 2.0 * y, Re_L, Cf, tau_w, u_tau, regime)


def _selftest() -> None:
    # Air over a 1 m plate at 50 m/s.
    rho, mu, U, L = 1.225, 1.81e-5, 50.0, 1.0
    print(f"Air, U={U} m/s, L={L} m, rho={rho}, mu={mu}")
    print(f"{'y+':>6} {'y [um]':>10} {'cell h (cc) [um]':>18}  regime")
    for yp in (1.0, 30.0, 50.0, 100.0, 300.0):
        r = estimate_first_cell(yp, U, L, rho, mu)
        print(f"{yp:>6.0f} {r.first_node_distance*1e6:>10.2f} "
              f"{r.first_cell_height_cellcentred*1e6:>18.2f}  {r.regime}")
    # Assert the documented value.
    r1 = estimate_first_cell(1.0, U, L, rho, mu)
    assert abs(r1.first_node_distance * 1e6 - 7.8) < 0.1, r1.first_node_distance
    print(f"\nRe_L = {r1.Re_L:.3e}, Cf = {r1.Cf:.5f}, tau_w = {r1.tau_w:.3f} Pa, "
          f"u_tau = {r1.u_tau:.3f} m/s")
    print("OK: self-test passed.")


if __name__ == "__main__":
    _selftest()
