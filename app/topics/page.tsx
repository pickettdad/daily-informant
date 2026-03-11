import { loadTopics, loadDaily } from "@/lib/data";
import Link from "next/link";

const s = {
  headline: "'Source Serif 4', Georgia, serif",
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
  red: "#8B3A3A",
  redLight: "#FDF0F0",
  surface: "#FFFDFC",
  border: "#DED8CF",
  borderLight: "#EDE8E2",
};

const phaseColors: Record<string, { bg: string; text: string }> = {
  escalating: { bg: "#FDF0F0", text: "#8B3A3A" },
  active: { bg: "#FDF0F0", text: "#8B3A3A" },
  stalemate: { bg: "#F6EEDF", text: "#8B6914" },
  stalled: { bg: "#F6EEDF", text: "#8B6914" },
  negotiation: { bg: "#EAF2FB", text: "#1F4E79" },
  recovery: { bg: "#EAF5EF", text: "#2F6E59" },
  "expanded conflict": { bg: "#FDF0F0", text: "#8B3A3A" },
  developing: { bg: "#EAF2FB", text: "#1F4E79" },
  "policy shifts": { bg: "#F6EEDF", text: "#8B6914" },
  "policy shift": { bg: "#F6EEDF", text: "#8B6914" },
  uncertain: { bg: "#F6EEDF", text: "#8B6914" },
  "market pressure": { bg: "#F6EEDF", text: "#8B6914" },
  ceasefire: { bg: "#EAF5EF", text: "#2F6E59" },
};

export default async function TopicsListPage() {
  const topicsData = await loadTopics();
  const daily = await loadDaily();
  const topics = topicsData.topics || [];

  return (
    <div style={{ maxWidth: 960, margin: "0 auto" }}>
      <div style={{ marginBottom: 28 }}>
        <p style={{ marginBottom: 16 }}>
          <Link href="/" style={{ fontSize: 14, color: s.accent, fontWeight: 500, textDecoration: "none" }}>
            ← Back to today&#39;s edition
          </Link>
        </p>
        <h1 style={{
          fontFamily: s.headline, fontSize: 32, fontWeight: 700,
          lineHeight: 1.2, marginBottom: 8, letterSpacing: "-0.01em",
        }}>Ongoing Situations</h1>
        <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.55 }}>
          Major stories tracked over time with timelines, key facts, and daily updates.
        </p>
      </div>

      <div className="di-story-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
        {topics.map((topic: any) => {
          const pc = phaseColors[(topic.phase || "").toLowerCase()] || { bg: "#F0F0F0", text: "#666" };
          const hasUpdates = topic.what_changed_today?.length > 0;
          const linkedCount = [...(daily.top_stories || []), ...(daily.good_developments || [])].filter(
            (a: any) => a.related_ongoing === topic.slug
          ).length;

          return (
            <Link key={topic.slug} href={`/topics/${topic.slug}`} className="di-card di-card-link" style={{
              padding: "20px 24px",
              borderLeft: hasUpdates ? `3px solid ${s.amber}` : undefined,
            }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
                <span style={{
                  fontSize: 10, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase",
                  background: topic.status === "active" ? s.redLight : "#F0F0F0",
                  color: topic.status === "active" ? s.red : s.muted,
                  padding: "2px 8px", borderRadius: 3,
                }}>{topic.status || "Active"}</span>
                <span style={{
                  fontSize: 10, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase",
                  background: pc.bg, color: pc.text, padding: "2px 8px", borderRadius: 3,
                }}>{topic.phase}</span>
                {topic.started && <span style={{ fontSize: 11, color: s.light }}>Since {topic.started}</span>}
                <span style={{ fontSize: 11, color: s.light }}>
                  · {topic.timeline?.length || 0} events
                </span>
              </div>

              <h2 style={{
                fontFamily: s.headline, fontSize: 20, fontWeight: 700,
                lineHeight: 1.25, margin: "0 0 8px 0",
              }}>{topic.topic}</h2>

              <p style={{
                fontSize: 14, color: s.muted, lineHeight: 1.55, margin: 0,
                display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as any, overflow: "hidden",
              }}>{topic.summary}</p>

              {(hasUpdates || linkedCount > 0) && (
                <div style={{ display: "flex", gap: 12, marginTop: 10 }}>
                  {hasUpdates && (
                    <span style={{ fontSize: 11, color: s.amber, fontWeight: 600 }}>
                      ● Updated today
                    </span>
                  )}
                  {linkedCount > 0 && (
                    <span style={{ fontSize: 11, color: s.accent, fontWeight: 500 }}>
                      {linkedCount} article{linkedCount > 1 ? "s" : ""} today
                    </span>
                  )}
                </div>
              )}
            </Link>
          );
        })}
      </div>

      {topics.length === 0 && (
        <p style={{ color: s.muted, padding: 20 }}>No ongoing situations being tracked yet.</p>
      )}
    </div>
  );
}
