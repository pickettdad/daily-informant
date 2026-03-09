#!/usr/bin/env python3
"""
The Daily Informant — Morning Pipeline v9.2
==========================================

v9.1 changes:
  - ADDED: Google Gemini 2.5 Flash for selection + bias review (4th AI model)
  - FIXED: Article word count too low (224 avg). Strengthened writing prompt.
  - FIXED: Grok selection silent failure. Added better error handling.
  - FIXED: Oslo explosion mis-tagged as middle-east-israel-gaza.

Required env vars:
  OPENAI_API_KEY, ANTHROPIC_API_KEY (optional), XAI_API_KEY (optional), GOOGLE_API_KEY (optional)
"""

import json, os, re, sys, time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

TORONTO = ZoneInfo("America/Toronto")

FEEDS = [
    # ── Local (Bay of Quinte / Belleville / Hastings / Prince Edward ONLY) ──
    {"name": "Quinte News",        "url": "https://www.quintenews.com/feed/",                       "lean": "Center",       "region": "Local"},
    {"name": "inQuinte",           "url": "https://inquinte.ca/feed",                                "lean": "Center",       "region": "Local"},
    # ── Ontario ──
    {"name": "Toronto Star",       "url": "https://www.thestar.com/search/?f=rss&t=article&c=news*&l=50&s=start_time&sd=desc", "lean": "Center-Left", "region": "Ontario"},
    {"name": "Toronto Sun",        "url": "https://torontosun.com/feed",                              "lean": "Right",        "region": "Ontario"},
    {"name": "Global News Canada", "url": "https://globalnews.ca/feed/",                              "lean": "Center",       "region": "Ontario"},
    # ── Canada ──
    {"name": "Globe and Mail",     "url": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/world/", "lean": "Center", "region": "Canada"},
    {"name": "National Post",      "url": "https://nationalpost.com/feed/",                            "lean": "Center-Right", "region": "Canada"},
    {"name": "CBC News",           "url": "https://rss.cbc.ca/lineup/canada.xml",                     "lean": "Center-Left",  "region": "Canada"},
    # ── US: Left ──
    {"name": "NPR News",           "url": "https://feeds.npr.org/1001/rss.xml",                       "lean": "Left",         "region": "US"},
    {"name": "NPR World",          "url": "https://feeds.npr.org/1004/rss.xml",                       "lean": "Left",         "region": "US"},
    {"name": "The Guardian US",    "url": "https://www.theguardian.com/us-news/rss",                   "lean": "Left",         "region": "US"},
    {"name": "PBS NewsHour",       "url": "https://www.pbs.org/newshour/feeds/rss/headlines",          "lean": "Left",         "region": "US"},
    # ── Center ──
    {"name": "BBC World",          "url": "https://feeds.bbci.co.uk/news/world/rss.xml",               "lean": "Center",       "region": "World"},
    {"name": "BBC Business",       "url": "https://feeds.bbci.co.uk/news/business/rss.xml",            "lean": "Center",       "region": "World"},
    {"name": "Al Jazeera",         "url": "https://www.aljazeera.com/xml/rss/all.xml",                 "lean": "Center",       "region": "World"},
    {"name": "France 24",          "url": "https://www.france24.com/en/rss",                           "lean": "Center",       "region": "World"},
    {"name": "ABC News",           "url": "https://abcnews.go.com/abcnews/topstories",                "lean": "Center",       "region": "US"},
    {"name": "CBS News",           "url": "https://www.cbsnews.com/latest/rss/main",                   "lean": "Center",       "region": "US"},
    # ── US: Right ──
    {"name": "Fox News",           "url": "https://moxie.foxnews.com/google-publisher/latest.xml",     "lean": "Right",        "region": "US"},
    {"name": "NY Post",            "url": "https://nypost.com/feed/",                                   "lean": "Right",        "region": "US"},
    {"name": "Daily Wire",         "url": "https://www.dailywire.com/feeds/rss.xml",                   "lean": "Right",        "region": "US"},
    {"name": "Breitbart",          "url": "https://feeds.feedburner.com/breitbart",                    "lean": "Right",        "region": "US"},
    {"name": "Washington Examiner", "url": "https://www.washingtonexaminer.com/feed",                  "lean": "Right",        "region": "US"},
    {"name": "The Hill",           "url": "https://thehill.com/feed/",                                  "lean": "Center-Right", "region": "US"},
    {"name": "RealClearPolitics",  "url": "https://www.realclearpolitics.com/index.xml",               "lean": "Center-Right", "region": "US"},
    # ── Science / Health / Tech ──
    {"name": "BBC Science",        "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "lean": "Center", "region": "World"},
    {"name": "BBC Health",         "url": "https://feeds.bbci.co.uk/news/health/rss.xml",              "lean": "Center",       "region": "World"},
    {"name": "BBC Tech",           "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",          "lean": "Center",       "region": "World"},
    {"name": "NPR Science",       "url": "https://feeds.npr.org/1007/rss.xml",                        "lean": "Left",         "region": "World"},
    {"name": "NPR Health",        "url": "https://feeds.npr.org/1128/rss.xml",                        "lean": "Left",         "region": "World"},
    {"name": "Ars Technica",      "url": "https://feeds.arstechnica.com/arstechnica/index",            "lean": "Center",       "region": "World"},
    {"name": "Phys.org",          "url": "https://phys.org/rss-feed/",                                 "lean": "Center",       "region": "World"},
    # ── Good News / Constructive ──
    {"name": "Good News Network",  "url": "https://www.goodnewsnetwork.org/feed/",                     "lean": "Center",       "region": "World"},
    {"name": "Positive News",      "url": "https://www.positive.news/feed/",                            "lean": "Center",       "region": "World"},
    {"name": "Christianity Today", "url": "https://www.christianitytoday.com/feed/",                    "lean": "Center",       "region": "World"},
    {"name": "Deseret News Faith", "url": "https://www.deseret.com/arc/outboundfeeds/rss/category/faith/", "lean": "Center",  "region": "World"},
]

ITEMS_PER_FEED = 6
MAX_ARTICLES = 25
MIN_CONSENSUS = 2
OPENAI_MODEL = "gpt-4o-mini"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
GROK_MODEL = "grok-4-1-fast-non-reasoning"
GEMINI_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_BASE_DELAY = 5

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

DAILY_PATH = Path("data/daily.json")
TOPICS_PATH = Path("data/topics.json")
ARCHIVE_PATH = Path("data/archive.json")

CATEGORY_ORDER = ["Local", "Ontario", "Canada", "US", "World", "Health", "Science", "Tech"]

# Category floors for selection
CATEGORY_FLOORS = {"Local": 2, "Ontario": 1, "Canada": 2, "US": 3, "World": 3, "Health": 1, "Science": 1, "Tech": 0}

# Canadian national keywords for category classification
CANADA_NATIONAL_KW = {
    "ottawa", "trudeau", "poilievre", "parliament", "house of commons", "senate canada",
    "bank of canada", "federal budget", "rcmp", "csis", "immigration canada",
    "federal court", "supreme court canada", "provinces", "interprovincial",
    "canadian forces", "liberal party", "conservative party", "ndp", "bloc",
}

ONGOING_TOPICS_PRIORITY = [
    ("iran-conflict",          {"iran", "tehran", "persian gulf", "irgc", "pezeshkian", "iranian"}),
    ("ukraine-russia",         {"ukraine", "kyiv", "russia", "moscow", "donbas", "crimea", "zelenskyy", "ukrainian"}),
    ("us-tariffs-trade",       {"tariff", "customs", "trade war", "import duties", "cbp", "trade court"}),
    ("economy-inflation",      {"inflation", "interest rate", "federal reserve", "bank of canada", "jobs report", "unemployment", "recession", "stagflation"}),
    ("middle-east-israel-gaza", {"gaza", "hamas", "palestinian", "west bank", "hostage", "ceasefire gaza"}),
    ("sudan-south-sudan",      {"sudan", "south sudan", "khartoum", "darfur", "rsf", "juba"}),
    ("ai-regulation",          {"ai act", "artificial intelligence regulation", "ai safety", "deepfake", "ai policy"}),
    ("climate-environment",    {"climate", "emissions", "renewable energy", "carbon", "paris agreement", "cop28", "cop29", "global warming"}),
]

# ── Noise Filter ───────────────────────────────────────────────────
NOISE_RE = re.compile(
    r"\bslam[s]?\b|\bblast[s]?\b|\bclap[s]? back\b|\bfires back\b|"
    r"\bgoes (off|viral)\b|\bspar[s]?\b|\boutrage[d]?\b|\bbacklash\b|"
    r"\bcalls out\b|\bdoubles down\b|\bmocks?\b|\brant[s]?\b|"
    r"\bfeud\b|\bsparks controversy\b|\btrending\b|\bshocking\b|"
    r"\bexplosive\b|\bbombshell\b", re.IGNORECASE)
ACTION_RE = re.compile(
    r"\bsign[s|ed]?\b|\bpass(es|ed)?\b|\bapprov(es|ed)?\b|"
    r"\brul(es|ed|ing)\b|\bveto\b|\bexecutive order\b|\blaw\b|"
    r"\bregulat\w+\b|\bsanction\b|\btreaty\b|\barrest\w*\b|"
    r"\bconvict\w*\b|\bsentenc\w*\b|\bdepl(oy|oyed)\b|\bstrike\b|"
    r"\bbudget\b|\breport\w*\b|\blaunch\w*\b|\bdiscover\w*\b|"
    r"\bvaccine\b|\belection\b|\bresign\w*\b|\bappoint\w*\b", re.IGNORECASE)

def is_noise(title, desc=""):
    combined = f"{title} {desc}"
    return not ACTION_RE.search(combined) and bool(NOISE_RE.search(combined))

# ── Helpers ─────────────────────────────────────────────────────────
STOP_WORDS = {"a","an","the","in","on","at","to","for","of","and","or","is","are","was","were","be","been","has","have","had","it","its","that","this","with","from","by","as","but","not","no","will","can","do","does","did","may","says","said","new","over","after","how","why","what","who","could","would","about","into","up","out","more","than"}

def kw(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP_WORDS and len(w) > 2}

def _api_call(url, headers, payload_dict, timeout=120):
    data = json.dumps(payload_dict).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(RETRY_BASE_DELAY * (attempt + 1)); continue
            try: body = e.read().decode("utf-8", "replace")[:200]
            except: body = ""
            raise RuntimeError(f"HTTP {e.code}: {body}")
        except URLError:
            time.sleep(RETRY_BASE_DELAY)
    raise RuntimeError("Failed after retries")

def _call_openai(messages, schema=None):
    payload = {"model": OPENAI_MODEL, "messages": messages}
    if schema: payload["response_format"] = schema
    data = _api_call("https://api.openai.com/v1/chat/completions",
                     {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
                     payload)
    return data["choices"][0]["message"]["content"]

def _call_grok_text(messages):
    payload = {"model": GROK_MODEL, "input": messages, "temperature": 0.3, "store": False}
    data = _api_call("https://api.x.ai/v1/responses", 
                     {"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}", "User-Agent": "DailyInformant/1.0"},
                     payload, timeout=180)
    raw = ""
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text": raw += c.get("text", "")
    return raw.strip()

def _call_grok_with_search(messages):
    payload = {"model": GROK_MODEL, "input": messages, "tools": [{"type": "web_search"}], "temperature": 0.1, "store": False}
    data = _api_call("https://api.x.ai/v1/responses",
                     {"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}", "User-Agent": "DailyInformant/1.0"},
                     payload, timeout=180)
    raw = ""
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text": raw += c.get("text", "")
    return raw.strip()

def _call_gemini(prompt_text):
    """Call Google Gemini 2.5 Flash via generateContent API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GOOGLE_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt_text}]}], "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096}}
    data = _api_call(url, {"Content-Type": "application/json"}, payload, timeout=120)
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        return ""

def _parse_json_from_text(text):
    """Safely extract first JSON array or object from text."""
    text = text.strip()
    # Try to find a JSON array
    for match in re.finditer(r'\[', text):
        try:
            start = match.start()
            result = json.loads(text[start:])
            return result
        except json.JSONDecodeError:
            # Try finding the matching bracket
            depth = 0
            for i, ch in enumerate(text[start:]):
                if ch == '[': depth += 1
                elif ch == ']': depth -= 1
                if depth == 0:
                    try: return json.loads(text[start:start+i+1])
                    except: break
    return []

# ── RSS Fetching ────────────────────────────────────────────────────
def fetch_feed(url, timeout=15):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; DailyInformantBot/1.0)"})
    with urlopen(req, timeout=timeout) as resp: return resp.read()

def parse_rss(xml_bytes, source_name, lean, region):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall(".//channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        desc = re.sub(r"<[^>]+>", "", (item.findtext("description") or "")).strip()
        if title and link:
            items.append({"source_name": source_name, "lean": lean, "region": region,
                          "title": title, "link": link, "pub_date": pub_date, "description": desc[:500]})
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "").strip() if link_el is not None else ""
        pub_date = (entry.findtext("atom:updated", namespaces=ns) or "").strip()
        desc = re.sub(r"<[^>]+>", "", (entry.findtext("atom:summary", namespaces=ns) or "")).strip()
        if title and link:
            items.append({"source_name": source_name, "lean": lean, "region": region,
                          "title": title, "link": link, "pub_date": pub_date, "description": desc[:500]})
    return items

def fetch_all_feeds():
    all_items, success = [], 0
    for feed in FEEDS:
        try:
            parsed = parse_rss(fetch_feed(feed["url"]), feed["name"], feed["lean"], feed["region"])
            all_items.extend(parsed[:ITEMS_PER_FEED])
            success += 1
            print(f"  ✓ {feed['name']} ({feed['lean']}, {feed['region']}): {len(parsed)} items")
        except Exception as e:
            print(f"  ✗ {feed['name']}: {e}")
    print(f"\n   Feeds succeeded: {success}/{len(FEEDS)}")
    return all_items

# ── Grouping ────────────────────────────────────────────────────────
def group_pass_1(items):
    groups, used = [], set()
    for i, item in enumerate(items):
        if i in used: continue
        group = [item]; used.add(i)
        item_kw = kw(item["title"] + " " + item.get("description", "")[:200])
        if len(item_kw) < 3: groups.append(group); continue
        for j, other in enumerate(items):
            if j in used: continue
            other_kw = kw(other["title"] + " " + other.get("description", "")[:200])
            if len(other_kw) < 3: continue
            overlap = len(item_kw & other_kw)
            if min(len(item_kw), len(other_kw)) > 0 and overlap / min(len(item_kw), len(other_kw)) >= 0.30:
                group.append(other); used.add(j)
        groups.append(group)
    groups.sort(key=lambda g: -len(g))
    return groups

def group_pass_2_ai(groups):
    if not OPENAI_API_KEY or len(groups) < 5: return groups
    cap = min(len(groups), 80)
    summaries = [f"{i+1}. [{len(groups[i])} art] {groups[i][0]['title'][:80]}" for i in range(cap)]
    prompt = f"Below are {len(summaries)} story groups. Some cover the SAME event/topic. Identify groups to merge.\nReturn ONLY a JSON array of arrays. Example: [[1,4,7],[3,9]]\nIf none, return [].\n\n" + "\n".join(summaries)
    try:
        raw = _call_openai([{"role": "user", "content": prompt}])
        merges = _parse_json_from_text(raw)
        absorbed = set()
        for merge_set in merges:
            if not isinstance(merge_set, list) or len(merge_set) < 2: continue
            indices = [n-1 for n in merge_set if isinstance(n, int) and 1 <= n <= cap]
            if len(indices) < 2: continue
            target = indices[0]
            for src in indices[1:]:
                if src != target and src not in absorbed:
                    groups[target] = groups[target] + groups[src]; absorbed.add(src)
        new_groups = [g for i, g in enumerate(groups) if i not in absorbed]
        new_groups.sort(key=lambda g: -len(g))
        if absorbed: print(f"   AI merged {len(absorbed)} groups → {len(new_groups)} remaining")
        return new_groups
    except Exception as e:
        print(f"   AI merge failed: {e}"); return groups

# ── Category Classification ─────────────────────────────────────────
def classify_group_category(group):
    """Pre-classify a group's likely category based on source regions and keywords."""
    regions = [item["region"] for item in group]
    text = " ".join(item["title"].lower() + " " + item.get("description", "").lower()[:100] for item in group)
    
    if any(r == "Local" for r in regions): return "Local"
    # Check for Canada national before Ontario
    if any(k in text for k in CANADA_NATIONAL_KW): return "Canada"
    if any(r == "Ontario" for r in regions): return "Ontario"
    if any(r == "Canada" for r in regions): return "Canada"
    if any(r == "US" for r in regions):
        if any(w in text for w in ["health", "medical", "disease", "vaccine", "drug"]): return "Health"
        if any(w in text for w in ["nasa", "space", "research", "study", "discovery"]): return "Science"
        if any(w in text for w in ["ai ", "artificial intelligence", "tech", "software", "cyber"]): return "Tech"
        return "US"
    if any(w in text for w in ["health", "medical", "disease"]): return "Health"
    if any(w in text for w in ["nasa", "space", "research", "climate"]): return "Science"
    return "World"

# ── Bucket-Based Selection ──────────────────────────────────────────

SELECTION_PROMPT = """You are the editorial director for The Daily Informant (DI), a calm, unbiased morning briefing for a Canadian reader based in Bay of Quinte, Ontario.

Below are story groups ORGANIZED BY CATEGORY. For each category, rank the stories by importance.

Then assemble the BEST cross-category lineup of 25 stories for a morning briefing that a busy Canadian reads in 10-15 minutes.

CATEGORY FLOORS (include at least this many IF quality stories exist):
- Local (Bay of Quinte): 2-3
- Ontario: 2-3
- Canada: 2-4 (IMPORTANT: always include national Canadian stories when available)
- US: 4-6
- World: 4-6
- Health/Science/Tech: 2-3

Mark constructive/positive stories with + prefix.
DO NOT select sports stories.
DO NOT select multiple stories about the same topic.

Return ONLY a JSON array of group numbers (up to 25). Prefix positive stories with +.
"""

def build_bucketed_pool_text(groups):
    """Build pool text organized by category buckets."""
    buckets = {}
    for i, group in enumerate(groups):
        cat = classify_group_category(group)
        buckets.setdefault(cat, []).append((i, group))
    
    lines = []
    for cat in CATEGORY_ORDER:
        items = buckets.get(cat, [])
        if not items: continue
        lines.append(f"\n=== {cat.upper()} ({len(items)} groups) ===")
        for idx, group in items:
            sources = set(item["source_name"] for item in group)
            leans = set(item["lean"] for item in group)
            p = group[0]
            line = f"{idx+1}. [{len(group)} art, {', '.join(sorted(leans))}] {p['title']}"
            if p.get("description"): line += f" — {p['description'][:100]}"
            if len(sources) > 1: line += f" (Also: {', '.join(sorted(sources - {p['source_name']}))})"
            lines.append(line)
    
    # Also show uncategorized
    other = buckets.get("Other", [])
    if other:
        lines.append(f"\n=== OTHER ({len(other)} groups) ===")
        for idx, group in other:
            lines.append(f"{idx+1}. [{len(group)} art] {group[0]['title']}")
    
    return "\n".join(lines)

def _parse_picks(text):
    match = re.search(r'\[([^\]]+)\]', text)
    if not match: return [], set()
    nums, good = [], set()
    for p in match.group(1).split(","):
        p = p.strip()
        is_g = p.startswith("+"); p = p.lstrip("+").strip()
        try: n = int(p); nums.append(n); (good.add(n) if is_g else None)
        except ValueError: pass
    return nums, good

def run_selection(pool_text):
    results, all_good = {}, set()
    for name, key, fn in [
        ("OpenAI", OPENAI_API_KEY, lambda pt: _call_openai([{"role": "system", "content": SELECTION_PROMPT}, {"role": "user", "content": pt}])),
        ("Claude", ANTHROPIC_API_KEY, lambda pt: _api_call("https://api.anthropic.com/v1/messages",
            {"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
            {"model": CLAUDE_MODEL, "max_tokens": 2048, "messages": [{"role": "user", "content": f"{SELECTION_PROMPT}\n\n{pt}"}], "temperature": 0.3})["content"][0]["text"]),
        ("Grok", XAI_API_KEY, lambda pt: _call_grok_text([{"role": "user", "content": f"{SELECTION_PROMPT}\n\n{pt}"}])),
        ("Gemini", GOOGLE_API_KEY, lambda pt: _call_gemini(f"{SELECTION_PROMPT}\n\n{pt}")),
    ]:
        if not key: continue
        print(f"  → {name}...")
        try:
            raw = fn(pool_text)
            if not raw:
                print(f"    {name}: empty response")
                continue
            picks, good = _parse_picks(raw)
            if picks:
                results[name] = picks; all_good.update(good)
                print(f"    {name}: {len(picks)} groups, {len(good)} constructive")
            else:
                print(f"    {name}: no valid picks parsed. Response starts: {raw[:150]}...")
        except Exception as e:
            print(f"    {name} FAILED: {type(e).__name__}: {e}")
        time.sleep(1)
    return results, all_good

def build_consensus(selections, pool_size):
    n = len(selections)
    if n == 0: return []
    if n == 1: return list(selections.values())[0][:MAX_ARTICLES]
    votes, ranks = {}, {}
    for model, picks in selections.items():
        for rank, num in enumerate(picks):
            if 1 <= num <= pool_size:
                votes[num] = votes.get(num, 0) + 1; ranks[num] = ranks.get(num, 0) + rank
    min_v = min(MIN_CONSENSUS, n)
    consensus = sorted([s for s, v in votes.items() if v >= min_v], key=lambda s: (-votes[s], ranks[s]/votes[s]))
    print(f"\n   Consensus ({n} models): {len(consensus)} groups agreed")
    if len(consensus) < MAX_ARTICLES:
        extra = sorted([s for s in votes if s not in consensus], key=lambda s: (-votes[s], ranks[s]/max(votes[s],1)))
        consensus.extend(extra[:MAX_ARTICLES - len(consensus)])
    return consensus[:MAX_ARTICLES]

# ── Two-Pass Article Generation ─────────────────────────────────────

EVIDENCE_PROMPT = """Extract structured evidence from these related news articles. Output ONLY valid JSON.

{
  "confirmed_facts": ["fact1", "fact2", ...],
  "timeline": ["earliest event", "next event", ...],
  "stakes": ["who is affected and how"],
  "unknowns": ["what is not yet confirmed"],
  "next_steps": ["what happens next"],
  "key_quotes": [{"speaker": "Name", "quote": "exact words", "source": "outlet"}],
  "perspective_differences": ["where sources disagree or frame differently"],
  "category": "Local|Ontario|Canada|US|World|Health|Science|Tech",
  "is_constructive": false,
  "is_negative": false,
  "related_ongoing": ""
}

CATEGORY RULES:
- "Local" = ONLY Bay of Quinte, Belleville, Trenton, Hastings County, Prince Edward County, Tyendinaga, Campbellford
- "Ontario" = Toronto, Ottawa, provincial Ontario stories
- "Canada" = National Canadian stories
- "US"/"World"/"Health"/"Science"/"Tech" as appropriate

is_constructive: TRUE for volunteer efforts, charitable giving, rescues, breakthroughs, milestones, community wins, scientific advances, policy progress. FALSE for anything involving death, crime, conflict.
is_negative: TRUE if involves conflict, death, hardship, disaster, suffering.
related_ongoing: Match ONLY if the story is DIRECTLY about one of these situations:
- "iran-conflict" = military operations between U.S./Israel and Iran, Iranian military targets, Persian Gulf incidents
- "ukraine-russia" = fighting in Ukraine, Russia-Ukraine diplomacy, sanctions on Russia over Ukraine
- "economy-inflation" = central bank rates, jobs reports, recession data, inflation statistics
- "us-tariffs-trade" = tariff policy, trade disputes, customs enforcement
- "middle-east-israel-gaza" = Gaza, Hamas, Palestinian territories, West Bank ONLY (NOT general Middle East)
- "sudan-south-sudan" = Sudan civil war, South Sudan conflict
- "ai-regulation" = AI policy, regulation, safety legislation
- "climate-environment" = climate policy, emissions, renewable energy policy
Do NOT tag stories that merely mention a related country or region. The story must be ABOUT the situation. Empty string if no clear match."""

ARTICLE_PROMPT = """You are a senior editor at a calm, neutral morning briefing called The Daily Informant. You write like The Economist — authoritative, clear, never sensational.

Write a finished briefing article from the evidence below. The reader will NOT open the source links — your article IS their complete understanding of this story. Write like a journalist, not a summarizer.

CRITICAL LENGTH REQUIREMENT: The body MUST be 350-500 words. This is a HARD minimum. Count carefully. Short articles (under 300 words) are unacceptable. Use the evidence fully — include timeline details, stakeholder positions, implications, and unknowns. If you have rich evidence, write closer to 500 words.

STRUCTURE (follow exactly):
1. bottom_line: ONE sentence (25-40 words) — the single most important takeaway a busy reader needs
2. headline: Neutral, informative, 8-12 words. No clickbait, no loaded words (avoid: slams, blasts, shocking, controversial)
3. body: 350-500 word article in flowing paragraphs (4-6 paragraphs). Structure:
   - Paragraph 1: The most important new fact — what happened, where, when
   - Paragraph 2: Key details, confirmed facts, numbers
   - Paragraph 3: Background and context — how we got here
   - Paragraph 4: Stakeholder reactions and different perspectives
   - Paragraph 5: Implications and what this means going forward
   - Paragraph 6 (if needed): Unknowns, disputed points, what remains unclear
   Never say "according to sources" or "several outlets reported." State confirmed facts directly. When sources disagree, note the disagreement specifically.
4. why_it_matters: 2-3 sentences — the "so what" for a busy Canadian reader. Be specific about real-world impact.
5. what_to_watch: 1-2 sentences — the next concrete event (upcoming vote, deadline, announcement, hearing)
6. key_developments: 4-6 bullet points of the most concrete facts from the evidence
7. stakeholder_quotes: 0-3 real quotes from the evidence (NEVER invent quotes)
8. positive_thought: Write a brief prayer-like thought for EVERY article. Make it specific to THIS story — mention a real person, place, or detail from the evidence. Express genuine hope for the people involved. Be heartfelt and unique, not generic. NO God, NO Amen. For negative stories, focus on comfort and hope for those suffering. For positive stories, express gratitude and hope the good continues. Examples: "May the families in Kharkiv find warmth tonight, and may the first responders who rushed toward danger find rest and safety." or "May the scientists behind this breakthrough see their work reach the communities who need it most."

DIVERSITY RULE: If the evidence includes perspectives from different political leanings, the article MUST fairly represent multiple viewpoints. Include at least one factual point or quote from right-leaning sources when present. Never force false equivalence, but never omit a consequential perspective.

Output ONLY valid JSON matching the required schema."""

EVIDENCE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "evidence_packet",
        "schema": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "confirmed_facts": {"type": "array", "items": {"type": "string"}},
                "timeline": {"type": "array", "items": {"type": "string"}},
                "stakes": {"type": "array", "items": {"type": "string"}},
                "unknowns": {"type": "array", "items": {"type": "string"}},
                "next_steps": {"type": "array", "items": {"type": "string"}},
                "key_quotes": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "properties": {"speaker": {"type": "string"}, "quote": {"type": "string"}, "source": {"type": "string"}},
                    "required": ["speaker", "quote", "source"]}},
                "perspective_differences": {"type": "array", "items": {"type": "string"}},
                "category": {"type": "string"},
                "is_constructive": {"type": "boolean"},
                "is_negative": {"type": "boolean"},
                "related_ongoing": {"type": "string"},
            },
            "required": ["confirmed_facts", "timeline", "stakes", "unknowns", "next_steps",
                         "key_quotes", "perspective_differences", "category", "is_constructive",
                         "is_negative", "related_ongoing"],
        }, "strict": True,
    },
}

ARTICLE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "di_article",
        "schema": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "bottom_line": {"type": "string"},
                "headline": {"type": "string"},
                "body": {"type": "string"},
                "why_it_matters": {"type": "string"},
                "what_to_watch": {"type": "string"},
                "key_developments": {"type": "array", "items": {"type": "string"}},
                "stakeholder_quotes": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "properties": {"speaker": {"type": "string"}, "quote": {"type": "string"}},
                    "required": ["speaker", "quote"]}},
                "positive_thought": {"type": "string"},
            },
            "required": ["bottom_line", "headline", "body", "why_it_matters", "what_to_watch",
                         "key_developments", "stakeholder_quotes", "positive_thought"],
        }, "strict": True,
    },
}

def build_source_text(group):
    text = ""
    for i, item in enumerate(group):
        text += f"\n--- Source {i+1} [{item['source_name']}, {item['lean']}, {item['region']}] ---\n"
        text += f"Title: {item['title']}\nPublished: {item['pub_date']}\nDescription: {item['description']}\nLink: {item['link']}\n"
    return text

def extract_evidence(group):
    """Pass A: Extract structured evidence from sources."""
    source_text = build_source_text(group)
    raw = _call_openai([{"role": "system", "content": EVIDENCE_PROMPT}, {"role": "user", "content": source_text}], EVIDENCE_SCHEMA)
    return json.loads(raw)

def write_article(evidence, source_count, source_leans):
    """Pass B: Write article from evidence packet."""
    evidence_text = json.dumps(evidence, indent=2)
    context = f"This story was covered by {source_count} sources across these leanings: {', '.join(sorted(source_leans))}."
    raw = _call_openai([
        {"role": "system", "content": ARTICLE_PROMPT},
        {"role": "user", "content": f"{context}\n\nEvidence:\n{evidence_text}"}
    ], ARTICLE_SCHEMA)
    return json.loads(raw)

def find_related_sources(primary, all_items):
    primary_kw = kw(primary["title"] + " " + primary.get("description", "")[:200])
    if len(primary_kw) < 2: return [{"name": primary["source_name"], "url": primary["link"]}]
    sources = [{"name": primary["source_name"], "url": primary["link"]}]
    seen = {primary["source_name"]}
    for item in all_items:
        if item["source_name"] in seen: continue
        item_kw = kw(item["title"] + " " + item.get("description", "")[:200])
        if len(item_kw) < 2: continue
        overlap = len(primary_kw & item_kw)
        smaller = min(len(primary_kw), len(item_kw))
        if smaller > 0 and overlap / smaller >= 0.18:
            sources.append({"name": item["source_name"], "url": item["link"]}); seen.add(item["source_name"])
    return sources

def enrich_sources_post_selection(articles, all_items):
    """Post-selection: scan ALL feed items for each article to boost source count."""
    for article in articles:
        headline_kw = kw(article["headline"])
        if len(headline_kw) < 3: continue
        existing = {ca["url"] for ca in article.get("component_articles", [])}
        existing_sources = {s["name"] for s in article.get("sources", [])}
        for item in all_items:
            if item["link"] in existing or item["source_name"] in existing_sources: continue
            item_kw = kw(item["title"] + " " + item.get("description", "")[:200])
            if len(item_kw) < 3: continue
            overlap = len(headline_kw & item_kw)
            if min(len(headline_kw), len(item_kw)) > 0 and overlap / min(len(headline_kw), len(item_kw)) >= 0.25:
                article["component_articles"].append({"source": item["source_name"], "lean": item["lean"], "title": item["title"], "url": item["link"]})
                article["sources"].append({"name": item["source_name"], "url": item["link"]})
                existing.add(item["link"]); existing_sources.add(item["source_name"])
    enriched = sum(1 for a in articles if len(a.get("component_articles",[])) > 1)
    print(f"   Source enrichment: {enriched}/{len(articles)} articles have 2+ sources")
    return articles

def build_di_article(group, idx, all_items, is_good_flagged=False):
    slug = f"article-{idx + 1}"
    sources = find_related_sources(group[0], all_items)
    component_articles = [{"source": i["source_name"], "lean": i["lean"], "title": i["title"], "url": i["link"]} for i in group]
    source_leans = set(i["lean"] for i in group)
    
    try:
        # Pass A: Evidence
        evidence = extract_evidence(group)
        category = evidence.get("category", "World").strip()
        # FIX: Validate category against allowed values — prevent slug leaking into category
        if category not in CATEGORY_ORDER:
            category = classify_group_category(group)
        is_constructive = evidence.get("is_constructive", False) or is_good_flagged
        is_neg = evidence.get("is_negative", False)
        related = evidence.get("related_ongoing", "").strip()
        
        # Validate
        valid_slugs = {s for s, _ in ONGOING_TOPICS_PRIORITY}
        if related not in valid_slugs: related = ""
        if is_constructive and is_neg: is_constructive = False
        
        # Pass B: Article (with retry if too short)
        article = write_article(evidence, len(group), source_leans)
        body = article.get("body", "").strip()
        # Retry once if article body is a stub (under 200 words)
        if len(body.split()) < 200 and len(group) > 0:
            print(f"    ↻ Retrying article (only {len(body.split())}w)...")
            time.sleep(1)
            article = write_article(evidence, len(group), source_leans)
            body = article.get("body", "").strip()
        
        headline = article.get("headline", group[0]["title"]).strip()
        bottom_line = article.get("bottom_line", "").strip()
        why_matters = article.get("why_it_matters", "").strip()
        what_watch = article.get("what_to_watch", "").strip()
        pos = article.get("positive_thought", "").strip()
        
        key_devs = [{"text": d.strip(), "source_url": group[0]["link"]}
                    for d in article.get("key_developments", []) if isinstance(d, str) and d.strip()]
        quotes = [{"speaker": q["speaker"], "quote": q["quote"], "url": group[0]["link"]}
                  for q in article.get("stakeholder_quotes", []) if q.get("speaker") and q.get("quote")]
        # Add quotes from evidence too
        for eq in evidence.get("key_quotes", []):
            if eq.get("speaker") and eq.get("quote"):
                if not any(q["speaker"] == eq["speaker"] for q in quotes):
                    quotes.append({"speaker": eq["speaker"], "quote": eq["quote"], "url": group[0]["link"], "source_outlet": eq.get("source", "")})
        
        tags = ""
        if is_constructive: tags += " [CONSTRUCTIVE]"
        if is_neg: tags += " [NEG]"
        if related: tags += f" [{related}]"
        word_count = len(body.split())
        print(f"  ✓ [{category}] \"{headline[:48]}\" ({word_count}w, {len(key_devs)}kd, {len(sources)}s, {len(group)}art){tags}")
        
        return {
            "slug": slug, "headline": headline, "bottom_line": bottom_line,
            "body": body, "why_it_matters": why_matters, "what_to_watch": what_watch,
            "category": category, "key_points": key_devs,
            "sources": sources, "component_articles": component_articles,
            "stakeholder_quotes": quotes, "is_good_development": is_constructive,
            "is_negative": is_neg, "positive_thought": pos,
            "related_ongoing": related,
        }
    except Exception as e:
        print(f"  ✗ Article {idx+1} failed: {e}")
        return {
            "slug": slug, "headline": group[0]["title"], "bottom_line": "",
            "body": group[0].get("description", "")[:300], "why_it_matters": "", "what_to_watch": "",
            "category": classify_group_category(group),
            "key_points": [{"text": group[0].get("description", "")[:200], "source_url": group[0]["link"]}],
            "sources": sources, "component_articles": component_articles,
            "stakeholder_quotes": [], "is_good_development": False,
            "is_negative": False, "positive_thought": "", "related_ongoing": "",
        }

# ── Bias Review ─────────────────────────────────────────────────────
BIAS_PROMPT = """Review these articles for bias, sensationalism, or missing perspectives. Return ONLY a JSON array of corrections.
Each: {"article_index": N, "field": "headline"|"body"|"bottom_line", "issue": "brief description", "corrected_text": "fixed version"}
If none needed, return []."""

def run_bias_review(articles):
    batch = "\n".join(f"--- Article {i} [{a.get('category')}] ---\nHeadline: {a['headline']}\nBottom Line: {a.get('bottom_line','')}\nBody: {a.get('body','')[:300]}" for i, a in enumerate(articles))
    total = 0
    reviewers = []
    if ANTHROPIC_API_KEY:
        reviewers.append(("Claude", lambda: _api_call("https://api.anthropic.com/v1/messages",
            {"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
            {"model": CLAUDE_MODEL, "max_tokens": 4096, "messages": [{"role": "user", "content": f"{BIAS_PROMPT}\n\n{batch}"}], "temperature": 0.1})["content"][0]["text"]))
    if XAI_API_KEY:
        reviewers.append(("Grok", lambda: _call_grok_text([{"role": "user", "content": f"{BIAS_PROMPT}\n\n{batch}"}])))
    if GOOGLE_API_KEY:
        reviewers.append(("Gemini", lambda: _call_gemini(f"{BIAS_PROMPT}\n\n{batch}")))
    for name, fn in reviewers:
        print(f"  → {name} reviewing...")
        try:
            raw = fn()
            corrections = _parse_json_from_text(raw)
            if isinstance(corrections, list):
                applied = 0
                for fix in corrections:
                    try:
                        idx, field, corrected = fix.get("article_index",-1), fix.get("field",""), fix.get("corrected_text","")
                        if 0 <= idx < len(articles) and field in ("headline","body","bottom_line","why_it_matters") and corrected:
                            articles[idx][field] = corrected; applied += 1; total += 1
                            print(f"    {name} fixed article {idx} {field}: {fix.get('issue','')}")
                    except: pass
                print(f"    {name}: {applied} corrections applied")
        except Exception as e: print(f"    {name} review failed: {e}")
        time.sleep(1)
    print(f"   Total bias corrections: {total}")
    return articles

# ── X/Twitter Quotes ────────────────────────────────────────────────
X_PROMPT = """Find real X (Twitter) quotes from public figures on OPPOSING sides of each article topic. Return ONLY a JSON array:
[{"article_index": 0, "quotes": [{"speaker": "Name", "quote": "text", "perspective": "supporting"}, {"speaker": "Name2", "quote": "text2", "perspective": "opposing"}]}]
Skip local/community stories. Only include real, verifiable quotes. If no opposing quotes found, return empty quotes array."""

def fetch_x_quotes(articles):
    if not XAI_API_KEY: return articles
    searchable = [(i, a) for i, a in enumerate(articles) if a.get("category") in ("World","US","Canada","Ontario") or a.get("related_ongoing")]
    if not searchable: return articles
    batch = "\n".join(f"--- Article {i} [{a.get('category')}] ---\nHeadline: {a['headline']}\nBody: {a.get('body','')[:150]}" for i, a in searchable)
    try:
        raw = _call_grok_with_search([{"role": "user", "content": f"{X_PROMPT}\n\n{batch}"}])
        results = _parse_json_from_text(raw)
        if not isinstance(results, list): return articles
        added = 0
        for result in results:
            idx = result.get("article_index", -1)
            if not (0 <= idx < len(articles)): continue
            for q in result.get("quotes", []):
                if q.get("speaker") and q.get("quote"):
                    articles[idx].setdefault("stakeholder_quotes", []).append({
                        "speaker": q["speaker"], "quote": q["quote"], "url": "",
                        "source": "X", "perspective": q.get("perspective", ""),
                    }); added += 1
        print(f"   Added {added} X quotes")
    except Exception as e: print(f"   X quotes failed: {e}")
    return articles

# ── Ongoing Topics ──────────────────────────────────────────────────
def load_json(path):
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except: pass
    return None

def update_ongoing_topics(articles, topics_data, today):
    if not topics_data.get("topics"): return topics_data
    now_iso = datetime.now(TORONTO).isoformat()
    
    for topic in topics_data["topics"]:
        slug = topic["slug"]
        entities = dict(ONGOING_TOPICS_PRIORITY).get(slug)
        if not entities: continue
        
        # Reset daily changes
        topic["what_changed_today"] = []
        matched_articles = []
        
        for article in articles:
            text = (article["headline"] + " " + article.get("body", "")[:200]).lower()
            if sum(1 for e in entities if e in text) >= 2:
                if article.get("related_ongoing", "") and article["related_ongoing"] != slug:
                    continue
                matched_articles.append(article)
        
        if not matched_articles:
            continue
        
        # Add timeline entries (append-only, one per day per topic)
        existing_dates = {e["date"] for e in topic.get("timeline", [])}
        if today not in existing_dates:
            # Pick the most significant article (most sources)
            best = max(matched_articles, key=lambda a: len(a.get("component_articles", [])))
            # Determine category from article content
            cat = "military"
            body_lower = (best.get("body", "") + " " + best["headline"]).lower()
            if any(w in body_lower for w in ["diplomat", "talks", "negotiat", "summit", "mediator", "ceasefire"]):
                cat = "diplomatic"
            elif any(w in body_lower for w in ["humanitarian", "refugee", "displaced", "aid", "famine"]):
                cat = "humanitarian"
            elif any(w in body_lower for w in ["price", "market", "trade", "tariff", "economic", "oil", "jobs"]):
                cat = "economic"
            elif any(w in body_lower for w in ["court", "legal", "ruling", "lawsuit", "judge"]):
                cat = "legal"
            elif any(w in body_lower for w in ["election", "parliament", "vote", "legislation", "policy"]):
                cat = "political"
            
            topic.setdefault("timeline", []).insert(0, {
                "date": today,
                "text": best["headline"],
                "category": cat,
                "source_url": best["sources"][0]["url"] if best.get("sources") else "#"
            })
            topic["timeline"] = topic["timeline"][:30]
        
        # Build what_changed_today from all matched articles
        for art in matched_articles[:3]:  # max 3 changes per topic
            change = art.get("bottom_line", "") or art["headline"]
            if change and change not in topic["what_changed_today"]:
                topic["what_changed_today"].append(change)
        
        # Update timestamps
        topic["last_material_update"] = now_iso
        
        print(f"  → Updated \"{topic['topic']}\" ({len(matched_articles)} articles, {len(topic['what_changed_today'])} changes)")
    
    return topics_data

# ── Main ────────────────────────────────────────────────────────────
def main():
    today = datetime.now(TORONTO).strftime("%Y-%m-%d")
    print("=" * 65)
    print("  The Daily Informant — Morning Pipeline v9.2")
    print(f"  {datetime.now(TORONTO).strftime('%Y-%m-%d %H:%M %Z')}")
    print("=" * 65)

    models = [n for n, k in [("OpenAI", OPENAI_API_KEY), ("Claude", ANTHROPIC_API_KEY), ("Grok", XAI_API_KEY), ("Gemini", GOOGLE_API_KEY)] if k]
    print(f"\n  AI models: {', '.join(models) or 'NONE'}")
    if not OPENAI_API_KEY: print("\n✗ OPENAI_API_KEY required."); sys.exit(1)

    print("\n─── Step 1: Fetching RSS feeds ───")
    all_items = fetch_all_feeds()
    if not all_items: print("\n✗ No items."); sys.exit(1)
    print(f"\n   Raw items: {len(all_items)}")

    print("\n─── Step 2: Noise filter ───")
    filtered = [i for i in all_items if not is_noise(i["title"], i.get("description", ""))]
    print(f"   Filtered {len(all_items)-len(filtered)} noise | Remaining: {len(filtered)}")

    print("\n─── Step 3: Grouping ───")
    groups = group_pass_1(filtered)
    print(f"   Pass 1: {len(groups)} groups")
    for g in groups[:5]: print(f"    [{len(g)} art] {g[0]['title'][:60]}")
    groups = group_pass_2_ai(groups)
    print(f"   Final groups: {len(groups)}")

    print("\n─── Step 4: Bucket-based AI selection ───")
    pool_text = build_bucketed_pool_text(groups)
    selections, good_indices = run_selection(pool_text)
    consensus_indices = build_consensus(selections, len(groups)) if selections else list(range(1, min(MAX_ARTICLES+1, len(groups)+1)))
    consensus_groups = [groups[i-1] for i in consensus_indices if 1 <= i <= len(groups)]
    print(f"\n   Final: {len(consensus_groups)} DI articles")

    print("\n─── Step 5: Two-pass article generation ───")
    articles = []
    for i, group in enumerate(consensus_groups):
        idx = consensus_indices[i] if i < len(consensus_indices) else 0
        articles.append(build_di_article(group, i, all_items, idx in good_indices))
        if i < len(consensus_groups) - 1: time.sleep(0.5)

    print("\n─── Step 5b: Bias review ───")
    articles = run_bias_review(articles)

    print("\n─── Step 5c: X/Twitter quotes ───")
    articles = fetch_x_quotes(articles)

    print("\n─── Step 5d: Source enrichment ───")
    articles = enrich_sources_post_selection(articles, all_items)

    # Separate
    regular, good_devs = [], []
    for a in articles:
        (good_devs if a.get("is_good_development") else regular).append(a)
    regular.sort(key=lambda a: CATEGORY_ORDER.index(a.get("category","World")) if a.get("category","World") in CATEGORY_ORDER else 99)

    print(f"\n   Regular: {len(regular)} | Constructive: {len(good_devs)}")
    cats = {}
    for a in articles: cats[a.get("category","?")] = cats.get(a.get("category","?"), 0) + 1
    print(f"   Category breakdown: {dict(sorted(cats.items()))}")

    print("\n─── Step 6: Archive & ongoing ───")
    archive = load_json(ARCHIVE_PATH) or []
    for a in articles:
        archive.append({"date": today, "headline": a["headline"], "category": a.get("category","World"),
                        "slug": a["slug"], "source_count": len(a.get("component_articles",[]))})
    ARCHIVE_PATH.write_text(json.dumps(archive[-900:], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    
    topics_data = load_json(TOPICS_PATH) or {"topics": []}
    topics_data = update_ongoing_topics(articles, topics_data, today)
    TOPICS_PATH.write_text(json.dumps(topics_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ongoing_for_daily = [{"slug": t["slug"], "topic": t["topic"], "summary": t.get("summary",""),
                          "status": t.get("status", "active"), "phase": t.get("phase", ""),
                          "what_changed_today": t.get("what_changed_today", []),
                          "timeline": t.get("timeline",[])[:5]} for t in topics_data.get("topics",[])]

    # Need to know: top 5 most important stories (prioritize World/US/Canada, highest source count)
    all_for_ntk = regular + good_devs
    ntk_priority = {"World": 0, "US": 1, "Canada": 2, "Ontario": 3, "Health": 4, "Science": 4, "Tech": 4, "Local": 5}
    all_for_ntk.sort(key=lambda a: (ntk_priority.get(a.get("category","World"), 5), -len(a.get("component_articles",[]))))
    need_to_know = [{"headline": a["headline"], "bottom_line": a.get("bottom_line","")} for a in all_for_ntk[:5]]

    DAILY_PATH.write_text(json.dumps({
        "date": today,
        "need_to_know": need_to_know,
        "top_stories": regular,
        "ongoing_topics": ongoing_for_daily,
        "good_developments": good_devs,
        "_meta": {
            "pipeline_version": "9.2", "models_used": list(selections.keys()),
            "feeds_attempted": len(FEEDS), "raw_items": len(all_items),
            "groups_formed": len(groups), "consensus_articles": len(consensus_groups),
            "good_developments": len(good_devs), "category_breakdown": cats,
            "category_order": CATEGORY_ORDER,
        },
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n{'='*65}")
    print(f"  DONE — {len(articles)} DI articles → data/daily.json")
    print(f"  Models: {', '.join(selections.keys())}")
    print(f"  Categories: {dict(sorted(cats.items()))}")
    print(f"  Sources: {sum(len(a.get('sources',[])) for a in articles)} | Consolidated: {sum(len(a.get('component_articles',[])) for a in articles)}")
    print(f"  Avg words/article: {sum(len(a.get('body','').split()) for a in articles)//max(len(articles),1)}")
    print(f"  Negative: {sum(1 for a in articles if a.get('is_negative'))} | Constructive: {len(good_devs)} | Ongoing: {sum(1 for a in articles if a.get('related_ongoing'))}")
    print(f"{'='*65}")

if __name__ == "__main__":
    main()
