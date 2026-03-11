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
          href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <style>{`
          *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
          body {
            font-family: 'Inter', 'Source Sans 3', 'Segoe UI', sans-serif;
            background: #F6F3EE;
            color: #1F2328;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
          }
          a { color: #1F4E79; text-decoration: none; }
          a:hover { text-decoration: underline; }
          ::selection { background: #EAF2FB; color: #1F4E79; }
          
          /* Card depth — use class="di-card" on any content card */
          .di-card {
            background: #FFFDFC;
            border: 1px solid #DED8CF;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            transition: box-shadow 0.2s ease;
          }
          .di-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.07); }
          .di-card-link { text-decoration: none !important; color: inherit !important; display: block; }
          
          /* Mobile responsive */
          @media (max-width: 768px) {
            .di-layout-grid { grid-template-columns: 1fr !important; }
            .di-3col { grid-template-columns: 1fr !important; }
            .di-2col { grid-template-columns: 1fr !important; }
            .di-pills-scroll {
              overflow-x: auto;
              white-space: nowrap;
              flex-wrap: nowrap !important;
              -webkit-overflow-scrolling: touch;
              padding-bottom: 4px;
              scrollbar-width: none;
            }
            .di-pills-scroll::-webkit-scrollbar { display: none; }
            .di-hero-pad { padding: 20px 18px !important; }
            .di-section-pad { padding: 16px !important; }
          }
          @media (max-width: 480px) {
            .di-h1 { font-size: 24px !important; }
            .di-hero-headline { font-size: 22px !important; }
          }
        `}</style>
      </head>
      <body>
        {/* Site Header */}
        <header style={{
          borderBottom: "1px solid #DED8CF",
          background: "#FFFDFC",
          position: "sticky",
          top: 0,
          zIndex: 100,
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
        }}>
          <div style={{
            maxWidth: 1100,
            margin: "0 auto",
            padding: "16px 24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 12,
          }}>
            <a href="/" style={{ textDecoration: "none" }}>
              <h1 style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                fontSize: 26,
                fontWeight: 800,
                color: "#1F2328",
                letterSpacing: "-0.02em",
                lineHeight: 1.1,
              }}>
                The Daily Informant
              </h1>
              <p style={{
                fontSize: 10,
                color: "#9B9590",
                marginTop: 2,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                fontWeight: 600,
                fontFamily: "'Inter', sans-serif",
              }}>
                Facts · Sources · Clarity
              </p>
            </a>
            <nav style={{ display: "flex", gap: 20, alignItems: "center" }}>
              {[
                { href: "/", label: "Today" },
                { href: "/topics", label: "Situations" },
                { href: "/archive", label: "Archive" },
                { href: "/how-it-works", label: "How It Works" },
              ].map(link => (
                <a key={link.href} href={link.href} style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: "#6B6A67",
                  textDecoration: "none",
                  padding: "4px 0",
                  letterSpacing: "0.01em",
                }}>
                  {link.label}
                </a>
              ))}
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main style={{ maxWidth: 1100, margin: "0 auto", padding: "28px 24px", minHeight: "60vh" }}>
          {children}
        </main>

        {/* Footer */}
        <footer style={{
          borderTop: "1px solid #DED8CF",
          background: "#FFFDFC",
          padding: "20px 24px",
          textAlign: "center",
        }}>
          <p style={{ fontSize: 12, color: "#9B9590", lineHeight: 1.7, fontFamily: "'Inter', sans-serif" }}>
            The Daily Informant · Updated once daily at 6 AM EST · No ads · No sponsors · No paywall
          </p>
          <p style={{ fontSize: 11, color: "#9B9590", marginTop: 4, opacity: 0.7, fontFamily: "'Inter', sans-serif" }}>
            Stories consolidated from multiple sources via multi-AI consensus · All rights to original sources
          </p>
        </footer>
      </body>
    </html>
  );
}
