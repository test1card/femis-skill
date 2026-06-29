# Evidence & Maturity

This file states what is actually checked in this repository, what is only sourced, and what remains unproven.
It is intentionally conservative: `femis` is a governance skill, not a certified CAE solver or a sign-off authority.

## What Is Verified By CI

Run:

```bash
python -m pytest tests/ -q
python scripts/run_skill_evals.py
python scripts/provenance_coverage.py --check
```

These commands verify:

| Area | Evidence | Boundary |
|---|---|---|
| Calculator helpers | `tests/test_scripts.py` checks known values and error paths for GCI, y+, units, rainflow, MAC/COMAC, and hourglass energy gates. | This validates the helper scripts, not a solver model. |
| Skill metadata | `tests/test_skill_metadata.py` parses `SKILL.md` frontmatter as YAML and checks required discovery fields. | This validates packaging, not engineering behavior. |
| Eval harness | `tests/test_eval_scoring.py` checks response scoring, including numeric ground-truth matching. | The scorer is a heuristic first-pass signal. |
| Eval set structure | `scripts/run_skill_evals.py` validates referenced files/scripts, expected modes, behaviors, and numeric expectations. | Most evals are activation/behavior cases, not benchmark problems. |
| Provenance coverage | `scripts/provenance_coverage.py --check` keeps `references/provenance-coverage.md` in sync with `references/*.md`. | Tag coverage is partial; untagged files can still be cited, but are not author-executed evidence. |

## What Is Sourced, Not Certified

- `references/claims-validation.md` is a sourcing map for the router's load-bearing claims. It is useful for audit,
  but it is not an independent certification artifact.
- The detailed reference files include citations and source lists. They should be treated as engineering guidance to
  verify against the user's solver, geometry, material data, standards, and consequence level.
- Provenance tags are currently uneven. See `references/provenance-coverage.md` for the current coverage snapshot.

## Live Agent Evidence

`evals/RESULTS.md` records a single-family live A/B run. It shows that loading `femis` changes the answer shape toward
mode labels, provenance, tool routing, and refusal/escalation discipline.

Limitations:

- one model family
- small number of cases
- heuristic scoring
- mostly governance behavior, not numeric benchmark correctness

## What Is Not Proven Yet

- `femis` has not been demonstrated as a full end-to-end executor integration with OASiS, PyMAPDL, Abaqus, COMSOL, or
  another solver driver in this repository.
- It does not mesh, solve, parse `.rst`/`.op2`, or authorize engineering sign-off by itself.
- It has one numeric GCI ground-truth eval case, but no full NAFEMS-style benchmark suite.
- Agent portability beyond the tested hosts is text portability in principle, not a certified behavior guarantee.

## Next Evidence Milestones

1. Add runnable examples under `examples/` for GCI, unit corruption, and single-mesh claim refusal.
2. Add one minimal OASiS or other open-source executor demo that produces a result plus a traceable manifest.
3. Expand provenance tags in the highest-risk automation references before broadening the reference set.
4. Run live evals across at least one non-Claude model family and keep the results separate from CI claims.
