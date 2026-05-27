# Bookstore Requirements (intentionally flawed)

These requirements describe a fictional online bookstore. Each entry below carries at least one intentional defect, marked with an inline `<!-- defect: <dimension> -->` comment. See `README.md` for the defect-marking convention.

## Functional requirements

<!-- defect: clarity -->
REQ-001: The system shall provide a robust and seamless user experience leveraging modern best-of-breed paradigms.

<!-- defect: testability -->
REQ-002: The site shall be user-friendly.

<!-- defect: completeness -->
REQ-003: The user shall be able to check out.

<!-- defect: consistency -->
REQ-004: Guest users may purchase books without creating an account.

<!-- defect: consistency -->
REQ-005: All purchases require an authenticated user account.

<!-- defect: atomicity -->
REQ-006: The system shall allow users to search the catalog, add items to cart, apply coupons, and complete checkout.

<!-- defect: measurability -->
REQ-007: The catalog search shall return results quickly.

<!-- defect: ac-quality -->
REQ-008: The recommendations engine shall surface relevant titles for each user. See acceptance criteria below (acceptance criteria deliberately omitted to exercise the rubric).

<!-- defect: edge-cases -->
REQ-009: When a user submits an order, the system shall process payment and confirm the order.

<!-- defect: negative-cases -->
REQ-010: Users can apply promo codes at checkout to receive a discount.

<!-- defect: data-rules -->
REQ-011: User passwords are stored by the system.

<!-- defect: roles-permissions -->
REQ-012: Users can issue refunds for completed orders.

<!-- defect: nfrs -->
REQ-013: The system shall be available for use.

<!-- defect: dependencies -->
REQ-014: The order-confirmation email is sent only after REQ-099 (inventory deduction) completes successfully. REQ-099 is referenced but does not exist in this document.

<!-- defect: ambiguity -->
REQ-015: The shopping cart shall persist across sessions for a reasonable time.

<!-- defect: risk -->
REQ-016: The site shall accept and store credit-card primary account numbers directly, without third-party tokenization, to simplify the checkout flow.

<!-- defect: automation-suitability -->
REQ-017: The visual theme of every page shall match the brand style guide and feel inviting to readers. Marked as a candidate for automated regression checks.
