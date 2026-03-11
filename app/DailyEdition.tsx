"use client";
import { useState } from "react";
import Link from "next/link";

/* ── Design Tokens v2 ── */
const s = {
  headline: "'Source Serif 4', Georgia, serif",
  display: "'Playfair Display', Georgia, serif",
  body: "'Inter', sans-serif",
  accent: "#1F4E79",
  accentLight: "#EAF2FB",
  accentSoft: "#D4E4F4",
  text: "#1F2328",
  muted: "#6B6A67",
  light: "#9B9590",
  amber: "#A96E2E",
  amberLight: "#F6EEDF",
  green: "#2F6E59",
  greenLight: "#EAF5EF",
  red: "#8B3A3A",
  surface: "#FFFDFC",
  bg: "#F6F3EE",
  border: "#DED8CF",
  borderLight: "#EDE8E2",
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
const CATS = ["Local", "Ontario", "Canada", "US", "World", "Health", "Science", "Tech"];
function gc(c: string) { return catColors[c] || { bg: "#F0F0F0", text: "#666", border: "#DDD" }; }
function fmtDate(d: string) { return new Date(d + "T12:00:00").toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" }); }
function readTime(body: string) { return Math.max(1, Math.ceil((body || "").split(/\s+/).length / 200)); }

/* ── Hero Story Card ── */
function HeroStory({ article }: { article: any }) {
  const cs = gc(article.category);
  return (
    <Link href={`/article/${article.slug}`} className="di-card di-card-link di-hero-pad" style={{
      padding: "28px 32px",
      marginBottom: 24,
    }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
        <span style={{
          fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase",
          color: s.surface, background: s.accent, padding: "3px 10px", borderRadius: 3,
        }}>Top Story</span>
        <span style={{
          fontSize: 10, fontWeight: 700, background: cs.bg, color: cs.text,
          padding: "3px 10px", borderRadius: 3, textTransform: "uppercase",
          border: `1px solid ${cs.border}`,
        }}>{article.category}</span>
        <span style={{ fontSize: 12, color: s.light }}>
          {readTime(article.body)} min read · {article.component_articles?.length || 1} sources
        </span>
        {article.related_ongoing && (
          <span style={{ fontSize: 10, color: s.amber, fontWeight: 600 }}>● Ongoing</span>
        )}
      </div>
      <h2 className="di-hero-headline" style={{
        fontFamily: s.headline, fontSize: 28, fontWeight: 700,
        lineHeight: 1.2, margin: "0 0 12px 0", letterSpacing: "-0.01em",
      }}>{article.headline}</h2>
      {article.bottom_line && (
        <p style={{
          fontSize: 15, color: s.accent, fontWeight: 500,
          lineHeight: 1.55, margin: "0 0 12px 0",
          borderLeft: `3px solid ${s.accent}`, paddingLeft: 14,
        }}>{article.bottom_line}</p>
      )}
      <p style={{
        fontSize: 15, lineHeight: 1.65, color: s.muted, margin: 0,
        display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical" as any, overflow: "hidden",
      }}>{article.body || article.summary || ""}</p>
    </Link>
  );
}

/* ── Compact Need to Know ── */
function NeedToKnow({ items }: { items: any[] }) {
  if (!items?.length) return null;
  // Max 4 items, one sentence each
  const display = items.slice(0, 4);
  return (
    <div style={{
      background: s.accentLight, borderRadius: 8,
      padding: "14px 20px", marginBottom: 20,
      borderLeft: `3px solid ${s.accent}`,
    }}>
      <h3 style={{
        fontSize: 11, fontWeight: 700, letterSpacing: "0.1em",
        textTransform: "uppercase", color: s.accent, marginBottom: 10,
        fontFamily: s.body,
      }}>What You Need to Know</h3>
      <ol style={{ listStyleType: "none", padding: 0, margin: 0 }}>
        {display.map((item: any, i: number) => (
          <li key={i} style={{
            fontSize: 14, lineHeight: 1.5, color: s.text,
            padding: "5px 0",
            borderBottom: i < display.length - 1 ? `1px solid ${s.accentSoft}` : "none",
            display: "flex", gap: 10, alignItems: "baseline",
          }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: s.accent, flexShrink: 0, fontFamily: s.body }}>{i + 1}.</span>
            <span style={{
              overflow: "hidden", textOverflow: "ellipsis",
              whiteSpace: "nowrap" as any, display: "block",
            }}>{item.bottom_line || item.headline}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/* ── Story Row ── */
function StoryRow({ article }: { article: any }) {
  const cs = gc(article.category);
  return (
    <Link href={`/article/${article.slug}`} style={{
      display: "block", padding: "16px 0",
      borderBottom: `1px solid ${s.borderLight}`,
      textDecoration: "none", color: "inherit",
    }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
        <span style={{
          fontSize: 10, fontWeight: 700, background: cs.bg, color: cs.text,
          padding: "2px 8px", borderRadius: 3, textTransform: "uppercase",
          letterSpacing: "0.05em", border: `1px solid ${cs.border}`,
        }}>{article.category}</span>
        <span style={{ fontSize: 11, color: s.light }}>
          {readTime(article.body)} min · {article.component_articles?.length || 1} src
        </span>
        {article.related_ongoing && (
          <span style={{ fontSize: 10, color: s.amber, fontWeight: 600 }}>● Ongoing</span>
        )}
      </div>
      <h3 style={{
        fontFamily: s.headline, fontSize: 17, fontWeight: 700,
        lineHeight: 1.3, margin: "0 0 4px 0",
      }}>{article.headline}</h3>
      <p style={{
        fontSize: 14, color: s.muted, lineHeight: 1.5, margin: 0,
        display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as any, overflow: "hidden",
      }}>{article.bottom_line || article.body?.substring(0, 140) || ""}</p>
    </Link>
  );
}

/* ── Good Development Card ── */
function GoodCard({ article }: { article: any }) {
  return (
    <Link href={`/article/${article.slug}`} className="di-card-link" style={{
      display: "block", background: s.greenLight,
      border: `1px solid #C0DCD0`, borderRadius: 8,
      padding: "12px 16px", marginBottom: 8,
      boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
    }}>
      <h4 style={{
        fontFamily: s.headline, fontSize: 14, fontWeight: 700,
        color: s.green, marginBottom: 4, lineHeight: 1.3,
      }}>{article.headline}</h4>
      <p style={{
        fontSize: 13, color: "#3D6B55", lineHeight: 1.45, margin: 0,
        display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as any, overflow: "hidden",
      }}>{article.bottom_line || article.body?.substring(0, 100) || ""}</p>
    </Link>
  );
}

/* ── Sidebar ── */
function Sidebar({ topics, goodDevs }: { topics: any[]; goodDevs: any[] }) {
  return (
    <aside style={{ position: "sticky", top: 110, maxHeight: "calc(100vh - 130px)", overflowY: "auto" }}>
      {/* Ongoing Situations */}
      {topics?.length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <h2 style={{
            fontFamily: s.headline, fontSize: 16, fontWeight: 700,
            color: s.accent, marginBottom: 12, letterSpacing: "-0.01em",
          }}>Ongoing Situations</h2>
          {topics.map((t: any) => {
            const hasUpdates = t.what_changed_today?.length > 0;
            return (
              <Link key={t.slug} href={`/topics/${t.slug}`} className="di-card di-card-link" style={{
                padding: "10px 14px", marginBottom: 8,
                borderLeft: hasUpdates ? `3px solid ${s.amber}` : undefined,
              }}>
                <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 3 }}>
                  <h3 style={{
                    fontFamily: s.headline, fontSize: 13, fontWeight: 700,
                    margin: 0, lineHeight: 1.3, flex: 1,
                  }}>{t.topic}</h3>
                  {t.phase && (
                    <span style={{
                      fontSize: 8, fontWeight: 700, textTransform: "uppercase",
                      letterSpacing: "0.05em", color: s.light,
                      background: s.borderLight, padding: "1px 5px", borderRadius: 3,
                    }}>{t.phase}</span>
                  )}
                </div>
                {hasUpdates && (
                  <p style={{ fontSize: 10, color: s.amber, fontWeight: 600, margin: "3px 0 0 0" }}>
                    ● Updated today
                  </p>
                )}
                {!hasUpdates && t.timeline?.[0] && (
                  <p style={{
                    fontSize: 11, color: s.light, marginTop: 3, lineHeight: 1.3,
                    display: "-webkit-box", WebkitLineClamp: 1, WebkitBoxOrient: "vertical" as any, overflow: "hidden",
                  }}>{t.timeline[0].text}</p>
                )}
              </Link>
            );
          })}
        </div>
      )}

      {/* Constructive Developments */}
      {goodDevs?.length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <h2 style={{
            fontFamily: s.headline, fontSize: 16, fontWeight: 700,
            color: s.green, marginBottom: 12, letterSpacing: "-0.01em",
          }}>Constructive Developments</h2>
          {goodDevs.map((g: any) => <GoodCard key={g.slug} article={g} />)}
        </div>
      )}

      <div style={{ paddingTop: 8, borderTop: `1px solid ${s.borderLight}` }}>
        <Link href="/archive" style={{ fontSize: 12, color: s.light, fontWeight: 500, textDecoration: "none", display: "block", marginBottom: 6 }}>
          Browse past editions →
        </Link>
        <Link href="/how-it-works" style={{ fontSize: 12, color: s.light, fontWeight: 500, textDecoration: "none" }}>
          How The Daily Informant works →
        </Link>
      </div>
    </aside>
  );
}

/* ── Main Edition Component ── */
export default function DailyEdition({ daily }: { daily: any }) {
  const [filter, setFilter] = useState("All");
  const activeCats = CATS.filter(c => daily.top_stories.some((a: any) => a.category === c));
  const stories = filter === "All" ? daily.top_stories : daily.top_stories.filter((a: any) => a.category === filter);
  const hero = stories[0];
  const rest = stories.slice(1);
  const totalMinutes = daily.top_stories.reduce((sum: number, a: any) => sum + readTime(a.body), 0);

  return (
    <div>
      {/* Edition header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "baseline",
        marginBottom: 18, paddingBottom: 12,
        borderBottom: `1px solid ${s.borderLight}`,
        flexWrap: "wrap", gap: 8,
      }}>
        <div>
          <p style={{ fontSize: 14, fontWeight: 600, color: s.accent, margin: 0, fontFamily: s.body }}>
            Morning Edition
          </p>
          <p style={{ fontSize: 14, color: s.muted, marginTop: 3 }}>
            {fmtDate(daily.date)}
          </p>
        </div>
        <p style={{ fontSize: 12, color: s.light, margin: 0 }}>
          Today in {totalMinutes} minutes · {daily.top_stories.length + (daily.good_developments?.length || 0)} articles
        </p>
      </div>

      {/* Category filter pills — horizontal scroll on mobile */}
      <div className="di-pills-scroll" style={{
        display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 22,
      }}>
        {["All", ...activeCats].map(c => {
          const active = filter === c;
          const cs = c === "All" ? { bg: s.accent, text: "#fff", border: s.accent } : gc(c);
          return (
            <button key={c} onClick={() => setFilter(c)} style={{
              fontSize: 11, fontWeight: 600, letterSpacing: "0.04em",
              textTransform: "uppercase" as any,
              padding: "5px 14px", borderRadius: 20, cursor: "pointer",
              border: active ? "none" : `1px solid ${s.border}`,
              background: active ? (c === "All" ? s.accent : cs.bg) : s.surface,
              color: active ? (c === "All" ? "#fff" : cs.text) : s.muted,
              fontFamily: s.body,
              whiteSpace: "nowrap" as any,
              flexShrink: 0,
            }}>
              {c}
            </button>
          );
        })}
      </div>

      {/* Main 2-column grid */}
      <div className="di-layout-grid" style={{
        display: "grid", gridTemplateColumns: "1fr 280px",
        gap: 32, alignItems: "start",
      }}>
        <main>
          {/* Hero story FIRST (before Need to Know) */}
          {hero && filter === "All" && <HeroStory article={hero} />}

          {/* Compact Need to Know strip */}
          {filter === "All" && <NeedToKnow items={daily.need_to_know} />}

          {/* Story list */}
          <div>
            {(filter === "All" ? rest : stories).map((a: any) => (
              <StoryRow key={a.slug} article={a} />
            ))}
          </div>

          {stories.length === 0 && (
            <p style={{ color: s.muted, padding: 20 }}>No articles in this category today.</p>
          )}

          {/* Daily reflection — homepage only, below stories */}
          {filter === "All" && daily.optional_reflection && (
            <div style={{
              marginTop: 32, padding: "18px 22px",
              background: s.amberLight, borderRadius: 8,
              borderLeft: `3px solid ${s.amber}`,
            }}>
              <p style={{
                fontSize: 12, fontWeight: 700, textTransform: "uppercase",
                letterSpacing: "0.08em", color: s.amber, marginBottom: 8,
                fontFamily: s.body,
              }}>A Thought for the Day</p>
              <p style={{
                fontSize: 16, lineHeight: 1.65, color: "#5A4A30",
                fontStyle: "italic", fontFamily: s.headline, margin: 0,
              }}>{daily.optional_reflection}</p>
            </div>
          )}
        </main>

        {/* Sidebar */}
        <Sidebar topics={daily.ongoing_topics} goodDevs={daily.good_developments} />
      </div>
    </div>
  );
}
