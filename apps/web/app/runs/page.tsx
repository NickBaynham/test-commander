import Nav from "../../components/Nav";
import { getJson } from "../../lib/api";

type Run = {
  run_id: string; mode: string; generated: string;
  passed: number; failed: number; flaky: number;
};
export const dynamic = "force-dynamic";

export default async function Runs() {
  const rows = await getJson<Run[]>("/api/runs");
  return (
    <>
      <Nav />
      <section>
        <h1>Test runs</h1>
        <ul>
          {rows.map((r) => (
            <li key={r.run_id}>
              {r.run_id}: {r.passed} passed, {r.failed} failed, {r.flaky} flaky
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
