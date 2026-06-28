#!/usr/bin/env python3
"""Consistent-units and 1g mass sanity checks for FE models.

FE solvers are unit-agnostic -- they trust whatever numbers you feed. The classic
silent corruptor is DENSITY entered in the wrong system: a static gravity run may
still pass (the g-error cancels) while every dynamic / modal / transient-thermal
result is wrong (frequencies scale as 1/sqrt(rho)).

This tool:
  (1) lists coherent unit systems with their reference values (steel),
  (2) flags a density that looks like the WRONG system,
  (3) runs the 1g mass check:  sum(rho*V)*g  == total reaction under 1g (within ~1%).

In MAPDL/PyMAPDL `/UNITS` is METADATA ONLY -- it does not convert anything; you stay
responsible for a coherent set. See SKILL.md "Consistent units".

Vendor-neutral; no project data. Run `python units_check.py` for a self-test.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class UnitSystem:
    name: str
    length: str
    force: str
    stress: str
    mass: str
    density_steel: float   # coherent density of structural steel in this system
    E_steel: float         # Young's modulus of steel in this system
    g: float               # standard gravity in this system


# Coherent (self-consistent) unit systems. Values are for structural steel,
# textbook orders of magnitude -- verify against your own material data.
SYSTEMS = {
    "SI-m":      UnitSystem("SI-m",      "m",  "N",   "Pa",  "kg",      7850.0,   2.00e11, 9.81),
    "mm-t-s":    UnitSystem("mm-t-s",    "mm", "N",   "MPa", "tonne",   7.85e-9,  2.00e5,  9810.0),
    "mm-kg-ms":  UnitSystem("mm-kg-ms",  "mm", "kN",  "GPa", "kg",      7.85e-6,  2.00e2,  9.81e-3),
    "cgs":       UnitSystem("cgs",       "cm", "dyn", "Ba",  "g",       7.85,     2.00e12, 981.0),
    "in-lbf-s":  UnitSystem("in-lbf-s",  "in", "lbf", "psi", "slinch",  7.34e-4,  2.90e7,  386.1),
}


def nearest_system(density: float, rel_tol: float = 0.25):
    """Return (name, system) whose steel density best matches `density`
    within rel_tol (decades, log10), else (None, None)."""
    best, best_err = None, float("inf")
    for name, s in SYSTEMS.items():
        err = abs(math.log10(density / s.density_steel))
        if err < best_err:
            best, best_err = name, err
    # rel_tol ~0.25 decade ~ factor 1.8 tolerance band
    return (best, SYSTEMS[best]) if best_err <= rel_tol else (None, None)


def check_density(declared_system: str, density: float) -> str:
    """Warn if `density` looks like it belongs to a different unit system than
    the one declared. Returns a human-readable verdict string."""
    if density <= 0:
        raise ValueError("density must be positive")
    if declared_system not in SYSTEMS:
        raise ValueError(f"unknown system {declared_system!r}; choose from {list(SYSTEMS)}")
    s = SYSTEMS[declared_system]
    match_name, _ = nearest_system(density)
    if match_name == declared_system:
        return f"OK: density {density:g} is consistent with {declared_system} (steel ~ {s.density_steel:g})."
    if match_name is None:
        return (f"WARNING: density {density:g} matches NO known steel value; "
                f"{declared_system} expects ~ {s.density_steel:g}. Verify the material/units.")
    return (f"WARNING: density {density:g} looks like '{match_name}' units, but you declared "
            f"'{declared_system}' (which expects steel ~ {s.density_steel:g}). "
            f"This is the classic silent unit corruptor -- dynamics/thermal will be wrong.")


def gravity_mass_check(total_mass: float, g: float, measured_reaction: float,
                       tol: float = 0.01) -> str:
    """1g mass check: the total reaction under a 1g gravity load must equal
    total_mass * g within `tol` (default 1%). Catches unit/density errors that
    statics otherwise hides. total_mass = sum(rho*V) in coherent units."""
    if total_mass <= 0 or g <= 0:
        raise ValueError("total_mass and g must be positive")
    expected = total_mass * g
    rel = abs(measured_reaction - expected) / abs(expected)
    verdict = "OK" if rel <= tol else "FAIL"
    return (f"{verdict}: expected {expected:g}, got {measured_reaction:g} "
            f"(rel err {rel*100:.3f}%, tol {tol*100:.1f}%).")


def _selftest() -> None:
    print("Coherent unit systems (steel):")
    print(f"{'system':>10} {'len':>4} {'force':>5} {'stress':>6} {'mass':>8} "
          f"{'rho_steel':>10} {'g':>9}")
    for s in SYSTEMS.values():
        print(f"{s.name:>10} {s.length:>4} {s.force:>5} {s.stress:>6} {s.mass:>8} "
              f"{s.density_steel:>10g} {s.g:>9g}")
    print()
    # Correct: SI density in an SI model.
    print(check_density("SI-m", 7850.0))
    # The classic trap: SI density left in a mm-t-s model.
    print(check_density("mm-t-s", 7850.0))
    # Correct mm-t-s density.
    print(check_density("mm-t-s", 7.85e-9))
    print()
    # 1g mass check: 10 kg in SI -> 98.1 N reaction.
    print(gravity_mass_check(total_mass=10.0, g=9.81, measured_reaction=98.1))
    print(gravity_mass_check(total_mass=10.0, g=9.81, measured_reaction=110.0))

    # Assertions.
    assert check_density("mm-t-s", 7850.0).startswith("WARNING")
    assert check_density("SI-m", 7850.0).startswith("OK")
    assert gravity_mass_check(10.0, 9.81, 98.1).startswith("OK")
    print("\nOK: self-test passed.")


if __name__ == "__main__":
    _selftest()
