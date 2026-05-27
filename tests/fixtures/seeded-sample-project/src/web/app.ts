// knowledge: language-unsupported-in-v1
// This TypeScript file exists to seed the language-unsupported-in-v1 gap
// signal. The Phase 3 /tc:learn-from-code helper parses Python only in v1;
// non-Python files are counted and reported as gaps rather than silently
// ignored.

export interface Session {
  id: string;
  accountId: string;
  expiresAt: string;
}

export function isExpired(session: Session, now: Date): boolean {
  return new Date(session.expiresAt) <= now;
}
