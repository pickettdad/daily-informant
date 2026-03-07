import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "The Daily Informant",
  description: "Facts · Sources · Clarity — A calm, unbiased morning news briefing.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800&family=Source+Sans+3:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <style>{`
          *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
          body {
            font-family: 'Source Sans 3', 'Segoe UI', sans-serif;
            background: #FAF8F5;
            color: #1A1A1A;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
          }
          a { color: #2B5C8A; text-decoration: none; }
          a:hover { text-decoration: underline; }
          ::selection { background: #E8F0F7; color: #2B5C8A; }
          @media (max-width: 768px) {
            .di-layout-grid { grid-template-columns: 1fr !important; }
          }
        `}</style>
      </head>
      <body>
        {/* Site Header */}
        <header style={{
          borderBottom: "1px solid #E5DFD8",
          background: "#FFFFFF",
          position: "sticky",
          top: 0,
          zIndex: 100,
        }}>
          <div style={{
            maxWidth: 1100,
            margin: "0 auto",
            padding: "14px 24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 12,
          }}>
            <a href="/" style={{ textDecoration: "none" }}>
              <h1 style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                fontSize: 24,
                fontWeight: 800,
                color: "#1A1A1A",
                letterSpacing: "-0.02em",
              }}>
                The Daily Informant
              </h1>
              <p style={{
                fontSize: 10,
                color: "#9B9590",
                marginTop: 1,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                fontWeight: 600,
              }}>
                Facts · Sources · Clarity
              </p>
            </a>
            <nav style={{ display: "flex", gap: 18 }}>
              <a href="/" style={{ fontSize: 13, fontWeight: 600, color: "#6B6560" }}>Today</a>
              <a href="/topics" style={{ fontSize: 13, fontWeight: 600, color: "#6B6560" }}>Situations</a>
              <a href="/how-it-works" style={{ fontSize: 13, fontWeight: 600, color: "#6B6560" }}>How It Works</a>
            </nav>
          </div>
        </header>

        {/* Main Content — wider for sidebar layout */}
        <main style={{ maxWidth: 1100, margin: "0 auto", padding: "24px 24px", minHeight: "60vh" }}>
          {children}
        </main>

        {/* Footer */}
        <footer style={{
          borderTop: "1px solid #E5DFD8",
          background: "#FFFFFF",
          padding: 20,
          textAlign: "center",
        }}>
          <p style={{ fontSize: 11, color: "#9B9590", lineHeight: 1.7 }}>
            The Daily Informant · Updated once daily at 6 AM EST · No ads · No sponsors · No paywall
          </p>
          <p style={{ fontSize: 10, color: "#9B9590", marginTop: 3, opacity: 0.7 }}>
            Stories consolidated from multiple sources across the political spectrum via multi-AI consensus · All rights to original sources
          </p>
        </footer>
      </body>
    </html>
  );
}
