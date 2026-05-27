# Bookstore Acceptance Criteria (intentionally flawed)

These acceptance criteria describe expected behavior for selected bookstore stories. Each AC carries at least one defect, marked with an inline `<!-- defect: ac-<dimension> -->` comment. See `README.md` for the defect-marking convention.

## US-001: Checkout

<!-- defect: ac-missing-edge-cases -->
AC-001-01: Given a customer with at least one item in their cart, When they click "Checkout" and enter valid payment details, Then the order is placed and a confirmation page is shown. (Happy path only — no coverage of out-of-stock items, expired-cart edge cases, or split-shipment behavior.)

<!-- defect: ac-missing-negative-cases -->
AC-001-02: Given a logged-in customer at the checkout page, When they submit the order, Then the order is placed successfully. (No negative case: what happens when payment is declined, validation fails, or the network drops mid-submit?)

## US-002: Buy-now button

<!-- defect: ac-untestable-predicate -->
AC-002-01: Given the customer is on the homepage, When they scroll the page, Then the page should feel responsive and snappy.

## US-003: Refactor checkout (engineering story)

<!-- defect: ac-ambiguous-data-rule -->
AC-003-01: Given the customer enters their email address at checkout, When they submit the form, Then the system processes the email appropriately and stores it as needed. (What format is required, what storage rule applies, what happens for duplicate addresses?)

## US-004: Refunds (role unspecified)

<!-- defect: ac-missing-role-context -->
AC-004-01: Given an active session, When the refund button is clicked on a completed order, Then a refund is issued to the original payment method. (Which role is permitted to click the refund button — customer, store manager, admin? Not specified.)
