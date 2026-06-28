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

**COMAC (Coordinate MAC)** is the per-DOF companion (Lieven & Ewins): across a
set of already-correlated mode PAIRS it returns one value per coordinate, low
where the two models disagree spatially -- it localises WHERE the mismatch is,
which MAC (a per-mode scalar) cannot. Like MAC, the canonical Lieven & Ewins COMAC
sums per-pair |conj(A_k)*B_k| magnitudes, so it is amplitude/sign-insensitive by
construction: it flags amplitude-ratio inconsistency across mode pairs, NOT a pure
sign/phase flip at a DOF.

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


def comac(set_A: Sequence[Sequence[Number]],
          set_B: Sequence[Sequence[Number]],
          pairs: Optional[Sequence[Tuple[int, int]]] = None) -> List[float]:
    """Coordinate MAC: one value per DOF, in [0, 1], across matched mode pairs.

        COMAC(k) = (sum_pairs |conj(A_k) * B_k|)^2
                   / (sum_pairs |A_k|^2 * sum_pairs |B_k|^2)

    set_A, set_B : lists of mode-shape vectors, SAME DOF count & ordering.
    pairs        : list of (iA, iB) correlated mode-index pairs; default pairs
                   them on the diagonal (0,0),(1,1),... over the shorter set.
    Returns a list of length = number of DOFs. A LOW value at DOF k flags the
    coordinate where the two models disagree most (e.g. a missing local stiffener
    or a bad sensor). Complex shapes supported.
    """
    if not set_A or not set_B:
        raise ValueError("both mode sets must be non-empty")
    ndof = len(set_A[0])
    for v in list(set_A) + list(set_B):
        if len(v) != ndof:
            raise ValueError("all mode shapes must have the same DOF count")
    if pairs is None:
        pairs = [(i, i) for i in range(min(len(set_A), len(set_B)))]

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

    # --- COMAC: identical sets -> 1.0 at every DOF; a DOF the two sets disagree
    #     on -> low COMAC there, ~1 elsewhere. ---
    A = [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]
    assert all(abs(c - 1.0) < 1e-12 for c in comac(A, A)), comac(A, A)
    # COMAC is sign/scale-insensitive per DOF (it uses |A_k*B_k|); it flags a DOF
    # whose AMPLITUDE ratio is INCONSISTENT across mode pairs. Here DOF 2 loses
    # amplitude in mode 2 of model B only -> COMAC(2) drops, others stay ~1.
    B = [[1.0, 1.0, 1.0], [1.0, 1.0, 0.0]]
    c = comac(A, B)
    assert abs(c[0] - 1.0) < 1e-12 and abs(c[1] - 1.0) < 1e-12, c
    assert c[2] < 0.99, c                       # DOF 2 flagged as the mismatch
    print(f"COMAC(A vs B)       = [{', '.join(f'{v:.3f}' for v in c)}]  (DOF 2 flagged)")

    print("OK: self-test passed.")


if __name__ == "__main__":
    _selftest()
