# Database-layer assertions

API and UI assertions confirm what the application *returns*. Database-layer
assertions confirm what it *stored* — that a write actually landed, with the
right shape and the right relationships. They catch a class of defect the other
layers miss: a value silently dropped on write, a relationship stored against the
wrong record, a "success" response that never persisted, a rejected record that
was written anyway.

This is the third layer named in the test plan (UI / API / DB) and the one most
often left empty. It lives under `tests/db/`.

## When a DB assertion earns its place

Add one when the test already exercises a write and the *persistence* is the
risk, not just the response:

- **Create** — after creating an entity, read it back from the store and assert
  the fields match (especially fields the API transforms or omits).
- **Relationships** — assert foreign-key-style references are stored correctly
  (the appointment's `patient_id`/`doctor_id` point at the right documents).
- **Updates** — after a status change, assert the new value is in the store, not
  just in the response.
- **Negative writes** — after a rejected create, assert the record was **not**
  inserted (the collection count is unchanged). A 4xx response that still writes
  is a real bug.
- **No orphans** — after a delete, assert nothing dangles.

Do not mirror every API assertion at the DB layer — that is noise. Assert at the
DB only where persistence or relationships are the thing under test.

## The two things that bite

1. **ID representation.** The store and the API rarely agree. A document `_id`
   may be a native object id while the API returns a string; a relationship field
   may be stored as that native type while the API serializes it to a string.
   Centralize the translation (`idEquals(stored, apiId)` in the template) instead
   of scattering `.toString()` calls.
2. **Connection lifecycle.** Open one connection per worker, not per test — a
   **worker-scoped, lazy** fixture. Lazy matters: only tests that take the `db`
   fixture should open a connection, so pure UI/API tests stay decoupled from the
   datastore being reachable.

## The fixture

```ts
export const test = base.extend<{}, { db: DbClient }>({
  db: [async ({}, use) => {
    const client = await DbClient.connect();
    await use(client);
    await client.close();
  }, { scope: 'worker' }],
});
```

A test then asks for it and asserts against the store:

```ts
test('REQ-NNN create persists with the right reference', async ({ request, db }) => {
  const created = await (await request.post('/appointments', { data })).json();
  const stored = await db.findById('appointments', created.id);
  expect(stored?.status).toBe('scheduled');
  expect(idEquals(stored!.patient_id, created.patient_id)).toBeTruthy();
});
```

See [db-client-template.ts](../templates/db-client-template.ts) for the client and
[playwright-standards.md](playwright-standards.md) for where it sits in the tree.
