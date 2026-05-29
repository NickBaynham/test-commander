// Page object template - rendered by /tc:automate into tests/pages/<Area>Page.ts.
// One page object per @area: namespace. Locators live here, never in specs.
// See methodology/locator-strategy.md for the locator priority order.
import { type Page, type Locator } from '@playwright/test';

export class <AreaName>Page {
  readonly page: Page;

  // Prefer role/label/test-id locators over CSS or XPath (locator-strategy.md).
  readonly <elementName>: Locator;

  constructor(page: Page) {
    this.page = page;
    this.<elementName> = page.getByRole('<role>', { name: '<accessible name>' });
  }

  async goto(): Promise<void> {
    await this.page.goto('/<area-path>');
  }

  async <behaviorName>(): Promise<void> {
    // Behavior-level method - one user-meaningful action per method.
    await this.<elementName>.click();
  }
}
