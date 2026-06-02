import type { ReactNode } from "react";

export const metadata = {
  title: "Test Commander",
  description: "Read-only quality console over a .test-commander workspace.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header>
          <strong>Test Commander</strong> <span>read-only console</span>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
