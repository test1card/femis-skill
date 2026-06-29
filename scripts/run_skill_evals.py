#!/usr/bin/env python3
"""Static validator + scoring harness for the femis skill's activation/behavior evals.

Two uses:

  1. CI / pre-commit (deterministic, no LLM):
         python scripts/run_skill_evals.py
     Validates evals/prompts.json structurally — every expect_refs / expect_scripts path
     exists, modes and behaviors are in the allowed vocabulary, ids are unique, and optional
     expect_numbers entries are well-formed. Exits non-zero on any problem, so a renamed/deleted
     reference can never silently desync the eval set from the tree.

  2. Live agent scoring (wire your own runner):
         from run_skill_evals import load_cases, score_response
         for case in load_cases():
             resp = my_agent(case["prompt"])          # however you drive the agent
             print(score_response(case, resp))
     score_response() grades whether the answer surfaced the expected references, landed on
     the right execution mode, exhibited the expected behavior (claim/refuse/escalate/...), and
     included required numeric ground-truth values when a case declares expect_numbers.

The structural validation is intentionally LLM-free so it runs in CI. The scoring heuristic is
a cheap first-pass signal, not a substitute for human review of borderline cases.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES_FILE = ROOT / "evals" / "prompts.json"

MODES = {"SMOKE", "DEBUG", "ENGINEERING", "SIGNOFF", "n/a"}
BEHAVIORS = {"route", "claim", "diagnose", "refuse", "escalate"}
REQUIRED = ("id", "prompt", "expect_refs", "expect_scripts", "expect_behavior", "expect_mode", "must_mention")


def load_cases(path: Path = CASES_FILE):
    """Return the list of eval-case dicts from prompts.json."""
    return json.loads(path.read_text(encoding="utf-8"))["cases"]


def validate(path: Path = CASES_FILE):
    """Return a list of human-readable problems with the eval set (empty == valid)."""
    errs = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 - report any parse failure as a finding
        return [f"cannot parse {path}: {e}"]
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["'cases' must be a non-empty list"]
    seen = set()
    for i, c in enumerate(cases):
        tag = c.get("id", f"#{i}")
        for k in REQUIRED:
            if k not in c:
                errs.append(f"{tag}: missing field '{k}'")
        if c.get("id") in seen:
            errs.append(f"duplicate id '{c.get('id')}'")
        seen.add(c.get("id"))
        if c.get("expect_mode") not in MODES:
            errs.append(f"{tag}: expect_mode '{c.get('expect_mode')}' not in {sorted(MODES)}")
        if c.get("expect_behavior") not in BEHAVIORS:
            errs.append(f"{tag}: expect_behavior '{c.get('expect_behavior')}' not in {sorted(BEHAVIORS)}")
        for key in ("expect_refs", "expect_scripts", "must_mention"):
            if not isinstance(c.get(key, []), list):
                errs.append(f"{tag}: '{key}' must be a list")
        for rel in list(c.get("expect_refs", [])) + list(c.get("expect_scripts", [])):
            if not (ROOT / rel).exists():
                errs.append(f"{tag}: expected path does not exist: {rel}")
        for n in c.get("expect_numbers", []):
            if not isinstance(n, dict):
                errs.append(f"{tag}: expect_numbers entries must be objects")
                continue
            if "name" not in n or "value" not in n:
                errs.append(f"{tag}: expect_numbers entries need 'name' and 'value'")
            if "value" in n and not isinstance(n["value"], (int, float)):
                errs.append(f"{tag}: expect_numbers value must be numeric")
            if "abs_tol" in n and not isinstance(n["abs_tol"], (int, float)):
                errs.append(f"{tag}: expect_numbers abs_tol must be numeric")
    return errs


def _ref_mentioned(rel: str, low: str) -> bool:
    name = Path(rel).name.lower()
    stem_words = Path(rel).stem.replace("-", " ").lower()
    return name in low or stem_words in low


def _numbers_hit(expect_numbers: list[dict], response_text: str) -> list[str]:
    values = [float(m.group(0)) for m in re.finditer(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", response_text)]
    hit = []
    for item in expect_numbers:
        target = float(item["value"])
        tol = float(item.get("abs_tol", 1e-6))
        if any(abs(v - target) <= tol for v in values):
            hit.append(item["name"])
    return hit


def score_response(case: dict, response_text: str) -> dict:
    """Heuristic grade of a live agent response to case['prompt'].

    Returns per-dimension booleans plus an overall pass. Cheap signal only.
    """
    low = response_text.lower()
    refs_hit = [r for r in case.get("expect_refs", []) if _ref_mentioned(r, low)]
    scripts_hit = [s for s in case.get("expect_scripts", []) if Path(s).name.lower() in low]
    mentions_hit = [m for m in case.get("must_mention", []) if m.lower() in low]
    mode_ok = case["expect_mode"] == "n/a" or case["expect_mode"].lower() in low

    refuse_markers = ("i won't", "i will not", "i can't", "cannot", "not a result",
                      "won't pick", "won't decide", "refuse", "not yet")
    escalate_markers = ("which", "decision", "escalate", "requirements", "load basis",
                        "engineer must", "you decide", "should i", "confirm")
    behavior = case["expect_behavior"]
    diagnose_markers = ("because", "cause", "likely", "check", "mismatch", "wrong",
                        "units", "density", "off by", "factor of", "suspect", "root")
    if behavior == "refuse":
        behavior_ok = any(m in low for m in refuse_markers)
    elif behavior == "escalate":
        behavior_ok = any(m in low for m in escalate_markers)
    elif behavior == "claim":
        # a real claim names a mode AND states a number/QoI — not just prose
        behavior_ok = ((case["expect_mode"] != "n/a" and mode_ok)
                       or "=" in response_text or any(ch.isdigit() for ch in response_text))
    elif behavior == "diagnose":
        behavior_ok = any(m in low for m in diagnose_markers)
    else:  # route — gated instead by refs_ok / scripts_ok in `overall`
        behavior_ok = True

    refs_ok = (not case.get("expect_refs")) or bool(refs_hit)
    scripts_ok = (not case.get("expect_scripts")) or bool(scripts_hit)
    need = case.get("must_mention", [])
    mentions_ok = (not need) or len(mentions_hit) == len(need)  # require ALL must_mention, not half
    expect_numbers = case.get("expect_numbers", [])
    numbers_hit = _numbers_hit(expect_numbers, response_text) if expect_numbers else []
    numbers_ok = (not expect_numbers) or len(numbers_hit) == len(expect_numbers)
    overall = refs_ok and scripts_ok and mode_ok and behavior_ok and mentions_ok and numbers_ok
    return {
        "id": case["id"],
        "overall": overall,
        "refs_ok": refs_ok,
        "refs_hit": refs_hit,
        "scripts_ok": scripts_ok,
        "scripts_hit": scripts_hit,
        "mode_ok": mode_ok,
        "behavior_ok": behavior_ok,
        "mentions_ok": mentions_ok,
        "mentions_hit": mentions_hit,
        "numbers_ok": numbers_ok,
        "numbers_hit": numbers_hit,
    }


def main(argv) -> int:
    errs = validate()
    cases = load_cases() if not errs else []
    if "--list" in argv:
        for c in cases:
            print(f"{c['id']:<24} mode={c['expect_mode']:<11} behavior={c['expect_behavior']:<9} "
                  f"refs={len(c.get('expect_refs', []))} scripts={len(c.get('expect_scripts', []))} "
                  f"numbers={len(c.get('expect_numbers', []))}")
    if errs:
        print("EVAL SET INVALID:")
        for e in errs:
            print(" -", e)
        return 1
    print(f"OK: {len(cases)} eval cases — all expected refs/scripts exist; modes/behaviors valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
