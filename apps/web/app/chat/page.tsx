"use client";

import { useState } from "react";
import Nav from "../../components/Nav";
import { API_BASE } from "../../lib/api";

type Proposal = { command: string; rationale: string; executed: boolean } | null;
type ChatResponse = { kind: string; answer: string; proposal: Proposal; executed: boolean };

export default function Chat() {
  const [question, setQuestion] = useState("");
  const [resp, setResp] = useState<ChatResponse | null>(null);

  async function ask() {
    const r = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    setResp((await r.json()) as ChatResponse);
  }

  return (
    <>
      <Nav />
      <section>
        <h1>Chat</h1>
        <p>
          Read-only Q&amp;A over the workspace. The chat answers from indexed
          artifacts and suggests commands as proposal cards — it never runs a
          command or changes the workspace.
        </p>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about requirements, runs, failures, risks…"
          aria-label="question"
        />
        <button onClick={ask}>Ask</button>
        {resp && (
          <div>
            <p>{resp.answer}</p>
            {resp.proposal && (
              <aside aria-label="proposal">
                <strong>Proposed command:</strong> <code>{resp.proposal.command}</code>
                <p>{resp.proposal.rationale}</p>
                <small>Review and run it yourself — the console never executes.</small>
              </aside>
            )}
          </div>
        )}
      </section>
    </>
  );
}
