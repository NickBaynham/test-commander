// knowledge: unsupported-test-runner
// Playwright spec file exists to seed the unsupported-test-runner gap signal:
// the Phase 3 /tc:learn-from-tests helper detects .spec.ts files by extension
// and counts them, but does not parse Playwright tests in v1.

import { test, expect } from "@playwright/test";

test("session detection", () => {
  expect(1 + 1).toBe(2);
});
