import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_examples_index_lists_existing_examples():
    index = (EXAMPLES / "README.md").read_text(encoding="utf-8")

    for name in ("gci-known-values", "units-density-corruption", "single-mesh-claim-refusal"):
        path = EXAMPLES / name
        assert path.is_dir()
        assert f"`{name}`" in index
        assert (path / "README.md").is_file()
        assert (path / "expected-output.txt").is_file()


def test_gci_example_matches_expected_output():
    expected = (EXAMPLES / "gci-known-values" / "expected-output.txt").read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "scripts/gci.py", "1.0", "305.20", "2.0", "306.10", "4.0", "308.50"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == expected


def test_units_example_matches_expected_output():
    spec = json.loads((EXAMPLES / "units-density-corruption" / "input.json").read_text(encoding="utf-8"))
    expected = (EXAMPLES / "units-density-corruption" / "expected-output.txt").read_text(encoding="utf-8")
    code = (
        "import sys; sys.path.insert(0, 'scripts'); import units_check; "
        f"print(units_check.check_density({spec['system']!r}, {spec['density']!r}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == expected


def test_single_mesh_refusal_example_contains_required_claim_gates():
    text = (EXAMPLES / "single-mesh-claim-refusal" / "expected-output.txt").read_text(encoding="utf-8").lower()

    for phrase in ("not an engineering result", "single mesh", "discretization", "singular"):
        assert phrase in text
