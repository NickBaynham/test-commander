// Deliberately-flawed generated spec for the Step 6.5 automation review.
// Each test below seeds one defect from the universal automation-review rubric,
// marked with a `// knowledge: <category>` comment so the review test can
// verify rubric coverage. The file is intentionally NOT listed in
// automation-map.md, which seeds the file-level untraceable-spec finding.
// Not a claim about any product's scope (D19).
import { test, expect } from '../fixtures/sign-in';
import { SignInPage } from '../pages/SignInPage';

test.describe('Flawed sign-in automation (review fixture)', () => {
  // knowledge: inline-test-data
  // @req:REQ-001 @cs:CS-001-001
  test('inlines credentials instead of using the fixture', async ({ page }) => {
    await page.getByLabel('Email').fill('user@example.com');
    await expect(page).toHaveURL(/dashboard/);
  });

  // knowledge: hardcoded-wait
  // @req:REQ-001 @cs:CS-001-002
  test('uses a hardcoded wait', async ({ page }) => {
    await page.waitForTimeout(3000);
    await expect(page).toHaveURL(/dashboard/);
  });

  // knowledge: missing-provenance
  test('has no provenance comment', async ({ page, data }) => {
    await expect(page).toHaveTitle(/.+/);
  });

  // knowledge: weak-locator
  // @req:REQ-001 @cs:CS-001-003
  test('uses a brittle CSS locator', async ({ page }) => {
    await page.locator('#submit').click();
    await expect(page).toHaveURL(/dashboard/);
  });

  // knowledge: assertion-free
  // @req:REQ-001 @cs:CS-001-001
  test('asserts nothing', async ({ page, data }) => {
    const signIn = new SignInPage(page);
    await signIn.goto();
  });
});
