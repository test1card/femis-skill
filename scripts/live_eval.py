#!/usr/bin/env python3
"""Live A/B eval runner — measures whether loading the fem-cae skill changes agent behavior.

This is the *live* complement to `run_skill_evals.py` (which is the deterministic, LLM-free
structural validator run in CI). It runs each case in `evals/prompts.json` through an agent
**twice** — once with the fem-cae skill loaded as the system prompt (skill-on), once with no
skill (skill-off baseline) — scores both with `run_skill_evals.score_response`, and reports the
uplift. That uplift is the evidence that the skill governs behavior, not just reads well.

OPTIONAL by design: the Anthropic SDK is a thin, lazily-imported adapter. The core `run_ab()`
takes any `agent_fn(system, user) -> str` callable, so you can wire it to any backend. With no
`anthropic` package and no `ANTHROPIC_API_KEY`, this script prints how to enable it and exits 0 —
it never breaks a CI run or a checkout.

    pip install anthropic && export ANTHROPIC_API_KEY=...   # then:
    python scripts/live_eval.py                 # A/B all cases, print uplift
    python scripts/live_eval.py --limit 8       # first 8 cases
    python scripts/live_eval.py --model claude-sonnet-4-6

Wire a custom backend instead of the Anthropic adapter:

    from live_eval import run_ab
    rows = run_ab(lambda system, user: my_agent(system, user))
"""
from __future__ import annotations

import sys
from pathlib import Path

from run_skill_evals import load_cases, score_response  # same scripts/ dir

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "claude-opus-4-8"  # default; override with --model

SKILL_ON_PREAMBLE = (
    "You are an AI engineering agent operating UNDER the fem-cae governance skill included "
    "below. Follow it faithfully: apply its execution-mode gates (SMOKE/DEBUG/ENGINEERING/"
    "SIGNOFF) and the pre-claim self-check before stating any number, honor the headless-vs-"
    "human contract, and escalate human-judgment decisions (load case, contact type, "
    "allowable, defeature, sign-off) instead of deciding them yourself. Answer the user's "
    "prompt exactly as that governed agent would.\n\n===== fem-cae SKILL.md =====\n"
)


def systems() -> tuple[str, str]:
    """Return (skill_on_system, skill_off_system). Skill-off is a bare, capable assistant."""
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    skill_on = SKILL_ON_PREAMBLE + skill
    skill_off = "You are a capable engineering assistant. Answer the user's question directly."
    return skill_on, skill_off


def anthropic_agent(model: str = DEFAULT_MODEL, max_tokens: int = 1024):
    """Thin optional adapter over the Anthropic Python SDK. Imported lazily so the module
    loads (and run_ab works with a custom agent_fn) even when `anthropic` isn't installed."""
    import anthropic  # noqa: PLC0415 - intentional lazy/optional import

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    def run(system: str, user: str) -> str:
        kwargs = {"model": model, "max_tokens": max_tokens,
                  "messages": [{"role": "user", "content": user}]}
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")

    return run


def run_ab(agent_fn, cases=None):
    """Run every case skill-on vs skill-off through agent_fn; return per-case result rows.

    Each row: {id, mode, behavior, on (skill-on overall pass), off (skill-off overall pass)}.
    """
    cases = cases if cases is not None else load_cases()
    skill_on_system, skill_off_system = systems()
    rows = []
    for c in cases:
        on = score_response(c, agent_fn(skill_on_system, c["prompt"]))
        off = score_response(c, agent_fn(skill_off_system, c["prompt"]))
        rows.append({
            "id": c["id"], "mode": c["expect_mode"], "behavior": c["expect_behavior"],
            "on": on["overall"], "off": off["overall"],
        })
    return rows


def _print_report(rows) -> None:
    print(f"{'case':<24} {'behavior':<9} {'skill-off':<10} {'skill-on':<9}")
    for r in rows:
        print(f"{r['id']:<24} {r['behavior']:<9} "
              f"{'PASS' if r['off'] else 'fail':<10} {'PASS' if r['on'] else 'fail':<9}")
    n = len(rows) or 1
    off_rate = sum(r["off"] for r in rows) / n
    on_rate = sum(r["on"] for r in rows) / n
    print(f"\nskill-off pass rate: {off_rate:.0%}   skill-on pass rate: {on_rate:.0%}   "
          f"uplift: {on_rate - off_rate:+.0%}")


def main(argv) -> int:
    model = DEFAULT_MODEL
    limit = None
    if "--model" in argv:
        model = argv[argv.index("--model") + 1]
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])

    try:
        agent_fn = anthropic_agent(model=model)
    except ImportError:
        print("live_eval is optional and needs the Anthropic SDK:\n"
              "  pip install anthropic && export ANTHROPIC_API_KEY=...\n"
              "Then re-run, or call run_ab(your_agent_fn) with a custom backend.")
        return 0
    except Exception as e:  # noqa: BLE001 - typically a missing/invalid API key
        print(f"live_eval could not initialize the Anthropic client ({e}).\n"
              "Set ANTHROPIC_API_KEY (or wire run_ab to a custom agent_fn). Skipping.")
        return 0

    cases = load_cases()
    if limit is not None:
        cases = cases[:limit]
    print(f"Running live A/B over {len(cases)} cases on {model} (skill-on vs skill-off)...\n")
    _print_report(run_ab(agent_fn, cases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
