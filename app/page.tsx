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
};

const categoryColors: Record<string, { bg: string; text: string }> = {
  World:    { bg: "#E8F0F7", text: "#2B5C8A" },
  Business: { bg: "#FDF6EC", text: "#8B6914" },
  Science:  { bg: "#EDF7F2", text: "#2D7D5F" },
  Health:   { bg: "#F5EDF7", text: "#6B3FA0" },
  Tech:     { bg: "#EDEFF7", text: "#3F4FA0" },
  Canada:   { bg: "#FDEDF0", text: "#A03F4F" },
};

function formatDate(dateStr: string) {
  const d = new Date(dateStr + "T12:00:00");
  return d.toLocaleDateString("en-US", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });
}

function getCategoryStyle(category: string) {
  return categoryColors[category] || { bg: "#F0F0F0", text: "#666666" };
}

export default async function HomePage() {
  const daily = await loadDaily();

  return (
    <div>
      {/* Date banner */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "baseline",
        marginBottom: 32, paddingBottom: 16, borderBottom: `1px solid ${s.borderLight}`,
        flexWrap: "wrap", gap: 8,
      }}>
        <div>
          <p style={{ fontSize: 14, fontWeight: 600, color: s.accent }}>Morning Edition</p>
          <p style={{ fontSize: 15, color: s.muted, marginTop: 4 }}>{formatDate(daily.date)}</p>
        </div>
        <p style={{ fontSize: 12, color: s.light }}>Updated 6:00 AM EST</p>
      </div>

      {/* ── Top Stories ── */}
      <section style={{ marginBottom: 48 }}>
        <div style={{ marginBottom: 20 }}>
          <h2 style={{ fontFamily: s.display, fontSize: 24, fontWeight: 700 }}>
            ◆ Today&#39;s Key Facts
          </h2>
          <p style={{ fontSize: 13, color: s.light, marginTop: 4 }}>
            {daily.top_stories.length} stories · Source-linked · No commentary
          </p>
        </div>

        {daily.top_stories.map((story: any) => {
          const catStyle = getCategoryStyle(story.category);
          return (
            <article
              key={story.slug}
              style={{
                background: "#FFFFFF",
                border: `1px solid ${s.border}`,
                borderRadius: 8,
                padding: "24px 28px",
                marginBottom: 16,
              }}
            >
              {/* Category badge + headline */}
              <div style={{ display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 6 }}>
                {story.category && (
                  <span style={{
                    fontSize: 11, fontWeight: 700, letterSpacing: "0.06em",
                    textTransform: "uppercase", background: catStyle.bg, color: catStyle.text,
                    padding: "3px 8px", borderRadius: 4, whiteSpace: "nowrap", marginTop: 4,
                  }}>
                    {story.category}
                  </span>
                )}
                <h3 style={{
                  fontFamily: s.display, fontSize: 20, fontWeight: 700,
                  lineHeight: 1.35, margin: 0,
                }}>
                  {story.headline}
                </h3>
              </div>

              {/* Context paragraph */}
              {story.context && (
                <p style={{
                  fontSize: 14, lineHeight: 1.65, color: s.muted,
                  margin: "8px 0 16px 0",
                  borderLeft: `3px solid ${s.borderLight}`,
                  paddingLeft: 14,
                  fontStyle: "italic",
                }}>
                  {story.context}
                </p>
              )}

              {/* Facts */}
              <ul style={{ listStyleType: "none", padding: 0 }}>
                {story.facts.map((f: any, i: number) => (
                  <li key={i} style={{
                    fontSize: 15, lineHeight: 1.6, color: s.muted,
                    marginBottom: 8, paddingLeft: 16, position: "relative",
                  }}>
                    <span style={{ position: "absolute", left: 0, color: s.gold, fontWeight: 700 }}>·</span>
                    {f.text}{" "}
                    <a href={f.source_url} target="_blank" rel="noreferrer"
                      style={{ fontSize: 11, color: s.accent, opacity: 0.8, textDecoration: "none" }}>
                      source ↗
                    </a>
                  </li>
                ))}
              </ul>

              {/* Sources */}
              <div style={{
                marginTop: 14, display: "flex", alignItems: "center",
                gap: 6, flexWrap: "wrap",
              }}>
                <span style={{
                  fontSize: 11, color: s.light, fontWeight: 600,
                  letterSpacing: "0.05em", textTransform: "uppercase",
                }}>Sources:</span>
                {story.sources.map((src: any, i: number) => (
                  <a key={i} href={src.url} target="_blank" rel="noreferrer"
                    style={{
                      fontSize: 12, color: s.accent, background: s.accentLight,
                      padding: "2px 8px", borderRadius: 4, fontWeight: 500,
                      textDecoration: "none",
                    }}>
                    {src.name}
                  </a>
                ))}
              </div>

              {/* Stakeholder quotes */}
              {story.stakeholder_quotes?.length > 0 && (
                <details style={{ marginTop: 12 }}>
                  <summary style={{
                    cursor: "pointer", fontSize: 13, color: s.accent,
                    fontWeight: 600, letterSpacing: "0.02em",
                  }}>
                    Primary Stakeholder Statements ({story.stakeholder_quotes.length})
                  </summary>
                  <div style={{ marginTop: 10, paddingLeft: 16, borderLeft: `2px solid ${s.borderLight}` }}>
                    {story.stakeholder_quotes.map((q: any, i: number) => (
                      <div key={i} style={{ marginBottom: 10 }}>
                        <span style={{ fontWeight: 600, fontSize: 13 }}>{q.speaker}:</span>
                        <span style={{ fontSize: 13, color: s.muted, fontStyle: "italic", marginLeft: 6 }}>
                          &ldquo;{q.quote}&rdquo;
                        </span>
                        <a href={q.url} target="_blank" rel="noreferrer"
                          style={{ fontSize: 11, color: s.accent, marginLeft: 6, textDecoration: "none" }}>
                          source ↗
                        </a>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </article>
          );
        })}
      </section>

      {/* ── Ongoing Situations ── */}
      {daily.ongoing_topics?.length > 0 && (
        <section style={{ marginBottom: 48 }}>
          <h2 style={{ fontFamily: s.display, fontSize: 24, fontWeight: 700, color: s.accent, marginBottom: 8 }}>
            ◎ Ongoing Situations
          </h2>
          <p style={{ fontSize: 13, color: s.light, marginBottom: 20 }}>
            Where major stories stand today
          </p>
          <div style={{ display: "grid", gap: 12 }}>
            {daily.ongoing_topics.map((topic: any) => (
              <Link key={topic.slug} href={`/topics/${topic.slug}`}
                style={{
                  display: "block", background: "#FFFFFF",
                  border: `1px solid ${s.border}`, borderRadius: 8,
                  padding: "20px 24px", textDecoration: "none", color: "inherit",
                }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <h3 style={{ fontFamily: s.display, fontSize: 18, fontWeight: 700 }}>
                    {topic.topic}
                  </h3>
                  <span style={{ fontSize: 11, color: s.accent, fontWeight: 600, whiteSpace: "nowrap" }}>
                    {topic.timeline?.length || 0} updates →
                  </span>
                </div>
                <p style={{ fontSize: 14, color: s.muted, lineHeight: 1.55, marginTop: 10 }}>
                  {topic.summary}
                </p>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ── Good Developments ── */}
      {daily.good_developments?.length > 0 && (
        <section style={{ marginBottom: 48 }}>
          <h2 style={{ fontFamily: s.display, fontSize: 24, fontWeight: 700, color: s.good, marginBottom: 8 }}>
            ☀ Good Developments
          </h2>
          <p style={{ fontSize: 13, color: s.light, marginBottom: 20 }}>Verified positive updates</p>
          <div style={{ display: "grid", gap: 12 }}>
            {daily.good_developments.map((g: any, i: number) => (
              <div key={i} style={{
                background: s.goodLight, border: "1px solid #C8E6D8",
                borderRadius: 8, padding: "18px 22px",
              }}>
                <h4 style={{ fontFamily: s.display, fontSize: 16, fontWeight: 700, color: s.good, marginBottom: 8 }}>
                  {g.headline}
                </h4>
                {g.facts.map((f: any, j: number) => (
                  <p key={j} style={{ fontSize: 14, color: "#3D6B55", lineHeight: 1.55, marginBottom: 4 }}>
                    {f.text}{" "}
                    <a href={f.source_url} target="_blank" rel="noreferrer"
                      style={{ fontSize: 11, color: s.good, textDecoration: "none" }}>
                      source ↗
                    </a>
                  </p>
                ))}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Reflection ── */}
      {daily.optional_reflection && (
        <section style={{ borderTop: `1px solid ${s.borderLight}`, paddingTop: 24, marginBottom: 40 }}>
          <details>
            <summary style={{
              cursor: "pointer", fontSize: 13, color: s.gold,
              fontWeight: 600, letterSpacing: "0.03em",
            }}>
              Reflection &amp; Prayer (optional)
            </summary>
            <div style={{
              marginTop: 14, padding: "18px 22px", background: s.goldLight,
              borderRadius: 8, border: "1px solid #EDE0C8",
            }}>
              <p style={{
                fontSize: 14, lineHeight: 1.7, color: "#7A6840",
                fontStyle: "italic", fontFamily: s.display,
              }}>
                {daily.optional_reflection}
              </p>
            </div>
          </details>
        </section>
      )}
    </div>
  );
}
