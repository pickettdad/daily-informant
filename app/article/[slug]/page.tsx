import { loadDaily } from "@/lib/data";
import Link from "next/link";

const s = {
  display: "'Playfair Display', Georgia, serif",
  accent: "#2B5C8A",
  accentLight: "#E8F0F7",
  muted: "#6B6560",
  light: "#9B9590",
  gold: "#C4985A",
  goldLight: "#FDF6EC",
  border: "#E5DFD8",
  borderLight: "#EDE8E2",
  good: "#2D7D5F",
  goodLight: "#EDF7F2",
  supporting: "#2B6B3D",
  supportingBg: "#EDF7F0",
  opposing: "#8B3A3A",
  opposingBg: "#FDF0F0",
};

const categoryColors: Record<string, { bg: string; text: string }> = {
  Local: { bg: "#FFF3E8", text: "#B85C1F" },
  Ontario: { bg: "#FDEDF0", text: "#A03F4F" },
  Canada: { bg: "#FDEDF0", text: "#A03F4F" },
  US: { bg: "#EEE8F7", text: "#5A3FA0" },
  World: { bg: "#E8F0F7", text: "#2B5C8A" },
  Health: { bg: "#F5EDF7", text: "#6B3FA0" },
  Science: { bg: "#EDF7F2", text: "#2D7D5F" },
  Tech: { bg: "#EDEFF7", text: "#3F4FA0" },
  Business: { bg: "#FDF6EC", text: "#8B6914" },
};

export default async function ArticlePage({ params }: any) {
  const { slug } = await params;
  const daily = await loadDaily();

  let article = daily.top_stories?.find((a: any) => a.slug === slug);
  if (!article) {
    article = daily.good_developments?.find((a: any) => a.slug === slug);
  }

  if (!article) {
    return (
      <div style={{ padding: 40 }}>
        <h1 style={{ fontFamily: s.display }}>Article not found</h1>
        <p style={{ marginTop: 12 }}>
          <Link href="/">← Back to today&#39;s edition</Link>
        </p>
      </div>
    );
  }

  const catStyle = categoryColors[article.category] || { bg: "#F0F0F0", text: "#666" };
  const componentArticles = article.component_articles || [];
  const quotes = article.stakeholder_quotes || [];
  const keyPoints = article.key_points || article.facts || [];

  // Separate news quotes from X quotes
  const newsQuotes = quotes.filter((q: any) => q.source !== "X");
  const xQuotes = quotes.filter((q: any) => q.source === "X");

  return (
    <div style={{ maxWidth: 700 }}>
      <p style={{ marginBottom: 20 }}>
        <Link href="/" style={{ fontSize: 14, color: s.accent, fontWeight: 500, textDecoration: "none" }}>
          ← Back to today&#39;s edition
        </Link>
      </p>

      {/* Category + Ongoing link */}
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
        <span style={{
          fontSize: 11, fontWeight: 700, letterSpacing: "0.06em",
          textTransform: "uppercase", background: catStyle.bg, color: catStyle.text,
          padding: "3px 10px", borderRadius: 4,
        }}>
          {article.category}
        </span>

        {article.related_ongoing && (
          <Link href={`/topics/${article.related_ongoing}`} style={{
            fontSize: 12, color: s.gold, fontWeight: 600, textDecoration: "none",
            background: s.goldLight, padding: "3px 10px", borderRadius: 4,
          }}>
            ● Related Ongoing Situation →
          </Link>
        )}
      </div>

      {/* Headline */}
      <h1 style={{
        fontFamily: s.display, fontSize: 30, fontWeight: 700,
        lineHeight: 1.3, marginBottom: 16,
      }}>
        {article.headline}
      </h1>

      {/* Context / Background */}
      {article.context && (
        <div style={{
          borderLeft: `3px solid ${s.borderLight}`, paddingLeft: 16,
          marginBottom: 24,
        }}>
          <p style={{ fontSize: 14, lineHeight: 1.65, color: s.muted, fontStyle: "italic" }}>
            {article.context}
          </p>
        </div>
      )}

      {/* Full Summary */}
      {article.summary && (
        <section style={{ marginBottom: 28 }}>
          <p style={{ fontSize: 16, lineHeight: 1.75, color: "#333" }}>
            {article.summary}
          </p>
        </section>
      )}

      {/* Key Points */}
      {keyPoints.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 12,
          }}>
            Key Points
          </h2>
          <ul style={{ listStyleType: "none", padding: 0 }}>
            {keyPoints.map((kp: any, i: number) => {
              const text = typeof kp === "string" ? kp : kp.text;
              const url = typeof kp === "object" ? kp.source_url : null;
              return (
                <li key={i} style={{
                  fontSize: 15, lineHeight: 1.6, color: s.muted,
                  marginBottom: 10, paddingLeft: 18, position: "relative",
                }}>
                  <span style={{ position: "absolute", left: 0, color: s.gold, fontWeight: 700 }}>·</span>
                  {text}
                  {url && (
                    <a href={url} target="_blank" rel="noreferrer"
                      style={{ fontSize: 11, color: s.accent, marginLeft: 6, textDecoration: "none" }}>
                      source ↗
                    </a>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      )}

      {/* News Stakeholder Quotes */}
      {newsQuotes.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 12,
          }}>
            Key Statements
          </h2>
          <div style={{ display: "grid", gap: 10 }}>
            {newsQuotes.map((q: any, i: number) => (
              <div key={i} style={{
                background: s.accentLight, borderRadius: 8,
                padding: "14px 18px", borderLeft: `3px solid ${s.accent}`,
              }}>
                <p style={{ fontSize: 14, color: s.accent, fontStyle: "italic", margin: "0 0 6px 0", lineHeight: 1.5 }}>
                  &ldquo;{q.quote}&rdquo;
                </p>
                <p style={{ fontSize: 12, color: s.muted, margin: 0, fontWeight: 600 }}>
                  — {q.speaker}
                  {q.url && (
                    <a href={q.url} target="_blank" rel="noreferrer"
                      style={{ fontSize: 11, color: s.accent, marginLeft: 8, fontWeight: 400, textDecoration: "none" }}>
                      source ↗
                    </a>
                  )}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* X/Twitter Opposing Viewpoints */}
      {xQuotes.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 4,
          }}>
            Voices on 𝕏
          </h2>
          <p style={{ fontSize: 12, color: s.light, marginBottom: 12 }}>
            Public figures weigh in — both sides of the conversation
          </p>
          <div style={{ display: "grid", gap: 10 }}>
            {xQuotes.map((q: any, i: number) => {
              const isSupporting = q.perspective === "supporting";
              const borderColor = isSupporting ? s.supporting : s.opposing;
              const bgColor = isSupporting ? s.supportingBg : s.opposingBg;
              const label = isSupporting ? "Supporting" : "Opposing";
              return (
                <div key={i} style={{
                  background: bgColor, borderRadius: 8,
                  padding: "14px 18px", borderLeft: `3px solid ${borderColor}`,
                }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                    <span style={{
                      fontSize: 10, fontWeight: 700, letterSpacing: "0.06em",
                      textTransform: "uppercase", color: borderColor,
                      background: isSupporting ? "#D4EDDA" : "#F5D5D5",
                      padding: "1px 6px", borderRadius: 3,
                    }}>
                      {label}
                    </span>
                    <span style={{ fontSize: 11, color: s.light }}>via 𝕏</span>
                  </div>
                  <p style={{ fontSize: 14, color: "#333", fontStyle: "italic", margin: "0 0 6px 0", lineHeight: 1.5 }}>
                    &ldquo;{q.quote}&rdquo;
                  </p>
                  <p style={{ fontSize: 12, color: s.muted, margin: 0, fontWeight: 600 }}>
                    — {q.speaker}
                  </p>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Component Articles (sources used) */}
      {componentArticles.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 12,
          }}>
            Articles Used ({componentArticles.length})
          </h2>
          <div style={{ display: "grid", gap: 8 }}>
            {componentArticles.map((ca: any, i: number) => (
              <a key={i} href={ca.url} target="_blank" rel="noreferrer"
                style={{
                  display: "block", background: "#FFFFFF",
                  border: `1px solid ${s.border}`, borderRadius: 6,
                  padding: "10px 14px", textDecoration: "none", color: "inherit",
                }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                  <div style={{ flex: 1 }}>
                    <span style={{
                      fontSize: 10, fontWeight: 600, color: s.light,
                      textTransform: "uppercase", letterSpacing: "0.05em",
                    }}>
                      {ca.source} ({ca.lean})
                    </span>
                    <p style={{ fontSize: 13, margin: "4px 0 0 0", lineHeight: 1.4 }}>
                      {ca.title}
                    </p>
                  </div>
                  <span style={{ fontSize: 11, color: s.accent, flexShrink: 0 }}>↗</span>
                </div>
              </a>
            ))}
          </div>
        </section>
      )}

      {/* Sources summary (fallback if no component articles) */}
      {article.sources?.length > 0 && !componentArticles.length && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 12,
          }}>
            Sources
          </h2>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {article.sources.map((src: any, i: number) => (
              <a key={i} href={src.url} target="_blank" rel="noreferrer"
                style={{
                  fontSize: 13, color: s.accent, background: s.accentLight,
                  padding: "4px 12px", borderRadius: 4, fontWeight: 500, textDecoration: "none",
                }}>
                {src.name} ↗
              </a>
            ))}
          </div>
        </section>
      )}

      {/* Positive Thought (for negative stories) */}
      {article.is_negative && article.positive_thought && (
        <section style={{
          marginBottom: 28, background: s.goldLight,
          border: "1px solid #EDE0C8", borderRadius: 8,
          padding: "16px 20px",
        }}>
          <p style={{
            fontSize: 13, fontWeight: 600, color: s.gold,
            textTransform: "uppercase", letterSpacing: "0.06em",
            marginBottom: 6,
          }}>
            A Positive Thought
          </p>
          <p style={{
            fontSize: 15, lineHeight: 1.65, color: "#7A6840",
            fontStyle: "italic", fontFamily: s.display, margin: 0,
          }}>
            {article.positive_thought}
          </p>
        </section>
      )}

      {/* Footer */}
      <div style={{
        borderTop: `1px solid ${s.borderLight}`, paddingTop: 16,
        marginTop: 12,
      }}>
        <p style={{ fontSize: 12, color: s.light, lineHeight: 1.6 }}>
          This article was generated by AI consensus from multiple news sources across the political spectrum.
          All facts link to original reporting. Read more about{" "}
          <Link href="/how-it-works" style={{ color: s.accent, textDecoration: "none" }}>how this works</Link>.
        </p>
      </div>
    </div>
  );
}
