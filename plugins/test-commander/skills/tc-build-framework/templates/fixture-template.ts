// Fixture template - rendered by /tc:automate into tests/fixtures/<name>.ts.
// Fixtures are the only path test data reaches a spec (Decision D6): they load
// declarative data from the .test-commander/test-data/ tree that
// /tc:generate-test-data populates, never inlining literals in the spec.
//
// Best practice for a shared backend (a database that persists between tests):
//   1. an auto `resetState` fixture restores a known state before every test;
//   2. expose typed data so specs read it instead of re-fetching;
//   3. for data-driven cases, loop a dataset (see the footer) so adding a case
//      is adding a row, not copying a test.
import { test as base, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

type <FixtureName>Data = {
  // Shape mirrors the matching .test-commander/test-data/ manifest.
  <field>: string;
};

function load<FixtureName>(): <FixtureName>Data {
  const dataPath = resolve(
    __dirname,
    '../../.test-commander/test-data/seed/<name>.json',
  );
  return JSON.parse(readFileSync(dataPath, 'utf-8')) as <FixtureName>Data;
}

export const test = base.extend<{ <fixtureName>: <FixtureName>Data; resetState: void }>({
  // Auto: reset to a known state before each test when a reset endpoint is
  // configured (PLAYWRIGHT_RESET_PATH). No-op otherwise. Required for isolation on
  // a shared backend; harmless for a per-test or stateless target.
  resetState: [
    async ({ request }, use) => {
      const resetPath = process.env.PLAYWRIGHT_RESET_PATH;
      if (resetPath) {
        const res = await request.post(resetPath);
        expect(res.ok(), `reset failed: ${resetPath}`).toBeTruthy();
      }
      await use();
    },
    { auto: true },
  ],

  <fixtureName>: async ({}, use) => {
    await use(load<FixtureName>());
  },
});

export { expect };

// Data-driven example - one row per case, each carrying its @req id so coverage
// ingestion still links it:
//   for (const tc of <fixtureName>.cases) {
//     test(`${tc.req} ${tc.name}`, async ({ page }) => { /* ... */ });
//   }
