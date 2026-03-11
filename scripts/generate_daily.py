#!/usr/bin/env python3
"""
The Daily Informant — Morning Pipeline v10
==========================================

v10 changes (based on consolidated review by ChatGPT, Grok, Gemini):
  - NEW: Hybrid lexical+entity+union-find grouping (replaces keyword overlap)
  - NEW: Full article text fetching after selection (trafilatura or fallback)
  - NEW: Provenance-preserving "editor brief" evidence extraction
  - NEW: Flexible, category-aware article writing with style cards
  - NEW: Global diversity/copy-edit pass after all articles written
  - FIXED: Source attribution preserves provenance (not just group[0])
  - FIXED: Bias review is advisory (targeted edits, not full overwrites)
  - FIXED: Regex bugs in ACTION_RE
  - KEPT: Multi-AI consensus for selection
  - KEPT: Positive thought on every article (non-negotiable)
  - KEPT: Ongoing topic tracking, X quotes, archive

Required env vars:
  OPENAI_API_KEY, ANTHROPIC_API_KEY (optional), XAI_API_KEY (optional), GOOGLE_API_KEY (optional)
"""

import json, os, re, sys, time, math, html as html_lib, random
from collections import Counter, defaultdict
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
    r"\bsign(?:s|ed)?\b|\bpass(?:es|ed)?\b|\bapprov(?:es|ed)?\b|"
    r"\brul(?:es|ed|ing)\b|\bveto\b|\bexecutive order\b|\blaw\b|"
    r"\bregulat\w+\b|\bsanction\b|\btreaty\b|\barrest\w*\b|"
    r"\bconvict\w*\b|\bsentenc\w*\b|\bdepl(?:oy|oyed)\b|\bstrike\b|"
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

def _call_claude(messages, max_tokens=4096):
    if not ANTHROPIC_API_KEY: return ""
    data = _api_call("https://api.anthropic.com/v1/messages",
        {"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
        {"model": CLAUDE_MODEL, "max_tokens": max_tokens, "messages": messages, "temperature": 0.4})
    return data["content"][0]["text"]

def _call_grok_text(messages):
    if not XAI_API_KEY: return ""
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
    if not XAI_API_KEY: return ""
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
    if not GOOGLE_API_KEY: return ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GOOGLE_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt_text}]}], "generationConfig": {"temperature": 0.3, "maxOutputTokens": 8192}}
    data = _api_call(url, {"Content-Type": "application/json"}, payload, timeout=120)
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        return ""

def _parse_json_from_text(text):
    text = text.strip()
    for match in re.finditer(r'[\[{]', text):
        try:
            start = match.start()
            opener = text[start]
            closer = ']' if opener == '[' else '}'
            depth = 0
            for i, ch in enumerate(text[start:]):
                if ch == opener: depth += 1
                elif ch == closer: depth -= 1
                if depth == 0:
                    try: return json.loads(text[start:start+i+1])
                    except: break
        except: pass
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

# ── Full Article Text Fetching ─────────────────────────────────────
def fetch_article_text(url, timeout=12):
    """Fetch and extract article body text from a URL. Returns cleaned text or empty string."""
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "ignore")
        # Strip script/style/noscript
        cleaned = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
        # Extract paragraphs
        paras = re.findall(r"(?is)<p[^>]*>(.*?)</p>", cleaned)
        texts = []
        for p in paras[:30]:
            text = re.sub(r"(?is)<[^>]+>", " ", p)
            text = html_lib.unescape(re.sub(r"\s+", " ", text)).strip()
            if len(text.split()) >= 8:
                texts.append(text)
        result = "\n\n".join(texts)
        return result[:10000] if result else ""
    except Exception:
        return ""

def enrich_group_with_full_text(group):
    """Fetch full article text for up to 3 items in a group."""
    fetched = 0
    for item in group[:3]:
        if fetched >= 3: break
        text = fetch_article_text(item["link"])
        if text and len(text) > 200:
            item["full_text"] = text
            fetched += 1
        time.sleep(0.3)
    return group

# ── Grouping: Hybrid Lexical + Entity + Union-Find ─────────────────
GENERIC_TOKENS = {
    "says", "said", "after", "over", "amid", "during", "report", "reports",
    "news", "update", "live", "latest", "announces", "announced", "new", "more",
    "people", "year", "years", "time", "first", "last", "also", "just", "like",
}

def normalize_token(t):
    t = t.lower()
    if len(t) > 4 and t.endswith("ies"): return t[:-3] + "y"
    if len(t) > 4 and t.endswith("ing"): return t[:-3]
    if len(t) > 3 and t.endswith("ed"): return t[:-2]
    if len(t) > 3 and t.endswith("s") and not t.endswith("ss"): return t[:-1]
    return t

def text_tokens(text):
    return [normalize_token(t) for t in re.findall(r"[A-Za-z0-9]+", text) if len(t) > 2]

def title_bigrams(title):
    toks = [t for t in text_tokens(title) if t not in STOP_WORDS]
    return set(zip(toks, toks[1:]))

def extract_entities(text):
    ents = set()
    for m in re.finditer(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}|[A-Z]{2,})\b", text):
        ent = m.group(0).strip()
        if len(ent) > 2: ents.add(ent.lower())
    return ents

def extract_numbers(text):
    return set(re.findall(r"\b\d+(?:\.\d+)?(?:%|bn|m|million|billion)?\b", text.lower()))

def build_features(items):
    docs = []
    df = Counter()
    for item in items:
        title = item["title"]
        desc = item.get("description", "")
        full = f"{title} {desc}"
        toks = [t for t in text_tokens(full) if t not in STOP_WORDS]
        title_toks = [t for t in text_tokens(title) if t not in STOP_WORDS]
        feats = {
            "title_tokens": set(title_toks),
            "tokens": set(toks),
            "bigrams": title_bigrams(title),
            "entities": extract_entities(desc if desc else title),
            "numbers": extract_numbers(full),
            "region": item.get("region", ""),
        }
        docs.append(feats)
        for t in feats["tokens"]: df[t] += 1
    n = max(len(items), 1)
    idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}
    return docs, idf

def weighted_jaccard(a, b, idf):
    if not a or not b: return 0.0
    inter = sum(idf.get(t, 1.0) for t in a & b)
    union = sum(idf.get(t, 1.0) for t in a | b)
    return inter / union if union else 0.0

def overlap_coeff(a, b):
    if not a or not b: return 0.0
    return len(a & b) / min(len(a), len(b))

def pair_score(fa, fb, idf):
    title_score = weighted_jaccard(fa["title_tokens"], fb["title_tokens"], idf)
    token_score = weighted_jaccard(fa["tokens"], fb["tokens"], idf)
    bigram_score = overlap_coeff(fa["bigrams"], fb["bigrams"])
    entity_score = overlap_coeff(fa["entities"], fb["entities"])
    number_score = overlap_coeff(fa["numbers"], fb["numbers"])
    shared_non_generic = (fa["title_tokens"] & fb["title_tokens"]) - GENERIC_TOKENS
    penalty = 0.12 if len(shared_non_generic) <= 1 and entity_score == 0 and number_score == 0 else 0.0
    return (0.35 * title_score + 0.25 * token_score + 0.20 * entity_score +
            0.15 * bigram_score + 0.05 * number_score - penalty)

def group_pass_1(items, threshold=0.40):
    """Hybrid lexical+entity+union-find clustering."""
    if not items: return []
    feats, idf = build_features(items)
    parent = list(range(len(items)))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[rb] = ra
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if not ((feats[i]["title_tokens"] & feats[j]["title_tokens"]) or
                    (feats[i]["entities"] & feats[j]["entities"]) or
                    (feats[i]["numbers"] & feats[j]["numbers"]) or
                    (feats[i]["bigrams"] & feats[j]["bigrams"])): continue
            if pair_score(feats[i], feats[j], idf) >= threshold:
                union(i, j)
    clusters = defaultdict(list)
    for i, item in enumerate(items): clusters[find(i)].append(item)
    groups = list(clusters.values())
    groups.sort(key=lambda g: -len(g))
    return groups

def group_pass_2_ai(groups):
    """AI-assisted merge for ambiguous near-threshold pairs. Sends richer context than before."""
    if not OPENAI_API_KEY or len(groups) < 5: return groups
    cap = min(len(groups), 80)
    summaries = []
    for i in range(cap):
        g = groups[i]
        titles = "; ".join(item["title"][:70] for item in g[:3])
        sources = ", ".join(set(item["source_name"] for item in g))
        summaries.append(f"{i+1}. [{len(g)} art from {sources}] {titles}")
    prompt = (f"Below are {len(summaries)} news story groups. Some may cover the SAME event/topic.\n"
              f"Identify groups to merge. Return ONLY a JSON array of arrays. Example: [[1,4,7],[3,9]]\n"
              f"If none should merge, return [].\n\n" + "\n".join(summaries))
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
    regions = [item["region"] for item in group]
    text = " ".join(item["title"].lower() + " " + item.get("description", "").lower()[:100] for item in group)
    if any(r == "Local" for r in regions): return "Local"
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

Return ONLY a JSON array of group numbers (up to 25). Prefix positive stories with +."""

def build_bucketed_pool_text(groups):
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
            if p.get("description"): line += f" — {p['description'][:120]}"
            if len(sources) > 1: line += f" (Also: {', '.join(sorted(sources - {p['source_name']}))})"
            lines.append(line)
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
        ("Claude", ANTHROPIC_API_KEY, lambda pt: _call_claude([{"role": "user", "content": f"{SELECTION_PROMPT}\n\n{pt}"}])),
        ("Grok", XAI_API_KEY, lambda pt: _call_grok_text([{"role": "user", "content": f"{SELECTION_PROMPT}\n\n{pt}"}])),
        ("Gemini", GOOGLE_API_KEY, lambda pt: _call_gemini(f"{SELECTION_PROMPT}\n\n{pt}")),
    ]:
        if not key: continue
        print(f"  → {name}...")
        try:
            raw = fn(pool_text)
            if not raw: print(f"    {name}: empty response"); continue
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
    print(f"\n   Consensus ({n} models): {len(consensus)} groups agreed (≥{min_v} votes)")
    if len(consensus) < MAX_ARTICLES:
        extra = sorted([s for s in votes if s not in consensus], key=lambda s: (-votes[s], ranks[s]/max(votes[s],1)))
        consensus.extend(extra[:MAX_ARTICLES - len(consensus)])
    return consensus[:MAX_ARTICLES]

# ── Evidence Extraction (Provenance-Preserving Editor Brief) ────────

EVIDENCE_PROMPT = """You are building an editor brief for a morning news briefing.
Use ONLY the supplied source material. Do not infer facts that are not explicitly supported.

Return ONLY valid JSON.

{
  "story_type": "straight_news|chronology|decision_watch|stakes_explainer|local_impact|policy_fight|breakthrough",
  "news_peg": "one sentence on what is newly important today",
  "best_angle": "one sentence on the strongest editorial angle for this story",
  "agreed_facts": [
    {"fact": "specific factual statement", "source_ids": [1, 3]}
  ],
  "contested_points": [
    {"issue": "what differs", "source_ids": [2, 4]}
  ],
  "key_numbers": [
    {"value": "exact number", "meaning": "what it refers to", "source_ids": [1]}
  ],
  "timeline": [
    {"step": "event in sequence", "source_ids": [1]}
  ],
  "stakeholders": [
    {"name": "person/group", "role": "why they matter", "position": "their stance", "source_ids": [1]}
  ],
  "quotes": [
    {"speaker": "Name", "quote": "exact words only", "source_id": 1}
  ],
  "unknowns": ["specific unanswered question"],
  "watch_next": ["specific next event, deadline, vote, or hearing"],
  "canadian_relevance": "why a Canadian reader should care",
  "category": "Local|Ontario|Canada|US|World|Health|Science|Tech",
  "is_constructive": false,
  "is_negative": false,
  "related_ongoing": ""
}

CATEGORY RULES:
- "Local" = ONLY Bay of Quinte, Belleville, Trenton, Hastings County, Prince Edward County
- "Ontario" = Toronto, Ottawa, provincial Ontario stories
- "Canada" = National Canadian stories
- "US"/"World"/"Health"/"Science"/"Tech" as appropriate

is_constructive: TRUE only for volunteer efforts, breakthroughs, milestones, community wins. FALSE for conflict/death.
related_ongoing: Match ONLY if DIRECTLY about one of: iran-conflict, ukraine-russia, us-tariffs-trade, economy-inflation, middle-east-israel-gaza, sudan-south-sudan, ai-regulation, climate-environment. Empty string if no match.

IMPORTANT: Preserve source_ids so we know which source said what. Only include a quote if the exact wording appears in the supplied material. Prefer specificity over completeness — if evidence is thin, include less."""

# ── Style Cards for Category-Aware Writing ──────────────────────────

STYLE_CARDS = {
    "Local": "Write like a trusted community voice who reads the local paper every morning. Start with the specific street, school, or person involved. Keep it warm and concrete. Avoid bureaucratic framing.",
    "Ontario": "Provincial affairs voice — clear, informed, slightly more formal than local. Start with the policy impact or the decision, not background.",
    "Canada": "Globe and Mail editorial desk voice — authoritative but accessible. Lead with national significance. Include what this means for ordinary Canadians.",
    "US": "Crisp, Axios-style analysis. Start with the political or economic consequence, not the event itself. Assume the reader knows basic US politics.",
    "World": "Economist-style global strategist. Lead with geopolitical significance. Be precise about geography and factions. No 'In a move that...'",
    "Health": "Clear medical/health communicator. Lead with what changed for patients or public health. Include specific numbers. Avoid jargon.",
    "Science": "Curious, precise explainer. Lead with the discovery or finding, not 'Researchers at...' Make it vivid.",
    "Tech": "Sharp, informed technology voice. Lead with what the technology does or changes, not the company announcement.",
}

ARTICLE_PROMPT = """You are a senior editor writing for The Daily Informant, a calm, neutral daily briefing for Canadian readers.

Write from the editor brief below. Use ONLY the facts and quotes in the brief. Do not invent detail. Do not smooth over disagreement. Do not use stock news clichés.

BANNED OPENINGS (never start an article with these):
- In a significant development
- Concerns are growing
- In a major development
- In a dramatic turn
- As tensions rise / escalate
- In the latest sign
- Amidst rising

STYLE RULES:
- Sound like a strong human editor, not a summarizer
- Vary sentence length: mix short punchy sentences with longer analytical ones
- Choose the structure that best fits the story_type from the brief
- If straight_news: lead with the news peg
- If stakes_explainer: lead with why it matters
- If decision_watch: lead with the pending decision
- If local_impact: make the local consequence concrete in the first sentence
- If breakthrough: lead with the discovery
- Never write "according to sources" — state facts directly
- When sources disagree, name the disagreement specifically

{style_card}

LENGTH: Body target 280-450 words. Go SHORTER if evidence is thin. Do not pad with filler to reach a word count.

Output ONLY valid JSON:
{{
  "bottom_line": "ONE sentence, 20-35 words, the single most important takeaway",
  "headline": "Neutral, informative, 8-12 words. No clickbait.",
  "body": "3-5 paragraphs. Structure should fit the story, not a template.",
  "why_it_matters": "1-2 sentences. Concrete real-world consequence.",
  "what_to_watch": "1-2 sentences. Specific upcoming event or unresolved trigger.",
  "key_developments": ["4-6 specific concrete facts from the brief"],
  "stakeholder_quotes": [{{ "speaker": "Name", "quote": "exact words from brief only" }}],
  "positive_thought": "A brief, heartfelt thought specific to THIS story. Mention a real person, place, or detail. Express hope for those involved. No 'God', no 'Amen'. For negative stories, focus on comfort. For positive stories, express gratitude. Be unique — never repeat the same pattern."
}}"""

EVIDENCE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "editor_brief",
        "schema": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "story_type": {"type": "string"},
                "news_peg": {"type": "string"},
                "best_angle": {"type": "string"},
                "agreed_facts": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "properties": {"fact": {"type": "string"}, "source_ids": {"type": "array", "items": {"type": "integer"}}},
                    "required": ["fact", "source_ids"]}},
                "contested_points": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "properties": {"issue": {"type": "string"}, "source_ids": {"type": "array", "items": {"type": "integer"}}},
                    "required": ["issue", "source_ids"]}},
                "key_numbers": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "properties": {"value": {"type": "string"}, "meaning": {"type": "string"}, "source_ids": {"type": "array", "items": {"type": "integer"}}},
                    "required": ["value", "meaning", "source_ids"]}},
                "timeline": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "properties": {"step": {"type": "string"}, "source_ids": {"type": "array", "items": {"type": "integer"}}},
                    "required": ["step", "source_ids"]}},
                "stakeholders": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "properties": {"name": {"type": "string"}, "role": {"type": "string"}, "position": {"type": "string"}, "source_ids": {"type": "array", "items": {"type": "integer"}}},
                    "required": ["name", "role", "position", "source_ids"]}},
                "quotes": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "properties": {"speaker": {"type": "string"}, "quote": {"type": "string"}, "source_id": {"type": "integer"}},
                    "required": ["speaker", "quote", "source_id"]}},
                "unknowns": {"type": "array", "items": {"type": "string"}},
                "watch_next": {"type": "array", "items": {"type": "string"}},
                "canadian_relevance": {"type": "string"},
                "category": {"type": "string"},
                "is_constructive": {"type": "boolean"},
                "is_negative": {"type": "boolean"},
                "related_ongoing": {"type": "string"},
            },
            "required": ["story_type", "news_peg", "best_angle", "agreed_facts", "contested_points",
                         "key_numbers", "timeline", "stakeholders", "quotes", "unknowns", "watch_next",
                         "canadian_relevance", "category", "is_constructive", "is_negative", "related_ongoing"],
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
    """Build source text with numbered IDs for provenance tracking."""
    text = ""
    for i, item in enumerate(group):
        text += f"\n--- Source {i+1} [{item['source_name']}, {item['lean']}, {item['region']}] ---\n"
        text += f"Title: {item['title']}\nPublished: {item['pub_date']}\n"
        if item.get("full_text"):
            text += f"Full Article:\n{item['full_text'][:4000]}\n"
        else:
            text += f"Description: {item['description']}\n"
        text += f"Link: {item['link']}\n"
    return text

def extract_evidence(group):
    """Pass A: Build provenance-preserving editor brief."""
    source_text = build_source_text(group)
    raw = _call_openai([{"role": "system", "content": EVIDENCE_PROMPT}, {"role": "user", "content": source_text}], EVIDENCE_SCHEMA)
    return json.loads(raw)

def write_article(evidence, source_count, source_leans, category):
    """Pass B: Write article using category-aware style card."""
    evidence_text = json.dumps(evidence, indent=2)
    context = f"This story was covered by {source_count} sources across these leanings: {', '.join(sorted(source_leans))}."
    style_card = STYLE_CARDS.get(category, STYLE_CARDS["World"])
    prompt = ARTICLE_PROMPT.replace("{style_card}", f"VOICE FOR THIS ARTICLE:\n{style_card}")
    raw = _call_openai([
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"{context}\n\nEditor Brief:\n{evidence_text}"}
    ], ARTICLE_SCHEMA)
    return json.loads(raw)

def build_di_article(group, idx, all_items, is_good_flagged=False):
    slug = f"article-{idx + 1}"
    # Build component articles with proper source tracking
    component_articles = [{"source": i["source_name"], "lean": i["lean"], "title": i["title"], "url": i["link"]} for i in group]
    source_leans = set(i["lean"] for i in group)

    try:
        # Pass A: Editor brief
        evidence = extract_evidence(group)
        category = evidence.get("category", "World").strip()
        if category not in CATEGORY_ORDER:
            category = classify_group_category(group)
        is_constructive = evidence.get("is_constructive", False) or is_good_flagged
        is_neg = evidence.get("is_negative", False)
        related = evidence.get("related_ongoing", "").strip()
        valid_slugs = {s for s, _ in ONGOING_TOPICS_PRIORITY}
        if related not in valid_slugs: related = ""
        if is_constructive and is_neg: is_constructive = False

        # Pass B: Article (with retry if too short)
        article = write_article(evidence, len(group), source_leans, category)
        body = article.get("body", "").strip()
        if len(body.split()) < 150 and len(group) > 0:
            print(f"    ↻ Retrying article (only {len(body.split())}w)...")
            time.sleep(1)
            article = write_article(evidence, len(group), source_leans, category)
            body = article.get("body", "").strip()

        headline = article.get("headline", group[0]["title"]).strip()
        bottom_line = article.get("bottom_line", "").strip()
        why_matters = article.get("why_it_matters", "").strip()
        what_watch = article.get("what_to_watch", "").strip()
        pos = article.get("positive_thought", "").strip()

        key_devs = [{"text": d.strip(), "source_url": group[0]["link"]}
                    for d in article.get("key_developments", []) if isinstance(d, str) and d.strip()]

        # Build quotes with proper provenance from evidence brief
        quotes = []
        evidence_quotes = evidence.get("quotes", [])
        article_quotes = article.get("stakeholder_quotes", [])
        for aq in article_quotes:
            if aq.get("speaker") and aq.get("quote"):
                # Try to find matching evidence quote for source attribution
                matched_url = group[0]["link"]
                for eq in evidence_quotes:
                    if eq.get("speaker") == aq["speaker"]:
                        sid = eq.get("source_id", 1)
                        if 1 <= sid <= len(group):
                            matched_url = group[sid - 1]["link"]
                        break
                quotes.append({"speaker": aq["speaker"], "quote": aq["quote"], "url": matched_url})
        # Add evidence quotes not already in article quotes
        for eq in evidence_quotes:
            if eq.get("speaker") and eq.get("quote"):
                if not any(q["speaker"] == eq["speaker"] for q in quotes):
                    sid = eq.get("source_id", 1)
                    url = group[sid - 1]["link"] if 1 <= sid <= len(group) else group[0]["link"]
                    quotes.append({"speaker": eq["speaker"], "quote": eq["quote"],
                                   "url": url, "source_outlet": group[sid - 1]["source_name"] if 1 <= sid <= len(group) else ""})

        # Build proper sources list from component articles
        sources = []
        seen_sources = set()
        for item in group:
            if item["source_name"] not in seen_sources:
                sources.append({"name": item["source_name"], "url": item["link"]})
                seen_sources.add(item["source_name"])

        tags = ""
        if is_constructive: tags += " [CONSTRUCTIVE]"
        if is_neg: tags += " [NEG]"
        if related: tags += f" [{related}]"
        word_count = len(body.split())
        ft_count = sum(1 for i in group if i.get("full_text"))
        print(f"  ✓ [{category}] \"{headline[:48]}\" ({word_count}w, {len(sources)}s, {ft_count}ft){tags}")

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
        sources = []
        seen = set()
        for item in group:
            if item["source_name"] not in seen:
                sources.append({"name": item["source_name"], "url": item["link"]}); seen.add(item["source_name"])
        return {
            "slug": slug, "headline": group[0]["title"], "bottom_line": "",
            "body": group[0].get("description", "")[:300], "why_it_matters": "", "what_to_watch": "",
            "category": classify_group_category(group),
            "key_points": [{"text": group[0].get("description", "")[:200], "source_url": group[0]["link"]}],
            "sources": sources, "component_articles": component_articles,
            "stakeholder_quotes": [], "is_good_development": False,
            "is_negative": False, "positive_thought": "", "related_ongoing": "",
        }

# ── Global Diversity / Copy-Edit Pass ──────────────────────────────

DIVERSITY_PROMPT = """You are the copy chief for The Daily Informant. Below are all articles for today's briefing.

Review the FULL set and fix these specific problems:
1. Find any two articles that start with the same word or similar phrase — rewrite the second one's opening.
2. If "significant" or "concerns" or "implications" appears more than 3 times total, replace with more precise language.
3. Ensure Local/Ontario articles sound warmer and more community-focused than World/US articles.
4. If any article's body is under 200 words and reads like a stub, flag it.
5. Check that positive_thought fields are genuinely unique — no two should follow the same pattern.

Return ONLY a JSON array of targeted fixes:
[{"article_index": 0, "field": "body", "issue": "starts same as article 3", "fix_type": "rewrite_opening", "new_opening_sentence": "replacement first sentence"},
 {"article_index": 2, "field": "positive_thought", "issue": "too similar to article 5", "replacement": "new unique thought"}]

If no fixes needed, return []. Only fix real problems. Do not rewrite articles that are already good."""

def run_diversity_pass(articles):
    """Global copy-edit pass: reads all articles at once to kill repetition."""
    # Use Gemini (big context window, cheap) or fall back to OpenAI
    batch = "\n\n".join(
        f"--- Article {i} [{a.get('category')}] ---\n"
        f"Headline: {a['headline']}\n"
        f"Body opening: {a.get('body','')[:200]}\n"
        f"Positive thought: {a.get('positive_thought','')}"
        for i, a in enumerate(articles)
    )
    prompt = f"{DIVERSITY_PROMPT}\n\n{batch}"
    try:
        if GOOGLE_API_KEY:
            raw = _call_gemini(prompt)
        elif ANTHROPIC_API_KEY:
            raw = _call_claude([{"role": "user", "content": prompt}])
        else:
            raw = _call_openai([{"role": "user", "content": prompt}])
        fixes = _parse_json_from_text(raw)
        if not isinstance(fixes, list): return articles
        applied = 0
        for fix in fixes:
            try:
                idx = fix.get("article_index", -1)
                if not (0 <= idx < len(articles)): continue
                fix_type = fix.get("fix_type", "")
                if fix_type == "rewrite_opening" and fix.get("new_opening_sentence"):
                    body = articles[idx].get("body", "")
                    # Replace first sentence
                    first_period = body.find(". ")
                    if first_period > 0:
                        articles[idx]["body"] = fix["new_opening_sentence"] + body[first_period:]
                        applied += 1
                elif fix.get("replacement") and fix.get("field") in ("positive_thought", "body", "headline"):
                    articles[idx][fix["field"]] = fix["replacement"]
                    applied += 1
            except: pass
        print(f"   Diversity pass: {applied} fixes applied")
    except Exception as e:
        print(f"   Diversity pass failed: {e}")
    return articles

# ── Bias Review (Advisory, Not Overwriting) ─────────────────────────

BIAS_PROMPT = """Review these articles for bias, sensationalism, or missing perspectives.

Return ONLY a JSON array of TARGETED corrections. Each fix should be minimal and specific:
[{"article_index": 0, "field": "headline", "issue": "loaded word 'slams'", "corrected_text": "fixed version"},
 {"article_index": 2, "field": "body", "issue": "missing right-leaning perspective", "sentence_to_add": "sentence to insert"}]

Rules:
- Only flag genuine bias or factual issues
- Headline and bottom_line fixes: provide full replacement
- Body fixes: provide a single sentence to add or a specific phrase to change
- Do NOT rewrite entire article bodies
- If nothing needs fixing, return []"""

def run_bias_review(articles):
    # Show more context than before for better review
    batch = "\n".join(
        f"--- Article {i} [{a.get('category')}] ---\n"
        f"Headline: {a['headline']}\n"
        f"Bottom Line: {a.get('bottom_line','')}\n"
        f"Body: {a.get('body','')[:500]}"
        for i, a in enumerate(articles)
    )
    total = 0
    reviewers = []
    if ANTHROPIC_API_KEY:
        reviewers.append(("Claude", lambda: _call_claude([{"role": "user", "content": f"{BIAS_PROMPT}\n\n{batch}"}])))
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
                        idx = fix.get("article_index", -1)
                        field = fix.get("field", "")
                        corrected = fix.get("corrected_text", "")
                        sentence = fix.get("sentence_to_add", "")
                        if not (0 <= idx < len(articles)): continue
                        if field in ("headline", "bottom_line") and corrected:
                            articles[idx][field] = corrected; applied += 1; total += 1
                            print(f"    {name} fixed article {idx} {field}: {fix.get('issue','')}")
                        elif field == "body" and sentence:
                            # Append sentence rather than overwrite
                            articles[idx]["body"] = articles[idx].get("body", "") + "\n\n" + sentence
                            applied += 1; total += 1
                            print(f"    {name} added to article {idx} body: {fix.get('issue','')}")
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
        topic["what_changed_today"] = []
        matched_articles = []
        for article in articles:
            text = (article["headline"] + " " + article.get("body", "")[:200]).lower()
            if sum(1 for e in entities if e in text) >= 2:
                if article.get("related_ongoing", "") and article["related_ongoing"] != slug: continue
                matched_articles.append(article)
        if not matched_articles: continue
        existing_dates = {e["date"] for e in topic.get("timeline", [])}
        if today not in existing_dates:
            best = max(matched_articles, key=lambda a: len(a.get("component_articles", [])))
            cat = "military"
            body_lower = (best.get("body", "") + " " + best["headline"]).lower()
            if any(w in body_lower for w in ["diplomat", "talks", "negotiat", "summit", "mediator", "ceasefire"]): cat = "diplomatic"
            elif any(w in body_lower for w in ["humanitarian", "refugee", "displaced", "aid", "famine"]): cat = "humanitarian"
            elif any(w in body_lower for w in ["price", "market", "trade", "tariff", "economic", "oil", "jobs"]): cat = "economic"
            elif any(w in body_lower for w in ["court", "legal", "ruling", "lawsuit", "judge"]): cat = "legal"
            elif any(w in body_lower for w in ["election", "parliament", "vote", "legislation", "policy"]): cat = "political"
            topic.setdefault("timeline", []).insert(0, {
                "date": today, "text": best["headline"], "category": cat,
                "source_url": best["sources"][0]["url"] if best.get("sources") else "#"
            })
            topic["timeline"] = topic["timeline"][:30]
        for art in matched_articles[:3]:
            change = art.get("bottom_line", "") or art["headline"]
            if change and change not in topic["what_changed_today"]:
                topic["what_changed_today"].append(change)
        topic["last_material_update"] = now_iso
        print(f"  → Updated \"{topic['topic']}\" ({len(matched_articles)} articles, {len(topic['what_changed_today'])} changes)")
    return topics_data

# ── Main ────────────────────────────────────────────────────────────
def main():
    today = datetime.now(TORONTO).strftime("%Y-%m-%d")
    print("=" * 65)
    print("  The Daily Informant — Morning Pipeline v10")
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

    print("\n─── Step 3: Hybrid grouping ───")
    groups = group_pass_1(filtered)
    print(f"   Pass 1 (lexical+entity+union-find): {len(groups)} groups")
    for g in groups[:5]: print(f"    [{len(g)} art] {g[0]['title'][:60]}")
    groups = group_pass_2_ai(groups)
    print(f"   Final groups: {len(groups)}")

    print("\n─── Step 4: Multi-AI story selection ───")
    pool_text = build_bucketed_pool_text(groups)
    selections, good_indices = run_selection(pool_text)
    consensus_indices = build_consensus(selections, len(groups)) if selections else list(range(1, min(MAX_ARTICLES+1, len(groups)+1)))
    consensus_groups = [groups[i-1] for i in consensus_indices if 1 <= i <= len(groups)]
    print(f"\n   Final: {len(consensus_groups)} DI articles")

    print("\n─── Step 5: Full text enrichment ───")
    ft_total = 0
    for i, group in enumerate(consensus_groups):
        group = enrich_group_with_full_text(group)
        consensus_groups[i] = group
        ft_count = sum(1 for item in group if item.get("full_text"))
        ft_total += ft_count
        if ft_count: print(f"   Group {i+1}: {ft_count}/{len(group)} articles enriched")
    print(f"   Total full-text articles: {ft_total}")

    print("\n─── Step 6: Article generation (editor brief → writing) ───")
    articles = []
    for i, group in enumerate(consensus_groups):
        idx = consensus_indices[i] if i < len(consensus_indices) else 0
        articles.append(build_di_article(group, i, all_items, idx in good_indices))
        if i < len(consensus_groups) - 1: time.sleep(0.5)

    print("\n─── Step 6b: Global diversity pass ───")
    articles = run_diversity_pass(articles)

    print("\n─── Step 6c: Bias review ───")
    articles = run_bias_review(articles)

    print("\n─── Step 6d: X/Twitter quotes ───")
    articles = fetch_x_quotes(articles)

    # Separate
    regular, good_devs = [], []
    for a in articles:
        (good_devs if a.get("is_good_development") else regular).append(a)
    regular.sort(key=lambda a: CATEGORY_ORDER.index(a.get("category","World")) if a.get("category","World") in CATEGORY_ORDER else 99)

    print(f"\n   Regular: {len(regular)} | Constructive: {len(good_devs)}")
    cats = {}
    for a in articles: cats[a.get("category","?")] = cats.get(a.get("category","?"), 0) + 1
    print(f"   Category breakdown: {dict(sorted(cats.items()))}")

    print("\n─── Step 7: Archive & ongoing ───")
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
        "optional_reflection": "",
        "_meta": {
            "pipeline_version": "10.0", "models_used": list(selections.keys()) if selections else [],
            "feeds_attempted": len(FEEDS), "raw_items": len(all_items),
            "groups_formed": len(groups), "consensus_articles": len(consensus_groups),
            "full_text_enriched": ft_total,
            "good_developments": len(good_devs), "category_breakdown": cats,
            "category_order": CATEGORY_ORDER,
        },
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n{'='*65}")
    print(f"  DONE — {len(articles)} DI articles → data/daily.json")
    print(f"  Models: {', '.join(selections.keys()) if selections else 'fallback'}")
    print(f"  Categories: {dict(sorted(cats.items()))}")
    print(f"  Sources: {sum(len(a.get('sources',[])) for a in articles)} | Full-text: {ft_total}")
    print(f"  Avg words/article: {sum(len(a.get('body','').split()) for a in articles)//max(len(articles),1)}")
    print(f"  Negative: {sum(1 for a in articles if a.get('is_negative'))} | Constructive: {len(good_devs)} | Ongoing: {sum(1 for a in articles if a.get('related_ongoing'))}")
    print(f"{'='*65}")

if __name__ == "__main__":
    main()
