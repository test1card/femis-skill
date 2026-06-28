#!/usr/bin/env python3
"""Modal Assurance Criterion (MAC) and Coordinate MAC (COMAC) for mode-shape
correlation in FEA model validation / model updating.

MAC quantifies the consistency (linear correlation) between two mode-shape
vectors using the conjugate (Hermitian) inner product:

    MAC(i, j) = |phi_i^H phi_j|^2 / ((phi_i^H phi_i) (phi_j^H phi_j))

It is bounded in [0, 1]: 1.0 means the two shapes are scalar multiples of each
other (the same mode), 0.0 means they are orthogonal (unrelated). It is
amplitude- and phase/sign-insensitive (it normalises), so it checks SHAPE
agreement, not frequency or modal mass. Standard uses:
  * test-vs-analysis pairing -- the MAC matrix between a measured (EMA) set and
    an FE set; the diagonal should be high (~>0.9) and off-diagonals low.
  * AutoMAC -- a set against itself; off-diagonal terms reveal modes not well
    separated (spatially aliased by a sparse sensor / DOF set).

**Complex modes supported.** The conjugate inner product makes MAC correct for
COMPLEX mode shapes (from damped / gyroscopic / FRF-derived analyses) as well as
real (normal) modes; for real input it reduces exactly to the real MAC.

**COMAC (Coordinate MAC)** is the per-DOF companion: across a set of already-correlated
mode PAIRS it returns one value per coordinate, low where the two models disagree -- it
localises WHERE the mismatch is, which MAC (a per-mode scalar) cannot. Two variants ship:
  * `comac()` (default, **signed / phase-aware**):
      COMAC(k) = |sum_k conj(A_k)*B_k|^2 / (sum|A_k|^2 * sum|B_k|^2).
    The per-coordinate correlation is summed *with sign* before squaring, so it drops at a
    DOF whose sign/phase is INCONSISTENT across the mode pairs -- the diagnostic most people
    mean by "coordinate-level correlation."
  * `amplitude_comac()`: the classic Lieven & Ewins form, sum_k |conj(A_k)*B_k| then squared
    -- amplitude-only, sign-robust; flags amplitude-ratio inconsistency but is blind to a
    sign/phase flip.
**Known limit of *both* (squared, sign-normalised) COMACs:** a coordinate that is
*consistently* sign-reversed across every mode (a reversed sensor / flipped local DOF) still
reads ~1.0 -- squaring normalises out the global sign. Use `coordinate_sign_flips()` to catch
that case (it flags DOFs whose summed real correlation is negative).

The vectors must be sampled at the SAME, consistently ORDERED degrees of freedom
(reduce/expand the FE shape to the measured DOFs first). Stdlib only; vectors are
plain lists/sequences of real or complex floats. Run `python mac.py` for a
self-test. See references/dynamics-nvh-acoustics.md.
"""
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

Number = complex  # real floats are a subset; functions accept float or complex


def _as_real(z) -> float:
    """Real part of a value that is mathematically real (e.g. phi^H phi)."""
    return z.real if isinstance(z, complex) else float(z)


def _inner(a: Sequence[Number], b: Sequence[Number]):
    """Conjugate (Hermitian) inner product <a, b> = sum(conj(a_i) * b_i).

    Reduces to the ordinary dot product when a is real.
    """
    if len(a) != len(b):
        raise ValueError(f"vector length mismatch: {len(a)} vs {len(b)}")
    return sum((ai.conjugate() if isinstance(ai, complex) else ai) * bi
               for ai, bi in zip(a, b))


def mac(phi_i: Sequence[Number], phi_j: Sequence[Number]) -> float:
    """MAC between two (real or complex) mode-shape vectors, in [0, 1].

    Returns 0.0 if either vector is all zeros (degenerate, no shape to compare).
    """
    cross = _inner(phi_i, phi_j)
    nii = _as_real(_inner(phi_i, phi_i))
    njj = _as_real(_inner(phi_j, phi_j))
    denom = nii * njj
    if denom == 0.0:
        return 0.0
    return (abs(cross) ** 2) / denom


def mac_matrix(set_A: Sequence[Sequence[Number]],
               set_B: Sequence[Sequence[Number]]) -> List[List[float]]:
    """Full MAC matrix M[i][j] = mac(set_A[i], set_B[j]).

    set_A, set_B : lists of mode-shape vectors (rows = modes). For an AutoMAC
                   pass the same set as both arguments.
    """
    return [[mac(a, b) for b in set_B] for a in set_A]


def _comac_setup(set_A, set_B, pairs):
    """Shared validation + default diagonal pairing for the COMAC helpers."""
    if not set_A or not set_B:
        raise ValueError("both mode sets must be non-empty")
    ndof = len(set_A[0])
    for v in list(set_A) + list(set_B):
        if len(v) != ndof:
            raise ValueError("all mode shapes must have the same DOF count")
    if pairs is None:
        pairs = [(i, i) for i in range(min(len(set_A), len(set_B)))]
    return ndof, pairs


def comac(set_A: Sequence[Sequence[Number]],
          set_B: Sequence[Sequence[Number]],
          pairs: Optional[Sequence[Tuple[int, int]]] = None) -> List[float]:
    """Coordinate MAC -- SIGNED / phase-aware (default). One value per DOF, in [0, 1].

        COMAC(k) = |sum_pairs conj(A_k) * B_k|^2
                   / (sum_pairs |A_k|^2 * sum_pairs |B_k|^2)

    The per-coordinate correlation is summed WITH sign/phase before squaring, so COMAC(k)
    drops where the two models disagree -- including a sign/phase flip that is INCONSISTENT
    across the matched mode pairs. A LOW value localises the DOF where they disagree (missing
    local stiffener, bad sensor, ...). Real or complex shapes.

    set_A, set_B : lists of mode-shape vectors, SAME DOF count & ordering.
    pairs        : list of (iA, iB) correlated mode-index pairs; default = diagonal
                   (0,0),(1,1),... over the shorter set.

    NOTE: like any squared COMAC this normalises out *global* sign, so a coordinate that is
    CONSISTENTLY reversed across every mode still reads ~1.0 -- use `coordinate_sign_flips()`
    for that. See `amplitude_comac()` for the classic (sign-robust) Lieven & Ewins variant.
    """
    ndof, pairs = _comac_setup(set_A, set_B, pairs)
    out: List[float] = []
    for k in range(ndof):
        s_ab: complex = 0j
        s_aa = 0.0
        s_bb = 0.0
        for ia, ib in pairs:
            ak = set_A[ia][k]
            bk = set_B[ib][k]
            akc = ak.conjugate() if isinstance(ak, complex) else ak
            s_ab += akc * bk
            s_aa += abs(ak) ** 2
            s_bb += abs(bk) ** 2
        denom = s_aa * s_bb
        out.append(0.0 if denom == 0.0 else (abs(s_ab) ** 2) / denom)
    return out


def amplitude_comac(set_A: Sequence[Sequence[Number]],
                    set_B: Sequence[Sequence[Number]],
                    pairs: Optional[Sequence[Tuple[int, int]]] = None) -> List[float]:
    """Classic Lieven & Ewins COMAC -- AMPLITUDE-only, sign-robust. One value per DOF.

        COMAC(k) = (sum_pairs |conj(A_k) * B_k|)^2
                   / (sum_pairs |A_k|^2 * sum_pairs |B_k|^2)

    Magnitudes are summed per pair, so this flags amplitude-ratio inconsistency across mode
    pairs but is BLIND to any sign/phase flip at a DOF. Prefer `comac()` unless you
    specifically want the sign-insensitive original.
    """
    ndof, pairs = _comac_setup(set_A, set_B, pairs)
    out: List[float] = []
    for k in range(ndof):
        s_ab = 0.0
        s_aa = 0.0
        s_bb = 0.0
        for ia, ib in pairs:
            ak = set_A[ia][k]
            bk = set_B[ib][k]
            akc = ak.conjugate() if isinstance(ak, complex) else ak
            s_ab += abs(akc * bk)
            s_aa += abs(ak) ** 2
            s_bb += abs(bk) ** 2
        denom = s_aa * s_bb
        out.append(0.0 if denom == 0.0 else (s_ab ** 2) / denom)
    return out


def coordinate_sign_flips(set_A: Sequence[Sequence[Number]],
                          set_B: Sequence[Sequence[Number]],
                          pairs: Optional[Sequence[Tuple[int, int]]] = None) -> List[int]:
    """DOF indices that are CONSISTENTLY sign/phase-reversed between the two sets.

    For each DOF k it sums the per-pair correlation s_k = sum_pairs conj(A_k)*B_k; a
    NEGATIVE real part means the coordinate points the opposite way in B vs A across the
    matched modes -- a reversed sensor / flipped local DOF. This is the one defect a squared
    COMAC (signed or amplitude) is mathematically blind to, because squaring normalises out
    global sign. Returns the sorted list of offending DOF indices (empty if none).
    """
    ndof, pairs = _comac_setup(set_A, set_B, pairs)
    flips: List[int] = []
    for k in range(ndof):
        s: complex = 0j
        for ia, ib in pairs:
            ak = set_A[ia][k]
            bk = set_B[ib][k]
            akc = ak.conjugate() if isinstance(ak, complex) else ak
            s += akc * bk
        if _as_real(s) < -1e-12:
            flips.append(k)
    return flips


def _selftest() -> None:
    # Identical mode sets -> AutoMAC is identity-like (diagonal 1, off-diag low).
    modes = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0],
    ]
    M = mac_matrix(modes, modes)
    print("AutoMAC of an identical set:")
    for row in M:
        print("  " + "  ".join(f"{v:5.3f}" for v in row))
    for i in range(len(modes)):
        assert abs(M[i][i] - 1.0) < 1e-12, M[i][i]      # diagonal = 1
    assert abs(M[0][1] - 0.0) < 1e-12, M[0][1]          # orthogonal pair -> 0

    # Sign / scale insensitivity: a scaled, flipped copy still correlates 1.0.
    a = [0.2, -0.5, 0.7, 0.1]
    b = [-2.0 * x for x in a]
    assert abs(mac(a, b) - 1.0) < 1e-12, mac(a, b)

    # Orthogonal vectors -> exactly 0.
    assert abs(mac([1.0, 0.0], [0.0, 3.0]) - 0.0) < 1e-12

    # Near-aligned pair -> high but < 1.
    aligned = mac([1.0, 1.0, 1.0], [1.0, 1.0, 0.95])
    assert 0.99 < aligned < 1.0, aligned
    print(f"\nmac(scaled/flipped) = {mac(a, b):.6f}  (sign/scale invariant)")
    print(f"mac(near-aligned)   = {aligned:.6f}  (high, < 1)")

    # Degenerate (zero) vector -> 0.0, no division blow-up.
    assert mac([0.0, 0.0], [1.0, 2.0]) == 0.0

    # Rectangular cross-MAC (test set 2 modes vs analysis set 3 modes).
    test = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    analysis = [[0.99, 0.05, 0.0], [0.0, 1.0, 0.02], [0.0, 0.0, 1.0]]
    X = mac_matrix(test, analysis)
    assert len(X) == 2 and len(X[0]) == 3, (len(X), len(X[0]))
    assert X[0][0] > 0.99 and X[1][1] > 0.99, X
    assert X[0][0] > X[0][2] and X[1][1] > X[1][0], X

    # --- COMPLEX modes: a complex mode vs its complex scalar multiple -> 1.0 ---
    ca = [1 + 1j, 0.5 - 0.2j, -0.3 + 0.4j]
    cb = [(2 - 1j) * x for x in ca]          # scaled by a complex constant
    assert abs(mac(ca, cb) - 1.0) < 1e-12, mac(ca, cb)
    # Two orthogonal complex vectors -> 0.
    assert abs(mac([1 + 0j, 0 + 0j], [0 + 0j, 1 + 2j])) < 1e-12
    print(f"mac(complex scaled) = {mac(ca, cb):.6f}  (complex/Hermitian correct)")

    # --- COMAC (signed, default): identical sets -> 1.0 at every DOF; a DOF the two
    #     sets disagree on -> low COMAC there, ~1 elsewhere. ---
    A = [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]
    assert all(abs(c - 1.0) < 1e-12 for c in comac(A, A)), comac(A, A)
    B = [[1.0, 1.0, 1.0], [1.0, 1.0, 0.0]]      # DOF 2 loses amplitude in mode 2 of B
    c = comac(A, B)
    assert abs(c[0] - 1.0) < 1e-12 and abs(c[1] - 1.0) < 1e-12, c
    assert c[2] < 0.99, c                        # DOF 2 flagged as the mismatch
    print(f"COMAC(A vs B)       = [{', '.join(f'{v:.3f}' for v in c)}]  (DOF 2 flagged)")

    # signed COMAC catches an INCONSISTENT sign flip that amplitude COMAC misses:
    As = [[1.0, 1.0], [1.0, 1.0]]
    Bs = [[1.0, 1.0], [1.0, -1.0]]              # DOF 1 flipped in mode 2 only
    assert comac(As, Bs)[1] < 1e-9, comac(As, Bs)            # signed -> ~0 (cancels)
    assert abs(amplitude_comac(As, Bs)[1] - 1.0) < 1e-12     # amplitude -> blind, 1.0
    print(f"signed COMAC(flip)  = {comac(As, Bs)[1]:.3f}   "
          f"amplitude COMAC = {amplitude_comac(As, Bs)[1]:.3f}")

    # a CONSISTENTLY reversed coordinate is invisible to squared COMAC -> sign helper:
    Br = [[1.0, -1.0], [1.0, -1.0]]             # DOF 1 reversed in EVERY mode
    assert abs(comac(As, Br)[1] - 1.0) < 1e-12, comac(As, Br)   # COMAC blind -> 1.0
    assert coordinate_sign_flips(As, Br) == [1], coordinate_sign_flips(As, Br)
    assert coordinate_sign_flips(As, As) == []
    print(f"coordinate_sign_flips(reversed DOF 1) = {coordinate_sign_flips(As, Br)}")

    print("OK: self-test passed.")


if __name__ == "__main__":
    _selftest()
