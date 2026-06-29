# Examples

These examples are intentionally small and reproducible. They show how `femis` turns a raw helper result or a risky
prompt into a bounded engineering claim.

| Example | Type | What it demonstrates |
|---|---|---|
| `gci-known-values` | runnable calculator | A three-grid GCI calculation with known numeric output. |
| `units-density-corruption` | runnable calculator | The classic SI-density-in-mm-t-s unit mistake. |
| `single-mesh-claim-refusal` | governance template | Why a single-mesh peak stress must not be reported as an engineering result. |

Run the runnable examples from the repository root:

```bash
python scripts/gci.py 1.0 305.20 2.0 306.10 4.0 308.50
python -c "import sys; sys.path.insert(0, 'scripts'); import units_check; print(units_check.check_density('mm-t-s', 7850.0))"
```
