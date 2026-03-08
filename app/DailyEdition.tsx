"use client";

import { useState } from "react";
import Link from "next/link";

const s = {
  display: "'Playfair Display', Georgia, serif",
  body: "'Source Sans 3', sans-serif",
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
  bg: "#FAF8F5",
};

const categoryColors: Record<string, { bg: string; text: string }> = {
  Local:    { bg: "#FFF3E8", text: "#B85C1F" },
  Ontario:  { bg: "#FDEDF0", text: "#A03F4F" },
  Canada:   { bg: "#FDEDF0", text: "#A03F4F" },
  US:       { bg: "#EEE8F7", text: "#5A3FA0" },
  World:    { bg: "#E8F0F7", text: "#2B5C8A" },
  Health:   { bg: "#F5EDF7", text: "#6B3FA0" },
  Science:  { bg: "#EDF7F2", text: "#2D7D5F" },
  Tech:     { bg: "#EDEFF7", text: "#3F4FA0" },
  Business: { bg: "#FDF6EC", text: "#8B6914" },
};

const CATEGORY_ORDER = ["Local", "Ontario", "Canada", "US", "World", "Health", "Science", "Tech", "Business"];

function getCatStyle(cat: string) {
  return categoryColors[cat] || { bg: "#F0F0F0", text: "#666" };
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr + "T12:00:00");
  return d.toLocaleDateString("en-US", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });
}

function StoryCard({ article }: { article: any }) {
  const catStyle = getCatStyle(article.category);
  const sourceCount = article.component_articles?.length || article.sources?.length || 1;

  return (
    <Link
      href={`/article/${article.slug}`}
      style={{
        display: "block", background: "#FFFFFF",
        border: `1px solid ${s.border}`, borderRadius: 8,
        padding: "18px 22px", textDecoration: "none", color: "inherit",
        transition: "border-color 0.15s, box-shadow 0.15s",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = s.accent;
        (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 12px rgba(43,92,138,0.08)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = s.border;
        (e.currentTarget as HTMLElement).style.boxShadow = "none";
      }}
    >
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
        <span style={{
          fontSize: 10, fontWeight: 700, letterSpacing: "0.06em",
          textTransform: "uppercase", background: catStyle.bg, color: catStyle.text,
          padding: "2px 7px", borderRadius: 3,
        }}>
          {article.category}
        </span>
        <span style={{ fontSize: 11, color: s.light }}>
          {sourceCount} source{sourceCount !== 1 ? "s" : ""}
        </span>
        {article.related_ongoing && (
          <span style={{ fontSize: 10, color: s.gold, fontWeight: 600 }}>
            ● Ongoing
          </span>
        )}
      </div>

      <h3 style={{
        fontFamily: s.display, fontSize: 17, fontWeight: 700,
        lineHeight: 1.3, margin: "0 0 8px 0",
      }}>
        {article.headline}
      </h3>

      <p style={{
        fontSize: 13, lineHeight: 1.5, color: s.muted,
        display: "-webkit-box", WebkitLineClamp: 3,
        WebkitBoxOrient: "vertical", overflow: "hidden",
        margin: 0,
      }}>
        {article.summary || article.context || ""}
      </p>
    </Link>
  );
}

function GoodNewsCard({ article }: { article: any }) {
  return (
    <Link
      href={`/article/${article.slug}`}
      style={{
        display: "block", background: s.goodLight,
        border: "1px solid #C8E6D8", borderRadius: 8,
        padding: "16px 20px", textDecoration: "none", color: "inherit",
        transition: "border-color 0.15s, box-shadow 0.15s",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = s.good;
        (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 12px rgba(45,125,95,0.1)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "#C8E6D8";
        (e.currentTarget as HTMLElement).style.boxShadow = "none";
      }}
    >
      <h4 style={{
        fontFamily: s.display, fontSize: 15, fontWeight: 700,
        color: s.good, marginBottom: 6,
      }}>
        {article.headline}
      </h4>
      <p style={{
        fontSize: 13, color: "#3D6B55", lineHeight: 1.5,
        display: "-webkit-box", WebkitLineClamp: 3,
        WebkitBoxOrient: "vertical", overflow: "hidden",
      }}>
        {article.summary || article.context || ""}
      </p>
      {article.sources?.length > 0 && (
        <p style={{ fontSize: 11, color: "#5A9A7A", marginTop: 6 }}>
          {article.component_articles?.length || article.sources?.length || 1} source{(article.component_articles?.length || article.sources?.length || 1) !== 1 ? "s" : ""}
        </p>
      )}
    </Link>
  );
}

function OngoingSidebar({ topics }: { topics: any[] }) {
  if (!topics || topics.length === 0) return null;

  return (
    <div>
      <h2 style={{
        fontFamily: s.display, fontSize: 18, fontWeight: 700,
        color: s.accent, marginBottom: 16,
      }}>
        Ongoing Situations
      </h2>
      <div style={{ display: "grid", gap: 10 }}>
        {topics.map((topic: any) => (
          <Link
            key={topic.slug}
            href={`/topics/${topic.slug}`}
            style={{
              display: "block", background: "#FFFFFF",
              border: `1px solid ${s.border}`, borderRadius: 8,
              padding: "14px 16px", textDecoration: "none", color: "inherit",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{
                fontFamily: s.display, fontSize: 14, fontWeight: 700,
                margin: 0, lineHeight: 1.3,
              }}>
                {topic.topic}
              </h3>
              {topic.timeline?.length > 0 && (
                <span style={{ fontSize: 10, color: s.accent, fontWeight: 600, whiteSpace: "nowrap" }}>
                  {topic.timeline.length} →
                </span>
              )}
            </div>
            {topic.timeline?.[0] && (
              <p style={{
                fontSize: 11, color: s.light, marginTop: 6,
                lineHeight: 1.4, display: "-webkit-box",
                WebkitLineClamp: 2, WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}>
                {topic.timeline[0].date}: {topic.timeline[0].text}
              </p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}

export default function DailyEdition({ daily }: { daily: any }) {
  const [activeFilter, setActiveFilter] = useState("All");

  const allCategories = CATEGORY_ORDER.filter(cat =>
    daily.top_stories.some((a: any) => a.category === cat)
  );
  const filterOptions = ["All", ...allCategories];

  const filteredStories = activeFilter === "All"
    ? daily.top_stories
    : daily.top_stories.filter((a: any) => a.category === activeFilter);

  return (
    <div>
      {/* Date banner */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "baseline",
        marginBottom: 20, paddingBottom: 12, borderBottom: `1px solid ${s.borderLight}`,
        flexWrap: "wrap", gap: 8,
      }}>
        <div>
          <p style={{ fontSize: 14, fontWeight: 600, color: s.accent, margin: 0 }}>Morning Edition</p>
          <p style={{ fontSize: 14, color: s.muted, marginTop: 2 }}>{formatDate(daily.date)}</p>
        </div>
        <p style={{ fontSize: 11, color: s.light, margin: 0 }}>Updated 6:00 AM EST</p>
      </div>

      {/* Category filter bar */}
      <div style={{
        position: "sticky", top: 56, zIndex: 50, background: s.bg,
        paddingTop: 10, paddingBottom: 10, marginBottom: 16,
        borderBottom: `1px solid ${s.borderLight}`,
      }}>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {filterOptions.map((cat) => {
            const isActive = activeFilter === cat;
            const catStyle = cat === "All" ? { bg: s.accent, text: "#fff" } : getCatStyle(cat);
            return (
              <button key={cat} onClick={() => setActiveFilter(cat)}
                style={{
                  fontSize: 11, fontWeight: 600, letterSpacing: "0.04em",
                  textTransform: "uppercase", padding: "4px 12px",
                  borderRadius: 16, cursor: "pointer",
                  border: isActive ? "none" : `1px solid ${s.border}`,
                  background: isActive ? (cat === "All" ? s.accent : catStyle.bg) : "transparent",
                  color: isActive ? (cat === "All" ? "#fff" : catStyle.text) : s.muted,
                  fontFamily: s.body,
                }}
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main layout: sidebar + grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "280px 1fr",
        gap: 24,
        alignItems: "start",
      }}>
        {/* Left sidebar — Ongoing Situations */}
        <aside style={{ position: "sticky", top: 110, maxHeight: "calc(100vh - 130px)", overflowY: "auto" }}>
          <OngoingSidebar topics={daily.ongoing_topics} />

          {/* How it works link */}
          <div style={{ marginTop: 20, paddingTop: 16, borderTop: `1px solid ${s.borderLight}` }}>
            <Link href="/how-it-works" style={{
              fontSize: 12, color: s.light, fontWeight: 500, textDecoration: "none",
            }}>
              How this site works →
            </Link>
          </div>
        </aside>

        {/* Right content — Story grid */}
        <main>
          <h2 style={{
            fontFamily: s.display, fontSize: 20, fontWeight: 700,
            marginBottom: 14,
          }}>
            {activeFilter === "All" ? "Today's Briefing" : activeFilter}
            <span style={{ fontSize: 13, color: s.light, fontWeight: 400, marginLeft: 10 }}>
              {filteredStories.length} article{filteredStories.length !== 1 ? "s" : ""}
            </span>
          </h2>

          {filteredStories.length === 0 ? (
            <p style={{ color: s.muted }}>No articles in this category today.</p>
          ) : (
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, 1fr)",
              gap: 14,
            }}>
              {filteredStories.map((article: any) => (
                <StoryCard key={article.slug} article={article} />
              ))}
            </div>
          )}

          {/* Good Developments — clickable cards */}
          {daily.good_developments?.length > 0 && activeFilter === "All" && (
            <section style={{ marginTop: 40 }}>
              <h2 style={{
                fontFamily: s.display, fontSize: 20, fontWeight: 700,
                color: s.good, marginBottom: 14,
              }}>
                ☀ Good Developments
              </h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 14 }}>
                {daily.good_developments.map((g: any) => (
                  <GoodNewsCard key={g.slug} article={g} />
                ))}
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
