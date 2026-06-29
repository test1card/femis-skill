# Changelog

## v1.0.1 - 2026-06-29

Release polish and evidence hardening after the initial public tag.

- Fixed `SKILL.md` YAML frontmatter so the skill entrypoint parses cleanly.
- Quoted the GitHub Actions `"on"` trigger key for YAML 1.1-compatible tooling.
- Updated open-source FEM executor guidance from archived Open FEM Agent to OASiS.
- Added `EVIDENCE.md` to state what is verified, sourced, and not yet proven.
- Added generated provenance coverage in `references/provenance-coverage.md`.
- Added checked examples for GCI known values, unit-density corruption, and single-mesh claim refusal.
- Added numeric ground-truth scoring support to `scripts/run_skill_evals.py`.
- Clarified that `references/claims-validation.md` is a sourcing map, not an audit certificate.

Verification for this release:

- `pytest tests/ -q`
- `python scripts/run_skill_evals.py`
- `python scripts/provenance_coverage.py --check`
- script self-tests for GCI, y+, units, rainflow, MAC/COMAC, and hourglass checks
- `actionlint` for `.github/workflows/ci.yml`
- `claude plugin validate .claude-plugin/plugin.json`

## v1.0.0 - 2026-06-29

Initial public release of `femis` as a governance/decision Agent Skill for FEM/CAE:

- `SKILL.md` router with execution modes, pre-claim self-check, and headless-vs-human contract.
- 33 reference files covering FEM/CAE workflow, failure disciplines, automation boundaries, and V&V/UQ.
- Dependency-free helper scripts for GCI, y+, units, rainflow/Miner, MAC/COMAC, and hourglass checks.
- Structural eval set and live A/B results documenting the governance effect.
