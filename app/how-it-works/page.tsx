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
  surface: "#FFFDFC",
  border: "#DED8CF",
  borderLight: "#EDE8E2",
};

export default function HowItWorksPage() {
  return (
    <div style={{ maxWidth: 740, margin: "0 auto" }}>
      <p style={{ marginBottom: 24 }}>
        <Link href="/" style={{ fontSize: 14, color: s.accent, fontWeight: 500, textDecoration: "none" }}>
          ← Back to today&#39;s edition
        </Link>
      </p>

      {/* Hero */}
      <h1 style={{ fontFamily: s.headline, fontSize: 34, fontWeight: 700, lineHeight: 1.2, marginBottom: 16 }}>
        Why The Daily Informant Exists
      </h1>
      <p style={{ fontSize: 18, color: s.text, lineHeight: 1.75, fontFamily: s.headline, marginBottom: 32 }}>
        Modern news media has a problem. It is built on a business model that profits from anxiety, outrage, and division. Headlines are designed to provoke, not inform. Politicians are elevated to celebrity status while the quiet, remarkable things ordinary people do every day go unreported. The worst of humanity is broadcast on repeat. The best of it is buried.
      </p>
      <p style={{ fontSize: 18, color: s.text, lineHeight: 1.75, fontFamily: s.headline, marginBottom: 32 }}>
        Over time, this shapes how we see the world. We begin to believe things are worse than they are. We become suspicious of each other. We consume more news to manage the anxiety that the news itself created.
      </p>
      <p style={{ fontSize: 18, color: s.text, lineHeight: 1.75, fontFamily: s.headline, marginBottom: 40 }}>
        The Daily Informant was built to break that cycle.
      </p>

      {/* What DI Is */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontFamily: s.headline, fontSize: 22, fontWeight: 700, marginBottom: 12 }}>What It Is</h2>
        <p style={{ fontSize: 16, color: s.text, lineHeight: 1.7, marginBottom: 14 }}>
          The Daily Informant is a once-daily morning briefing that delivers the top news stories from local to world level, rewritten to be unbiased, fact-focused, and free of sensationalism. Hard news and positive news are mixed together — not separated into sections — so that your picture of the world stays balanced and honest.
        </p>
        <p style={{ fontSize: 16, color: s.text, lineHeight: 1.7 }}>
          Every article links back to its original sources so you can verify everything yourself. No paywalls, no ads, no algorithms trying to keep you scrolling. Read the morning edition, get informed, and go live your day.
        </p>
      </div>

      {/* How It Works - The Pipeline */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontFamily: s.headline, fontSize: 22, fontWeight: 700, marginBottom: 16 }}>How It Works</h2>

        <div style={{ background: s.surface, border: `1px solid ${s.border}`, borderRadius: 8, padding: "20px 24px", marginBottom: 16 }}>
          <h3 style={{ fontFamily: s.headline, fontSize: 17, fontWeight: 700, color: s.accent, marginBottom: 8 }}>1. Cast a Wide Net</h3>
          <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.65 }}>
            Every morning, the pipeline pulls stories from 35+ news sources spanning the full political and geographic spectrum — from NPR, The Guardian, and PBS on the left, through BBC, Reuters, Al Jazeera, and France 24 in the center, to Fox News, Daily Wire, Breitbart, and the Washington Examiner on the right. Local sources from the Bay of Quinte area, Ontario provincial outlets, and national Canadian papers are included alongside U.S. and world coverage. Positive news sources like Good News Network, Positive News, and Christianity Today are part of the mix from the start.
          </p>
        </div>

        <div style={{ background: s.surface, border: `1px solid ${s.border}`, borderRadius: 8, padding: "20px 24px", marginBottom: 16 }}>
          <h3 style={{ fontFamily: s.headline, fontSize: 17, fontWeight: 700, color: s.accent, marginBottom: 8 }}>2. Group by Story, Not by Source</h3>
          <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.65 }}>
            The pipeline uses semantic analysis to identify which articles from different outlets are actually about the same story. When five different sources cover the same event, they get grouped together. When a single major event dominates the news cycle — like a conflict or economic crisis — all related articles are consolidated into one comprehensive update instead of six repetitive ones. This is reasoning-based, not just keyword matching.
          </p>
        </div>

        <div style={{ background: s.surface, border: `1px solid ${s.border}`, borderRadius: 8, padding: "20px 24px", marginBottom: 16 }}>
          <h3 style={{ fontFamily: s.headline, fontSize: 17, fontWeight: 700, color: s.accent, marginBottom: 8 }}>3. Four AI Models Decide What Matters</h3>
          <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.65 }}>
            The full pool of grouped stories is sent independently to four different AI models — OpenAI GPT-4o, Anthropic Claude, xAI Grok, and Google Gemini. Each model selects the stories it believes are most important for a Canadian morning briefing, without seeing what the others chose. Only stories that two or more models agree on make the final edition. This consensus approach means no single AI&#39;s bias, blind spots, or tendencies control what you read.
          </p>
        </div>

        <div style={{ background: s.surface, border: `1px solid ${s.border}`, borderRadius: 8, padding: "20px 24px", marginBottom: 16 }}>
          <h3 style={{ fontFamily: s.headline, fontSize: 17, fontWeight: 700, color: s.accent, marginBottom: 8 }}>4. Read the Full Sources, Not Just Headlines</h3>
          <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.65 }}>
            After stories are selected, the pipeline fetches the full article text from each source — not just the RSS headline and blurb. This means the AI is writing from real reporting, not summaries of summaries. An evidence brief is built for each story that tracks which facts came from which sources, where outlets agree, where they disagree, and what remains unknown.
          </p>
        </div>

        <div style={{ background: s.surface, border: `1px solid ${s.border}`, borderRadius: 8, padding: "20px 24px", marginBottom: 16 }}>
          <h3 style={{ fontFamily: s.headline, fontSize: 17, fontWeight: 700, color: s.accent, marginBottom: 8 }}>5. Write with Care, Not Templates</h3>
          <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.65 }}>
            Each article is written from its evidence brief with a style adapted to the story type. A local community story sounds warm and specific. A world affairs piece sounds like The Economist. A health story leads with what changed for patients. Cliché openings are explicitly banned. The goal is journalism that sounds human, not generated. Every article includes a quiet, hopeful reflection at the end — a moment of grace to balance whatever weight the news may carry.
          </p>
        </div>

        <div style={{ background: s.surface, border: `1px solid ${s.border}`, borderRadius: 8, padding: "20px 24px", marginBottom: 16 }}>
          <h3 style={{ fontFamily: s.headline, fontSize: 17, fontWeight: 700, color: s.accent, marginBottom: 8 }}>6. Check for Bias — Then Check Again</h3>
          <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.65 }}>
            After all articles are written, they go through two review passes. First, a diversity check reads every article in the edition together and flags repetitive language, similar openings, or overused phrases. Second, independent bias reviewers (Claude, Grok, and Gemini) examine each article for loaded language, missing perspectives, sensationalism, and factual concerns. Corrections are applied as targeted fixes — not wholesale rewrites. The AI models work both together and against each other to catch what any single one might miss.
          </p>
        </div>

        <div style={{ background: s.surface, border: `1px solid ${s.border}`, borderRadius: 8, padding: "20px 24px" }}>
          <h3 style={{ fontFamily: s.headline, fontSize: 17, fontWeight: 700, color: s.accent, marginBottom: 8 }}>7. Publish Once. Stay Calm.</h3>
          <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.65 }}>
            The edition publishes once each morning at 6 AM Eastern. No push notifications, no breaking news alerts, no infinite scroll, no algorithm deciding what to show you next. The same edition is available to everyone. Read it over coffee, catch up on what matters, and move on with your day.
          </p>
        </div>
      </div>

      {/* Ongoing Situations */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontFamily: s.headline, fontSize: 22, fontWeight: 700, marginBottom: 12 }}>Ongoing Situations</h2>
        <p style={{ fontSize: 16, color: s.text, lineHeight: 1.7 }}>
          When a major story unfolds over weeks or months — a conflict, a trade dispute, an economic crisis — The Daily Informant tracks it on a dedicated situation page. These pages include background context, key facts, a timeline of events, and daily updates. They serve as a dashboard: &ldquo;Where does this situation stand today?&rdquo; Timeline entries are append-only — past events are never altered, only new developments are added.
        </p>
      </div>

      {/* The Politician Filter */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontFamily: s.headline, fontSize: 22, fontWeight: 700, marginBottom: 12 }}>The Politician Filter</h2>
        <p style={{ fontSize: 16, color: s.text, lineHeight: 1.7 }}>
          Politicians are public servants, not celebrities. The Daily Informant covers what they do — laws passed, orders signed, policies enacted, court rulings issued. It does not amplify what they say for attention — the tweets, the insults, the cable news theatrics, the partisan posturing designed to generate outrage rather than outcomes. If a politician&#39;s words don&#39;t result in measurable action, they don&#39;t make the edition.
        </p>
      </div>

      {/* What This Is Not */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontFamily: s.headline, fontSize: 22, fontWeight: 700, marginBottom: 12 }}>What This Is Not</h2>
        <p style={{ fontSize: 16, color: s.text, lineHeight: 1.7, marginBottom: 14 }}>
          The Daily Informant is not a news organization. We do not employ reporters. We do not conduct original investigations. We are a curation, consolidation, and summarization layer built on top of the real journalism done by real reporters at real outlets around the world. All credit for the underlying reporting belongs to them, and every article links directly to their work.
        </p>
        <p style={{ fontSize: 16, color: s.text, lineHeight: 1.7 }}>
          AI writes the summaries. AI selects the stories. AI checks for bias. We are transparent about this because transparency is the foundation of trust. The facts and sources are real, verifiable, and linked. The AI is a tool — the editorial principles are human.
        </p>
      </div>

      {/* The Promise */}
      <div style={{
        background: s.amberLight, borderRadius: 8, padding: "24px 28px",
        borderLeft: `3px solid ${s.amber}`, marginBottom: 40,
      }}>
        <h2 style={{ fontFamily: s.headline, fontSize: 22, fontWeight: 700, marginBottom: 12, color: "#5A4A30" }}>The Promise</h2>
        <p style={{ fontSize: 17, color: "#5A4A30", lineHeight: 1.75, fontFamily: s.headline, fontStyle: "italic", margin: 0 }}>
          No ads. No sponsors. No paywall. No outrage optimization. No engagement tricks. No personalization algorithm. No comments section. No push notifications. Just the news — honestly told, properly sourced, and balanced with the good that is happening in the world every single day.
        </p>
      </div>

      {/* Technical transparency */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontFamily: s.headline, fontSize: 22, fontWeight: 700, marginBottom: 12 }}>Under the Hood</h2>
        <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.7, marginBottom: 14 }}>
          For those who want the technical details: The Daily Informant runs on a Python pipeline triggered by GitHub Actions every morning. It fetches RSS feeds from 35+ sources, groups related stories using hybrid semantic analysis (lexical overlap, entity matching, bigram comparison, and union-find clustering), then sends the pool to four AI models for independent selection. Selected stories are enriched with full article text, processed through a two-pass system (evidence extraction → article writing), reviewed for bias by three independent AI models, and published as a static Next.js site on Vercel.
        </p>
        <p style={{ fontSize: 15, color: s.muted, lineHeight: 1.7 }}>
          The entire codebase is open. The pipeline logs are visible. Every editorial decision is made by documented rules, not hidden algorithms.
        </p>
      </div>

      {/* Footer */}
      <div style={{ borderTop: `1px solid ${s.borderLight}`, paddingTop: 16 }}>
        <p style={{ fontSize: 13, color: s.light, lineHeight: 1.65 }}>
          The Daily Informant is a personal project built for family and friends who wanted a calmer, more honest way to stay informed. If it helps you too, that&#39;s the whole point.
        </p>
      </div>
    </div>
  );
}
