import { loadTopics } from "@/lib/data";
import Link from "next/link";

const s = {
  display: "'Playfair Display', Georgia, serif",
  accent: "#2B5C8A",
  muted: "#6B6560",
  light: "#9B9590",
  border: "#E5DFD8",
};

export default async function TopicsPage() {
  const data = await loadTopics();
  const topics = data.topics ?? [];

  return (
    <div>
      <p style={{ marginBottom: 24 }}>
        <Link href="/" style={{ fontSize: 14, color: s.accent, fontWeight: 500 }}>
          ← Back to today&#39;s edition
        </Link>
      </p>

      <h1 style={{ fontFamily: s.display, fontSize: 28, fontWeight: 700, marginBottom: 8 }}>
        Ongoing Situations
      </h1>
      <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.6, marginBottom: 28 }}>
        Major stories tracked with dated, source-linked updates. Click any topic for the full timeline.
      </p>

      <div style={{ display: "grid", gap: 16 }}>
        {topics.map((topic: any) => (
          <Link
            key={topic.slug}
            href={`/topics/${topic.slug}`}
            style={{
              display: "block",
              background: "#FFFFFF",
              border: `1px solid ${s.border}`,
              borderRadius: 8,
              padding: "20px 24px",
              textDecoration: "none",
              color: "inherit",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <h2 style={{ fontFamily: s.display, fontSize: 20, fontWeight: 700, margin: 0 }}>
                {topic.topic}
              </h2>
              <span style={{ fontSize: 11, color: s.accent, fontWeight: 600, whiteSpace: "nowrap" }}>
                {topic.timeline?.length || 0} updates →
              </span>
            </div>
            <p style={{ fontSize: 14, color: s.muted, lineHeight: 1.55, marginTop: 10 }}>
              {topic.summary}
            </p>
            {topic.timeline?.[0] && (
              <p style={{ fontSize: 12, color: s.light, marginTop: 12 }}>
                Latest: {topic.timeline[0].date} — {topic.timeline[0].text.slice(0, 100)}…
              </p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
