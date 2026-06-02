import Nav from "../../components/Nav";
import { getJson } from "../../lib/api";

type QR = { facts: Record<string, string>; source: string };
export const dynamic = "force-dynamic";

export default async function QualityReport() {
  const data = await getJson<QR>("/api/quality-report");
  return (
    <>
      <Nav />
      <section>
        <h1>Quality report</h1>
        <table>
          <tbody>
            {Object.entries(data.facts).map(([k, v]) => (
              <tr key={k}><th>{k}</th><td>{v}</td></tr>
            ))}
          </tbody>
        </table>
        <footer>Source: {data.source}</footer>
      </section>
    </>
  );
}
