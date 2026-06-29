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
| Examples | `tests/test_examples.py` keeps runnable example output synchronized with real scripts and checks the single-mesh refusal template. | These examples are small fixtures, not full solver workflows. |
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

## Verified-Depth Map

This is the current evidence boundary by artifact type. It is intentionally conservative.

| Area | Current depth | What this proves | What it does not prove |
|---|---|---|---|
| Helper calculators | AUTHOR-TESTED by pytest known values and error-path checks for GCI, y+, units, rainflow, MAC/COMAC, and hourglass gates. | The shipped dependency-free scripts compute the documented examples and reject known bad inputs. | That any solver model using those scripts is correct. |
| Checked examples | AUTHOR-TESTED runnable GCI and units examples; one checked refusal template. | The examples stay synchronized with the scripts and claim discipline. | Full solver execution or benchmark-grade engineering accuracy. |
| Router claims | SOURCE-BACKED map in `references/claims-validation.md`; some rows are qualified. | The router's compressed claims have traceable standards/textbook/vendor sources. | Independent certification, exhaustive source excerpts, or proof that every reference-file claim is audited. |
| Reference guidance | Mixed: cited guidance across all reference files; provenance tags in 7/33 files. | The reference set is navigable and source-oriented. | Systematic author-executed verification across the full corpus. |
| Agent behavior | One live A/B snapshot on a Claude-family model plus structural eval cases. | Loading the skill changes answer shape toward modes, provenance, tool routing, and escalation. | Cross-model portability or statistically powered behavioral performance. |
| Executor integration | Not yet demonstrated in this repository. | The intended OASiS/PyMAPDL/etc. pairing is documented. | End-to-end solve evidence, result parsing, or SIGNOFF support. |

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
- It has one numeric GCI ground-truth eval case and small runnable examples, but no full NAFEMS-style benchmark suite.
- Agent portability beyond the tested hosts is text portability in principle, not a certified behavior guarantee.

## Next Evidence Milestones

1. Add one minimal OASiS or other open-source executor demo that produces a result plus a traceable manifest.
2. Expand provenance tags in the highest-risk automation references before broadening the reference set.
3. Run live evals across at least one non-Claude model family and keep the results separate from CI claims.
