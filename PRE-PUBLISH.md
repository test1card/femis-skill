# Pre-Publish Checklist

This skill's current release line is **`v1.0.2`** at `https://github.com/test1card/femis-skill` (branch `main`).
This file records the owner-bound publishing steps; the remaining unchecked items are optional follow-ups.

## 1. Repository identity
- [x] Plugin/skill name `femis`; **GitHub repo `femis-skill`** (owner `test1card`). The skill installs
      into a `femis/` folder, so the repo name and skill-folder name intentionally differ.
- [x] `.claude-plugin/plugin.json` carries `homepage` + `repository` = `https://github.com/test1card/femis-skill`.
- [x] `README.md` documents copy-based install **and** `git clone … skills/femis` using the repo URL.
- [x] **Repository created, pushed (branch `main`), and tagged `v1.0.0`** — live at
      `https://github.com/test1card/femis-skill`.
- [x] `v1.0.2` release metadata and release notes live in `CHANGELOG.md`.

## 2. Attribution / license
- [ ] `NOTICE` reads `Copyright 2026 The femis Authors`. Change to your name/org if desired.
- [ ] Keep `.claude-plugin/plugin.json` `author.name` in sync with `NOTICE`.
- [ ] `LICENSE` is stock Apache-2.0; its APPENDIX `[yyyy] [name of copyright owner]` is template
      boilerplate, intentionally left as-is — the real copyright lives in `NOTICE`, not the appendix.

## 3. Packaging (do not zip the working tree)
- [ ] Build the `v1.0.2` release artifact from a clean checkout via `git archive`
      (`git archive --format=zip --output=femis-1.0.2.zip v1.0.2`).
- [x] Tagged `v1.0.0` and `v1.0.1` so analyses can pin fixed methodology revisions.

## 4. Final gate
- [x] Local release gate green on 2026-06-29: `pytest`, evals, provenance coverage, script smoke-tests,
      `actionlint`, YAML parsing, **internal**-link & banned-domain check, placeholder/cache scan,
      cache scan, and `claude plugin validate`.
- [ ] Verify GitHub CI green after pushing each release commit/tag.
- [ ] **External URL health** (not covered by CI): run a link checker (e.g. `lychee`/`markdown-link-check` over `references/`) — CI validates *internal* links and banned domains only, not whether external URLs still resolve.
- [ ] Confirm no placeholder tokens (`<owner>`, `<you>`, `TODO-OWNER`) remain anywhere in the tree.
