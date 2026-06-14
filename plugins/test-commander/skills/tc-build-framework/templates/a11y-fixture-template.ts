// Accessibility-scan fixture template - copy into tests/fixtures/a11y.ts.
// Adds an `a11y` fixture that runs an axe-core scan of the current page and
// fails on WCAG violations - an optional quality gate on key surfaces.
// Requires the @axe-core/playwright dev dependency:  npm i -D @axe-core/playwright
// See methodology/ui-test-quality.md.
import { test as base, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

export const test = base.extend<{ a11yScan: () => Promise<void> }>({
  a11yScan: async ({ page }, use) => {
    await use(async () => {
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();
      expect(results.violations, 'page has no accessibility violations').toEqual([]);
    });
  },
});

export { expect };

// Usage:
//   test('REQ-NNN dashboard is accessible', async ({ page, a11yScan }) => {
//     await page.goto('/');
//     await a11yScan();
//   });
