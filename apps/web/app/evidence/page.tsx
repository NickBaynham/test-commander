import Nav from "../../components/Nav";
import { getJson } from "../../lib/api";

type Ev = { artifact: string; run_id: string; candidate: string; kind: string };
export const dynamic = "force-dynamic";

export default async function Evidence() {
  const rows = await getJson<Ev[]>("/api/evidence");
  return (
    <>
      <Nav />
      <section>
        <h1>Evidence</h1>
        <ul>
          {rows.map((e) => (
            <li key={e.artifact}>{e.artifact} ({e.kind}, {e.run_id})</li>
          ))}
        </ul>
      </section>
    </>
  );
}
