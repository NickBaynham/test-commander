# Learning from tests

The methodology for `/tc:learn-from-tests` (Phase 3 Step 3.6). Sits underneath the umbrella [`project-knowledge.md`](project-knowledge.md). This is the final `/tc:learn-from-*` command in Phase 3; it closes the helper sweep.

## What this command consumes

Test files under the configured tests source root (default `<workspace>/documents/uploaded/tests/`, configurable via `tc-knowledge.tests.source-root`):

- **pytest-style Python**: files matching `test_*.py` or `*_test.py`. Parsed with stdlib `ast`. Every function whose name starts with `test_` is captured as a test function with `<path>:<line>` provenance and the set of identifier references inside its body.
- **Playwright spec files**: files matching `*.spec.ts`. Detected by extension and counted by a regex pass against `test(` calls, but **not parsed** in v1 - TypeScript parsing is deferred to a future phase. The methodology calls this out explicitly with the `unsupported-test-runner` gap so consuming projects know what is unreachable in v1.

If the tests root is missing, the helper writes a `_No tests found_` stub for `tests-coverage.md` and exits 0.

## Universal-core extraction rules

Three positive dimensions plus two gap signals.

### `test-files`

Every file matching one of the recognized patterns. Pytest files get an `ast.parse` pass; Playwright files get a regex pass. The rendered table groups by runner (`pytest` vs `playwright (counted, not parsed)`).

### `test-functions`

For pytest, every `ast.FunctionDef` and `ast.AsyncFunctionDef` whose name starts with `test_`. Class-nested test methods (`class TestSomething:` with `def test_foo`) are captured via `ast.walk` traversal so nested classes don't hide tests.

For Playwright, the regex matches `test('label', ...)` and `test("label", ...)`. The label is recorded only at the count level; v1 does not list per-test labels.

### `covered-symbols`

For each pytest test function, the helper walks the function body and collects every `ast.Name.id` (identifier reference) and every `ast.Attribute.attr` (attribute access). The aggregate union across all pytest tests becomes the "covered symbols" set, which feeds the `untested-function` cross-check.

**Worked example** (seeded fixture - `tests/fixtures/seeded-sample-project/tests/test_auth.py`):

```python
from app.api.auth import sign_in, sign_out


def test_sign_in_returns_session():
    session = sign_in("acc-123", "code-abc")
    assert session["account_id"] == "acc-123"
    assert session["id"].startswith("sess-")
```

The helper captures the test function `test_sign_in_returns_session` with referenced symbols `{sign_in, sign_out, session, startswith, ...}`. The covered-symbols aggregate then includes `sign_in`, `sign_out`, `is_non_empty_string`, `is_positive_int` across the seeded suite.

**Claude judgment layer:** distinguish "the symbol appears in the test body" (mechanical signal) from "the symbol is actually exercised by the test" (intent-level). A test that imports a symbol but never calls it shows up as covered under the mechanical heuristic but is not genuinely tested. Claude flags suspicious imports for human review.

## Gap signals

Both gaps route to `<workspace>/requirements/open-questions.md` with the `[<kind>]` prefix (Step-3.4 convention) and deduplicated by `(source-id, question-text)`.

### `unsupported-test-runner`

Every `*.spec.ts` file emits this gap. The helper detects the file, counts the test calls, but does not parse the TypeScript. The gap surfaces the presence so consuming projects know v1 cannot tell which symbols a Playwright test exercises.

**Worked example** (seeded fixture): `web.spec.ts` fires the gap.

### `untested-function`

Requires `code-derived-model.md` to be generated (i.e., `/tc:learn-from-code` has run). The helper imports `extract_knowledge_from_code` (mirroring Step 3.5's cross-helper import pattern) and walks its parsed functions. A public function (`name` not starting with `_`, and `Class.method` form where method also does not start with `_`) is flagged when its plain name does not appear in the covered-symbols aggregate.

**Worked example** (seeded fixture): `app.api.files.upload_file` is defined in `src/` but never imported by any test. After `/tc:learn-from-code` runs, `/tc:learn-from-tests` emits the `[untested-function]` open question.

When `code-derived-model.md` is not generated (workspace stub or empty-run sentinel), the cross-check is silent. Order-independent: running tests before code produces no `untested-function` gaps; running code later then re-running tests lands them.

## Cross-cutting contributions

`/tc:learn-from-tests` contributes only to `entities.md`:

- `## From tests` lists each class from `code-derived-model.md` annotated with coverage confidence:
  - **covered** - the class name appears in the covered-symbols aggregate (at least one test references it);
  - **uncovered** - the class is defined in code but no test references it.

The section is rendered only when `code-derived-model.md` is generated; without code, the helper has no class list to annotate.

`/tc:learn-from-tests` does NOT touch:

- `user-journeys.md` - tests encode no journeys.
- `assumptions.md` - test files are confirmed facts.
- `business-rules.md` - tests express coverage, not rules.

Four explicit negative tests in `tests/test_learn_from_tests.py` defend the scope contract.

## Idempotency contract

Re-running `/tc:learn-from-tests` against unchanged input produces:

- byte-identical `tests-coverage.md`;
- byte-identical `## From tests` section body in `entities.md`;
- no new lines in `open-questions.md`;
- a byte-identical `system-model.md` regenerated by `synthesize_system_model.py`.

The dedup key includes the `[<kind>]` prefix, so `unsupported-test-runner` for a specific file and `untested-function` for a specific function are tracked independently.

## Configurable extensions

```yaml
tc-knowledge:
  tests:
    source-root: tests                              # default: documents/uploaded/tests
    ignored-paths: [__pycache__, fixtures, .venv]
```

- `source-root` resolves relative to the workspace root. Use `../tests` to point at the consuming project's actual test directory if it lives outside the workspace.
- `ignored-paths` does part-matching against the relative path; default includes common Python test detritus.

## See also

- [Umbrella methodology](project-knowledge.md)
- [Per-command page](../commands/learn-from-tests.md)
- [Output template](../templates/tests-coverage-template.md)
