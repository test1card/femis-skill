from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import provenance_coverage  # noqa: E402


def test_build_table_covers_every_reference_file():
    entries = provenance_coverage.collect_entries(ROOT)
    reference_files = sorted(p for p in (ROOT / "references").glob("*.md")
                             if p.name != "provenance-coverage.md")

    assert [entry.path for entry in entries] == [p.relative_to(ROOT) for p in reference_files]


def test_known_tagged_file_counts_are_stable():
    entries = {entry.path.as_posix(): entry for entry in provenance_coverage.collect_entries(ROOT)}
    ansys = entries["references/ansys-thermal-contact-pitfalls.md"]

    assert ansys.author_verified == 7
    assert ansys.docs_only == 4
    assert ansys.verified_web == 0
    assert ansys.total_tags == 11
    assert ansys.status == "partial"


def test_rendered_markdown_matches_checked_in_table():
    expected = provenance_coverage.render_markdown(provenance_coverage.collect_entries(ROOT))
    actual = (ROOT / "references" / "provenance-coverage.md").read_text(encoding="utf-8")

    assert actual == expected
