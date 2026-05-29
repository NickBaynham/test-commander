# Locator strategy

How page objects locate elements. The order below is the priority Test
Commander's generated page objects follow; it favors locators that survive
markup churn and assert accessibility, over brittle structural selectors. It is
universal (Decision D19) - it names locator *kinds*, not any product's elements.

## Priority order

Prefer the first kind that uniquely identifies the element:

1. **Role + accessible name** - `page.getByRole('button', { name: 'Sign in' })`.
   The most resilient: it ties the locator to the element's semantics and
   doubles as an accessibility assertion.
2. **Label** - `page.getByLabel('Email')`. For form controls associated with a
   visible label.
3. **Placeholder / text** - `page.getByPlaceholder(...)`, `page.getByText(...)`.
   For elements identified by user-visible content.
4. **Test id** - `page.getByTestId('<id>')`. When no semantic locator is stable,
   a deliberate `data-testid` is the explicit contract between app and test.
5. **CSS / XPath** - last resort only. Brittle against markup churn; a
   generated page object that reaches for CSS is a `weak-locator` finding in the
   Phase 6.5 automation review.

## Scope components

Component objects scope their locators to a root (`getByTestId('<root>')`) so
the same control on two pages does not collide. Page objects own page-level
locators; components own fragment-level locators.

## No waits-as-sleeps

Use Playwright's auto-waiting and web-first assertions (`expect(locator)`),
never a fixed `page.waitForTimeout(...)`. A hard-coded wait is a
`hardcoded-wait` finding in the automation review.

## See also

- [Playwright standards](playwright-standards.md) - framework layout and discipline.
- [Page object template](../templates/page-object-template.ts) - the locator declarations in context.
