import Nav from "../../components/Nav";
import { getJson } from "../../lib/api";

type Req = { req_id: string; source: string; body: string };
export const dynamic = "force-dynamic";

export default async function Requirements() {
  const rows = await getJson<Req[]>("/api/requirements");
  return (
    <>
      <Nav />
      <section>
        <h1>Requirements</h1>
        <table>
          <thead>
            <tr><th>ID</th><th>Source</th><th>Body</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.req_id}><td>{r.req_id}</td><td>{r.source}</td><td>{r.body}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
