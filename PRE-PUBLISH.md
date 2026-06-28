# Pre-Publish Checklist

This skill's **content is a release candidate**. The owner-bound fields below are now wired to
`https://github.com/test1card/fem-cae-skill`, but the **repository must still be created and pushed**, and the
release **tagged**, before it is publicly installable. The repo is **not** published until every box is checked.

## 1. Repository identity
- [x] Plugin/skill name `fem-cae`; **GitHub repo `fem-cae-skill`** (owner `test1card`). The skill installs
      into a `fem-cae/` folder, so the repo name and skill-folder name intentionally differ.
- [x] `.claude-plugin/plugin.json` carries `homepage` + `repository` = `https://github.com/test1card/fem-cae-skill`.
- [x] `README.md` documents copy-based install **and** `git clone … skills/fem-cae` using the repo URL.
- [ ] **Create the GitHub repository `test1card/fem-cae-skill` and push** `master` — nothing is publicly
      installable until this is done. (Not done automatically; no push happens without your go-ahead.)

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
- [ ] Confirm no placeholder tokens (`<owner>`, `<you>`, `TODO-OWNER`) remain anywhere in the tree.
