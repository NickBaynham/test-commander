import { defineConfig } from "@playwright/test";

// End-to-end smoke lane for the running console. Drives the stack brought up by
// `make run` (api on 8100, web on 3100). Runs via `npm run e2e` / `make web-e2e`
// — Node + browsers, not part of the repo's `make verify`.
export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: process.env.TC_WEB_BASE ?? "http://localhost:3100",
  },
});
