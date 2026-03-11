import { loadTopics, loadDaily } from "@/lib/data";
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
  red: "#8B3A3A",
  redLight: "#FDF0F0",
  surface: "#FFFDFC",
  border: "#DED8CF",
  borderLight: "#EDE8E2",
};

const catColors: Record<string, string> = {
  military: "#8B3A3A", diplomatic: "#1F4E79", humanitarian: "#A96E2E",
  economic: "#5A3FA0", legal: "#2F6E59", political: "#A03F4F",
  regulatory: "#3F4FA0", environmental: "#2F6E59",
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

export default async function TopicPage({ params }: any) {
  const { slug } = await params;
  const topicsData = await loadTopics();
  const daily = await loadDaily();
  const topic = topicsData.topics?.find((t: any) => t.slug === slug);

  if (!topic) return (
    <div style={{ padding: 40 }}>
      <h1 style={{ fontFamily: s.headline }}>Situation not found</h1>
      <p style={{ marginTop: 12 }}><Link href="/">← Back</Link></p>
    </div>
  );

  const pc = phaseColors[(topic.phase || "").toLowerCase()] || { bg: "#F0F0F0", text: "#666" };
  const relatedTopics = (topic.related_situations || []).map((rs: string) =>
    topicsData.topics?.find((t: any) => t.slug === rs)
  ).filter(Boolean);
  const linkedArticles = [...(daily.top_stories || []), ...(daily.good_developments || [])].filter(
    (a: any) => a.related_ongoing === slug
  );

  return (
    <div style={{ maxWidth: 760 }}>
      <p style={{ marginBottom: 24 }}>
        <Link href="/topics" style={{ fontSize: 14, color: s.accent, fontWeight: 500, textDecoration: "none" }}>
          ← All Ongoing Situations
        </Link>
      </p>

      {/* ── 1. Title + Status + Last Updated ── */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10, flexWrap: "wrap" }}>
          <span style={{
            fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase",
            background: topic.status === "active" ? s.redLight : "#F0F0F0",
            color: topic.status === "active" ? s.red : s.muted,
            padding: "3px 10px", borderRadius: 3,
          }}>{topic.status || "Active"}</span>
          <span style={{
            fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase",
            background: pc.bg, color: pc.text, padding: "3px 10px", borderRadius: 3,
          }}>{topic.phase}</span>
          {topic.started && <span style={{ fontSize: 12, color: s.light }}>Since {topic.started}</span>}
          <span style={{ fontSize: 12, color: s.light }}>
            · {topic.primary_sources?.length || 0} sources
          </span>
        </div>
        <h1 className="di-h1" style={{
          fontFamily: s.headline, fontSize: 32, fontWeight: 700,
          lineHeight: 1.2, marginBottom: 10, letterSpacing: "-0.01em",
        }}>{topic.topic}</h1>
        <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.6 }}>{topic.summary}</p>
      </div>

      {/* ── 2. What Changed Today ── */}
      {topic.what_changed_today?.length > 0 && (
        <div className="di-card" style={{
          padding: "16px 20px", marginBottom: 20,
          borderLeft: `3px solid ${s.amber}`,
        }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.amber, marginBottom: 8,
            fontFamily: s.body,
          }}>What Changed Today</p>
          {topic.what_changed_today.map((change: string, i: number) => (
            <p key={i} style={{
              fontSize: 14, color: s.text, margin: "0 0 5px 0",
              paddingLeft: 14, position: "relative", lineHeight: 1.5,
            }}>
              <span style={{ position: "absolute", left: 0, color: s.amber, fontWeight: 700 }}>·</span>
              {change}
            </p>
          ))}
        </div>
      )}

      {/* ── 3. Catch Me Up ── */}
      {topic.catch_up_summary && (
        <div style={{
          background: s.accentLight, borderRadius: 8,
          padding: "18px 22px", marginBottom: 24,
          borderLeft: `3px solid ${s.accent}`,
        }}>
          <p style={{
            fontSize: 12, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.accent, marginBottom: 8,
            fontFamily: s.body,
          }}>Catch Me Up</p>
          <p style={{
            fontSize: 16, lineHeight: 1.7, color: s.text, margin: 0,
            fontFamily: s.headline,
          }}>{topic.catch_up_summary}</p>
        </div>
      )}

      {/* ── 4. Key Facts grid ── */}
      {topic.key_facts && Object.keys(topic.key_facts).length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 10,
            fontFamily: s.body,
          }}>Key Facts</p>
          <div className="di-2col" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {Object.entries(topic.key_facts).map(([k, v]: any) => (
              <div key={k} className="di-card" style={{ padding: "10px 14px" }}>
                <span style={{
                  fontSize: 10, fontWeight: 600, color: s.light,
                  textTransform: "uppercase", letterSpacing: "0.04em",
                }}>{k}</span>
                <p style={{ fontSize: 14, fontWeight: 600, color: s.text, margin: "3px 0 0 0" }}>{v}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 5. Why / Watch / Uncertainties — 3 columns ── */}
      <div className="di-3col" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 28 }}>
        {topic.why_it_matters?.length > 0 && (
          <div className="di-card" style={{ padding: "14px 16px" }}>
            <p style={{
              fontSize: 10, fontWeight: 700, letterSpacing: "0.08em",
              textTransform: "uppercase", color: s.amber, marginBottom: 8,
              fontFamily: s.body,
            }}>Why It Matters</p>
            {topic.why_it_matters.map((item: string, i: number) => (
              <p key={i} style={{ fontSize: 13, color: s.muted, margin: "0 0 6px 0", lineHeight: 1.45 }}>{item}</p>
            ))}
          </div>
        )}
        {topic.watchpoints?.length > 0 && (
          <div className="di-card" style={{ padding: "14px 16px" }}>
            <p style={{
              fontSize: 10, fontWeight: 700, letterSpacing: "0.08em",
              textTransform: "uppercase", color: s.accent, marginBottom: 8,
              fontFamily: s.body,
            }}>What to Watch</p>
            {topic.watchpoints.map((item: string, i: number) => (
              <p key={i} style={{ fontSize: 13, color: s.muted, margin: "0 0 6px 0", lineHeight: 1.45 }}>{item}</p>
            ))}
          </div>
        )}
        {topic.uncertainties?.length > 0 && (
          <div className="di-card" style={{ padding: "14px 16px" }}>
            <p style={{
              fontSize: 10, fontWeight: 700, letterSpacing: "0.08em",
              textTransform: "uppercase", color: s.red, marginBottom: 8,
              fontFamily: s.body,
            }}>Uncertainties</p>
            {topic.uncertainties.map((item: string, i: number) => (
              <p key={i} style={{ fontSize: 13, color: s.muted, margin: "0 0 6px 0", lineHeight: 1.45 }}>{item}</p>
            ))}
          </div>
        )}
      </div>

      {/* ── Key Parties — compact 2-col ── */}
      {topic.key_parties?.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 10,
            fontFamily: s.body,
          }}>Key Parties</p>
          <div className="di-2col" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
            {topic.key_parties.map((p: any, i: number) => (
              <div key={i} style={{
                display: "flex", gap: 8, alignItems: "baseline",
                padding: "6px 0",
              }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: s.text }}>{p.name}</span>
                <span style={{ fontSize: 12, color: s.muted }}>{p.role}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Today's Related Articles ── */}
      {linkedArticles.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 10,
            fontFamily: s.body,
          }}>Today&#39;s Coverage</p>
          {linkedArticles.map((a: any) => (
            <Link key={a.slug} href={`/article/${a.slug}`} className="di-card di-card-link" style={{
              padding: "10px 14px", marginBottom: 6,
            }}>
              <p style={{ fontSize: 14, fontWeight: 600, margin: 0, lineHeight: 1.3 }}>{a.headline}</p>
              {a.bottom_line && <p style={{ fontSize: 12, color: s.muted, margin: "4px 0 0 0" }}>{a.bottom_line}</p>}
            </Link>
          ))}
        </div>
      )}

      {/* ── Timeline ── */}
      {topic.timeline?.length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 14,
            fontFamily: s.body,
          }}>Timeline ({topic.timeline.length} events)</p>
          <div style={{ borderLeft: `2px solid ${s.border}`, paddingLeft: 22, marginLeft: 8 }}>
            {topic.timeline.map((entry: any, i: number) => {
              const cc = catColors[entry.category] || s.muted;
              return (
                <div key={i} style={{ marginBottom: 18, position: "relative" }}>
                  <div style={{
                    position: "absolute", left: -29, top: 4,
                    width: 10, height: 10, borderRadius: "50%",
                    background: i === 0 ? s.amber : s.borderLight,
                    border: `2px solid ${i === 0 ? s.amber : s.border}`,
                  }} />
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: s.amber }}>{entry.date}</span>
                    {entry.category && (
                      <span style={{
                        fontSize: 9, fontWeight: 700, textTransform: "uppercase",
                        letterSpacing: "0.06em", color: cc,
                        background: `${cc}15`, padding: "1px 6px", borderRadius: 3,
                      }}>{entry.category}</span>
                    )}
                  </div>
                  <p style={{ fontSize: 14, lineHeight: 1.55, margin: 0, color: s.text }}>
                    {entry.text}
                    {entry.source_url && (
                      <a href={entry.source_url} target="_blank" rel="noreferrer" style={{
                        fontSize: 11, color: s.accent, marginLeft: 6, textDecoration: "none",
                      }}>source ↗</a>
                    )}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Related Situations ── */}
      {relatedTopics.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 10,
            fontFamily: s.body,
          }}>Connected Situations</p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {relatedTopics.map((rt: any) => (
              <Link key={rt.slug} href={`/topics/${rt.slug}`} style={{
                fontSize: 13, color: s.accent, background: s.accentLight,
                padding: "6px 14px", borderRadius: 6, fontWeight: 500, textDecoration: "none",
              }}>
                {rt.topic} →
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ── Primary Sources — compact ── */}
      {topic.primary_sources?.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 10,
            fontFamily: s.body,
          }}>Primary Sources</p>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {topic.primary_sources.map((src: any, i: number) => (
              <a key={i} href={src.url} target="_blank" rel="noreferrer" style={{
                fontSize: 12, color: s.accent, background: s.accentLight,
                padding: "5px 12px", borderRadius: 6, fontWeight: 500, textDecoration: "none",
              }}>
                {src.name} ↗
              </a>
            ))}
          </div>
        </div>
      )}

      {/* ── Background (compressed) ── */}
      {topic.background && (
        <div style={{ marginBottom: 24 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 8,
            fontFamily: s.body,
          }}>Background</p>
          <p style={{ fontSize: 14, lineHeight: 1.65, color: s.muted }}>{topic.background}</p>
        </div>
      )}

      {/* ── Footer ── */}
      <div style={{ borderTop: `1px solid ${s.borderLight}`, paddingTop: 16, marginTop: 16 }}>
        <p style={{ fontSize: 13, color: s.light, lineHeight: 1.65 }}>
          This situation page is maintained automatically by AI and updated each morning.
          Timeline entries are append-only — past events are never altered.{" "}
          <Link href="/how-it-works" style={{ color: s.accent, textDecoration: "none" }}>
            Learn how DI works
          </Link>.
        </p>
      </div>
    </div>
  );
}
