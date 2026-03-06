import { loadTopics } from "@/lib/data";
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
};

export default async function TopicDetailPage({ params }: any) {
  const { slug } = await params;
  const data = await loadTopics();
  const topic = data.topics.find((t: any) => t.slug === slug);

  if (!topic) {
    return (
      <div style={{ padding: 40 }}>
        <h1 style={{ fontFamily: s.display }}>Topic not found</h1>
        <p style={{ marginTop: 12 }}>
          <Link href="/topics">← Back to all situations</Link>
        </p>
      </div>
    );
  }

  const keyFacts = topic.key_facts || {};
  const keyParties = topic.key_parties || [];
  const hasStats = Object.keys(keyFacts).length > 0;

  return (
    <div>
      <p style={{ marginBottom: 24 }}>
        <Link href="/topics" style={{ fontSize: 14, color: s.accent, fontWeight: 500 }}>
          ← Back to all situations
        </Link>
      </p>

      {/* ── Header ── */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: s.display, fontSize: 32, fontWeight: 700, marginBottom: 8 }}>
          {topic.topic}
        </h1>
        {topic.started && (
          <p style={{ fontSize: 13, color: s.light, marginBottom: 12 }}>
            Since {topic.started}
          </p>
        )}
        <p style={{ fontSize: 16, color: s.muted, lineHeight: 1.65, maxWidth: 650 }}>
          {topic.summary}
        </p>
      </div>

      {/* ── Key Facts Dashboard ── */}
      {hasStats && (
        <section style={{ marginBottom: 40 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 16,
          }}>
            Key Facts &amp; Figures
          </h2>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: 12,
          }}>
            {Object.entries(keyFacts).map(([label, value]: [string, any]) => (
              <div key={label} style={{
                background: "#FFFFFF",
                border: `1px solid ${s.border}`,
                borderRadius: 8,
                padding: "16px 18px",
              }}>
                <div style={{
                  fontSize: 12, fontWeight: 600, color: s.light,
                  textTransform: "uppercase", letterSpacing: "0.05em",
                  marginBottom: 6,
                }}>
                  {label}
                </div>
                <div style={{
                  fontSize: 16, fontWeight: 600, color: s.accent,
                  lineHeight: 1.35,
                }}>
                  {value}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Background ── */}
      {topic.background && (
        <section style={{ marginBottom: 40 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 12,
          }}>
            Background
          </h2>
          <div style={{
            background: "#FFFFFF",
            border: `1px solid ${s.border}`,
            borderRadius: 8,
            padding: "20px 24px",
          }}>
            <p style={{
              fontSize: 15, color: s.muted, lineHeight: 1.7,
              fontFamily: s.display, fontStyle: "italic",
            }}>
              {topic.background}
            </p>
          </div>
        </section>
      )}

      {/* ── Key Parties ── */}
      {keyParties.length > 0 && (
        <section style={{ marginBottom: 40 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 16,
          }}>
            Key Parties Involved
          </h2>
          <div style={{ display: "grid", gap: 8 }}>
            {keyParties.map((party: any, i: number) => (
              <div key={i} style={{
                background: "#FFFFFF",
                border: `1px solid ${s.border}`,
                borderRadius: 8,
                padding: "14px 18px",
                display: "flex",
                gap: 12,
                alignItems: "baseline",
              }}>
                <span style={{
                  fontSize: 14, fontWeight: 700, color: s.accent,
                  minWidth: 120, flexShrink: 0,
                }}>
                  {party.name}
                </span>
                <span style={{ fontSize: 14, color: s.muted, lineHeight: 1.5 }}>
                  {party.role}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Timeline ── */}
      {topic.timeline?.length > 0 && (
        <section style={{ marginBottom: 40 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 20,
          }}>
            Recent Updates
          </h2>
          <div style={{ borderLeft: `2px solid ${s.gold}`, paddingLeft: 20, marginLeft: 8 }}>
            {topic.timeline.map((entry: any, i: number) => (
              <div key={i} style={{ marginBottom: 24, position: "relative" }}>
                <div style={{
                  position: "absolute", left: -27, top: 4,
                  width: 10, height: 10, borderRadius: "50%",
                  background: i === 0 ? s.gold : s.borderLight,
                  border: `2px solid ${i === 0 ? s.gold : s.border}`,
                }} />
                <div style={{
                  fontSize: 12, fontWeight: 700, color: s.gold,
                  letterSpacing: "0.04em", marginBottom: 4,
                }}>
                  {entry.date}
                </div>
                <div style={{ fontSize: 15, lineHeight: 1.55 }}>
                  {entry.text}{" "}
                  <a href={entry.source_url} target="_blank" rel="noreferrer"
                    style={{ fontSize: 11, color: s.accent, textDecoration: "none" }}>
                    source ↗
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {topic.timeline?.length === 0 && (
        <section style={{ marginBottom: 40 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 12,
          }}>
            Recent Updates
          </h2>
          <p style={{ fontSize: 14, color: s.light, fontStyle: "italic" }}>
            Timeline updates will appear here as the pipeline runs each morning.
          </p>
        </section>
      )}

      {/* ── Primary Sources ── */}
      {topic.primary_sources?.length > 0 && (
        <section style={{ marginBottom: 40 }}>
          <h2 style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase", color: s.light, marginBottom: 12,
          }}>
            Primary Sources
          </h2>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {topic.primary_sources.map((src: any, i: number) => (
              <a key={i} href={src.url} target="_blank" rel="noreferrer"
                style={{
                  fontSize: 13, color: s.accent, background: s.accentLight,
                  padding: "6px 14px", borderRadius: 6, fontWeight: 500,
                  textDecoration: "none",
                }}>
                {src.name} ↗
              </a>
            ))}
          </div>
        </section>
      )}

      {/* ── Footer note ── */}
      <div style={{
        borderTop: `1px solid ${s.borderLight}`,
        paddingTop: 16, marginTop: 20,
      }}>
        <p style={{ fontSize: 12, color: s.light, lineHeight: 1.6 }}>
          This page is updated automatically each morning. Timeline entries are added when daily news stories
          match this ongoing situation. Key facts are maintained editorially.
        </p>
      </div>
    </div>
  );
}
