#!/usr/bin/env python3
"""
Explicit-dynamics energy-quality gate (hourglass / energy balance / KE).

In reduced-integration explicit dynamics, ZERO-ENERGY (hourglass) modes are
controlled by an artificial stiffness/viscosity. The amount of energy that
control absorbs is the proxy for solution quality: too much means the mesh is
too coarse, the elements are distorting in spurious modes, and the stresses are
unreliable. This helper takes ALREADY-EXTRACTED energy time-series and returns a
PASS/WARN/FAIL verdict against the standard gates (see SKILL.md):

  * hourglass energy / internal energy  : good < 5%, acceptable <= 10%, FAIL > 10%
  * global energy balance drift         : within ~ +-5% of the initial total
  * kinetic energy / internal energy    : for QUASI-STATIC loading, KE << IE
                                          (keep peak KE/IE below ~5-10%)

It does NOT parse solver binaries. Extract the series headlessly first:

  LS-DYNA
    glstat / matsum ASCII (request via *DATABASE_GLSTAT, *DATABASE_MATSUM), or
    read binout with `lsda` / `qd.lsdyna`. Columns of interest:
        internal energy, hourglass energy, kinetic energy, total energy
        (matsum gives per-part breakdowns; glstat the global totals).

  Abaqus/Explicit
    ODB history outputs (whole-model ENERGY) -> read headlessly with abaqus python
    and `odbAccess`, or `abaqus odbreport`:
        ALLIE   internal energy
        ALLAE   artificial strain energy  (== hourglass / drill / distortion)
        ALLKE   kinetic energy
        ETOTAL  total energy of the model  (energy balance ~ const)

Feed those lists into `energy_quality(...)`.

Stdlib only. Run `python hourglass_check.py` to execute the self-test.
"""
from __future__ import annotations
import sys


def _check_series(name, xs):
    """Validate one time-series: list-like, non-empty, all finite, non-negative."""
    if xs is None:
        return None
    xs = list(xs)
    if not xs:
        raise ValueError(f"{name}: empty time-series.")
    for v in xs:
        f = float(v)
        if f != f:  # NaN
            raise ValueError(f"{name}: contains NaN.")
        if f < 0.0:
            raise ValueError(f"{name}: energy must be non-negative (got {f}).")
    return [float(v) for v in xs]


def energy_quality(internal_energy, hourglass_energy,
                   total_energy=None, kinetic_energy=None,
                   quasi_static=False):
    """Grade an explicit-dynamics run from its energy histories.

    internal_energy, hourglass_energy : required, same length, >= 0.
    total_energy   : optional; used for the energy-balance drift check.
    kinetic_energy : optional; used for the KE/IE check (matters when quasi_static).
    quasi_static   : if True, KE/IE is gated (inertia should be negligible).

    Returns a dict with the worst-case fractions, the energy drift, the overall
    verdict string, and the list of reasons behind it.
    """
    ie = _check_series("internal_energy", internal_energy)
    hg = _check_series("hourglass_energy", hourglass_energy)
    if ie is None or hg is None:
        raise ValueError("internal_energy and hourglass_energy are required.")
    if len(ie) != len(hg):
        raise ValueError(
            f"length mismatch: internal_energy={len(ie)} hourglass_energy={len(hg)}.")
    te = _check_series("total_energy", total_energy)
    ke = _check_series("kinetic_energy", kinetic_energy)
    if te is not None and len(te) != len(ie):
        raise ValueError(f"length mismatch: total_energy={len(te)} internal_energy={len(ie)}.")
    if ke is not None and len(ke) != len(ie):
        raise ValueError(f"length mismatch: kinetic_energy={len(ke)} internal_energy={len(ie)}.")

    # Worst-case hourglass / internal fraction over the history. Guard the divide:
    # before contact engages IE can be ~0, so only score steps with meaningful IE.
    ie_peak = max(ie)
    ie_floor = 1e-12 * ie_peak if ie_peak > 0 else 0.0
    hg_frac = 0.0
    for hi, ii in zip(hg, ie):
        if ii > ie_floor:
            hg_frac = max(hg_frac, hi / ii)
    max_hg_internal = hg_frac

    # Energy-balance drift relative to the initial total energy.
    energy_drift = None
    if te is not None:
        e0 = te[0]
        energy_drift = (max(te) - min(te)) / e0 if e0 else float("inf")

    # Peak kinetic / internal energy ratio.
    max_ke_internal = None
    if ke is not None:
        r = 0.0
        for ki, ii in zip(ke, ie):
            if ii > ie_floor:
                r = max(r, ki / ii)
        max_ke_internal = r

    reasons = []
    fail = False
    warn = False

    if max_hg_internal > 0.10:
        fail = True
        reasons.append(f"hourglass {max_hg_internal*100:.1f}% of internal energy (>10% FAIL)")
    elif max_hg_internal >= 0.05:
        warn = True
        reasons.append(f"hourglass {max_hg_internal*100:.1f}% of internal energy (5-10% acceptable)")
    else:
        reasons.append(f"hourglass {max_hg_internal*100:.1f}% of internal energy (<5% good)")

    if energy_drift is not None:
        if energy_drift > 0.05:
            fail = True
            reasons.append(f"energy balance drift {energy_drift*100:.1f}% (>5% FAIL)")
        else:
            reasons.append(f"energy balance drift {energy_drift*100:.1f}% (within +-5%)")

    if max_ke_internal is not None:
        if quasi_static:
            if max_ke_internal > 0.10:
                fail = True
                reasons.append(f"KE {max_ke_internal*100:.1f}% of IE - NOT quasi-static (>10% FAIL)")
            elif max_ke_internal >= 0.05:
                warn = True
                reasons.append(f"KE {max_ke_internal*100:.1f}% of IE - marginal for quasi-static (5-10%)")
            else:
                reasons.append(f"KE {max_ke_internal*100:.1f}% of IE - inertia negligible (good)")
        else:
            reasons.append(f"KE {max_ke_internal*100:.1f}% of IE (informational; not quasi-static)")

    if fail:
        verdict = "FAIL"
    elif warn:
        verdict = "WARN"
    else:
        verdict = "PASS"

    return {
        "max_hourglass_internal_pct": 100.0 * max_hg_internal,
        "energy_drift_pct": None if energy_drift is None else 100.0 * energy_drift,
        "max_ke_internal_pct": None if max_ke_internal is None else 100.0 * max_ke_internal,
        "quasi_static": quasi_static,
        "verdict": verdict,
        "reasons": reasons,
    }


def _report(res):
    print(f"max hourglass/internal = {res['max_hourglass_internal_pct']:.2f} %")
    if res["energy_drift_pct"] is not None:
        print(f"energy balance drift   = {res['energy_drift_pct']:.2f} %")
    if res["max_ke_internal_pct"] is not None:
        tag = " (quasi-static)" if res["quasi_static"] else ""
        print(f"max KE/internal        = {res['max_ke_internal_pct']:.2f} %{tag}")
    print(f"verdict                = {res['verdict']}")
    for r in res["reasons"]:
        print(f"  - {r}")


def _selftest():
    # Clean case: hourglass ~2%, total energy drifts ~1%, KE small vs IE.
    ie = [0.0, 10.0, 50.0, 100.0, 100.0]
    hg = [0.0, 0.2, 1.0, 2.0, 2.0]            # ~2% of IE
    te = [100.0, 100.5, 101.0, 100.8, 99.5]   # (max-min)/init = 1.5/100 = 1.5%
    ke = [0.0, 0.2, 1.0, 2.0, 1.0]            # peak KE/IE = 2/100 = 2% (<<1)
    good = energy_quality(ie, hg, total_energy=te, kinetic_energy=ke, quasi_static=True)
    _report(good)
    assert good["verdict"] == "PASS", good
    assert good["max_hourglass_internal_pct"] < 5.0, good

    print("-" * 40)

    # Bad case: hourglass 15% of internal energy -> FAIL.
    ie_bad = [0.0, 10.0, 50.0, 100.0]
    hg_bad = [0.0, 1.5, 7.5, 15.0]            # 15% of IE
    bad = energy_quality(ie_bad, hg_bad)
    _report(bad)
    assert bad["verdict"] == "FAIL", bad
    assert bad["max_hourglass_internal_pct"] > 10.0, bad

    print("\nself-test PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
