# GCI Known Values

This example uses the documented three-grid data set from `scripts/gci.py` and `tests/test_scripts.py`.

Input:

| Grid | h | QoI |
|---|---:|---:|
| fine | 1.0 | 305.20 |
| medium | 2.0 | 306.10 |
| coarse | 4.0 | 308.50 |

Run from the repository root:

```bash
python scripts/gci.py 1.0 305.20 2.0 306.10 4.0 308.50
```

Expected key values:

- observed order `p ~= 1.415`
- Richardson extrapolated value `f_exact ~= 304.66`
- fine-grid GCI `~= 0.221%`
- asymptotic ratio `~= 0.997`

This is a calculator example, not a solver benchmark. It proves the GCI helper and the claim phrasing around
mesh-independence arithmetic.
