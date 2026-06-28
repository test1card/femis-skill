# Pre-Publish Checklist

This skill is **published** as **`v1.0.0`** at `https://github.com/test1card/femis-skill` (branch `main`).
This file records the owner-bound publishing steps; the remaining unchecked items are optional follow-ups.

## 1. Repository identity
- [x] Plugin/skill name `femis`; **GitHub repo `femis-skill`** (owner `test1card`). The skill installs
      into a `femis/` folder, so the repo name and skill-folder name intentionally differ.
- [x] `.claude-plugin/plugin.json` carries `homepage` + `repository` = `https://github.com/test1card/femis-skill`.
- [x] `README.md` documents copy-based install **and** `git clone … skills/femis` using the repo URL.
- [x] **Repository created, pushed (branch `main`), and tagged `v1.0.0`** — live at
      `https://github.com/test1card/femis-skill`.

## 2. Attribution / license
- [ ] `NOTICE` reads `Copyright 2026 The femis Authors`. Change to your name/org if desired.
- [ ] Keep `.claude-plugin/plugin.json` `author.name` in sync with `NOTICE`.
- [ ] `LICENSE` is stock Apache-2.0; its APPENDIX `[yyyy] [name of copyright owner]` is template
      boilerplate, intentionally left as-is — the real copyright lives in `NOTICE`, not the appendix.

## 3. Packaging (do not zip the working tree)
- [x] Built the release artifact from a clean checkout via `git archive` (`femis-1.0.0.zip`, 0 cache entries).
- [x] Tagged the release `v1.0.0` so an analysis can pin a fixed methodology revision.

## 4. Final gate
- [ ] CI green: `pytest`, leak scan, **internal**-link & banned-domain check, placeholder/cache scan, and `claude plugin validate`.
- [ ] **External URL health** (not covered by CI): run a link checker (e.g. `lychee`/`markdown-link-check` over `references/`) — CI validates *internal* links and banned domains only, not whether external URLs still resolve.
- [ ] Confirm no placeholder tokens (`<owner>`, `<you>`, `TODO-OWNER`) remain anywhere in the tree.
