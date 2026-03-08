import { loadDaily } from "@/lib/data";
import Link from "next/link";

const s = {
  display: "'Playfair Display', Georgia, serif",
  accent: "#2B5C8A", accentLight: "#E8F0F7",
  muted: "#6B6560", light: "#9B9590",
  gold: "#C4985A", goldLight: "#FDF6EC",
  border: "#E5DFD8", borderLight: "#EDE8E2",
  good: "#2D7D5F", goodLight: "#EDF7F2",
  supporting: "#2B6B3D", supportingBg: "#EDF7F0",
  opposing: "#8B3A3A", opposingBg: "#FDF0F0",
};
const catColors: Record<string,{bg:string;text:string}> = {
  Local:{bg:"#FFF3E8",text:"#B85C1F"}, Ontario:{bg:"#FDEDF0",text:"#A03F4F"},
  Canada:{bg:"#FDEDF0",text:"#A03F4F"}, US:{bg:"#EEE8F7",text:"#5A3FA0"},
  World:{bg:"#E8F0F7",text:"#2B5C8A"}, Health:{bg:"#F5EDF7",text:"#6B3FA0"},
  Science:{bg:"#EDF7F2",text:"#2D7D5F"}, Tech:{bg:"#EDEFF7",text:"#3F4FA0"},
};

export default async function ArticlePage({ params }: any) {
  const { slug } = await params;
  const daily = await loadDaily();
  let article = daily.top_stories?.find((a: any) => a.slug === slug);
  if (!article) article = daily.good_developments?.find((a: any) => a.slug === slug);
  if (!article) return (<div style={{padding:40}}><h1 style={{fontFamily:s.display}}>Article not found</h1><p style={{marginTop:12}}><Link href="/">← Back</Link></p></div>);

  const cs = catColors[article.category as string] || {bg:"#F0F0F0",text:"#666"};
  const components = article.component_articles || [];
  const keyPoints = article.key_points || article.facts || [];
  const newsQuotes = (article.stakeholder_quotes || []).filter((q: any) => q.source !== "X");
  const xQuotes = (article.stakeholder_quotes || []).filter((q: any) => q.source === "X");
  const wordCount = (article.body || article.summary || "").split(/\s+/).length;
  const readMin = Math.max(1, Math.ceil(wordCount / 200));

  return (
    <div style={{ maxWidth:720 }}>
      <p style={{ marginBottom:20 }}><Link href="/" style={{ fontSize:14, color:s.accent, fontWeight:500, textDecoration:"none" }}>← Back to today&#39;s edition</Link></p>

      {/* Meta bar */}
      <div style={{ display:"flex", gap:10, alignItems:"center", marginBottom:12, flexWrap:"wrap" }}>
        <span style={{ fontSize:11, fontWeight:700, letterSpacing:"0.06em", textTransform:"uppercase", background:cs.bg, color:cs.text, padding:"3px 10px", borderRadius:4 }}>{article.category}</span>
        <span style={{ fontSize:12, color:s.light }}>{readMin} min read · {components.length || article.sources?.length || 1} sources</span>
        {article.related_ongoing && (
          <Link href={`/topics/${article.related_ongoing}`} style={{ fontSize:12, color:s.gold, fontWeight:600, textDecoration:"none", background:s.goldLight, padding:"3px 10px", borderRadius:4 }}>● Related Ongoing Situation →</Link>
        )}
      </div>

      {/* Headline */}
      <h1 style={{ fontFamily:s.display, fontSize:30, fontWeight:700, lineHeight:1.25, marginBottom:12 }}>{article.headline}</h1>

      {/* Bottom Line */}
      {article.bottom_line && (
        <div style={{ background:s.accentLight, borderRadius:8, padding:"14px 18px", marginBottom:20, borderLeft:`3px solid ${s.accent}` }}>
          <p style={{ fontSize:11, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", color:s.accent, marginBottom:4 }}>Bottom Line</p>
          <p style={{ fontSize:15, fontWeight:500, color:s.accent, lineHeight:1.5, margin:0 }}>{article.bottom_line}</p>
        </div>
      )}

      {/* At a Glance (key developments as quick bullets) */}
      {keyPoints.length > 0 && (
        <div style={{ background:"#fff", border:`1px solid ${s.border}`, borderRadius:8, padding:"14px 18px", marginBottom:24 }}>
          <p style={{ fontSize:11, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", color:s.light, marginBottom:8 }}>At a Glance</p>
          {keyPoints.slice(0,4).map((kp: any, i: number) => (
            <p key={i} style={{ fontSize:14, lineHeight:1.5, color:s.muted, margin:"0 0 4px 0", paddingLeft:14, position:"relative" }}>
              <span style={{ position:"absolute", left:0, color:s.gold, fontWeight:700 }}>·</span>
              {typeof kp === "string" ? kp : kp.text}
            </p>
          ))}
        </div>
      )}

      {/* Full Article Body */}
      {(article.body || article.summary) && (
        <section style={{ marginBottom:28 }}>
          {(article.body || article.summary || "").split("\n\n").map((para: string, i: number) => (
            <p key={i} style={{ fontSize:16, lineHeight:1.8, color:"#333", marginBottom:14 }}>{para}</p>
          ))}
        </section>
      )}

      {/* Why It Matters */}
      {article.why_it_matters && (
        <section style={{ marginBottom:24, background:"#FFFBF5", border:`1px solid ${s.goldLight}`, borderRadius:8, padding:"14px 18px" }}>
          <p style={{ fontSize:11, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", color:s.gold, marginBottom:6 }}>Why It Matters</p>
          <p style={{ fontSize:15, lineHeight:1.65, color:"#5A4A30", margin:0 }}>{article.why_it_matters}</p>
        </section>
      )}

      {/* What to Watch */}
      {article.what_to_watch && (
        <section style={{ marginBottom:24 }}>
          <p style={{ fontSize:11, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", color:s.light, marginBottom:6 }}>What to Watch</p>
          <p style={{ fontSize:14, lineHeight:1.6, color:s.muted }}>{article.what_to_watch}</p>
        </section>
      )}

      {/* News Quotes */}
      {newsQuotes.length > 0 && (
        <section style={{ marginBottom:24 }}>
          <p style={{ fontSize:11, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", color:s.light, marginBottom:10 }}>Key Statements</p>
          {newsQuotes.map((q: any, i: number) => (
            <div key={i} style={{ background:s.accentLight, borderRadius:8, padding:"12px 16px", borderLeft:`3px solid ${s.accent}`, marginBottom:8 }}>
              <p style={{ fontSize:14, color:s.accent, fontStyle:"italic", margin:"0 0 4px 0", lineHeight:1.5 }}>&ldquo;{q.quote}&rdquo;</p>
              <p style={{ fontSize:12, color:s.muted, margin:0, fontWeight:600 }}>— {q.speaker} {q.source_outlet ? `(${q.source_outlet})` : ""}</p>
            </div>
          ))}
        </section>
      )}

      {/* X Quotes */}
      {xQuotes.length > 0 && (
        <section style={{ marginBottom:24 }}>
          <p style={{ fontSize:11, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", color:s.light, marginBottom:4 }}>Voices on 𝕏</p>
          <p style={{ fontSize:12, color:s.light, marginBottom:10 }}>Public figures weigh in — both sides</p>
          {xQuotes.map((q: any, i: number) => {
            const isSup = q.perspective === "supporting";
            return (
              <div key={i} style={{ background: isSup ? s.supportingBg : s.opposingBg, borderRadius:8, padding:"12px 16px", borderLeft:`3px solid ${isSup ? s.supporting : s.opposing}`, marginBottom:8 }}>
                <span style={{ fontSize:9, fontWeight:700, textTransform:"uppercase", color: isSup ? s.supporting : s.opposing, background: isSup ? "#D4EDDA" : "#F5D5D5", padding:"1px 6px", borderRadius:3 }}>{isSup ? "Supporting" : "Opposing"}</span>
                <p style={{ fontSize:14, color:"#333", fontStyle:"italic", margin:"6px 0 4px 0", lineHeight:1.5 }}>&ldquo;{q.quote}&rdquo;</p>
                <p style={{ fontSize:12, color:s.muted, margin:0, fontWeight:600 }}>— {q.speaker}</p>
              </div>
            );
          })}
        </section>
      )}

      {/* How DI Built This Story */}
      {components.length > 0 && (
        <section style={{ marginBottom:24 }}>
          <p style={{ fontSize:11, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", color:s.light, marginBottom:4 }}>How DI Built This Story</p>
          <p style={{ fontSize:12, color:s.light, marginBottom:10 }}>Synthesized from {components.length} reports across {new Set(components.map((c: any) => c.lean)).size} viewpoints · Reviewed for bias by Claude + Grok</p>
          <div style={{ display:"grid", gap:6 }}>
            {components.map((ca: any, i: number) => (
              <a key={i} href={ca.url} target="_blank" rel="noreferrer" style={{ display:"flex", justifyContent:"space-between", alignItems:"center", gap:8, background:"#fff", border:`1px solid ${s.border}`, borderRadius:6, padding:"8px 12px", textDecoration:"none", color:"inherit" }}>
                <div>
                  <span style={{ fontSize:10, fontWeight:600, color:s.light, textTransform:"uppercase" }}>{ca.source} ({ca.lean})</span>
                  <p style={{ fontSize:12, margin:"2px 0 0 0", lineHeight:1.3, color:s.muted }}>{ca.title}</p>
                </div>
                <span style={{ fontSize:11, color:s.accent, flexShrink:0 }}>↗</span>
              </a>
            ))}
          </div>
        </section>
      )}

      {/* Positive Thought */}
      {article.is_negative && article.positive_thought && (
        <section style={{ marginBottom:24, background:s.goldLight, border:"1px solid #EDE0C8", borderRadius:8, padding:"16px 20px" }}>
          <p style={{ fontSize:12, fontWeight:600, color:s.gold, textTransform:"uppercase", letterSpacing:"0.06em", marginBottom:6 }}>A Positive Thought</p>
          <p style={{ fontSize:15, lineHeight:1.65, color:"#7A6840", fontStyle:"italic", fontFamily:s.display, margin:0 }}>{article.positive_thought}</p>
        </section>
      )}

      {/* Footer */}
      <div style={{ borderTop:`1px solid ${s.borderLight}`, paddingTop:14, marginTop:12 }}>
        <p style={{ fontSize:12, color:s.light, lineHeight:1.6 }}>
          This article was written by AI from structured evidence extracted across multiple sources, then reviewed for bias by independent AI models.{" "}
          <Link href="/how-it-works" style={{ color:s.accent, textDecoration:"none" }}>Learn how The Daily Informant works</Link>.
        </p>
      </div>
    </div>
  );
}
