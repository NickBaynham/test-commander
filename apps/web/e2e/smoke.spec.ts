import { expect, test } from "@playwright/test";

// Smoke-navigates every console page against a running `make run` stack, then
// exercises the read-only chat and asserts no execution. Run with `make web-e2e`
// after `make run` is up against a populated workspace.

const PAGES = [
  { path: "/", heading: "Quality dashboard" },
  { path: "/quality-report", heading: "Quality report" },
  { path: "/journal", heading: "Journal" },
  { path: "/sessions", heading: "Sessions" },
  { path: "/requirements", heading: "Requirements" },
  { path: "/runs", heading: "Test runs" },
  { path: "/evidence", heading: "Evidence" },
  { path: "/chat", heading: "Chat" },
  { path: "/settings", heading: "Settings" },
];

for (const page of PAGES) {
  test(`navigates ${page.path}`, async ({ page: p }) => {
    await p.goto(page.path);
    await expect(p.getByRole("heading", { level: 1 })).toContainText(page.heading);
  });
}

test("chat answers read-only and proposes, never executes", async ({ page }) => {
  await page.goto("/chat");
  await page.getByLabel("question").fill("generate bdd for sign-in");
  await page.getByRole("button", { name: "Ask" }).click();
  await expect(page.getByText("/tc:generate-bdd")).toBeVisible();
  await expect(page.getByText("never executes")).toBeVisible();
});
