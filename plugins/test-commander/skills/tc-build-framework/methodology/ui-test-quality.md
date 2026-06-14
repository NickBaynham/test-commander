# UI test quality

Beyond the structural rubric (`/tc:review-automation`), three practices separate
a UI suite that gives real confidence from one that just clicks through happy
paths. They are judgment-layer expectations: the generator scaffolds the shape,
the author fills these in.

## 1. Component objects for shared fragments

Page objects own a page; **component objects** own a fragment that repeats across
pages — a nav bar, a dialog, and above all a **list table with its filters**.
Without one, every spec that touches the list re-declares row and filter
locators, and a markup change breaks them all.

Give any list/table/filter surface a component object
([component-object-template.ts](../templates/component-object-template.ts)): a
`rows()`, a `rowContaining(text)`, and a `filterBy(name, value)`. List-area specs
assert through the component — `expect(table.rowContaining('Jordan Lee')).toContainText('Active')`
— never inline `tbody tr` locators. This is where row-action, filter, and
empty-state assertions live.

## 2. Cover the empty state and the error state, not just the happy path

The two highest-bug, lowest-covered surfaces on any UI are the **empty state**
(no data) and the **error state** (a rejected action, a failed request). For each
UI area with a list or a form, expect at minimum:

- a **happy** scenario (the documented success path);
- an **empty-state** scenario (the list/dashboard with no data renders the empty
  state, not a broken table);
- an **error/validation** scenario (a rejected submit surfaces the error **and**
  does not perform the write — pair it with a count/DB assertion so a "success"
  message can't hide a no-op; see `unverified-write` in the automation review).

A UI area that only has a happy-path test is under-covered, however green it
looks. Track the gap in the coverage map rather than letting the green hide it.

## 3. Accessibility as an optional gate

Run an axe-core scan on key surfaces with the
[a11y-fixture-template.ts](../templates/a11y-fixture-template.ts) fixture
(`@axe-core/playwright`). A single `a11yScan()` per primary page catches the
common WCAG violations (missing labels, contrast, roles) cheaply and is a
genuine quality signal, not just a checkbox. Treat it as opt-in per project.

## See also

- [Playwright standards](playwright-standards.md) - the framework shape and the rubric.
- [Database assertions](database-assertions.md) - the third assertion layer.
- [Locator strategy](locator-strategy.md) - the locator priority order.
