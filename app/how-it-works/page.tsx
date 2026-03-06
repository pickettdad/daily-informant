import Link from "next/link";

const s = {
  display: "'Playfair Display', Georgia, serif",
  accent: "#2B5C8A",
  muted: "#6B6560",
  light: "#9B9590",
  borderLight: "#EDE8E2",
};

const sections = [
  {
    title: "Mission",
    content:
      "Publish a once-daily morning briefing that is unbiased, fact-focused, non-sensational, source-linked, and designed to help people think clearly — not react emotionally.",
  },
  {
    title: "Facts Only",
    content:
      "Every bullet must include a source link. No adjectives like 'shocking' or 'devastating.' No speculation. No 'experts warn.' Just what happened, what's verified, and what's scheduled next.",
  },
  {
    title: "Politician Filter",
    content:
      "We include policy actions: laws passed, executive orders signed, court rulings, regulatory changes, official reports. We exclude political theater: tweets, insults, cable news reactions, partisan talking points without measurable action.",
  },
  {
    title: "Sources",
    content:
      "We prefer primary documents (official releases, court filings, central bank statements, UN reports) over media commentary. Every story requires at least two credible sources, or one primary document source.",
  },
  {
    title: "Multi-AI Extraction",
    content:
      "Stories are processed by multiple AI systems independently. Only facts that appear across models and include verifiable source links are published. This prevents any single model's bias from influencing the output.",
  },
  {
    title: "Good Developments",
    content:
      "A dedicated section for verified positive news — medical breakthroughs, diplomatic progress, community wins. Same rules: facts only, source-linked, no spin.",
  },
  {
    title: "Ongoing Situations",
    content:
      "Major stories get persistent timeline pages with dated, sourced updates. These become reference pages showing 'where things stand' — not just the latest headline.",
  },
  {
    title: "No Ads. No Outrage.",
    content:
      "No advertisements. No engagement optimization. No comments section. No personalization algorithm. The site updates once per morning and stays calm.",
  },
];

export default function HowItWorksPage() {
  return (
    <div>
      <p style={{ marginBottom: 24 }}>
        <Link href="/" style={{ fontSize: 14, color: s.accent, fontWeight: 500 }}>
          ← Back to today&#39;s edition
        </Link>
      </p>

      <h1 style={{ fontFamily: s.display, fontSize: 32, fontWeight: 700, marginBottom: 8 }}>
        How This Site Works
      </h1>
      <p style={{
        fontSize: 15,
        color: s.muted,
        lineHeight: 1.7,
        maxWidth: 600,
        marginBottom: 32,
      }}>
        Transparency is trust. Here&#39;s exactly how we curate each morning&#39;s edition.
      </p>

      {sections.map((section, i) => (
        <div
          key={i}
          style={{
            marginBottom: 24,
            paddingBottom: 24,
            borderBottom: i < sections.length - 1 ? `1px solid ${s.borderLight}` : "none",
          }}
        >
          <h3 style={{
            fontFamily: s.display,
            fontSize: 18,
            fontWeight: 700,
            marginBottom: 8,
          }}>
            {section.title}
          </h3>
          <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.65 }}>
            {section.content}
          </p>
        </div>
      ))}
    </div>
  );
}
