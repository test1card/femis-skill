# Pre-Publish Checklist

This skill's **content is a release candidate**, but a few host-specific fields are intentionally left blank
until a Git remote exists — rather than ship placeholder URLs. The repo is **not** publish-ready until every
box below is checked. Complete these before publishing publicly.
A CI job (`pre-publish-check`) scans for the `<owner>` token below so none of this is missed.

## 1. Repository identity
- [ ] Create the Git repository (suggested name: `fem-cae`).
- [ ] In `.claude-plugin/plugin.json`, add the owner-bound URL fields (omitted while no remote exists):
      - `"homepage": "https://github.com/<owner>/fem-cae"`
      - `"repository": "https://github.com/<owner>/fem-cae"`
- [ ] In `README.md`, add `git clone https://github.com/<owner>/fem-cae …` install commands
      (the README currently documents copy-based install, which needs no URL).

## 2. Attribution / license
- [ ] `NOTICE` reads `Copyright 2026 The fem-cae Authors`. Change to your name/org if desired.
- [ ] Keep `.claude-plugin/plugin.json` `author.name` in sync with `NOTICE`.
- [ ] `LICENSE` is stock Apache-2.0; its APPENDIX `[yyyy] [name of copyright owner]` is template
      boilerplate, intentionally left as-is — the real copyright lives in `NOTICE`, not the appendix.

## 3. Packaging (do not zip the working tree)
- [ ] Build the release artifact from a clean git checkout via `git archive` — never zip the working
      directory, which carries `.pytest_cache/`, `.ruff_cache/`, and `__pycache__/`.
- [ ] Tag the release (e.g. `v1.0.0`) so an analysis can pin a fixed methodology revision.

## 4. Final gate
- [ ] CI green: `pytest`, leak scan, **internal**-link & banned-domain check, placeholder/cache scan, and `claude plugin validate`.
- [ ] **External URL health** (not covered by CI): run a link checker (e.g. `lychee`/`markdown-link-check` over `references/`) — CI validates *internal* links and banned domains only, not whether external URLs still resolve.
- [ ] `<owner>` appears **only** in this file — confirm it is nowhere in the shipped tree.
