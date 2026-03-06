import { loadTopics } from "@/lib/data";
import Link from "next/link";

const s = {
  display: "'Playfair Display', Georgia, serif",
  accent: "#2B5C8A",
  muted: "#6B6560",
  light: "#9B9590",
  gold: "#C4985A",
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
        <h1>Topic not found</h1>
        <p style={{ marginTop: 12 }}>
          <Link href="/topics">← Back to all situations</Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <p style={{ marginBottom: 24 }}>
        <Link href="/topics" style={{ fontSize: 14, color: s.accent, fontWeight: 500 }}>
          ← Back to all situations
        </Link>
      </p>

      <h1 style={{ fontFamily: s.display, fontSize: 28, fontWeight: 700, marginBottom: 8 }}>
        {topic.topic}
      </h1>
      <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.6, marginBottom: 28, maxWidth: 600 }}>
        {topic.summary}
      </p>

      {/* Timeline */}
      <h2 style={{
        fontSize: 14,
        fontWeight: 700,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        color: s.light,
        marginBottom: 20,
      }}>
        Timeline of Updates
      </h2>

      <div style={{ borderLeft: `2px solid ${s.gold}`, paddingLeft: 20, marginLeft: 8 }}>
        {topic.timeline.map((entry: any, i: number) => (
          <div key={i} style={{ marginBottom: 24, position: "relative" }}>
            <div style={{
              position: "absolute",
              left: -27,
              top: 4,
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: i === 0 ? s.gold : s.borderLight,
              border: `2px solid ${i === 0 ? s.gold : s.border}`,
            }} />
            <div style={{
              fontSize: 12,
              fontWeight: 700,
              color: s.gold,
              letterSpacing: "0.04em",
              marginBottom: 4,
            }}>
              {entry.date}
            </div>
            <div style={{ fontSize: 15, lineHeight: 1.55 }}>
              {entry.text}{" "}
              <a
                href={entry.source_url}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: 11, color: s.accent }}
              >
                source ↗
              </a>
            </div>
          </div>
        ))}
      </div>

      {/* Primary Sources */}
      {topic.primary_sources?.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h2 style={{
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: s.light,
            marginBottom: 12,
          }}>
            Primary Sources
          </h2>
          <ul style={{ listStyleType: "none", padding: 0 }}>
            {topic.primary_sources.map((src: any, i: number) => (
              <li key={i} style={{ marginBottom: 6 }}>
                <a href={src.url} target="_blank" rel="noreferrer" style={{ fontSize: 14, color: s.accent }}>
                  {src.name} ↗
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
