import { loadTopics, loadDaily } from "@/lib/data";
import Link from "next/link";

const s = {
  display: "'Playfair Display', Georgia, serif",
  accent: "#2B5C8A", accentLight: "#E8F0F7",
  muted: "#6B6560", light: "#9B9590",
  gold: "#C4985A", goldLight: "#FDF6EC",
  border: "#E5DFD8", borderLight: "#EDE8E2",
  good: "#2D7D5F", goodLight: "#EDF7F2",
  red: "#8B3A3A", redLight: "#FDF0F0",
};

const catColors: Record<string, string> = {
  military: "#8B3A3A", diplomatic: "#2B5C8A", humanitarian: "#C4985A",
  economic: "#5A3FA0", legal: "#2D7D5F", political: "#A03F4F",
  regulatory: "#3F4FA0", environmental: "#2D7D5F",
};

const phaseColors: Record<string, { bg: string; text: string }> = {
  escalating: { bg: "#FDF0F0", text: "#8B3A3A" },
  stalemate: { bg: "#FDF6EC", text: "#8B6914" },
  negotiation: { bg: "#E8F0F7", text: "#2B5C8A" },
  recovery: { bg: "#EDF7F2", text: "#2D7D5F" },
  "expanded conflict": { bg: "#FDF0F0", text: "#8B3A3A" },
  developing: { bg: "#E8F0F7", text: "#2B5C8A" },
  "policy shifts": { bg: "#FDF6EC", text: "#8B6914" },
  uncertain: { bg: "#FDF6EC", text: "#8B6914" },
};

export default async function TopicPage({ params }: any) {
  const { slug } = await params;
  const topicsData = await loadTopics();
  const daily = await loadDaily();
  const topic = topicsData.topics?.find((t: any) => t.slug === slug);

  if (!topic) return (
    <div style={{ padding: 40 }}>
      <h1 style={{ fontFamily: s.display }}>Situation not found</h1>
      <p style={{ marginTop: 12 }}><Link href="/">← Back</Link></p>
    </div>
  );

  const pc = phaseColors[topic.phase] || { bg: "#F0F0F0", text: "#666" };
  const relatedTopics = (topic.related_situations || []).map((rs: string) =>
    topicsData.topics?.find((t: any) => t.slug === rs)
  ).filter(Boolean);
  const linkedArticles = [...(daily.top_stories || []), ...(daily.good_developments || [])].filter(
    (a: any) => a.related_ongoing === slug
  );

  return (
    <div style={{ maxWidth: 760 }}>
      <p style={{ marginBottom: 20 }}>
        <Link href="/" style={{ fontSize: 14, color: s.accent, fontWeight: 500, textDecoration: "none" }}>← Back to today&#39;s edition</Link>
      </p>

      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", background: topic.status === "active" ? s.redLight : "#F0F0F0", color: topic.status === "active" ? s.red : s.muted, padding: "2px 8px", borderRadius: 3 }}>
            {topic.status || "Active"}
          </span>
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", background: pc.bg, color: pc.text, padding: "2px 8px", borderRadius: 3 }}>
            {topic.phase}
          </span>
          {topic.started && <span style={{ fontSize: 11, color: s.light }}>Since {topic.started}</span>}
        </div>
        <h1 style={{ fontFamily: s.display, fontSize: 30, fontWeight: 700, lineHeight: 1.25, marginBottom: 8 }}>{topic.topic}</h1>
        <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.5 }}>{topic.summary}</p>
      </div>

      {/* What Changed Today */}
      {topic.what_changed_today?.length > 0 && (
        <div style={{ background: "#FFFBE6", border: "1px solid #F0E68C", borderRadius: 8, padding: "14px 18px", marginBottom: 20 }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "#8B7D2A", marginBottom: 8 }}>Updated Today</p>
          {topic.what_changed_today.map((change: string, i: number) => (
            <p key={i} style={{ fontSize: 14, color: "#5A5020", margin: "0 0 4px 0", paddingLeft: 14, position: "relative" }}>
              <span style={{ position: "absolute", left: 0, color: "#C4985A", fontWeight: 700 }}>·</span>{change}
            </p>
          ))}
        </div>
      )}

      {/* Catch Me Up */}
      {topic.catch_up_summary && (
        <div style={{ background: s.accentLight, border: `1px solid ${s.accent}33`, borderRadius: 8, padding: "16px 20px", marginBottom: 24 }}>
          <p style={{ fontSize: 12, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.accent, marginBottom: 8 }}>Catch Me Up in 2 Minutes</p>
          <p style={{ fontSize: 15, lineHeight: 1.7, color: "#333", margin: 0 }}>{topic.catch_up_summary}</p>
        </div>
      )}

      {/* Why It Matters + Watchpoints + Uncertainties - 3 column grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 24 }}>
        {topic.why_it_matters?.length > 0 && (
          <div style={{ background: "#fff", border: `1px solid ${s.border}`, borderRadius: 8, padding: "12px 16px" }}>
            <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.gold, marginBottom: 8 }}>Why It Matters</p>
            {topic.why_it_matters.map((item: string, i: number) => (
              <p key={i} style={{ fontSize: 13, color: s.muted, margin: "0 0 6px 0", lineHeight: 1.4 }}>{item}</p>
            ))}
          </div>
        )}
        {topic.watchpoints?.length > 0 && (
          <div style={{ background: "#fff", border: `1px solid ${s.border}`, borderRadius: 8, padding: "12px 16px" }}>
            <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.accent, marginBottom: 8 }}>What to Watch</p>
            {topic.watchpoints.map((item: string, i: number) => (
              <p key={i} style={{ fontSize: 13, color: s.muted, margin: "0 0 6px 0", lineHeight: 1.4 }}>{item}</p>
            ))}
          </div>
        )}
        {topic.uncertainties?.length > 0 && (
          <div style={{ background: "#fff", border: `1px solid ${s.border}`, borderRadius: 8, padding: "12px 16px" }}>
            <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.red, marginBottom: 8 }}>Uncertainties</p>
            {topic.uncertainties.map((item: string, i: number) => (
              <p key={i} style={{ fontSize: 13, color: s.muted, margin: "0 0 6px 0", lineHeight: 1.4 }}>{item}</p>
            ))}
          </div>
        )}
      </div>

      {/* Key Facts */}
      {topic.key_facts && Object.keys(topic.key_facts).length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.light, marginBottom: 10 }}>Key Facts</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {Object.entries(topic.key_facts).map(([k, v]: any) => (
              <div key={k} style={{ background: "#fff", border: `1px solid ${s.border}`, borderRadius: 6, padding: "8px 12px" }}>
                <span style={{ fontSize: 10, fontWeight: 600, color: s.light, textTransform: "uppercase" }}>{k}</span>
                <p style={{ fontSize: 14, fontWeight: 600, color: "#333", margin: "2px 0 0 0" }}>{v}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Parties */}
      {topic.key_parties?.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.light, marginBottom: 10 }}>Key Parties</p>
          <div style={{ display: "grid", gap: 6 }}>
            {topic.key_parties.map((p: any, i: number) => (
              <div key={i} style={{ display: "flex", gap: 10, alignItems: "baseline", padding: "6px 0", borderBottom: i < topic.key_parties.length - 1 ? `1px solid ${s.borderLight}` : "none" }}>
                <span style={{ fontSize: 14, fontWeight: 700, color: "#333", minWidth: 140 }}>{p.name}</span>
                <span style={{ fontSize: 13, color: s.muted }}>{p.role}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Today's Related Articles */}
      {linkedArticles.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.light, marginBottom: 10 }}>Today&#39;s Coverage</p>
          {linkedArticles.map((a: any) => (
            <Link key={a.slug} href={`/article/${a.slug}`} style={{ display: "block", background: s.accentLight, borderRadius: 6, padding: "10px 14px", marginBottom: 6, textDecoration: "none", color: "inherit" }}>
              <p style={{ fontSize: 14, fontWeight: 600, margin: 0, lineHeight: 1.3 }}>{a.headline}</p>
              {a.bottom_line && <p style={{ fontSize: 12, color: s.muted, margin: "4px 0 0 0" }}>{a.bottom_line}</p>}
            </Link>
          ))}
        </div>
      )}

      {/* Timeline */}
      {topic.timeline?.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.light, marginBottom: 14 }}>Timeline ({topic.timeline.length} events)</p>
          <div style={{ borderLeft: `2px solid ${s.border}`, paddingLeft: 20, marginLeft: 8 }}>
            {topic.timeline.map((entry: any, i: number) => {
              const cc = catColors[entry.category] || s.muted;
              return (
                <div key={i} style={{ marginBottom: 16, position: "relative" }}>
                  <div style={{ position: "absolute", left: -27, top: 4, width: 10, height: 10, borderRadius: "50%", background: i === 0 ? s.gold : s.borderLight, border: `2px solid ${i === 0 ? s.gold : s.border}` }} />
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 3 }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: s.gold }}>{entry.date}</span>
                    {entry.category && (
                      <span style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: cc, background: `${cc}15`, padding: "1px 5px", borderRadius: 3 }}>{entry.category}</span>
                    )}
                  </div>
                  <p style={{ fontSize: 14, lineHeight: 1.5, margin: 0, color: "#333" }}>
                    {entry.text}
                    {entry.source_url && (
                      <a href={entry.source_url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: s.accent, marginLeft: 6, textDecoration: "none" }}>source ↗</a>
                    )}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Related Situations */}
      {relatedTopics.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.light, marginBottom: 10 }}>Connected Situations</p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {relatedTopics.map((rt: any) => (
              <Link key={rt.slug} href={`/topics/${rt.slug}`} style={{ fontSize: 13, color: s.accent, background: s.accentLight, padding: "6px 14px", borderRadius: 6, fontWeight: 500, textDecoration: "none" }}>
                {rt.topic} →
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Primary Sources */}
      {topic.primary_sources?.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.light, marginBottom: 10 }}>Primary Sources</p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {topic.primary_sources.map((src: any, i: number) => (
              <a key={i} href={src.url} target="_blank" rel="noreferrer" style={{ fontSize: 13, color: s.accent, background: s.accentLight, padding: "6px 14px", borderRadius: 6, fontWeight: 500, textDecoration: "none" }}>
                {src.name} ↗
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Background */}
      {topic.background && (
        <div style={{ marginBottom: 24 }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: s.light, marginBottom: 8 }}>Background</p>
          <p style={{ fontSize: 14, lineHeight: 1.65, color: s.muted }}>{topic.background}</p>
        </div>
      )}

      {/* Footer */}
      <div style={{ borderTop: `1px solid ${s.borderLight}`, paddingTop: 14, marginTop: 12 }}>
        <p style={{ fontSize: 12, color: s.light, lineHeight: 1.6 }}>
          This situation page is maintained automatically by AI and updated each morning. Timeline entries are append-only — past events are never altered.
          Key facts are updated when verified new data is available. {" "}
          <Link href="/how-it-works" style={{ color: s.accent, textDecoration: "none" }}>Learn how DI works</Link>.
        </p>
      </div>
    </div>
  );
}
