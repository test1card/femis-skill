# Unit-Density Corruption

This example catches a common FE unit-system failure: using SI steel density (`7850 kg/m^3`) in a `mm-t-s`
model, where steel density should be about `7.85e-9 t/mm^3`.

Run from the repository root:

```bash
python -c "import sys; sys.path.insert(0, 'scripts'); import units_check; print(units_check.check_density('mm-t-s', 7850.0))"
```

Expected behavior: warn that the supplied density looks like SI-m, not `mm-t-s`. This can pass static solves but
corrupt dynamics, gravity, and thermal-mass reasoning.
