# Learning from code

The methodology for `/tc:learn-from-code` (Phase 3 Step 3.4). Sits underneath the umbrella [`project-knowledge.md`](project-knowledge.md).

## What this command consumes

Python source under the configured source root (default `<workspace>/documents/uploaded/code/`, configurable via `tc-knowledge.code.source-root` in `<workspace>/config.yaml`). Non-Python source files (`.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.java`, `.rb`) are detected by extension and counted as `language-unsupported-in-v1` gaps; they are not silently ignored. v1 ships Python only via stdlib `ast`; future phases may extend the parsed-language set.

If the source root is missing or empty, the helper writes a `_No code source found_` stub for `code-derived-model.md` and exits 0.

## Universal-core extraction rules

Five positive dimensions plus three gap signals. The Python AST is itself the universal vocabulary; the extension hooks tune *where* the helper looks rather than *what* it recognizes.

### `modules`

Every `*.py` file under the source root that `ast.parse` accepts. Files that fail to parse are skipped silently (a corrupt Python file is the consumer's problem; the helper does not crash). The module's docstring (per `ast.get_docstring(tree)`) is captured.

### `classes`

Every `ast.ClassDef`. The helper captures the class name, line number, docstring, base classes (resolved via `ast.Name` for simple bases and `ast.Attribute` chains for dotted bases), and attributes assigned to `self` inside `__init__` (both plain `ast.Assign` and `ast.AnnAssign` shapes). Public methods (those whose name does not start with `_`) are also surfaced as `<ClassName>.<method>` functions.

**Worked example** (seeded fixture - `tests/fixtures/seeded-sample-project/src/app/models/account.py`):

```python
class Account:
    """A registered platform account."""

    def __init__(self, account_id: str, display_name: str, role: str = "member") -> None:
        self.id = account_id
        self.display_name = display_name
        self.role = role

    def is_admin(self) -> bool:
        """Return True when the account holds the admin role."""
        return self.role == "admin"
```

The helper captures `Account` with attributes `id, display_name, role` and the docstring, plus the method `Account.is_admin` as a function.

**Claude judgment layer:** decide which classes are domain entities (the kind that appear in glossaries) and which are implementation details (helpers, validators, exceptions). The helper cannot know that `Workspace` is a domain concept and `_PrivateCache` is not; Claude does.

### `functions`

Every `ast.FunctionDef` and `ast.AsyncFunctionDef`. The helper captures the function name, line, docstring, decorators (rendered back to a source-like string: `@app.get`, `@validator(...)`), and `is_async` flag.

**Worked example** (seeded fixture - `src/app/api/auth.py`):

```python
def sign_in(account_id: str, code: str) -> dict[str, str]:
    """Validate a one-time code and return a session record."""
    ...
```

The helper captures `sign_in` with no decorators, the first line of its docstring, and the line number.

**Claude judgment layer:** identify which functions are public-API entry points vs internal helpers; surface functions that are likely the implementations behind spec endpoints; flag functions whose signatures imply unspecified failure modes (e.g., a function that raises but whose docstring doesn't say so).

### `docstrings`

`ast.get_docstring()` is applied to every module / class / function. The first non-empty line of each docstring is surfaced in the rendered model alongside the structural finding.

### `decorators`

Decorator names captured per function. The renderer handles simple names (`@validator`), attribute chains (`@app.get`), and calls (`@router.get(...)` becomes `@router.get(...)` with the call elided).

Decorators are the cleanest signal for cross-checking spec endpoints in real-world code — if a function carries `@app.post("/sessions")`, the path is structurally available. The `tc-knowledge.code.endpoint-decorator-patterns` extension is reserved for future use; v1 cross-checks by operationId only.

## Gap signals

All three are routed to `<workspace>/requirements/open-questions.md`, deduplicated by `(source-id, question-text)`. The question text includes the gap kind as a prefix (`[undocumented-function] ...`) so grep over the open-questions file by kind works uniformly.

### `undocumented-function`

A public function (`name` not starting with `_`, and the qualified `Class.method` form where `method` also does not start with `_`) whose `ast.get_docstring()` is `None` or empty.

**Worked example** (seeded fixture): `app.api.files.upload_file` is defined without a docstring; the gap fires with the function path and line.

### `language-unsupported-in-v1`

Every file under the source root whose extension is one of `.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.java`, `.rb`. The helper does not attempt to parse them; the gap surfaces the presence so consuming projects know what is uncovered in v1.

**Worked example** (seeded fixture): `src/web/app.ts` fires the gap.

### `unimplemented-endpoint`

When `<workspace>/product-knowledge/spec-derived-model.md` has been generated by `/tc:learn-from-specs` (the helper checks for the file's `Auto-generated by /tc:learn-from-specs` marker, exactly the way Phase 2 helpers check for generator markers), the code helper parses the endpoints table and looks up each endpoint's operationId against the set of function names captured (both plain names and the trailing segment of `Class.method` forms). Endpoints whose operationId does not match any function name produce an `unimplemented-endpoint` gap.

**Worked example** (seeded fixture): the spec declares `GET /workspaces` with `operationId: list_workspaces`; no Python function named `list_workspaces` exists in `src/`. The gap fires with the method, path, and operationId.

When `spec-derived-model.md` is not generated (template stub or absent), the cross-check is skipped entirely. The cross-check is therefore order-independent: running `/tc:learn-from-code` before `/tc:learn-from-specs` produces no `unimplemented-endpoint` gaps; re-running `/tc:learn-from-code` after `/tc:learn-from-specs` ran later fires them.

## Cross-cutting contributions

`/tc:learn-from-code` writes to:

- `entities.md` `## From code` - classes contribute as domain-entity candidates with one bullet each (`- **ClassName** (path:line) - docstring summary`).
- `business-rules.md` `## From code` - reserved for module-level constants carrying explicit rule docstrings. The seeded fixture has no such constants, so the section is empty and omitted from the rendered file in v1.
- `user-journeys.md` and `assumptions.md` are **not touched**. Code declares no journeys, and code facts are confirmed not inferred.

## Idempotency contract

Re-running `/tc:learn-from-code` against unchanged input produces:

- byte-identical `code-derived-model.md`;
- byte-identical `## From code` section in `entities.md`;
- no new lines in `open-questions.md`;
- a byte-identical `system-model.md` regenerated by `synthesize_system_model.py`.

The dedup key includes the gap kind prefix, so different gap kinds for the same underlying file are independent open-question entries.

## Configurable extensions

```yaml
tc-knowledge:
  code:
    source-root: src                              # default: documents/uploaded/code
    enabled-languages: [python]                   # default: [python]; v1 parses python only
    ignored-paths: [migrations, __pycache__, .venv]
    endpoint-decorator-patterns: ["@app.{method}", "@router.{method}"]  # reserved (v1 unused)
```

- `source-root` resolves relative to the workspace root (`<workspace>/<source-root>`). Use `../src` to point at the consuming project's actual source directory if it lives outside the workspace.
- `enabled-languages` is a list; v1 recognizes only `python`. Setting `[]` disables the AST walk entirely while still flagging unsupported-language files.
- `ignored-paths` does substring matching against the relative path (so `migrations` excludes both `app/migrations/` and `tests/migrations/`).

## See also

- [Umbrella methodology](project-knowledge.md)
- [Per-command page](../commands/learn-from-code.md)
- [Output template](../templates/code-derived-model-template.md)
