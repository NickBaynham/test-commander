import LiveBadge from "../components/LiveBadge";
import Nav from "../components/Nav";
import { getJson } from "../lib/api";

type Dashboard = {
  requirements: number;
  open_questions: number;
  risks: number;
  latest_run: { run_id: string; passed: number; failed: number; flaky: number } | null;
  source: string[];
};

export const dynamic = "force-dynamic";

export default async function Home() {
  const data = await getJson<Dashboard>("/api/dashboard");
  return (
    <>
      <Nav />
      <section>
        <h1>
          Quality dashboard <LiveBadge />
        </h1>
        <ul>
          <li>Requirements: {data.requirements}</li>
          <li>Open questions: {data.open_questions}</li>
          <li>Risks: {data.risks}</li>
          {data.latest_run && (
            <li>
              Latest run {data.latest_run.run_id}: {data.latest_run.passed} passed,{" "}
              {data.latest_run.failed} failed, {data.latest_run.flaky} flaky
            </li>
          )}
        </ul>
        <footer>Sources: {data.source.join(", ")}</footer>
      </section>
    </>
  );
}
