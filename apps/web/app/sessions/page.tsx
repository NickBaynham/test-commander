import Nav from "../../components/Nav";
import { getJson } from "../../lib/api";

type Session = { session: string; source: string };
export const dynamic = "force-dynamic";

export default async function Sessions() {
  const rows = await getJson<Session[]>("/api/sessions");
  return (
    <>
      <Nav />
      <section>
        <h1>Sessions</h1>
        {rows.length === 0 ? <p>No sessions recorded.</p> : (
          <ul>{rows.map((s) => <li key={s.session}>{s.session}</li>)}</ul>
        )}
      </section>
    </>
  );
}
