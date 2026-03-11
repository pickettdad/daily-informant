import { loadDaily } from "@/lib/data";
import Link from "next/link";

const s = {
  headline: "'Source Serif 4', Georgia, serif",
  body: "'Inter', sans-serif",
  accent: "#1F4E79", accentLight: "#EAF2FB",
  text: "#1F2328", muted: "#6B6A67", light: "#9B9590",
  green: "#2F6E59", greenLight: "#EAF5EF",
  surface: "#FFFDFC",
  border: "#DED8CF", borderLight: "#EDE8E2",
};
const catColors: Record<string, { bg: string; text: string; border: string }> = {
  Local:   { bg: "#FFF3E8", text: "#B85C1F", border: "#F0D8B8" },
  Ontario: { bg: "#F6EEDF", text: "#8B6914", border: "#E8D9B8" },
  Canada:  { bg: "#FDEDF0", text: "#A03F4F", border: "#F0C8CF" },
  US:      { bg: "#EEE8F7", text: "#5A3FA0", border: "#D8CEE8" },
  World:   { bg: "#EAF2FB", text: "#1F4E79", border: "#C8D8E8" },
  Health:  { bg: "#F5EDF7", text: "#6B3FA0", border: "#DCC8E8" },
  Science: { bg: "#EAF5EF", text: "#2F6E59", border: "#C0DCD0" },
  Tech:    { bg: "#EDEFF7", text: "#3F4FA0", border: "#C8CCE0" },
};
function gc(c: string) { return catColors[c] || { bg: "#F0F0F0", text: "#666", border: "#DDD" }; }

export default async function GoodNewsPage() {
  const daily = await loadDaily();
  const goodNews = daily.good_developments || [];
  const editionDate = daily.date
    ? new Date(daily.date + "T12:00:00").toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })
    : "";

  return (
    <div style={{ maxWidth: 960, margin: "0 auto" }}>
      <p style={{ marginBottom: 16 }}>
        <Link href="/" style={{ fontSize: 14, color: s.accent, fontWeight: 500, textDecoration: "none" }}>
          ← Back to today&#39;s edition
        </Link>
      </p>

      <div style={{ marginBottom: 28 }}>
        <h1 style={{
          fontFamily: s.headline, fontSize: 32, fontWeight: 700,
          lineHeight: 1.2, marginBottom: 8, letterSpacing: "-0.01em",
          color: s.green,
        }}>Good News</h1>
        <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.55 }}>
          Positive developments, breakthroughs, and community wins — {editionDate}
        </p>
      </div>

      {goodNews.length > 0 ? (
        <div className="di-story-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
          {goodNews.map((article: any) => {
            const cs = gc(article.category);
            const wordCount = (article.body || "").split(/\s+/).length;
            const readMin = Math.max(1, Math.ceil(wordCount / 200));
            return (
              <Link key={article.slug} href={`/article/${article.slug}`} className="di-card di-card-link" style={{
                padding: "20px 22px", display: "flex", flexDirection: "column",
                borderLeft: `3px solid ${s.green}`,
              }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
                  <span style={{
                    fontSize: 10, fontWeight: 700, background: s.greenLight, color: s.green,
                    padding: "2px 8px", borderRadius: 3, textTransform: "uppercase", letterSpacing: "0.05em",
                  }}>Good News</span>
                  {article.category && (
                    <span style={{
                      fontSize: 10, fontWeight: 700, background: cs.bg, color: cs.text,
                      padding: "2px 8px", borderRadius: 3, textTransform: "uppercase",
                      border: `1px solid ${cs.border}`,
                    }}>{article.category}</span>
                  )}
                  <span style={{ fontSize: 11, color: s.light }}>{readMin} min · {article.component_articles?.length || 1} src</span>
                </div>
                <h3 style={{
                  fontFamily: s.headline, fontSize: 17, fontWeight: 700,
                  lineHeight: 1.3, margin: "0 0 8px 0", color: s.text,
                }}>{article.headline}</h3>
                <p style={{
                  fontSize: 14, color: s.muted, lineHeight: 1.55, margin: 0,
                  display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical" as any, overflow: "hidden",
                  flex: "1 1 auto",
                }}>{article.bottom_line || article.body?.substring(0, 180) || ""}</p>
              </Link>
            );
          })}
        </div>
      ) : (
        <div style={{ padding: "40px 20px", textAlign: "center", color: s.muted }}>
          <p style={{ fontSize: 16 }}>No good news stories in today&#39;s edition yet.</p>
          <p style={{ fontSize: 14, marginTop: 8 }}>Check back tomorrow — the pipeline looks for positive developments from Good News Network, Positive News, and other sources every morning.</p>
        </div>
      )}

      {/* Positive thought at bottom */}
      {daily.optional_reflection && (
        <div style={{
          marginTop: 32, padding: "18px 22px",
          background: "#F6EEDF", borderRadius: 8,
          borderLeft: `3px solid ${s.green}`,
        }}>
          <p style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: s.green, marginBottom: 8, fontFamily: s.body }}>A Thought for the Day</p>
          <p style={{ fontSize: 16, lineHeight: 1.65, color: "#3D5A40", fontStyle: "italic", fontFamily: s.headline, margin: 0 }}>{daily.optional_reflection}</p>
        </div>
      )}
    </div>
  );
}
