// Component object template - rendered by /tc:automate into
// tests/components/<Component>.ts. Use for UI fragments shared across pages
// (nav bars, dialogs, and especially tables/filters) so locators are defined
// once and list-area specs assert through the component, not inline row
// locators. See methodology/ui-test-quality.md.
import { type Page, type Locator } from '@playwright/test';

// Example: a list table with its filters. Adapt the test-ids to your app. The
// pattern - rows(), rowContaining(), cell(), filterBy() - keeps row/filter
// locators out of every spec that touches the list.
export class <ComponentName>Component {
  readonly page: Page;
  readonly root: Locator;

  constructor(page: Page) {
    this.page = page;
    // Scope the component to its root so its locators do not collide globally.
    this.root = page.getByTestId('<component-test-id>');
  }

  rows(): Locator {
    return this.root.locator('tbody tr');
  }

  /** The first row containing the given text - assert on its cells/actions. */
  rowContaining(text: string): Locator {
    return this.rows().filter({ hasText: text });
  }

  /** Apply a filter control by accessible name (e.g. a Status/Department select). */
  async filterBy(name: string, value: string): Promise<void> {
    await this.root.getByRole('combobox', { name }).selectOption({ label: value });
  }
}
