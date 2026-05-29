// Component object template - rendered by /tc:automate into
// tests/components/<Component>.ts. Use for UI fragments shared across pages
// (nav bars, dialogs, tables) so locators are defined once and reused.
import { type Page, type Locator } from '@playwright/test';

export class <ComponentName>Component {
  readonly page: Page;
  readonly root: Locator;

  constructor(page: Page) {
    this.page = page;
    // Scope the component to its root so its locators do not collide globally.
    this.root = page.getByTestId('<component-test-id>');
  }

  async <behaviorName>(): Promise<void> {
    await this.root.getByRole('<role>', { name: '<accessible name>' }).click();
  }
}
