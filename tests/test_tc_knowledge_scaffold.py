"""Step 3.1 - tc-knowledge skill scaffold and seeded-sample-project fixture.

Asserts the skill directory, SKILL.md frontmatter and body, the empty
commands/ methodology/ templates/ directories (to be filled by 3.2-3.6), and
the seeded-sample-project fixture covering every gap signal named in the
Phase 3 plan plus the structural presence of every positive rubric dimension.

The fixture uses the universal marker token ``knowledge: <dimension>`` embedded
in each file's native comment syntax: ``<!-- knowledge: ... -->`` for Markdown,
``# knowledge: ...`` for YAML and Python, ``// knowledge: ...`` for TypeScript,
and ``"_knowledge": "<dimension>"`` entries for JSON. The scaffold test parses
these tokens to verify gap-signal coverage. Positive rubric dimensions
(entities, terms, journeys, business-rules, assumptions, endpoints, schemas,
auth-schemes, modules / classes / functions, docstrings, test-coverage) are
structurally present in the fixture by design and asserted with shape checks.
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "test-commander" / "skills" / "tc-knowledge"
SKILL_MD = SKILL_DIR / "SKILL.md"
COMMANDS_DIR = SKILL_DIR / "commands"
METHODOLOGY_DIR = SKILL_DIR / "methodology"
TEMPLATES_DIR = SKILL_DIR / "templates"

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-sample-project"
FIXTURE_README = FIXTURE_DIR / "README.md"
FIXTURE_DOCUMENTS = FIXTURE_DIR / "documents"
FIXTURE_SPECS = FIXTURE_DIR / "specs"
FIXTURE_SRC = FIXTURE_DIR / "src"
FIXTURE_TESTS = FIXTURE_DIR / "tests"
FIXTURE_RECORDED_API = FIXTURE_DIR / "recorded-api"

FIXTURE_PRODUCT_OVERVIEW = FIXTURE_DOCUMENTS / "product-overview.md"
FIXTURE_GLOSSARY = FIXTURE_DOCUMENTS / "glossary.md"
FIXTURE_JOURNEY = FIXTURE_DOCUMENTS / "user-journey-sign-in.md"
FIXTURE_OPENAPI = FIXTURE_SPECS / "openapi.yaml"
FIXTURE_RESPONSES = FIXTURE_RECORDED_API / "responses.json"
FIXTURE_TS_FILE = FIXTURE_SRC / "web" / "app.ts"

COMMANDS = [
    "/tc:learn-from-docs",
    "/tc:learn-from-specs",
    "/tc:learn-from-code",
    "/tc:learn-from-api",
    "/tc:learn-from-tests",
]

GAP_SIGNALS = [
    "undefined-term",
    "contradictory-rule",
    "unspecified-status",
    "schema-without-type",
    "unimplemented-endpoint",
    "undocumented-function",
    "language-unsupported-in-v1",
    "unspecified-endpoint",
    "mismatched-status",
    "untested-function",
    "unsupported-test-runner",
]

# Endpoints declared in the seeded openapi.yaml. The responses.json fixture
# must record at least one playback entry for each. responses.json MAY include
# additional entries (the unspecified-endpoint seed).
EXPECTED_SPEC_ENDPOINTS = [
    ("POST", "/sessions"),
    ("DELETE", "/sessions/{id}"),
    ("GET", "/accounts/{id}"),
    ("GET", "/workspaces"),
    ("POST", "/workspaces/{id}/assets"),
    ("GET", "/workspaces/{id}/assets"),
]

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
    assert name_match.group(1) == "tc-knowledge", (
        f"expected name: tc-knowledge, got {name_match.group(1)}"
    )
    assert KEBAB_CASE_RE.fullmatch(name_match.group(1)), "name must be kebab-case"
    assert desc_match.group(1).strip(), "description must be non-empty"


def test_skill_md_body_references_all_five_commands():
    text = SKILL_MD.read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"SKILL.md body must reference {cmd}"


def test_commands_directory_exists():
    assert COMMANDS_DIR.is_dir(), (
        f"expected {COMMANDS_DIR.relative_to(REPO)} (filled in by 3.2-3.6)"
    )


def test_methodology_directory_exists():
    assert METHODOLOGY_DIR.is_dir(), (
        f"expected {METHODOLOGY_DIR.relative_to(REPO)} (filled in by 3.2-3.6)"
    )


def test_templates_directory_exists():
    assert TEMPLATES_DIR.is_dir(), (
        f"expected {TEMPLATES_DIR.relative_to(REPO)} (filled in by 3.2-3.6)"
    )


def test_fixture_directory_exists():
    assert FIXTURE_DIR.is_dir(), f"expected {FIXTURE_DIR.relative_to(REPO)}"


def test_fixture_readme_describes_marker_convention():
    assert FIXTURE_README.is_file(), f"missing {FIXTURE_README.relative_to(REPO)}"
    text = FIXTURE_README.read_text(encoding="utf-8")
    assert "knowledge:" in text, (
        "fixture README must document the universal knowledge-marker convention"
    )
    assert "universal" in text.lower(), (
        "fixture README must describe the narrative as universal (D19)"
    )


def test_fixture_five_subtrees_present():
    for path in (
        FIXTURE_DOCUMENTS,
        FIXTURE_SPECS,
        FIXTURE_SRC,
        FIXTURE_TESTS,
        FIXTURE_RECORDED_API,
    ):
        assert path.is_dir(), f"missing fixture sub-tree: {path.relative_to(REPO)}"


def test_documents_subtree_has_three_files():
    for path in (FIXTURE_PRODUCT_OVERVIEW, FIXTURE_GLOSSARY, FIXTURE_JOURNEY):
        assert path.is_file(), f"missing documents file: {path.relative_to(REPO)}"


def test_glossary_has_definition_entries():
    text = FIXTURE_GLOSSARY.read_text(encoding="utf-8")
    # Definition-list shape OR table-row shape - either is enough to seed terms.
    has_definition_list = re.search(r"^\S.+\n:\s+\S", text, re.MULTILINE) is not None
    has_table_row = re.search(r"^\|\s*\S+\s*\|\s*\S+", text, re.MULTILINE) is not None
    assert has_definition_list or has_table_row, (
        "glossary.md must seed at least one term using a definition list or table row"
    )


def test_user_journey_has_ordered_steps():
    text = FIXTURE_JOURNEY.read_text(encoding="utf-8")
    has_numbered = re.search(r"^\s*1\.\s+\S", text, re.MULTILINE) is not None
    has_bulleted = re.search(r"^\s*[-*]\s+\S", text, re.MULTILINE) is not None
    assert has_numbered or has_bulleted, (
        "user-journey-sign-in.md must seed at least one journey with ordered or bulleted steps"
    )


def test_openapi_spec_declares_expected_endpoints():
    assert FIXTURE_OPENAPI.is_file(), f"missing {FIXTURE_OPENAPI.relative_to(REPO)}"
    text = FIXTURE_OPENAPI.read_text(encoding="utf-8")
    # Cheap text-level check (real YAML parsing happens in the 3.3 helper).
    for method, path in EXPECTED_SPEC_ENDPOINTS:
        assert path in text, f"openapi.yaml must declare path {path}"
        assert method.lower() in text.lower(), (
            f"openapi.yaml must declare method {method}"
        )


def test_openapi_spec_declares_components_schemas():
    text = FIXTURE_OPENAPI.read_text(encoding="utf-8")
    assert re.search(r"\bcomponents\b", text), (
        "openapi.yaml must declare a components section to seed schemas"
    )
    assert re.search(r"\bschemas\b", text), (
        "openapi.yaml must declare components.schemas to seed schemas"
    )


def test_openapi_spec_declares_security_schemes():
    text = FIXTURE_OPENAPI.read_text(encoding="utf-8")
    assert re.search(r"\bsecuritySchemes\b", text), (
        "openapi.yaml must declare components.securitySchemes to seed auth-schemes"
    )


def test_src_has_python_modules_classes_and_functions():
    py_files = list(FIXTURE_SRC.rglob("*.py"))
    assert py_files, "src/ must contain at least one Python module"
    found_class = False
    found_function = False
    for path in py_files:
        text = path.read_text(encoding="utf-8")
        if re.search(r"^class\s+\w+", text, re.MULTILINE):
            found_class = True
        if re.search(r"^def\s+\w+", text, re.MULTILINE):
            found_function = True
    assert found_class, "src/ must seed at least one Python class"
    assert found_function, "src/ must seed at least one Python function"


def test_src_has_function_with_docstring():
    found = False
    for path in FIXTURE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if re.search(r'^def\s+\w+.*?:\s*\n\s*"""', text, re.MULTILINE | re.DOTALL):
            found = True
            break
    assert found, "src/ must seed at least one Python function with a docstring"


def test_src_has_typescript_file_for_unsupported_language_signal():
    assert FIXTURE_TS_FILE.is_file(), (
        "src/web/app.ts must exist to seed the language-unsupported-in-v1 gap"
    )


def test_tests_subtree_has_pytest_files():
    pytest_files = [
        p
        for p in FIXTURE_TESTS.rglob("*.py")
        if p.name.startswith("test_") or p.name.endswith("_test.py")
    ]
    assert pytest_files, "tests/ must contain at least one pytest-shaped file"
    found_test_function = False
    for path in pytest_files:
        text = path.read_text(encoding="utf-8")
        if re.search(r"^def\s+test_\w+", text, re.MULTILINE):
            found_test_function = True
            break
    assert found_test_function, "tests/ must seed at least one test function"


def test_recorded_responses_parses_as_json_list():
    assert FIXTURE_RESPONSES.is_file(), f"missing {FIXTURE_RESPONSES.relative_to(REPO)}"
    data = json.loads(FIXTURE_RESPONSES.read_text(encoding="utf-8"))
    assert isinstance(data, list), "responses.json must be a JSON list"
    assert data, "responses.json must contain at least one playback entry"
    required_keys = {"method", "path", "status"}
    for entry in data:
        assert isinstance(entry, dict), "each responses.json entry must be a JSON object"
        missing = required_keys - entry.keys()
        assert not missing, (
            f"responses.json entry missing required keys {missing}: {entry}"
        )


def test_recorded_responses_cover_every_spec_endpoint():
    data = json.loads(FIXTURE_RESPONSES.read_text(encoding="utf-8"))
    recorded = {(entry["method"].upper(), entry["path"]) for entry in data}
    for method, path in EXPECTED_SPEC_ENDPOINTS:
        assert (method, path) in recorded, (
            f"responses.json missing playback for {method} {path}"
        )


def test_every_gap_signal_seeded_somewhere_in_fixture():
    tokens = collect_knowledge_tokens(FIXTURE_DIR)
    missing = [signal for signal in GAP_SIGNALS if signal not in tokens]
    assert not missing, (
        f"fixture missing seeded knowledge-marker tokens for gap signals: {missing}"
    )
