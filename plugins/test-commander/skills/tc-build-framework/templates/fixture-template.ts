// Fixture template - rendered by /tc:automate into tests/fixtures/<name>.ts.
// Fixtures are the only path test data reaches a spec (Decision D6): they load
// declarative data from the .test-commander/test-data/ tree that
// /tc:generate-test-data populates, never inlining literals in the spec.
import { test as base } from '@playwright/test';
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

export const test = base.extend<{ <fixtureName>: <FixtureName>Data }>({
  <fixtureName>: async ({}, use) => {
    await use(load<FixtureName>());
  },
});

export { expect } from '@playwright/test';
