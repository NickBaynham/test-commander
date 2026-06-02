import Link from "next/link";

const LINKS: { href: string; label: string }[] = [
  { href: "/", label: "Dashboard" },
  { href: "/quality-report", label: "Quality Report" },
  { href: "/journal", label: "Journal" },
  { href: "/sessions", label: "Sessions" },
  { href: "/requirements", label: "Requirements" },
  { href: "/runs", label: "Test Runs" },
  { href: "/evidence", label: "Evidence" },
  { href: "/chat", label: "Chat" },
  { href: "/settings", label: "Settings" },
];

export default function Nav() {
  return (
    <nav aria-label="Primary">
      <ul>
        {LINKS.map((l) => (
          <li key={l.href}>
            <Link href={l.href}>{l.label}</Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
