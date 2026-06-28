#!/usr/bin/env python3
"""Pytest suite for the public FEM/CAE helper scripts.

Each script under ``scripts/`` ships a ``_selftest()`` with hand-verified
reference values; this suite imports the modules directly and re-asserts those
same known-good results so the runnable helpers are demonstrably correct in CI.

Stdlib + pytest only; vendor-neutral, no project data.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the sibling scripts/ directory importable.
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import gci          # noqa: E402
import yplus        # noqa: E402
import units_check  # noqa: E402
import rainflow     # noqa: E402
import mac          # noqa: E402
import hourglass_check  # noqa: E402


# --------------------------------------------------------------------------- #
# gci.py
# --------------------------------------------------------------------------- #
def _gci_doc_example():
    # The docstring example: (h1,f1)=(1.0,305.2), (h2,f2)=(2.0,306.1),
    # (h3,f3)=(4.0,308.5), r ~ 2 refinement on peak temperature [K].
    return gci.gci(1.0, 305.20, 2.0, 306.10, 4.0, 308.50)


def test_gci_observed_order_near_two():
    res = _gci_doc_example()
    # e32/e21 = 2.4/0.9 = 2.667, p = log(2.667)/log(2) ~ 1.415.
    assert res["observed_order_p"] == pytest.approx(1.415, abs=0.01)


def test_gci_asymptotic_ratio_near_one():
    res = _gci_doc_example()
    assert res["asymptotic_ratio"] == pytest.approx(0.997, abs=0.01)


def test_gci_fine_value_small():
    res = _gci_doc_example()
    # Fine-grid GCI should be a small percentage (well under the 3% gate).
    assert 0.0 < res["gci_fine_pct"] < 3.0


def test_gci_monotone_and_pass_verdict():
    res = _gci_doc_example()
    assert res["monotonic"] is True
    assert gci._verdict(res).startswith("PASS")


def test_gci_richardson_close_to_finest():
    res = _gci_doc_example()
    # QoI decreases monotonically as the mesh refines (308.5 -> 306.1 -> 305.2), so
    # the Richardson extrapolate (Celik form (r^p*f1 - f2)/(r^p - 1)) continues the
    # trend just BELOW the finest reading (~304.66) -- NOT above it.
    assert res["richardson_f_exact"] == pytest.approx(304.66, abs=0.1)
    assert res["richardson_f_exact"] < 305.20


def test_gci_requires_ordered_grids():
    with pytest.raises(ValueError):
        gci.gci(2.0, 305.2, 1.0, 306.1, 4.0, 308.5)  # h1 !< h2


def test_gci_rejects_identical_fine_pair():
    with pytest.raises(ValueError):
        gci.gci(1.0, 305.2, 2.0, 305.2, 4.0, 308.5)  # e21 == 0


def test_gci_rejects_diverging_data():
    # QoI change GROWS as the mesh refines (R = e21/e32 = 1/0.2 = 5 >= 1):
    # diverging, must NOT be reported as a passing GCI (regression for the
    # original false-PASS on gci(1,100,2,101,4,101.2)).
    res = gci.gci(1.0, 100.0, 2.0, 101.0, 4.0, 101.2)
    assert res["convergence_ratio_R"] == pytest.approx(5.0, abs=1e-6)
    assert res["converging"] is False
    assert res["valid"] is False
    assert gci._verdict(res).startswith("REJECT")


def test_gci_rejects_oscillatory_data():
    # QoI swings either side of the limit (R < 0): oscillatory, reject.
    res = gci.gci(1.0, 100.0, 2.0, 101.0, 4.0, 100.5)
    assert res["convergence_ratio_R"] < 0.0
    assert res["monotonic"] is False
    assert gci._verdict(res).startswith("REJECT")


def test_gci_unequal_ratio_recovers_true_order():
    # f = 100 + h^2 on UNEQUAL ratios (r21=1.5, r32=2): true p=2. The Celik
    # iterative solve must recover ~2 (the equal-ratio shortcut gives ~4.16).
    res = gci.gci(1.0, 101.0, 1.5, 102.25, 3.0, 109.0)
    assert res["observed_order_p"] == pytest.approx(2.0, abs=0.05)
    assert res["converging"] is True
    assert gci._verdict(res).startswith("PASS")


# --------------------------------------------------------------------------- #
# yplus.py
# --------------------------------------------------------------------------- #
def _yplus_air():
    # Air at 20 C over a 1 m plate at 50 m/s.
    return dict(U=50.0, L=1.0, rho=1.225, mu=1.81e-5)


def test_yplus_first_node_distance_documented():
    r = yplus.estimate_first_cell(1.0, **_yplus_air())
    # Documented: ~7.8 um for target y+ = 1 (within 0.1 um).
    assert r.first_node_distance * 1e6 == pytest.approx(7.8, abs=0.1)


def test_yplus_cell_height_is_twice_node_distance():
    r = yplus.estimate_first_cell(1.0, **_yplus_air())
    assert r.first_cell_height_cellcentred == pytest.approx(2.0 * r.first_node_distance)


def test_yplus_buffer_layer_flagged():
    r = yplus.estimate_first_cell(10.0, **_yplus_air())
    assert "BUFFER LAYER" in r.regime


def test_yplus_wall_resolved_regime():
    r = yplus.estimate_first_cell(1.0, **_yplus_air())
    assert "wall-resolved" in r.regime


def test_yplus_wall_function_regime():
    r = yplus.estimate_first_cell(50.0, **_yplus_air())
    assert "wall-function" in r.regime


def test_yplus_reynolds_number():
    r = yplus.estimate_first_cell(1.0, **_yplus_air())
    # Re_L = rho*U*L/mu = 1.225*50/1.81e-5 ~ 3.39e6.
    assert r.Re_L == pytest.approx(3.385e6, rel=1e-3)


def test_yplus_distance_scales_with_target():
    air = _yplus_air()
    r1 = yplus.estimate_first_cell(1.0, **air)
    r50 = yplus.estimate_first_cell(50.0, **air)
    # y is linear in the y+ target (same friction velocity).
    assert r50.first_node_distance == pytest.approx(50.0 * r1.first_node_distance, rel=1e-9)


def test_yplus_rejects_nonpositive_input():
    with pytest.raises(ValueError):
        yplus.estimate_first_cell(1.0, -50.0, 1.0, 1.225, 1.81e-5)


# --------------------------------------------------------------------------- #
# units_check.py
# --------------------------------------------------------------------------- #
def test_units_si_density_ok():
    assert units_check.check_density("SI-m", 7850.0).startswith("OK")


def test_units_si_density_in_mm_t_s_warns():
    # The classic silent unit corruptor: SI density in a mm-t-s model.
    assert units_check.check_density("mm-t-s", 7850.0).startswith("WARNING")


def test_units_correct_mm_t_s_density_ok():
    assert units_check.check_density("mm-t-s", 7.85e-9).startswith("OK")


def test_units_gravity_mass_check_ok():
    # 10 kg in SI -> 98.1 N reaction.
    assert units_check.gravity_mass_check(10.0, 9.81, 98.1).startswith("OK")


def test_units_gravity_mass_check_fail():
    assert units_check.gravity_mass_check(10.0, 9.81, 110.0).startswith("FAIL")


def test_units_check_density_rejects_negative():
    with pytest.raises(ValueError):
        units_check.check_density("SI-m", -1.0)


def test_units_check_density_rejects_unknown_system():
    with pytest.raises(ValueError):
        units_check.check_density("bogus-system", 7850.0)


def test_units_gravity_rejects_nonpositive():
    with pytest.raises(ValueError):
        units_check.gravity_mass_check(-10.0, 9.81, 98.1)


def test_units_nearest_system_identifies_si():
    name, _ = units_check.nearest_system(7850.0)
    assert name == "SI-m"


# --------------------------------------------------------------------------- #
# rainflow.py
# --------------------------------------------------------------------------- #
ASTM_E1049 = [-2.0, 1.0, -3.0, 5.0, -1.0, 3.0, -4.0, 4.0, -2.0]


def _grouped_by_range(cycles):
    by_range: dict = {}
    for c in cycles:
        key = round(c.range, 6)
        by_range[key] = by_range.get(key, 0.0) + c.count
    return by_range


def test_rainflow_astm_grouped_counts():
    cycles = rainflow.count_cycles(ASTM_E1049, already_reversals=True)
    grouped = {k: round(v, 6) for k, v in _grouped_by_range(cycles).items()}
    assert grouped == {3.0: 0.5, 4.0: 1.5, 6.0: 0.5, 8.0: 1.0, 9.0: 0.5}


def test_rainflow_astm_total_count():
    cycles = rainflow.count_cycles(ASTM_E1049, already_reversals=True)
    assert sum(c.count for c in cycles) == pytest.approx(4.0)


def test_rainflow_single_full_cycle_is_range_four():
    cycles = rainflow.count_cycles(ASTM_E1049, already_reversals=True)
    full = sorted(round(c.range, 6) for c in cycles if c.count == 1.0)
    assert full == [4.0]


def test_rainflow_count_conservation():
    open_hist = [0.0, 3.0, 1.0, 4.0, 2.0, 5.0]
    cycles = rainflow.count_cycles(open_hist, already_reversals=True)
    assert sum(c.count for c in cycles) == pytest.approx((len(open_hist) - 1) / 2.0)


def test_rainflow_turning_points_strips_ramp_and_plateau():
    raw = [0.0, 1.0, 2.0, 3.0, 2.0, 2.0, 1.0, 2.0, 0.0]
    assert rainflow.turning_points(raw) == [0.0, 3.0, 1.0, 2.0, 0.0]


def test_rainflow_miner_one_full_cycle_is_inverse_N():
    A, m = 1.0e12, 3.0
    N = rainflow.basquin_life(100.0, A=A, m=m)
    one = [rainflow.Cycle(100.0, 0.0, 1.0)]
    D1 = rainflow.miner_damage(one, A=A, m=m)
    assert D1 == pytest.approx(1.0 / N, rel=1e-12)


def test_rainflow_miner_is_additive():
    A, m = 1.0e12, 3.0
    one = [rainflow.Cycle(100.0, 0.0, 1.0)]
    D1 = rainflow.miner_damage(one, A=A, m=m)
    D2 = rainflow.miner_damage(one * 2, A=A, m=m)
    assert D2 == pytest.approx(2.0 * D1, rel=1e-12)


def test_rainflow_miner_callable_matches_basquin():
    A, m = 1.0e12, 3.0
    one = [rainflow.Cycle(100.0, 0.0, 1.0)]
    D_basquin = rainflow.miner_damage(one, A=A, m=m)
    D_callable = rainflow.miner_damage(one, sn_curve=lambda s: A * s ** -m)
    assert D_callable == pytest.approx(D_basquin, rel=1e-12)


def test_rainflow_miner_requires_curve_or_coefficients():
    with pytest.raises(ValueError):
        rainflow.miner_damage([rainflow.Cycle(100.0, 0.0, 1.0)])


# --------------------------------------------------------------------------- #
# mac.py
# --------------------------------------------------------------------------- #
def test_mac_identical_is_one():
    v = [0.2, -0.5, 0.7, 0.1]
    assert mac.mac(v, v) == pytest.approx(1.0, abs=1e-12)


def test_mac_orthogonal_is_zero():
    assert mac.mac([1.0, 0.0], [0.0, 3.0]) == pytest.approx(0.0, abs=1e-12)


def test_mac_sign_scale_invariant():
    a = [0.2, -0.5, 0.7, 0.1]
    b = [-2.0 * x for x in a]
    assert mac.mac(a, b) == pytest.approx(1.0, abs=1e-12)


def test_mac_complex_scaled_is_one():
    ca = [1 + 1j, 0.5 - 0.2j, -0.3 + 0.4j]
    cb = [(2 - 1j) * x for x in ca]
    assert mac.mac(ca, cb) == pytest.approx(1.0, abs=1e-12)


def test_mac_complex_orthogonal_is_zero():
    assert mac.mac([1 + 0j, 0 + 0j], [0 + 0j, 1 + 2j]) == pytest.approx(0.0, abs=1e-12)


def test_mac_degenerate_zero_vector_is_zero():
    assert mac.mac([0.0, 0.0], [1.0, 2.0]) == 0.0


def test_mac_near_aligned_high_but_below_one():
    aligned = mac.mac([1.0, 1.0, 1.0], [1.0, 1.0, 0.95])
    assert 0.99 < aligned < 1.0


def test_mac_matrix_automac_diagonal():
    modes = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0],
    ]
    M = mac.mac_matrix(modes, modes)
    for i in range(len(modes)):
        assert M[i][i] == pytest.approx(1.0, abs=1e-12)
    assert M[0][1] == pytest.approx(0.0, abs=1e-12)


def test_mac_matrix_rectangular_pairs_on_diagonal():
    test = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    analysis = [[0.99, 0.05, 0.0], [0.0, 1.0, 0.02], [0.0, 0.0, 1.0]]
    X = mac.mac_matrix(test, analysis)
    assert len(X) == 2 and len(X[0]) == 3
    assert X[0][0] > 0.99 and X[1][1] > 0.99
    assert X[0][0] > X[0][2] and X[1][1] > X[1][0]


def test_comac_identical_all_one():
    A = [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]
    assert all(c == pytest.approx(1.0, abs=1e-12) for c in mac.comac(A, A))


def test_comac_flags_inconsistent_dof():
    A = [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]
    B = [[1.0, 1.0, 1.0], [1.0, 1.0, 0.0]]
    c = mac.comac(A, B)
    assert c[0] == pytest.approx(1.0, abs=1e-12)
    assert c[1] == pytest.approx(1.0, abs=1e-12)
    assert c[2] < 0.99  # the low-amplitude DOF is flagged


def test_mac_length_mismatch_raises():
    with pytest.raises(ValueError):
        mac.mac([1.0, 2.0], [1.0, 2.0, 3.0])


def test_comac_empty_set_raises():
    with pytest.raises(ValueError):
        mac.comac([], [[1.0, 2.0]])


# --------------------------------------------------------------------------- #
# hourglass_check.py
# --------------------------------------------------------------------------- #
def test_hourglass_clean_case_passes():
    ie = [0.0, 10.0, 50.0, 100.0, 100.0]
    hg = [0.0, 0.2, 1.0, 2.0, 2.0]            # ~2% of IE
    te = [100.0, 100.5, 101.0, 100.8, 99.5]   # drift 1.5%
    ke = [0.0, 0.2, 1.0, 2.0, 1.0]            # peak KE/IE 2%
    res = hourglass_check.energy_quality(
        ie, hg, total_energy=te, kinetic_energy=ke, quasi_static=True)
    assert res["verdict"] == "PASS"
    assert res["max_hourglass_internal_pct"] < 5.0


def test_hourglass_15pct_case_fails():
    ie_bad = [0.0, 10.0, 50.0, 100.0]
    hg_bad = [0.0, 1.5, 7.5, 15.0]            # 15% of IE
    res = hourglass_check.energy_quality(ie_bad, hg_bad)
    assert res["verdict"] == "FAIL"
    assert res["max_hourglass_internal_pct"] > 10.0


def test_hourglass_marginal_case_warns():
    ie = [0.0, 100.0, 100.0]
    hg = [0.0, 7.0, 7.0]                       # 7% -> 5-10% acceptable band
    res = hourglass_check.energy_quality(ie, hg)
    assert res["verdict"] == "WARN"
    assert 5.0 <= res["max_hourglass_internal_pct"] <= 10.0


def test_hourglass_energy_drift_fail():
    ie = [10.0, 50.0, 100.0]
    hg = [0.1, 0.5, 1.0]                       # 1% hourglass, fine
    te = [100.0, 105.0, 110.0]                # drift 10% -> FAIL
    res = hourglass_check.energy_quality(ie, hg, total_energy=te)
    assert res["verdict"] == "FAIL"
    assert res["energy_drift_pct"] == pytest.approx(10.0, abs=1e-6)


def test_hourglass_quasi_static_high_ke_fails():
    ie = [10.0, 100.0]
    hg = [0.1, 1.0]
    ke = [5.0, 50.0]                           # KE/IE 50% -> not quasi-static
    res = hourglass_check.energy_quality(ie, hg, kinetic_energy=ke, quasi_static=True)
    assert res["verdict"] == "FAIL"


def test_hourglass_rejects_negative_energy():
    with pytest.raises(ValueError):
        hourglass_check.energy_quality([10.0, -1.0], [0.1, 0.2])


def test_hourglass_rejects_length_mismatch():
    with pytest.raises(ValueError):
        hourglass_check.energy_quality([10.0, 20.0], [0.1])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
