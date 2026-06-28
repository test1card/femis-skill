# Contributing to femis

Thanks for improving this skill. The goal is to make the agent more reliable on real FEA/CAE problems — not to expand its scope or inflate the router.

## What to contribute

**High value:**
- `[AUTHOR-VERIFIED]` headless recipes you have run on a real solver install (flag the solver version).
- Platform-specific gotchas that cost you time (contact KEYOPT traps, batch non-convergence silences, license error messages, etc.).
- Benchmarks or sanity-check cases with known answers (NAFEMS, Roark, analytical).
- Corrections to wrong or misleading values (material data, convergence criteria, element behaviour).

**Lower value (still welcome):**
- `[DOCS-ONLY]` recipes clearly tagged as such — useful if the docs are precise, misleading if paraphrased carelessly.
- New solver/platform coverage — add to `references/software-landscape.md` first; add a new reference file only when there is real depth to justify it.

**Not wanted:**
- Marketing language, feature lists, or paraphrased vendor docs presented as verified behaviour.
- Content that belongs in `SKILL.md` rather than a `references/` file — keep the router lean.
- Solver output dumps, large binary artefacts, or project-specific file paths.

## Confidence tags

Every headless recipe or numerical value should carry one tag:

| Tag | Meaning |
|---|---|
| `[AUTHOR-VERIFIED]` | Run on a real model; results checked. Include solver + version. |
| `[VERIFIED-web]` | Vendor-documented and cross-checked online; not run locally. |
| `[DOCS-ONLY]` | Taken from official documentation; not executed here. |
| `[NEEDS-HW-TEST]` | Plausible but untested; requires a licensed install to confirm. |

Treat any non-`[AUTHOR-VERIFIED]` entry as a hypothesis. Run a SMOKE reproducer before relying on it for ENGINEERING/SIGNOFF.

## Structure rules

- `SKILL.md` is the router. It must stay a concise decision layer — add a router entry, then put depth in `references/`.
- One topic per reference file. Cross-link with `references/<file>.md` rather than duplicating content.
- `scripts/` holds standalone, dependency-light utilities (pure Python stdlib preferred). Add a docstring explaining inputs/outputs and units.
- No project-specific paths, hostnames, or credentials anywhere.

## Workflow

1. Fork the repo and create a branch (`fix/contact-keyopt-trap`, `add/openfoam-recipes`, etc.).
2. Make your changes. If adding a new reference file, add a one-line entry to the `## References` section of `SKILL.md` and to the `What's inside` table in `README.md`.
3. Open a pull request. The PR description should state: what solver/version (if applicable), what the change fixes or adds, and how you verified it.
4. A maintainer will check that confidence tags are accurate and the router stays lean.

## Tests & packaging

- The `scripts/` are covered by `tests/test_scripts.py` — run `python -m pytest tests/ -q` before a PR. CI
  runs the suite on Python 3.10–3.13 plus a `manifest` job that validates `.claude-plugin/plugin.json` and checks
  every `references/`/`scripts/` path named in `SKILL.md` resolves (and that no pirated-doc links sneak in).
- **Distribute via git, not a raw copy of the working tree.** `.gitignore` excludes all build/test caches
  (`__pycache__/`, `.pytest_cache/`, `.ruff_cache/`). Package with `git archive --format=zip -o femis.zip HEAD`
  (after `git init && git add . && git commit`) or a fresh `git clone` — zipping the working directory directly
  would ship those caches.

## Style

- Write in plain, direct prose. Prefer tables over prose for lookup data.
- Use SI or mm-t-s units explicitly; never leave units implicit.
- Keep lines under ~120 characters for readability in split-pane editors.
- No emojis in reference files (SKILL.md uses a few sparingly as visual anchors — match that density).

## Questions

Open an issue before doing large structural changes. For small fixes or additions, a PR is fine without prior discussion.
