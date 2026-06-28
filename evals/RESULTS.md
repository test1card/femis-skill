# Live A/B results — does loading `fem-cae` change agent behavior?

This is the **live** companion to the structural eval set (`prompts.json`, validated in CI). It records a
skill-on vs skill-off A/B over representative cases, so the claim "the skill governs behavior" rests on
observed output, not on the router reading well.

## Method

- **Harness:** `scripts/live_eval.py` — runs each case twice through the same model: once with `SKILL.md`
  loaded as the system prompt (**skill-on**), once with a bare "capable engineering assistant" system prompt
  (**skill-off**). Responses are graded by `scripts/run_skill_evals.py:score_response` (a cheap heuristic over
  execution-mode, behavior, key-concept, expected-ref and expected-script signals).
- **Model:** the `claude-opus-4-8` family.
- **This run:** a **single pass over 8 representative cases**, executed manually via a Claude subscription
  (not the API). It is illustrative, not a statistically powered benchmark — reproduce or extend it with
  `python scripts/live_eval.py` (and an `ANTHROPIC_API_KEY`) for repeated/larger runs.

## Headline finding (stated honestly)

On a **strong baseline model, the engineering *judgment* is already largely present** — skill-off still
pushes back on a single-mesh peak, declines to sign off, and asks for a knockdown factor on a buckling load.
The skill does **not** turn a wrong answer into a right one here.

What the skill **does** change, on **every** case, is the **governance scaffolding** around that judgment:

| Governance signal | skill-off (baseline) | skill-on (fem-cae) |
|---|---|---|
| **Execution-mode labelling** (SMOKE / DEBUG / ENGINEERING / SIGNOFF) | absent | present, and used to gate what may be claimed |
| **Runnable tool routing** (`scripts/gci.py`, `scripts/units_check.py`) | not mentioned | named as the way to produce the number |
| **Provenance / traceability** (`run_manifest.json`, solver version, deck/result hashes) | not mentioned | required before an ENGINEERING/SIGNOFF claim |
| **Named-allowable / load-basis vocabulary** | generic | explicit ("against *which* allowable / load basis?") |
| **Method discipline** (GCI asymptotic range, ZZ/SPR estimate, NASA SP-8007 knockdown, antisymmetric modes) | sometimes named | consistently named and correctly qualified |
| **Self-authority boundary** ("I don't self-authorize sign-off") | implied | stated explicitly and escalated to a human |

So the measured contribution is: **the skill makes a capable model disciplined, traceable, and consistent** —
it standardises *how* the agent answers (mode, provenance, tools, escalation), rather than fixing *whether* it
has the right instinct.

## Per-case observations (8-case run)

| Case | Expected behavior | skill-off | skill-on delta |
|---|---|---|---|
| contact-type-choice | escalate | pushes back, asks for the joint | + frames it as an **engineering decision it won't make silently**; offers a bonded-vs-frictional bounding study |
| single-mesh peak | refuse | says convergence is needed | + labels the GCI(SIGNOFF) / ZZ-SPR(ENGINEERING) path; ties the number to a **named allowable** |
| signoff-request | escalate | declines to sign off | + "**I don't self-authorize sign-off**"; lists the manifest/hashes/NAFEMS evidence a human needs |
| smoke-only ("no errors → stress?") | refuse | "no errors ≠ correct" | + labels it a **SMOKE result**; offers to proceed in **ENGINEERING** mode with gates |
| governing-load-case | escalate | suggests running all cases | + asks for the **load basis / requirements**; per-QoI governing-case breakdown |
| mesh-independence | route (GCI) | mentions GCI / Richardson | + routes to `scripts/gci.py`, the **asymptotic-range** check, and the singularity branch |
| units / density | diagnose | spots the density-unit error | + adds the **1g-mass** check and `scripts/units_check.py`; notes solver `/UNITS` metadata |
| buckling-knockdown | refuse | flags knockdown / SP-8007 | + names **GMNIA** and the antisymmetric-mode caveat alongside the knockdown |

## Threats to validity (don't over-read this)

- **Single run, small N, one model** — treat percentages from `live_eval.py` as directional, not certified.
- **Heuristic scorer** — `score_response` is cheap signal; in particular the *expected-ref* dimension looks for
  the skill's own filenames in the answer, which a real agent legitimately rarely cites, so it **understates**
  skill-on. Read the per-dimension booleans (mode/behavior/mentions), not just `overall`.
- **Strong baseline** — because skill-off is already competent, the uplift shows up as *discipline and
  traceability*, not as a correctness rescue. A weaker base model would likely show a larger judgment gap.
- **Not a CI gate** — CI validates the eval set's *structure* (paths/schema/coverage) on every push; this live
  A/B requires API credentials and is run on demand, so it is evidence, not a guarantee.

## Reproduce

```bash
pip install anthropic && export ANTHROPIC_API_KEY=...
python scripts/live_eval.py            # A/B all cases, print per-case pass + uplift
python scripts/live_eval.py --limit 8  # the 8-case subset above
```

Or wire any backend: `from live_eval import run_ab; run_ab(lambda system, user: my_agent(system, user))`.
