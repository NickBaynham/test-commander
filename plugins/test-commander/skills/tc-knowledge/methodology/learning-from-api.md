# Learning from the API

The methodology for `/tc:learn-from-api` (Phase 3 Step 3.5). Sits underneath the umbrella [`project-knowledge.md`](project-knowledge.md).

## What this command consumes

Recorded API responses in JSON. The helper reads a single playback file at the configured path (default `<workspace>/documents/uploaded/recorded-api/responses.json`, overridable via `tc-knowledge.api.recorded-path`). Each entry is an object:

```json
{
  "method": "POST",
  "path": "/sessions",
  "status": 201,
  "headers": {"content-type": "application/json", "authorization": "Bearer ..."},
  "body": {"id": "sess-1", "account_id": "acc-1"}
}
```

The helper does not invent the playback; consuming projects supply it by recording a session against their running API (e.g., from a Postman run, a curl session, or an integration-test harness) and serializing the relevant request/response pairs.

If the playback file is missing or unparseable, the helper writes a `_No recorded API responses found_` stub for `api-model.md` and exits 0.

## Recorded vs live mode

Recorded mode is the default. `tc-knowledge.api.mode: live` opts into live HTTP probing against `tc-knowledge.api.base-url`. v1 ships only recorded mode; live mode is documented for future use and is **refused under pytest** — the helper detects pytest via the `PYTEST_CURRENT_TEST` environment variable and exits 2 with a clear error before issuing any network call. This guarantees the test suite never reaches the network.

In real-world use, live mode would loop over the endpoints declared by `spec-derived-model.md` (Step 3.3) and probe each one with the configured auth header. v1 stops at the refusal; the recorded playback is sufficient for every Phase-3 contract.

## Universal-core extraction rules

Three positive dimensions plus two gap signals. No domain vocabulary; the structural keys (`method`, `path`, `status`, `headers`, `body`) are themselves a universal vocabulary.

### `live-endpoints`

Every entry in the playback file is a recording of a live request that actually returned a response. The helper captures `(method, path, status, source-file:index)` per entry. The status is classified into a family (`2xx`, `3xx`, `4xx`, `5xx`) for quick scanning.

### `response-shapes`

For each recording whose body is a JSON object, the helper captures the sorted set of top-level keys. For JSON arrays of objects, the top-level keys of the first element. These shapes are the *runtime* answer to "what does this endpoint actually return"; they complement the spec's *declared* schema.

**Claude judgment layer:** correlate the observed shape with `spec-derived-model.md`'s declared schemas — does the response match a `components.schemas` entry, or is it an undocumented variant? Identify shapes that appear identical across multiple endpoints (a shared response envelope); flag shapes that include sensitive fields (`token`, `secret`) for review.

### `auth-required`

An endpoint is inferred to require authentication if the recorded request carried an `Authorization` header, OR if the recorded response returned 401 / 403 without one. The detection is intentionally permissive: a single recording is enough to flag the endpoint. The methodology assumes a real project records representative requests; spotty recording skews the result.

**Worked example** (seeded fixture): `GET /workspaces` carries `"authorization": "Bearer redacted"` in its headers, so the endpoint surfaces as auth-required in both `api-model.md` and `business-rules.md`'s `## From api` section.

**Claude judgment layer:** correlate auth-required endpoints with `components.securitySchemes` from the spec (which scheme is in use); identify endpoints that should require auth but don't (a write endpoint with no Authorization in any recording is suspicious); explain the auth flow in plain language for the project's testers.

## Gap signals

Both gaps are routed to `<workspace>/requirements/open-questions.md` with the `[<kind>]` prefix established in Step 3.4 and deduplicated by `(source-id, question-text)`. Both gaps require `spec-derived-model.md` to be generated (i.e., `/tc:learn-from-specs` has run); without a spec there is nothing to cross-check against.

### `unspecified-endpoint`

A recorded `(method, path)` that does not appear in the spec's endpoint list. The endpoint exists at runtime but the spec is silent on it.

**Worked example** (seeded fixture): `GET /accounts/me` returns 200 in the playback but the spec declares only `GET /accounts/{id}`. The gap fires; the open question prompts the consuming project to decide whether the endpoint is intentional (and should be added to the spec) or an accidental leak.

### `mismatched-status`

A recorded status code that the spec does not declare for that endpoint. The cross-check fires only when the spec actually declares some statuses for the endpoint — when the spec declares no responses (the `unspecified-status` gap on the spec side already covers it), this check is silent to avoid emitting two gaps for the same root cause.

**Worked example** (seeded fixture): `DELETE /sessions/{id}` is recorded returning 500, but the spec declares only 204 for that endpoint. The gap fires.

## Cross-cutting contributions

`/tc:learn-from-api` writes to two cross-cutting artifacts only:

- `entities.md` `## From api` - resources confirmed reachable at runtime. The resource name is the first non-templated URL segment (same convention `/tc:learn-from-specs` uses), and the bullet shows the methods observed plus the first citation.
- `business-rules.md` `## From api` - one rule per auth-required endpoint ("Endpoint X requires authentication").

`/tc:learn-from-api` does NOT touch `user-journeys.md` (the playback does not encode journeys; a sequence of requests in a session is just data, not a labeled journey) or `assumptions.md` (every recording is a confirmed observed fact, not an inference).

## Idempotency contract

Re-running `/tc:learn-from-api` against unchanged input produces:

- byte-identical `api-model.md`;
- byte-identical `## From api` section bodies in `entities.md` and `business-rules.md`;
- no new lines in `open-questions.md`;
- a byte-identical `system-model.md` regenerated by `synthesize_system_model.py`.

The dedup key includes the `[<kind>]` prefix, so the same endpoint emitting both `unspecified-endpoint` (recorded but not in spec) and `mismatched-status` (status not declared) would be independently tracked. The seeded fixture only exercises one gap per endpoint.

## Configurable extensions

```yaml
tc-knowledge:
  api:
    mode: recorded                              # or: live  (refused under pytest)
    recorded-path: documents/uploaded/recorded-api/responses.json
    base-url: http://localhost:8000             # live mode only
    auth-header: "Authorization: Bearer ${TC_API_TOKEN}"  # live mode only
```

- `mode` is `recorded` (default) or `live`. v1 only reaches the recorded path; live is documented for future-phase implementation and refused under pytest.
- `recorded-path` is resolved relative to the workspace root.
- `base-url` and `auth-header` are reserved for live mode; v1 ignores them when in recorded mode.

## See also

- [Umbrella methodology](project-knowledge.md)
- [Per-command page](../commands/learn-from-api.md)
- [Output template](../templates/api-model-template.md)
