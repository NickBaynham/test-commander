import Nav from "../../components/Nav";
import { API_BASE } from "../../lib/api";

export default function Settings() {
  return (
    <>
      <Nav />
      <section>
        <h1>Settings</h1>
        <p>API base: <code>{API_BASE}</code></p>
        <p>
          The console is read-only and proposal-only. It never changes the
          workspace or runs a command (execution is gated behind Phase 10.5).
        </p>
      </section>
    </>
  );
}
