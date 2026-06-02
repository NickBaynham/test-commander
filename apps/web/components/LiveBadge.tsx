"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

// Subscribes to the backend SSE stream and reloads the page when the workspace
// changes (a journal append, a new run, etc.). Read-only: it never POSTs.
export default function LiveBadge() {
  const [live, setLive] = useState(false);

  useEffect(() => {
    const source = new EventSource(`${API_BASE}/api/events`);
    source.addEventListener("connected", () => setLive(true));
    source.addEventListener("changed", () => {
      // The workspace changed on disk; refresh the rendered data.
      window.location.reload();
    });
    source.onerror = () => setLive(false);
    return () => source.close();
  }, []);

  return <span aria-live="polite">{live ? "live" : "offline"}</span>;
}
