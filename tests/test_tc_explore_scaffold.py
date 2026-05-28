"""Step 4.1 - tc-explore skill scaffold and seeded-exploration-session fixture.

Asserts the skill directory, SKILL.md frontmatter and body, the empty
commands/ methodology/ templates/ directories (to be filled by 4.2-4.5),
and the seeded-exploration-session fixture covering every universal
anomaly category plus the required charter frontmatter fields.

The fixture uses the universal marker token ``knowledge: <dimension>``
embedded in each file's native comment syntax (Markdown HTML comments;
JSON ``_knowledge`` value strings carrying the literal phrase), the same
convention established in Phase 3 Step 3.1. The scaffold test parses
these tokens to verify anomaly-category coverage. Charter required
fields (id, mission, target, time-box, risk-areas, acceptance-criteria)
are asserted as structural presence.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "test-commander" / "skills" / "tc-explore"
SKILL_MD = SKILL_DIR / "SKILL.md"
COMMANDS_DIR = SKILL_DIR / "commands"
METHODOLOGY_DIR = SKILL_DIR / "methodology"
TEMPLATES_DIR = SKILL_DIR / "templates"

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-exploration-session"
FIXTURE_README = FIXTURE_DIR / "README.md"
FIXTURE_CHARTER = FIXTURE_DIR / "charter.md"
FIXTURE_TARGET_APP = FIXTURE_DIR / "target-app.md"
FIXTURE_RECORDED_SESSION = FIXTURE_DIR / "recorded-session.json"

COMMANDS = [
    "/tc:create-charter",
    "/tc:explore",
    "/tc:session-summary",
    "/tc:test-ideas",
]

# Universal anomaly categories from the Phase 4 design decisions block.
ANOMALY_CATEGORIES = [
    "slow-response",
    "console-error",
    "broken-link",
    "missing-evidence",
    "auth-mismatch",
    "unexpected-state",
]

# Charter frontmatter required fields per the Step 4.1 deliverables.
CHARTER_REQUIRED_FIELDS = [
    "id",
    "mission",
    "target",
    "time-box",
    "risk-areas",
    "acceptance-criteria",
]

# Recorded-session event types per the Step 4.3 partition table.
EXPECTED_EVENT_TYPES = {
    "page_load",
    "click",
    "fill",
    "screenshot",
    "console_message",
    "network_request",
    "anomaly",
}

KNOWLEDGE_TOKEN_RE = re.compile(r"knowledge:\s*([a-z][a-z0-9-]*)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
NAME_LINE_RE = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)
DESCRIPTION_LINE_RE = re.compile(r"^description:\s*(.+?)\s*$", re.MULTILINE)
KEBAB_CASE_RE = re.compile(r"[a-z][a-z0-9-]*")


def collect_knowledge_tokens(root: Path) -> set[str]:
    """Walk every file under root and collect every ``knowledge: <dim>`` token."""
    tokens: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        tokens.update(KNOWLEDGE_TOKEN_RE.findall(text))
    return tokens


# ---------------------------------------------------------------------------
# Skill scaffold
# ---------------------------------------------------------------------------


def test_skill_directory_exists():
    assert SKILL_DIR.is_dir(), f"expected {SKILL_DIR.relative_to(REPO)}"


def test_skill_md_exists():
    assert SKILL_MD.is_file(), f"expected {SKILL_MD.relative_to(REPO)}"


def test_skill_md_has_valid_frontmatter():
    text = SKILL_MD.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match, "SKILL.md must begin with a YAML frontmatter block delimited by ---"
    fm = match.group(1)
    name_match = NAME_LINE_RE.search(fm)
    desc_match = DESCRIPTION_LINE_RE.search(fm)
    assert name_match, "frontmatter missing name"
    assert desc_match, "frontmatter missing description"
    assert name_match.group(1) == "tc-explore", (
        f"expected name: tc-explore, got {name_match.group(1)}"
    )
    assert KEBAB_CASE_RE.fullmatch(name_match.group(1)), "name must be kebab-case"
    assert desc_match.group(1).strip(), "description must be non-empty"


def test_skill_md_body_references_all_four_commands():
    text = SKILL_MD.read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"SKILL.md body must reference {cmd}"


def test_skill_md_body_references_review_sub_mode():
    text = SKILL_MD.read_text(encoding="utf-8").lower()
    assert "review" in text, (
        "SKILL.md must describe the internal review sub-mode (auto-runs at end of /tc:explore)"
    )


def test_commands_directory_exists():
    assert COMMANDS_DIR.is_dir(), (
        f"expected {COMMANDS_DIR.relative_to(REPO)} (filled in by 4.2-4.5)"
    )


def test_methodology_directory_exists():
    assert METHODOLOGY_DIR.is_dir(), (
        f"expected {METHODOLOGY_DIR.relative_to(REPO)} (filled in by 4.2-4.5)"
    )


def test_templates_directory_exists():
    assert TEMPLATES_DIR.is_dir(), (
        f"expected {TEMPLATES_DIR.relative_to(REPO)} (filled in by 4.2-4.5)"
    )


# ---------------------------------------------------------------------------
# Fixture - structural presence
# ---------------------------------------------------------------------------


def test_fixture_directory_exists():
    assert FIXTURE_DIR.is_dir(), f"expected {FIXTURE_DIR.relative_to(REPO)}"


def test_fixture_files_present():
    for path in (FIXTURE_README, FIXTURE_CHARTER, FIXTURE_TARGET_APP, FIXTURE_RECORDED_SESSION):
        assert path.is_file(), f"missing fixture file: {path.relative_to(REPO)}"


def test_fixture_readme_describes_marker_convention():
    text = FIXTURE_README.read_text(encoding="utf-8")
    assert "knowledge:" in text, (
        "fixture README must document the universal knowledge-marker convention"
    )
    assert "universal" in text.lower(), (
        "fixture README must describe the narrative as universal (D19)"
    )


# ---------------------------------------------------------------------------
# Charter frontmatter
# ---------------------------------------------------------------------------


def test_charter_has_yaml_frontmatter():
    text = FIXTURE_CHARTER.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match, "charter.md must begin with a YAML frontmatter block delimited by ---"


def test_charter_id_is_ch_001():
    text = FIXTURE_CHARTER.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match
    fm = match.group(1)
    id_line = re.search(r"^id:\s*(\S+)\s*$", fm, re.MULTILINE)
    assert id_line, "charter frontmatter must declare id"
    assert id_line.group(1) == "CH-001", (
        f"expected charter id: CH-001, got {id_line.group(1)}"
    )


def test_charter_has_all_required_fields():
    text = FIXTURE_CHARTER.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match
    fm = match.group(1)
    for field in CHARTER_REQUIRED_FIELDS:
        # Allow either bare key (e.g. ``mission:``) or value-on-same-line shape.
        pattern = rf"^{re.escape(field)}\s*:\s*"
        assert re.search(pattern, fm, re.MULTILINE), (
            f"charter frontmatter missing required field: {field}"
        )


def test_charter_disclaims_scope():
    """Per the D19 fixture-discipline lesson — the seeded charter must
    explicitly state it is a test asset, not a claim about scope."""
    text = FIXTURE_CHARTER.read_text(encoding="utf-8").lower()
    assert "test asset" in text or "not a claim about scope" in text, (
        "charter.md must carry the D19 fixture-discipline disclaimer"
    )


# ---------------------------------------------------------------------------
# Recorded-session JSON shape
# ---------------------------------------------------------------------------


def test_recorded_session_parses_as_json_list():
    data = json.loads(FIXTURE_RECORDED_SESSION.read_text(encoding="utf-8"))
    assert isinstance(data, list), "recorded-session.json must be a JSON list"
    assert len(data) >= 50, (
        f"recorded-session.json must carry at least 50 entries, got {len(data)}"
    )
    assert len(data) <= 80, (
        f"recorded-session.json must carry at most 80 entries (per spec), got {len(data)}"
    )


def test_recorded_session_entries_have_required_fields():
    data = json.loads(FIXTURE_RECORDED_SESSION.read_text(encoding="utf-8"))
    for i, entry in enumerate(data):
        assert isinstance(entry, dict), f"entry {i} must be a JSON object"
        assert "timestamp" in entry, f"entry {i} missing timestamp"
        assert "event_type" in entry, f"entry {i} missing event_type"
        assert entry["event_type"] in EXPECTED_EVENT_TYPES, (
            f"entry {i} carries unknown event_type {entry['event_type']!r}; "
            f"expected one of {sorted(EXPECTED_EVENT_TYPES)}"
        )


def test_recorded_session_covers_every_event_type():
    data = json.loads(FIXTURE_RECORDED_SESSION.read_text(encoding="utf-8"))
    observed = {entry["event_type"] for entry in data}
    missing = EXPECTED_EVENT_TYPES - observed
    assert not missing, (
        f"recorded-session.json missing event types: {sorted(missing)}; "
        f"observed: {sorted(observed)}"
    )


# ---------------------------------------------------------------------------
# Anomaly category coverage
# ---------------------------------------------------------------------------


def test_every_anomaly_category_seeded_in_fixture():
    tokens = collect_knowledge_tokens(FIXTURE_DIR)
    missing = [cat for cat in ANOMALY_CATEGORIES if cat not in tokens]
    assert not missing, (
        f"fixture missing seeded knowledge-marker tokens for anomaly categories: "
        f"{missing}; observed tokens: {sorted(tokens)}"
    )


def test_anomaly_entries_carry_kind_in_payload():
    """Anomaly entries must carry an anomaly payload with a category from the
    universal core. The scaffold test asserts at least one anomaly entry per
    universal category; Step 4.3's helper test will assert mechanical
    extraction against the full set."""
    data = json.loads(FIXTURE_RECORDED_SESSION.read_text(encoding="utf-8"))
    anomalies = [e for e in data if e["event_type"] == "anomaly"]
    assert anomalies, "recorded-session.json must seed at least one anomaly entry"
    categories_seen: set[str] = set()
    for entry in anomalies:
        anomaly = entry.get("anomaly")
        assert isinstance(anomaly, dict), (
            f"anomaly entry must carry an `anomaly` object payload; got {entry}"
        )
        cat = anomaly.get("category")
        assert cat in ANOMALY_CATEGORIES, (
            f"anomaly category {cat!r} not in universal core {ANOMALY_CATEGORIES}"
        )
        categories_seen.add(cat)
    missing = set(ANOMALY_CATEGORIES) - categories_seen
    assert not missing, (
        f"recorded-session.json must seed an anomaly entry for every universal "
        f"category; missing: {sorted(missing)}"
    )
