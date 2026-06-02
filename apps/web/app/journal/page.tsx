import LiveBadge from "../../components/LiveBadge";
import Nav from "../../components/Nav";
import { getJson } from "../../lib/api";

type Entry = { day: string; timestamp: string; title: string };
export const dynamic = "force-dynamic";

export default async function Journal() {
  const rows = await getJson<Entry[]>("/api/journal");
  return (
    <>
      <Nav />
      <section>
        <h1>Journal <LiveBadge /></h1>
        <ul>
          {rows.map((e, i) => (
            <li key={i}>{e.day} {e.timestamp} — {e.title}</li>
          ))}
        </ul>
      </section>
    </>
  );
}
