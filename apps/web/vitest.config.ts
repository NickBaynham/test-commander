import { defineConfig } from "vitest/config";

// Component-test lane for the console frontend. Runs via `npm run test`
// (or `make web-test`) — Node-managed, not part of the repo's `make verify`.
export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["components/**/*.test.tsx", "app/**/*.test.tsx"],
  },
});
