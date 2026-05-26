"""Step 0.8 — skill evaluation doc tests."""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs" / "skill-evaluation.md"

EXPECTED_CATEGORIES = [
    "Mermaid",
    "Devbox",
    "Traceability",
    "Accessibility",
    "Performance",
]

REQUIRED_FIELDS = ["What it does", "Why interesting", "Decision", "Link"]


def test_skill_evaluation_exists():
    assert DOC.exists(), f"expected {DOC.relative_to(REPO)}"


def test_skill_evaluation_under_100_lines():
    lines = DOC.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 100, f"file is {len(lines)} lines; cap is 100"


def test_five_categories_present():
    text = DOC.read_text(encoding="utf-8")
    for cat in EXPECTED_CATEGORIES:
        assert cat in text, f"category {cat!r} not mentioned in doc"


def test_each_section_has_required_fields():
    text = DOC.read_text(encoding="utf-8")
    sections = re.split(r"(?m)^## \d+\. ", text)[1:]
    assert len(sections) == 5, f"expected 5 numbered sections, got {len(sections)}"
    for idx, section in enumerate(sections, start=1):
        title = section.split("\n", 1)[0]
        for field in REQUIRED_FIELDS:
            marker = f"**{field}"
            assert marker in section, (
                f"section {idx} ({title!r}) missing field {field!r}"
            )
