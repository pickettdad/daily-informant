import { loadDaily } from "@/lib/data";
import Link from "next/link";

const s = {
  headline: "'Source Serif 4', Georgia, serif",
  display: "'Playfair Display', Georgia, serif",
  body: "'Inter', sans-serif",
  accent: "#1F4E79",
  accentLight: "#EAF2FB",
  text: "#1F2328",
  muted: "#6B6A67",
  light: "#9B9590",
  amber: "#A96E2E",
  amberLight: "#F6EEDF",
  green: "#2F6E59",
  greenLight: "#EAF5EF",
  surface: "#FFFDFC",
  border: "#DED8CF",
  borderLight: "#EDE8E2",
  supporting: "#2F6E59",
  supportingBg: "#EAF5EF",
  opposing: "#8B3A3A",
  opposingBg: "#FDF0F0",
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

export default async function ArticlePage({ params }: any) {
  const { slug } = await params;
  const daily = await loadDaily();
  let article = daily.top_stories?.find((a: any) => a.slug === slug);
  if (!article) article = daily.good_developments?.find((a: any) => a.slug === slug);

  const editionDate = daily.date
    ? new Date(daily.date + "T12:00:00").toLocaleDateString("en-US", {
        weekday: "long", year: "numeric", month: "long", day: "numeric",
      })
    : "";

  // Build article navigation
  const allStories = [...(daily.top_stories || []), ...(daily.good_developments || [])];
  const currentIdx = allStories.findIndex((a: any) => a.slug === slug);
  const prevArticle = currentIdx > 0 ? allStories[currentIdx - 1] : null;
  const nextArticle = currentIdx < allStories.length - 1 ? allStories[currentIdx + 1] : null;

  if (!article) return (
    <div style={{ padding: 40 }}>
      <h1 style={{ fontFamily: s.headline }}>Article not found</h1>
      <p style={{ marginTop: 12 }}><Link href="/">← Back</Link></p>
    </div>
  );

  const cs = catColors[article.category as string] || { bg: "#F0F0F0", text: "#666", border: "#DDD" };
  const components = article.component_articles || [];
  const keyPoints = article.key_points || article.facts || [];
  const newsQuotes = (article.stakeholder_quotes || []).filter((q: any) => q.source !== "X");
  const xQuotes = (article.stakeholder_quotes || []).filter((q: any) => q.source === "X");
  const wordCount = (article.body || article.summary || "").split(/\s+/).length;
  const readMin = Math.max(1, Math.ceil(wordCount / 200));

  return (
    <div style={{ maxWidth: 720 }}>
      <p style={{ marginBottom: 24 }}>
        <Link href="/" style={{ fontSize: 14, color: s.accent, fontWeight: 500, textDecoration: "none" }}>
          ← Back to today&#39;s edition
        </Link>
      </p>

      {/* ── 1. Category + Date + Read Time ── */}
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 14, flexWrap: "wrap" }}>
        <span style={{
          fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase",
          background: cs.bg, color: cs.text, padding: "3px 10px", borderRadius: 4,
          border: `1px solid ${cs.border}`,
        }}>{article.category}</span>
        <span style={{ fontSize: 13, color: s.light }}>
          {readMin} min read · {components.length || article.sources?.length || 1} sources
        </span>
        {editionDate && <span style={{ fontSize: 13, color: s.light }}>· {editionDate}</span>}
        {article.related_ongoing && (
          <Link href={`/topics/${article.related_ongoing}`} style={{
            fontSize: 12, color: s.amber, fontWeight: 600,
            textDecoration: "none", background: s.amberLight,
            padding: "3px 10px", borderRadius: 4,
          }}>● Ongoing Situation →</Link>
        )}
      </div>

      {/* ── 2. Headline ── */}
      <h1 className="di-h1" style={{
        fontFamily: s.headline, fontSize: 32, fontWeight: 700,
        lineHeight: 1.2, marginBottom: 16, letterSpacing: "-0.01em",
      }}>{article.headline}</h1>

      {/* ── 3. Bottom Line + Key Points (merged) ── */}
      {(article.bottom_line || keyPoints.length > 0) && (
        <div className="di-card di-section-pad" style={{ padding: "18px 22px", marginBottom: 24 }}>
          {article.bottom_line && (
            <p style={{
              fontSize: 15, fontWeight: 500, color: s.accent,
              lineHeight: 1.55, margin: 0,
              paddingBottom: keyPoints.length > 0 ? 12 : 0,
              borderBottom: keyPoints.length > 0 ? `1px solid ${s.borderLight}` : "none",
            }}>{article.bottom_line}</p>
          )}
          {keyPoints.length > 0 && (
            <div style={{ marginTop: article.bottom_line ? 12 : 0 }}>
              {keyPoints.slice(0, 4).map((kp: any, i: number) => (
                <p key={i} style={{
                  fontSize: 14, lineHeight: 1.55, color: s.muted,
                  margin: "0 0 5px 0", paddingLeft: 16, position: "relative",
                }}>
                  <span style={{ position: "absolute", left: 0, color: s.accent, fontWeight: 700, fontSize: 16 }}>·</span>
                  {typeof kp === "string" ? kp : kp.text}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── 4. Full Article Body ── */}
      {(article.body || article.summary) && (
        <section style={{ marginBottom: 28 }}>
          {(article.body || article.summary || "").split("\n\n").map((para: string, i: number) => (
            <p key={i} style={{
              fontSize: 17, lineHeight: 1.8, color: s.text,
              marginBottom: 16, fontFamily: s.headline,
            }}>{para}</p>
          ))}
        </section>
      )}

      {/* ── 5. Why It Matters + What to Watch (combined section) ── */}
      {(article.why_it_matters || article.what_to_watch) && (
        <section style={{
          marginBottom: 28, background: s.accentLight,
          borderRadius: 8, padding: "18px 22px",
          borderLeft: `3px solid ${s.accent}`,
        }}>
          {article.why_it_matters && (
            <div style={{ marginBottom: article.what_to_watch ? 14 : 0 }}>
              <p style={{
                fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
                textTransform: "uppercase", color: s.accent, marginBottom: 6,
                fontFamily: s.body,
              }}>Why It Matters</p>
              <p style={{ fontSize: 15, lineHeight: 1.65, color: s.text, margin: 0 }}>
                {article.why_it_matters}
              </p>
            </div>
          )}
          {article.what_to_watch && (
            <div style={{
              paddingTop: article.why_it_matters ? 14 : 0,
              borderTop: article.why_it_matters ? `1px solid ${s.accentLight}` : "none",
            }}>
              <p style={{
                fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
                textTransform: "uppercase", color: s.accent, marginBottom: 6,
                fontFamily: s.body,
              }}>What to Watch</p>
              <p style={{ fontSize: 14, lineHeight: 1.6, color: s.muted, margin: 0 }}>
                {article.what_to_watch}
              </p>
            </div>
          )}
        </section>
      )}

      {/* ── Key Statements (news quotes) ── */}
      {newsQuotes.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 10,
            fontFamily: s.body,
          }}>Key Statements</p>
          {newsQuotes.map((q: any, i: number) => (
            <div key={i} style={{
              background: s.surface, borderRadius: 8, padding: "12px 16px",
              borderLeft: `3px solid ${s.accent}`, marginBottom: 8,
              border: `1px solid ${s.borderLight}`, borderLeftWidth: 3, borderLeftColor: s.accent,
            }}>
              <p style={{ fontSize: 14, color: s.text, fontStyle: "italic", margin: "0 0 4px 0", lineHeight: 1.55 }}>
                &ldquo;{q.quote}&rdquo;
              </p>
              <p style={{ fontSize: 12, color: s.muted, margin: 0, fontWeight: 600 }}>
                — {q.speaker} {q.source_outlet ? `(${q.source_outlet})` : ""}
              </p>
            </div>
          ))}
        </section>
      )}

      {/* ── Voices on X ── */}
      {xQuotes.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 4,
            fontFamily: s.body,
          }}>Voices on 𝕏</p>
          <p style={{ fontSize: 12, color: s.light, marginBottom: 10 }}>Public figures weigh in — both sides</p>
          {xQuotes.map((q: any, i: number) => {
            const isSup = q.perspective === "supporting";
            return (
              <div key={i} style={{
                background: isSup ? s.supportingBg : s.opposingBg,
                borderRadius: 8, padding: "12px 16px",
                borderLeft: `3px solid ${isSup ? s.supporting : s.opposing}`,
                marginBottom: 8,
              }}>
                <span style={{
                  fontSize: 9, fontWeight: 700, textTransform: "uppercase",
                  color: isSup ? s.supporting : s.opposing,
                  background: isSup ? "#D4EDDA" : "#F5D5D5",
                  padding: "1px 6px", borderRadius: 3,
                }}>{isSup ? "Supporting" : "Opposing"}</span>
                <p style={{ fontSize: 14, color: s.text, fontStyle: "italic", margin: "6px 0 4px 0", lineHeight: 1.55 }}>
                  &ldquo;{q.quote}&rdquo;
                </p>
                <p style={{ fontSize: 12, color: s.muted, margin: 0, fontWeight: 600 }}>— {q.speaker}</p>
              </div>
            );
          })}
        </section>
      )}

      {/* ── 6. Sources — compact ── */}
      {components.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 4,
            fontFamily: s.body,
          }}>How DI Built This Story</p>
          <p style={{ fontSize: 12, color: s.light, marginBottom: 10 }}>
            Synthesized from {components.length} reports across {new Set(components.map((c: any) => c.lean)).size} viewpoints
          </p>
          <div style={{ display: "grid", gap: 4 }}>
            {components.map((ca: any, i: number) => (
              <a key={i} href={ca.url} target="_blank" rel="noreferrer" style={{
                display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8,
                padding: "6px 10px", borderRadius: 6,
                textDecoration: "none", color: "inherit",
                background: s.surface, border: `1px solid ${s.borderLight}`,
                minWidth: 0, maxWidth: "100%",
              }}>
                <div style={{ overflow: "hidden", minWidth: 0, flex: "1 1 0" }}>
                  <span style={{ fontSize: 10, fontWeight: 600, color: s.light, textTransform: "uppercase" }}>
                    {ca.source} ({ca.lean})
                  </span>
                  <p style={{
                    fontSize: 12, margin: "1px 0 0 0", lineHeight: 1.3, color: s.muted,
                    overflow: "hidden", textOverflow: "ellipsis",
                    display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as any,
                  }}>{ca.title}</p>
                </div>
                <span style={{ fontSize: 11, color: s.accent, flexShrink: 0 }}>↗</span>
              </a>
            ))}
          </div>
        </section>
      )}

      {/* ── 7. Positive Thought ── */}
      {article.positive_thought && (
        <section style={{
          marginBottom: 24, background: s.amberLight,
          border: `1px solid #E8D9B8`, borderRadius: 8,
          padding: "16px 20px",
        }}>
          <p style={{
            fontSize: 11, fontWeight: 700, textTransform: "uppercase",
            letterSpacing: "0.08em", color: s.amber, marginBottom: 8,
            fontFamily: s.body,
          }}>A Positive Thought</p>
          <p style={{
            fontSize: 16, lineHeight: 1.65, color: "#5A4A30",
            fontStyle: "italic", fontFamily: "'Source Serif 4', Georgia, serif",
            margin: 0,
          }}>{article.positive_thought}</p>
        </section>
      )}

      {/* ── 8. Disclosure footer ── */}
      <div style={{ borderTop: `1px solid ${s.borderLight}`, paddingTop: 16, marginTop: 16 }}>
        <p style={{ fontSize: 13, color: s.light, lineHeight: 1.65 }}>
          This article was written by AI from structured evidence extracted across multiple sources, then reviewed for bias by independent AI models.{" "}
          <Link href="/how-it-works" style={{ color: s.accent, textDecoration: "none" }}>
            Learn how The Daily Informant works
          </Link>.
        </p>
      </div>

      {/* ── 9. Next / Previous Article Navigation ── */}
      {(prevArticle || nextArticle) && (
        <div style={{
          display: "flex", justifyContent: "space-between", gap: 16,
          marginTop: 24, paddingTop: 20,
          borderTop: `1px solid ${s.borderLight}`,
          flexWrap: "wrap",
        }}>
          {prevArticle ? (
            <Link href={`/article/${prevArticle.slug}`} style={{
              flex: "1 1 45%", textDecoration: "none", color: "inherit",
              padding: "12px 16px", background: s.surface,
              border: `1px solid ${s.borderLight}`, borderRadius: 8,
            }}>
              <span style={{ fontSize: 11, color: s.light, textTransform: "uppercase", letterSpacing: "0.06em" }}>← Previous</span>
              <p style={{ fontSize: 14, fontWeight: 600, color: s.text, margin: "4px 0 0 0", lineHeight: 1.3 }}>{prevArticle.headline}</p>
            </Link>
          ) : <div style={{ flex: "1 1 45%" }} />}
          {nextArticle ? (
            <Link href={`/article/${nextArticle.slug}`} style={{
              flex: "1 1 45%", textDecoration: "none", color: "inherit",
              padding: "12px 16px", background: s.surface,
              border: `1px solid ${s.borderLight}`, borderRadius: 8,
              textAlign: "right",
            }}>
              <span style={{ fontSize: 11, color: s.light, textTransform: "uppercase", letterSpacing: "0.06em" }}>Next →</span>
              <p style={{ fontSize: 14, fontWeight: 600, color: s.text, margin: "4px 0 0 0", lineHeight: 1.3 }}>{nextArticle.headline}</p>
            </Link>
          ) : <div style={{ flex: "1 1 45%" }} />}
        </div>
      )}
    </div>
  );
}
