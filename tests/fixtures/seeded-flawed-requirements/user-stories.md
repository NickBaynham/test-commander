# Bookstore User Stories (intentionally flawed)

These user stories describe behavior for the fictional bookstore product. Each story carries at least one INVEST violation, marked with an inline `<!-- defect: invest-<letter> -->` comment. See `README.md` for the defect-marking convention.

## Stories

<!-- defect: invest-independent -->
US-001: As a returning customer, I want to checkout my cart, So that I can purchase the items I have selected. (Depends on US-002 "Add items to cart" being completed and released first; cannot be developed or shipped independently.)

<!-- defect: invest-negotiable -->
US-002: As a customer, I want a red "Buy now" button at coordinates (240, 480) on the cart page, measuring exactly 120px wide by 36px tall, with Helvetica 14pt bold text, So that I can complete my purchase. No deviation from these specifications is acceptable.

<!-- defect: invest-valuable -->
US-003: As a backend developer, I want to refactor the checkout service into smaller modules, So that the code is cleaner. (No direct user-facing or business-facing value articulated; this is engineering work disguised as a user story.)

<!-- defect: invest-estimable -->
US-004: As a user, I want better search, So that I find what I need.

<!-- defect: invest-small -->
US-005: As a customer, I want to browse, search, filter, sort, view detail pages, add to cart, apply coupons, checkout, manage my account, view order history, leave reviews, manage a wishlist, redeem gift cards, request returns, and contact support, So that I can fully use the bookstore. (Far too large for a single iteration; should be split.)

<!-- defect: invest-testable -->
US-006: As a user, I want the system to feel intuitive and delightful, So that I enjoy using it.
