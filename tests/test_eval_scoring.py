from pathlib import Path
import sys


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from run_skill_evals import score_response  # noqa: E402


def _numeric_gci_case():
    return {
        "id": "gci-known-values",
        "prompt": "Compute GCI values for the documented three-grid example.",
        "expect_refs": [],
        "expect_scripts": ["scripts/gci.py"],
        "expect_behavior": "claim",
        "expect_mode": "SIGNOFF",
        "must_mention": ["GCI"],
        "expect_numbers": [
            {"name": "observed_order_p", "value": 1.415, "abs_tol": 0.01},
            {"name": "richardson_f_exact", "value": 304.66, "abs_tol": 0.10},
        ],
    }


def test_score_response_requires_expected_numeric_values():
    case = _numeric_gci_case()

    scored = score_response(
        case,
        "SIGNOFF GCI using scripts/gci.py: p = 2.0 and Richardson f_exact = 305.20.",
    )

    assert scored["numbers_ok"] is False
    assert scored["overall"] is False


def test_score_response_accepts_expected_numeric_values():
    case = _numeric_gci_case()

    scored = score_response(
        case,
        "SIGNOFF GCI using scripts/gci.py: observed_order_p = 1.415; "
        "Richardson f_exact = 304.66 K.",
    )

    assert scored["numbers_ok"] is True
    assert scored["overall"] is True
