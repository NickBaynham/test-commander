// Read-only API client for the Test Commander web console.
// Every call is a GET (or a proposal POST that returns a card, never executes).

export const API_BASE =
  process.env.NEXT_PUBLIC_TC_API_BASE ?? process.env.TC_API_BASE ?? "http://localhost:8100";

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}
