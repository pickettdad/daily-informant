import { promises as fs } from "fs";
import path from "path";
import Link from "next/link";

const s = {
  display: "'Playfair Display', Georgia, serif",
  accent: "#2B5C8A", accentLight: "#E8F0F7",
  muted: "#6B6560", light: "#9B9590",
  gold: "#C4985A", border: "#E5DFD8", borderLight: "#EDE8E2",
};

const catColors: Record<string, { bg: string; text: string }> = {
  Local: { bg: "#FFF3E8", text: "#B85C1F" }, Ontario: { bg: "#FDEDF0", text: "#A03F4F" },
  Canada: { bg: "#FDEDF0", text: "#A03F4F" }, US: { bg: "#EEE8F7", text: "#5A3FA0" },
  World: { bg: "#E8F0F7", text: "#2B5C8A" }, Health: { bg: "#F5EDF7", text: "#6B3FA0" },
  Science: { bg: "#EDF7F2", text: "#2D7D5F" }, Tech: { bg: "#EDEFF7", text: "#3F4FA0" },
};

async function loadArchive() {
  const filePath = path.join(process.cwd(), "data", "archive.json");
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch { return []; }
}

export default async function ArchivePage() {
  const archive = await loadArchive();

  // Group by date, most recent first
  const byDate: Record<string, any[]> = {};
  for (const entry of archive) {
    const d = entry.date || "Unknown";
    if (!byDate[d]) byDate[d] = [];
    byDate[d].push(entry);
  }
  const dates = Object.keys(byDate).sort().reverse();

  return (
    <div style={{ maxWidth: 760 }}>
      <p style={{ marginBottom: 20 }}>
        <Link href="/" style={{ fontSize: 14, color: s.accent, fontWeight: 500, textDecoration: "none" }}>
          ← Back to today&#39;s edition
        </Link>
      </p>

      <h1 style={{ fontFamily: s.display, fontSize: 30, fontWeight: 700, marginBottom: 8 }}>
        Archive
      </h1>
      <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.6, marginBottom: 32 }}>
        Past editions of The Daily Informant. Each morning&#39;s stories are preserved here.
      </p>

      {dates.length === 0 && (
        <p style={{ color: s.muted }}>No archived editions yet.</p>
      )}

      {dates.map((date) => {
        const stories = byDate[date];
        const formatted = new Date(date + "T12:00:00").toLocaleDateString("en-US", {
          weekday: "long", year: "numeric", month: "long", day: "numeric",
        });
        return (
          <div key={date} style={{ marginBottom: 28 }}>
            <h2 style={{
              fontFamily: s.display, fontSize: 18, fontWeight: 700,
              color: s.accent, marginBottom: 10,
              paddingBottom: 6, borderBottom: `1px solid ${s.borderLight}`,
            }}>
              {formatted}
            </h2>
            <div>
              {stories.map((story: any, i: number) => {
                const cs = catColors[story.category] || { bg: "#F0F0F0", text: "#666" };
                return (
                  <div key={i} style={{
                    display: "flex", gap: 10, alignItems: "center",
                    padding: "6px 0",
                    borderBottom: i < stories.length - 1 ? `1px solid ${s.borderLight}` : "none",
                  }}>
                    <span style={{
                      fontSize: 9, fontWeight: 700, background: cs.bg, color: cs.text,
                      padding: "1px 6px", borderRadius: 3, textTransform: "uppercase",
                      letterSpacing: "0.05em", flexShrink: 0, minWidth: 50, textAlign: "center",
                    }}>
                      {story.category}
                    </span>
                    <span style={{ fontSize: 14, color: "#333", lineHeight: 1.3 }}>
                      {story.headline}
                    </span>
                    {story.source_count > 1 && (
                      <span style={{ fontSize: 11, color: s.light, flexShrink: 0 }}>
                        {story.source_count} src
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
