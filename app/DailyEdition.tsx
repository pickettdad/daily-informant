"use client";
import { useState } from "react";
import Link from "next/link";

const s = {
  display: "'Playfair Display', Georgia, serif",
  body: "'Source Sans 3', sans-serif",
  accent: "#2B5C8A", accentLight: "#E8F0F7",
  muted: "#6B6560", light: "#9B9590",
  gold: "#C4985A", goldLight: "#FDF6EC",
  border: "#E5DFD8", borderLight: "#EDE8E2",
  good: "#2D7D5F", goodLight: "#EDF7F2", bg: "#FAF8F5",
};
const catColors: Record<string, { bg: string; text: string }> = {
  Local: { bg: "#FFF3E8", text: "#B85C1F" }, Ontario: { bg: "#FDEDF0", text: "#A03F4F" },
  Canada: { bg: "#FDEDF0", text: "#A03F4F" }, US: { bg: "#EEE8F7", text: "#5A3FA0" },
  World: { bg: "#E8F0F7", text: "#2B5C8A" }, Health: { bg: "#F5EDF7", text: "#6B3FA0" },
  Science: { bg: "#EDF7F2", text: "#2D7D5F" }, Tech: { bg: "#EDEFF7", text: "#3F4FA0" },
};
const CATS = ["Local","Ontario","Canada","US","World","Health","Science","Tech"];
function gc(c: string) { return catColors[c] || { bg: "#F0F0F0", text: "#666" }; }
function fmtDate(d: string) { return new Date(d+"T12:00:00").toLocaleDateString("en-US",{weekday:"long",year:"numeric",month:"long",day:"numeric"}); }
function readTime(body: string) { return Math.max(1, Math.ceil((body || "").split(/\s+/).length / 200)); }

function HeroStory({ article }: { article: any }) {
  const cs = gc(article.category);
  return (
    <Link href={`/article/${article.slug}`} style={{ display:"block", background:"#fff", border:`1px solid ${s.border}`, borderRadius:10, padding:"28px 32px", textDecoration:"none", color:"inherit", marginBottom:24 }}>
      <div style={{ display:"flex", gap:10, alignItems:"center", marginBottom:10, flexWrap:"wrap" }}>
        <span style={{ fontSize:10, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", color:s.accent }}>TOP STORY</span>
        <span style={{ fontSize:10, fontWeight:700, background:cs.bg, color:cs.text, padding:"2px 8px", borderRadius:3, textTransform:"uppercase" }}>{article.category}</span>
        <span style={{ fontSize:11, color:s.light }}>{readTime(article.body)} min read · {article.component_articles?.length || 1} sources</span>
        {article.related_ongoing && <span style={{ fontSize:10, color:s.gold, fontWeight:600 }}>● Ongoing</span>}
      </div>
      <h2 style={{ fontFamily:s.display, fontSize:26, fontWeight:700, lineHeight:1.25, margin:"0 0 10px 0" }}>{article.headline}</h2>
      {article.bottom_line && <p style={{ fontSize:15, color:s.accent, fontWeight:500, lineHeight:1.5, margin:"0 0 10px 0" }}>{article.bottom_line}</p>}
      <p style={{ fontSize:14, lineHeight:1.6, color:s.muted, margin:0, display:"-webkit-box", WebkitLineClamp:3, WebkitBoxOrient:"vertical" as any, overflow:"hidden" }}>{article.body || article.summary || ""}</p>
    </Link>
  );
}

function NeedToKnow({ items }: { items: any[] }) {
  if (!items?.length) return null;
  return (
    <div style={{ background:"#fff", border:`1px solid ${s.border}`, borderRadius:10, padding:"20px 24px", marginBottom:24 }}>
      <h3 style={{ fontSize:13, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", color:s.accent, marginBottom:14 }}>What You Need to Know This Morning</h3>
      <ol style={{ listStyleType:"none", padding:0, margin:0, counterReset:"ntk" }}>
        {items.map((item: any, i: number) => (
          <li key={i} style={{ fontSize:14, lineHeight:1.55, color:"#333", padding:"6px 0", borderBottom: i < items.length-1 ? `1px solid ${s.borderLight}` : "none", display:"flex", gap:10, alignItems:"baseline" }}>
            <span style={{ fontSize:12, fontWeight:700, color:s.gold, flexShrink:0 }}>{i+1}.</span>
            <span>{item.bottom_line || item.headline}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function StoryRow({ article }: { article: any }) {
  const cs = gc(article.category);
  return (
    <Link href={`/article/${article.slug}`} style={{ display:"block", padding:"14px 0", borderBottom:`1px solid ${s.borderLight}`, textDecoration:"none", color:"inherit" }}>
      <div style={{ display:"flex", gap:10, alignItems:"center", marginBottom:4 }}>
        <span style={{ fontSize:9, fontWeight:700, background:cs.bg, color:cs.text, padding:"1px 6px", borderRadius:3, textTransform:"uppercase", letterSpacing:"0.05em" }}>{article.category}</span>
        <span style={{ fontSize:11, color:s.light }}>{readTime(article.body)} min · {article.component_articles?.length || 1} src</span>
        {article.related_ongoing && <span style={{ fontSize:9, color:s.gold, fontWeight:600 }}>● Ongoing</span>}
      </div>
      <h3 style={{ fontFamily:s.display, fontSize:16, fontWeight:700, lineHeight:1.3, margin:"0 0 3px 0" }}>{article.headline}</h3>
      <p style={{ fontSize:13, color:s.muted, lineHeight:1.4, margin:0, display:"-webkit-box", WebkitLineClamp:2, WebkitBoxOrient:"vertical" as any, overflow:"hidden" }}>{article.bottom_line || article.body?.substring(0,120) || ""}</p>
    </Link>
  );
}

function GoodCard({ article }: { article: any }) {
  return (
    <Link href={`/article/${article.slug}`} style={{ display:"block", background:s.goodLight, border:"1px solid #C8E6D8", borderRadius:8, padding:"12px 16px", textDecoration:"none", color:"inherit", marginBottom:8 }}>
      <h4 style={{ fontFamily:s.display, fontSize:13, fontWeight:700, color:s.good, marginBottom:4, lineHeight:1.3 }}>{article.headline}</h4>
      <p style={{ fontSize:12, color:"#3D6B55", lineHeight:1.4, margin:0, display:"-webkit-box", WebkitLineClamp:2, WebkitBoxOrient:"vertical" as any, overflow:"hidden" }}>{article.bottom_line || article.body?.substring(0,100) || ""}</p>
    </Link>
  );
}

function Sidebar({ topics, goodDevs }: { topics: any[]; goodDevs: any[] }) {
  return (
    <aside style={{ position:"sticky", top:110, maxHeight:"calc(100vh - 130px)", overflowY:"auto" }}>
      {topics?.length > 0 && (
        <div style={{ marginBottom:24 }}>
          <h2 style={{ fontFamily:s.display, fontSize:16, fontWeight:700, color:s.accent, marginBottom:12 }}>Ongoing Situations</h2>
          {topics.map((t: any) => {
            const hasUpdates = t.what_changed_today?.length > 0;
            return (
              <Link key={t.slug} href={`/topics/${t.slug}`} style={{ display:"block", background:"#fff", border:`1px solid ${hasUpdates ? s.gold : s.border}`, borderRadius:8, padding:"10px 14px", marginBottom:6, textDecoration:"none", color:"inherit" }}>
                <div style={{ display:"flex", gap:6, alignItems:"center", marginBottom:3 }}>
                  <h3 style={{ fontFamily:s.display, fontSize:13, fontWeight:700, margin:0, lineHeight:1.3, flex:1 }}>{t.topic}</h3>
                  {t.phase && <span style={{ fontSize:8, fontWeight:700, textTransform:"uppercase", letterSpacing:"0.05em", color:s.light, background:s.borderLight, padding:"1px 5px", borderRadius:3 }}>{t.phase}</span>}
                </div>
                {hasUpdates && <p style={{ fontSize:10, color:s.gold, fontWeight:600, margin:"2px 0 0 0" }}>● Updated today</p>}
                {!hasUpdates && t.timeline?.[0] && <p style={{ fontSize:10, color:s.light, marginTop:2, lineHeight:1.3, display:"-webkit-box", WebkitLineClamp:1, WebkitBoxOrient:"vertical" as any, overflow:"hidden" }}>{t.timeline[0].text}</p>}
              </Link>
            );
          })}
        </div>
      )}
      {goodDevs?.length > 0 && (
        <div style={{ marginBottom:24 }}>
          <h2 style={{ fontFamily:s.display, fontSize:16, fontWeight:700, color:s.good, marginBottom:12 }}>Constructive Developments</h2>
          {goodDevs.map((g: any) => <GoodCard key={g.slug} article={g} />)}
        </div>
      )}
      <Link href="/archive" style={{ fontSize:12, color:s.light, fontWeight:500, textDecoration:"none", display:"block", marginBottom:8 }}>Browse past editions →</Link>
      <Link href="/how-it-works" style={{ fontSize:12, color:s.light, fontWeight:500, textDecoration:"none" }}>How The Daily Informant works →</Link>
    </aside>
  );
}

export default function DailyEdition({ daily }: { daily: any }) {
  const [filter, setFilter] = useState("All");
  const activeCats = CATS.filter(c => daily.top_stories.some((a: any) => a.category === c));
  const stories = filter === "All" ? daily.top_stories : daily.top_stories.filter((a: any) => a.category === filter);
  const hero = stories[0];
  const rest = stories.slice(1);
  const totalMinutes = daily.top_stories.reduce((sum: number, a: any) => sum + readTime(a.body), 0);

  return (
    <div>
      {/* Header bar */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"baseline", marginBottom:16, paddingBottom:10, borderBottom:`1px solid ${s.borderLight}`, flexWrap:"wrap", gap:8 }}>
        <div>
          <p style={{ fontSize:14, fontWeight:600, color:s.accent, margin:0 }}>Morning Edition</p>
          <p style={{ fontSize:14, color:s.muted, marginTop:2 }}>{fmtDate(daily.date)}</p>
        </div>
        <p style={{ fontSize:12, color:s.light, margin:0 }}>Today in {totalMinutes} minutes · {daily.top_stories.length + (daily.good_developments?.length || 0)} articles</p>
      </div>

      {/* Category pills */}
      <div style={{ display:"flex", gap:6, flexWrap:"wrap", marginBottom:20 }}>
        {["All", ...activeCats].map(c => {
          const active = filter === c;
          const cs = c === "All" ? { bg: s.accent, text: "#fff" } : gc(c);
          return <button key={c} onClick={() => setFilter(c)} style={{ fontSize:11, fontWeight:600, letterSpacing:"0.04em", textTransform:"uppercase", padding:"4px 12px", borderRadius:16, cursor:"pointer", border: active ? "none" : `1px solid ${s.border}`, background: active ? (c==="All" ? s.accent : cs.bg) : "transparent", color: active ? (c==="All" ? "#fff" : cs.text) : s.muted, fontFamily:s.body }}>{c}</button>;
        })}
      </div>

      {/* Main layout */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 260px", gap:28, alignItems:"start" }}>
        <main>
          {/* Need to Know */}
          {filter === "All" && <NeedToKnow items={daily.need_to_know} />}

          {/* Hero */}
          {hero && filter === "All" && <HeroStory article={hero} />}

          {/* Story list */}
          <div>
            {(filter === "All" ? rest : stories).map((a: any) => <StoryRow key={a.slug} article={a} />)}
          </div>

          {stories.length === 0 && <p style={{ color:s.muted, padding:20 }}>No articles in this category today.</p>}
        </main>

        {/* Sidebar */}
        <Sidebar topics={daily.ongoing_topics} goodDevs={daily.good_developments} />
      </div>
    </div>
  );
}
