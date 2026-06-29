import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_skill_frontmatter_is_valid_yaml_with_required_fields():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert text.startswith("---\n")
    _, frontmatter, body = text.split("---", 2)
    data = yaml.safe_load(frontmatter)

    assert isinstance(data, dict)
    assert data["name"] == "femis"
    assert data["license"] == "Apache-2.0"
    version = data["metadata"]["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert data["description"].strip()
    assert len(data["description"]) <= 1024
    assert body.lstrip().startswith("# FEM / CAE")

    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "skills_index.json").read_text(encoding="utf-8"))
    openai = yaml.safe_load((ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))

    assert plugin["version"] == version
    assert index["version"] == version
    assert openai["version"] == version
