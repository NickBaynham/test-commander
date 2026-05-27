# Learning from specs

The methodology for `/tc:learn-from-specs` (Phase 3 Step 3.3). Sits underneath the umbrella [`project-knowledge.md`](project-knowledge.md).

## What this command consumes

Spec sources placed anywhere under `<workspace>/documents/uploaded/`:

- `openapi.yaml`, `openapi.yml`, `*.openapi.yaml`, `*.openapi.yml` - OpenAPI 3 in YAML.
- `openapi.json`, `*.openapi.json` - OpenAPI 3 in JSON.
- `*.postman_collection.json` - Postman v2.1 collections.

Auto-detection is by file extension; the helper does not look at the document root keys. OpenAPI 2 (Swagger) and OpenAPI 3.1 are accepted as long as PyYAML / `json.loads` can parse them — the extractors only reach into the canonical `paths` / `components.schemas` / `components.securitySchemes` shape that both versions share.

If multiple spec files exist, every one of them is parsed and the findings are unioned. If none exist, the helper writes a `_No spec found_` stub for `spec-derived-model.md` and exits 0.

## Universal-core extraction rules

Three positive dimensions plus two gap signals. No config extensions in 3.3 — the structural keys in OpenAPI and Postman are themselves a universal vocabulary.

### `endpoints`

Mechanical check (OpenAPI): every `paths.<path>.<method>` triple where `<method>` is one of `get`, `post`, `put`, `patch`, `delete`, `options`, `head`, `trace`. Mechanical check (Postman): every `item.request` with `request.method` populated. Provenance is the line of the method block in the source file.

**Worked example** (seeded fixture - `tests/fixtures/seeded-sample-project/specs/openapi.yaml`):

```yaml
paths:
  /sessions:
    post:
      summary: Create a session (sign in).
      operationId: create_session
      ...
```

The helper captures `POST /sessions` with `operationId=create_session`, the summary, and a citation to the `post:` line.

**Claude judgment layer:** decide which endpoints are core (sign-in, sign-out, primary CRUD on each resource) vs auxiliary (health checks, telemetry probes), and surface endpoint groups that lack expected operations (e.g., a `Workspace` resource with `GET` and `POST` but no `DELETE` — likely a gap worth raising as an open question).

### `schemas`

Mechanical check (OpenAPI): every entry under `components.schemas`. Each schema's `type` and `$ref` are recorded; everything else is summarized in the per-source model. Mechanical check (Postman): every `request.body.raw` JSON shape; the top-level keys become a named schema (`<request-label>Body`).

**Worked example** (seeded fixture):

```yaml
components:
  schemas:
    Account:
      type: object
      properties:
        id:
          type: string
        display_name:
          type: string
```

The helper captures `Account` with `type=object` and a citation to the `Account:` heading.

**Claude judgment layer:** identify when one schema's shape is a strict subset of another (a likely refactor target), name the canonical entity each schema represents (the spec's `Account` is the documentation's `Account`; the spec's `SignInRequest` represents the parameter set of one endpoint, not an entity), and flag schemas referenced by `$ref` but never defined.

### `auth-schemes`

Mechanical check (OpenAPI): every entry under `components.securitySchemes`. Mechanical check (Postman): every distinct `request.auth.type` value across all requests.

**Worked example** (seeded fixture):

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

The helper captures `bearerAuth` with `type=http`, `scheme=bearer`, and a citation to the `bearerAuth:` heading.

**Claude judgment layer:** explain the operational implications (what credentials a tester needs, what bearer-token format the API issues), correlate per-endpoint `security` requirements with the global scheme list, and surface endpoints that have no declared security where the operation suggests one should be required.

## Gap signals

Both are routed to `<workspace>/requirements/open-questions.md`, deduplicated by `(source-id, question-text)`.

### `unspecified-status`

An OpenAPI endpoint that declares no `responses` keys, or only the `default` response. The spec is silent on what status codes can come back; the consuming project cannot test what the spec does not promise.

### `schema-without-type`

A `components.schemas.<name>` entry with neither a `type` field nor a `$ref`. The shape of values matching the schema is ambiguous; tooling that relies on schema-driven serialization (clients, validators) cannot know what to do with such an entry.

## Cross-cutting contributions

`/tc:learn-from-specs` writes to two cross-cutting artifacts only:

- `entities.md` `## From specs` - endpoints grouped by HTTP-path resource (the first non-templated segment of the path). Each resource is a single bullet showing the HTTP methods exposed and the first citation. The convention is: spec endpoints describe the *resources* the system exposes; the resource name is the cross-source entity anchor.
- `business-rules.md` `## From specs` - each `securityScheme` becomes a rule ("Auth scheme X applies to protected endpoints"). Per-endpoint `security` declarations are visible in the per-source model; the cross-cutting summary surfaces only the scheme list.

`/tc:learn-from-specs` does NOT touch `user-journeys.md` (specs declare no journeys) or `assumptions.md` (specs are confirmed facts with citations, not inferences).

## Idempotency contract

Re-running `/tc:learn-from-specs` against unchanged input produces:

- byte-identical `spec-derived-model.md`;
- byte-identical `## From specs` section bodies in `entities.md` and `business-rules.md`;
- no new lines in `open-questions.md`;
- a byte-identical `system-model.md` regenerated by `synthesize_system_model.py`.

## See also

- [Umbrella methodology](project-knowledge.md)
- [Per-command page](../commands/learn-from-specs.md)
- [Output template](../templates/spec-derived-model-template.md)
