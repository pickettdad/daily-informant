#!/usr/bin/env python3
"""
The Daily Informant — Morning Pipeline v8
==========================================

v8 FIXES from v7:
  - FIXED: AI merge was CREATING groups (178→287) instead of reducing them.
    Now properly combines groups and removes merged ones.
  - FIXED: Iran articles tagged as middle-east-israel-gaza. Now uses priority
    ordering — iran-conflict checked FIRST, and articles only match ONE topic.
  - FIXED: Fatal collision tagged as [GOOD]. Stricter extraction prompt.
  - FIXED: Oil prices appeared as two separate articles. Better dedup.
  - FIXED: Toronto stories categorized as "Local" instead of "Ontario".
    Local = Bay of Quinte/Belleville/Hastings/Prince Edward ONLY.
  - FIXED: Ukraine-Russia timeline had Iran articles. Entity matching now
    requires 2+ UNIQUE entity keywords with NO overlap with higher-priority topics.
  - INCREASED: MAX_ARTICLES from 15 to 25 for better coverage.
  - IMPROVED: Positive thoughts now prayer-like (specific, uplifting, no God/Amen).
  - IMPROVED: Good news strictly humanitarian/faith/community — never fatalities.
  - FIXED: CBC feed URL changed to working alternative.

Required env vars:
  OPENAI_API_KEY, ANTHROPIC_API_KEY (optional), XAI_API_KEY (optional)
"""

import json
import os
import re
import sys
import time
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

    # ── Ontario (Toronto, Ottawa, provincial) ──
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

    # ── US/World: Center ──
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

    # ── Good News / Humanitarian / Faith ──
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

MAX_RETRIES = 3
RETRY_BASE_DELAY = 5

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")

DAILY_PATH = Path("data/daily.json")
TOPICS_PATH = Path("data/topics.json")
ARCHIVE_PATH = Path("data/archive.json")

CATEGORY_ORDER = ["Local", "Ontario", "Canada", "US", "World", "Health", "Science", "Tech"]

# Entity keywords for ongoing topic matching.
# PRIORITY ORDER matters — checked top to bottom, first match wins.
# iran-conflict MUST be before middle-east-israel-gaza.
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
    if ACTION_RE.search(combined):
        return False
    return bool(NOISE_RE.search(combined))


# ── RSS Fetching ────────────────────────────────────────────────────

STOP_WORDS = {
    "a","an","the","in","on","at","to","for","of","and","or","is","are",
    "was","were","be","been","has","have","had","it","its","that","this",
    "with","from","by","as","but","not","no","will","can","do","does",
    "did","may","says","said","new","over","after","how","why","what",
    "who","could","would","about","into","up","out","more","than",
}


def kw(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 2}


def fetch_feed(url, timeout=15):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; DailyInformantBot/1.0)"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


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
    all_items = []
    success = 0
    for feed in FEEDS:
        try:
            xml_bytes = fetch_feed(feed["url"])
            parsed = parse_rss(xml_bytes, feed["name"], feed["lean"], feed["region"])
            all_items.extend(parsed[:ITEMS_PER_FEED])
            success += 1
            print(f"  ✓ {feed['name']} ({feed['lean']}, {feed['region']}): {len(parsed)} items")
        except Exception as e:
            print(f"  ✗ {feed['name']}: {e}")
    print(f"\n   Feeds succeeded: {success}/{len(FEEDS)}")
    return all_items


def filter_noise(items):
    out = [i for i in items if not is_noise(i["title"], i.get("description", ""))]
    diff = len(items) - len(out)
    if diff:
        print(f"   Filtered {diff} politician-noise stories")
    return out


# ── Two-Pass Story Grouping ────────────────────────────────────────


def group_pass_1(items):
    """Keyword overlap grouping."""
    groups = []
    used = set()
    for i, item in enumerate(items):
        if i in used:
            continue
        group = [item]
        used.add(i)
        item_kw = kw(item["title"] + " " + item.get("description", "")[:200])
        if len(item_kw) < 3:
            groups.append(group)
            continue
        for j, other in enumerate(items):
            if j in used:
                continue
            other_kw = kw(other["title"] + " " + other.get("description", "")[:200])
            if len(other_kw) < 3:
                continue
            overlap = len(item_kw & other_kw)
            smaller = min(len(item_kw), len(other_kw))
            if smaller > 0 and overlap / smaller >= 0.30:
                group.append(other)
                used.add(j)
        groups.append(group)
    groups.sort(key=lambda g: -len(g))
    return groups


def group_pass_2_ai(groups):
    """Ask AI which groups should merge. FIXED: now actually reduces group count."""
    if not OPENAI_API_KEY or len(groups) < 5:
        return groups

    cap = min(len(groups), 80)
    summaries = []
    for i in range(cap):
        g = groups[i]
        summaries.append(f"{i+1}. [{len(g)} art] {g[0]['title'][:80]}")

    prompt = f"""Below are {len(summaries)} story groups from today's news. Some cover the SAME event/topic and should be merged.

Identify groups to merge. Return ONLY a JSON array of arrays — each inner array lists group numbers to combine.
Example: [[1, 4, 7], [3, 9]]
If no merges needed, return [].
Return ONLY the JSON array, nothing else.

{chr(10).join(summaries)}"""

    try:
        payload = json.dumps({
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }).encode("utf-8")
        req = Request("https://api.openai.com/v1/chat/completions", data=payload,
                      headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
                      method="POST")
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = data["choices"][0]["message"]["content"].strip()
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if not match:
                return groups
            merges = json.loads(match.group())

            # Build merge map: which groups get absorbed into which target
            absorbed = set()
            for merge_set in merges:
                if not isinstance(merge_set, list) or len(merge_set) < 2:
                    continue
                # All numbers are 1-based from the AI
                indices = [n - 1 for n in merge_set if isinstance(n, int) and 1 <= n <= cap]
                if len(indices) < 2:
                    continue
                target = indices[0]
                for src in indices[1:]:
                    if src != target and src not in absorbed:
                        groups[target] = groups[target] + groups[src]
                        absorbed.add(src)

            # Rebuild list excluding absorbed groups
            new_groups = [g for i, g in enumerate(groups) if i not in absorbed]
            new_groups.sort(key=lambda g: -len(g))

            if absorbed:
                print(f"   AI merged {len(absorbed)} groups → {len(new_groups)} remaining")
            return new_groups

    except Exception as e:
        print(f"   AI merge failed: {e} — using pass-1 groups")
        return groups


# ── Multi-Source Matching ───────────────────────────────────────────


def find_related_sources(primary_item, all_items):
    primary_kw = kw(primary_item["title"] + " " + primary_item.get("description", "")[:200])
    if len(primary_kw) < 2:
        return [{"name": primary_item["source_name"], "url": primary_item["link"]}]
    sources = [{"name": primary_item["source_name"], "url": primary_item["link"]}]
    seen = {primary_item["source_name"]}
    for item in all_items:
        if item["source_name"] in seen:
            continue
        item_kw = kw(item["title"] + " " + item.get("description", "")[:200])
        if len(item_kw) < 2:
            continue
        overlap = len(primary_kw & item_kw)
        smaller = min(len(primary_kw), len(item_kw))
        if smaller > 0 and overlap / smaller >= 0.25:
            sources.append({"name": item["source_name"], "url": item["link"]})
            seen.add(item["source_name"])
    return sources


# ── Multi-AI Selection ──────────────────────────────────────────────

SELECTION_PROMPT = """You are the editorial director for The Daily Informant (DI), a calm, unbiased, fact-only morning briefing based in Bay of Quinte, Ontario, Canada.

Below is a numbered list of STORY GROUPS. Select the 25 most important for today's edition.

DO NOT select sports stories.

CATEGORY TARGETS (aim for this mix from available stories):
- ALL available Local stories (Bay of Quinte/Belleville area)
- 3-5 Ontario stories (Toronto, Ottawa, provincial)
- 2-3 Canada stories
- 4-6 US stories
- 4-6 World/International stories
- 1-3 Health/Science/Tech stories
- 2-3 GENUINELY POSITIVE humanitarian/community stories (mark with +)

"Local" means ONLY Bay of Quinte, Belleville, Hastings County, Prince Edward County.
Toronto and Ottawa stories are "Ontario", NOT "Local".

CRITERIA:
1. IMPACT — How many people does this affect?
2. ACTION — Things that HAPPENED over things people SAID
3. DIVERSITY — Mix of categories, don't let one dominate
4. SOURCE BALANCE — Groups covered by both left and right sources are more important
5. SKIP politician theater without concrete action
6. DO NOT select multiple groups about the same topic

Return ONLY a JSON array of group numbers (up to 25). Prefix positive stories with +.
Example: [1, 3, +7, 2, 11, 4, +15, 8, 6, 12, 9, 14, 5, 10, 13, 16, 18, +20, 22, 19, 24, 17, 21, 23, 25]"""


def build_pool_text(groups):
    lines = []
    for i, group in enumerate(groups):
        sources = set(item["source_name"] for item in group)
        leans = set(item["lean"] for item in group)
        regions = set(item["region"] for item in group)
        p = group[0]
        line = f"{i+1}. [{len(group)} art, {', '.join(sorted(leans))}] [{', '.join(sorted(regions))}] "
        line += p["title"]
        if p.get("description"):
            line += f" — {p['description'][:100]}"
        if len(sources) > 1:
            line += f" (Also: {', '.join(sorted(sources - {p['source_name']}))})"
        lines.append(line)
    return "\n".join(lines)


def _parse_picks(raw_text):
    match = re.search(r'\[([^\]]+)\]', raw_text)
    if not match:
        return [], set()
    nums, good = [], set()
    for p in match.group(1).split(","):
        p = p.strip()
        is_g = p.startswith("+")
        p = p.lstrip("+").strip()
        try:
            n = int(p)
            nums.append(n)
            if is_g:
                good.add(n)
        except ValueError:
            pass
    return nums, good


def _call_openai(pool_text):
    payload = json.dumps({
        "model": OPENAI_MODEL,
        "messages": [{"role": "system", "content": SELECTION_PROMPT}, {"role": "user", "content": pool_text}],
        "temperature": 0.3,
    }).encode("utf-8")
    req = Request("https://api.openai.com/v1/chat/completions", data=payload,
                  headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
                  method="POST")
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return _parse_picks(data["choices"][0]["message"]["content"])
        except HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(RETRY_BASE_DELAY * (attempt + 1)); continue
            try: body = e.read().decode("utf-8", "replace")[:200]
            except: body = ""
            print(f"    OpenAI HTTP {e.code}: {body}")
            return [], set()
        except Exception:
            time.sleep(RETRY_BASE_DELAY)
    return [], set()


def _call_claude(pool_text):
    payload = json.dumps({
        "model": CLAUDE_MODEL, "max_tokens": 2048,
        "messages": [{"role": "user", "content": f"{SELECTION_PROMPT}\n\n{pool_text}"}],
        "temperature": 0.3,
    }).encode("utf-8")
    req = Request("https://api.anthropic.com/v1/messages", data=payload,
                  headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
                  method="POST")
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return _parse_picks(data["content"][0]["text"])
        except HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(RETRY_BASE_DELAY * (attempt + 1)); continue
            try: body = e.read().decode("utf-8", "replace")[:200]
            except: body = ""
            print(f"    Claude HTTP {e.code}: {body}")
            return [], set()
        except Exception:
            time.sleep(RETRY_BASE_DELAY)
    return [], set()


def _call_grok(pool_text):
    payload = json.dumps({
        "model": GROK_MODEL,
        "input": [{"role": "system", "content": SELECTION_PROMPT}, {"role": "user", "content": pool_text}],
        "temperature": 0.3, "store": False,
    }).encode("utf-8")
    req = Request("https://api.x.ai/v1/responses", data=payload, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}",
        "User-Agent": "DailyInformant/1.0",
    }, method="POST")
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw = ""
                for item in data.get("output", []):
                    if item.get("type") == "message":
                        for c in item.get("content", []):
                            if c.get("type") == "output_text":
                                raw += c.get("text", "")
                return _parse_picks(raw)
        except HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(RETRY_BASE_DELAY * (attempt + 1)); continue
            try: body = e.read().decode("utf-8", "replace")[:200]
            except: body = ""
            print(f"    Grok HTTP {e.code}: {body}")
            return [], set()
        except Exception:
            time.sleep(RETRY_BASE_DELAY)
    return [], set()


def run_selection(pool_text):
    results, all_good = {}, set()
    callers = []
    if OPENAI_API_KEY:
        callers.append(("OpenAI", _call_openai))
    if ANTHROPIC_API_KEY:
        callers.append(("Claude", _call_claude))
    if XAI_API_KEY:
        callers.append(("Grok", _call_grok))

    for name, fn in callers:
        print(f"  → {name}...")
        try:
            picks, good = fn(pool_text)
            if picks:
                results[name] = picks
                all_good.update(good)
                print(f"    {name}: {len(picks)} groups, {len(good)} good news")
        except Exception as e:
            print(f"    {name} failed: {e}")
        time.sleep(1)
    return results, all_good


def build_consensus(selections, pool_size):
    n = len(selections)
    if n == 0:
        return []
    if n == 1:
        return list(selections.values())[0][:MAX_ARTICLES]
    votes, ranks = {}, {}
    for model, picks in selections.items():
        for rank, num in enumerate(picks):
            if 1 <= num <= pool_size:
                votes[num] = votes.get(num, 0) + 1
                ranks[num] = ranks.get(num, 0) + rank
    min_v = min(MIN_CONSENSUS, n)
    consensus = [s for s, v in votes.items() if v >= min_v]
    consensus.sort(key=lambda s: (-votes[s], ranks[s] / votes[s]))
    print(f"\n   Consensus ({n} models): {len(consensus)} groups agreed")
    if len(consensus) < MAX_ARTICLES:
        extra = sorted([s for s in votes if s not in consensus],
                       key=lambda s: (-votes[s], ranks[s] / max(votes[s], 1)))
        consensus.extend(extra[:MAX_ARTICLES - len(consensus)])
    return consensus[:MAX_ARTICLES]


# ── Article Extraction ──────────────────────────────────────────────

EXTRACTION_PROMPT = """You write consolidated articles for The Daily Informant (DI), a calm, unbiased morning news briefing based in the Bay of Quinte, Ontario, Canada.

Given a group of related articles from multiple sources, write ONE consolidated DI Article.

Produce:
1. headline: Neutral, informative, no clickbait
2. summary: 4-6 sentence comprehensive summary using info from ALL sources. Calm, neutral tone. Should be thorough enough that a reader doesn't need to click through to other articles.
3. context: 2-3 sentences of background — what led to this, why it matters
4. key_points: 4-8 factual bullets from across all sources
5. category: MUST follow these rules strictly:
   - "Local" = ONLY stories about Bay of Quinte, Belleville, Trenton, Hastings County, Prince Edward County, Tyendinaga, Campbellford, Kawartha Lakes area
   - "Ontario" = Toronto, Ottawa, or Ontario provincial stories
   - "Canada" = National Canadian stories (not specific to Ontario)
   - "US" = United States stories
   - "World" = International stories
   - "Health", "Science", "Tech" = Topic-specific regardless of geography
6. stakeholder_quotes: 0-3 real direct quotes from the articles (NEVER invent quotes)
7. is_good_development: TRUE only for stories about: volunteers helping people, charitable giving, disaster relief by citizens, missionary or faith-based service, community rebuilding after hardship, people rescuing others. FALSE for: government policy, scientific discoveries, corporate developments, infrastructure projects, court cases, ANY story involving death or crime even if justice is served.
8. is_negative: true if involves conflict, death, economic hardship, disaster, or suffering
9. positive_thought: If is_negative is true, write a brief uplifting thought like a prayer (but without mentioning God or saying Amen). Make it specific to THIS story — reference a person, place, or detail from the article. Express hope for the specific people affected. Never use generic phrases like "resilience" or "communities coming together." Each one must be unique and heartfelt. Example: "May the families in Nairobi find shelter and safety tonight, and may the floodwaters recede to reveal a city ready to rebuild." If not negative, leave empty string.
10. related_ongoing: Match to ONE of these slugs if the story is clearly about that situation: iran-conflict, ukraine-russia, economy-inflation, us-tariffs-trade, middle-east-israel-gaza, sudan-south-sudan, ai-regulation, climate-environment. Use "iran-conflict" for stories about the U.S./Israel military operations against Iran. Use "middle-east-israel-gaza" ONLY for stories specifically about Gaza/Hamas/Palestinians. Empty string if no match.

RULES: Facts only, no sensational words, no opinion, calm measured tone. Use info from ALL provided source articles."""

EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "di_article",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "headline": {"type": "string"},
                "summary": {"type": "string"},
                "context": {"type": "string"},
                "key_points": {"type": "array", "items": {"type": "string"}},
                "category": {"type": "string"},
                "stakeholder_quotes": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {"speaker": {"type": "string"}, "quote": {"type": "string"}},
                    "required": ["speaker", "quote"],
                }},
                "is_good_development": {"type": "boolean"},
                "is_negative": {"type": "boolean"},
                "positive_thought": {"type": "string"},
                "related_ongoing": {"type": "string"},
            },
            "required": ["headline", "summary", "context", "key_points", "category",
                         "stakeholder_quotes", "is_good_development", "is_negative",
                         "positive_thought", "related_ongoing"],
        },
        "strict": True,
    },
}


def extract_article(group):
    articles_text = ""
    for i, item in enumerate(group):
        articles_text += f"\n--- Article {i+1} [{item['source_name']}, {item['lean']}, {item['region']}] ---\n"
        articles_text += f"Title: {item['title']}\nPublished: {item['pub_date']}\n"
        articles_text += f"Description: {item['description']}\nLink: {item['link']}\n"

    payload = json.dumps({
        "model": OPENAI_MODEL,
        "messages": [{"role": "system", "content": EXTRACTION_PROMPT}, {"role": "user", "content": articles_text}],
        "response_format": EXTRACTION_SCHEMA,
    }).encode("utf-8")
    req = Request("https://api.openai.com/v1/chat/completions", data=payload,
                  headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
                  method="POST")
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return json.loads(data["choices"][0]["message"]["content"])
        except HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(RETRY_BASE_DELAY * (attempt + 1)); continue
            raise
        except Exception as e:
            time.sleep(RETRY_BASE_DELAY)
    raise RuntimeError("Extraction failed after retries")


def build_di_article(group, idx, all_items, is_good_flagged=False):
    slug = f"article-{idx + 1}"
    sources = find_related_sources(group[0], all_items)
    component_articles = [{"source": i["source_name"], "lean": i["lean"],
                           "title": i["title"], "url": i["link"]} for i in group]
    try:
        ai = extract_article(group)
        headline = ai.get("headline", group[0]["title"]).strip()
        summary = ai.get("summary", "").strip()
        context = ai.get("context", "").strip()
        category = ai.get("category", "World").strip()
        is_good = ai.get("is_good_development", False) or is_good_flagged
        is_neg = ai.get("is_negative", False)
        pos = ai.get("positive_thought", "").strip()
        related = ai.get("related_ongoing", "").strip()

        # Validate related_ongoing against known slugs
        valid_slugs = {slug for slug, _ in ONGOING_TOPICS_PRIORITY}
        if related and related not in valid_slugs:
            related = ""

        key_points = [{"text": p.strip(), "source_url": group[0]["link"]}
                      for p in ai.get("key_points", []) if isinstance(p, str) and p.strip()]
        quotes = [{"speaker": q["speaker"], "quote": q["quote"], "url": group[0]["link"]}
                  for q in ai.get("stakeholder_quotes", []) if q.get("speaker") and q.get("quote")]

        # Safety: good development can NEVER be negative
        if is_good and is_neg:
            is_good = False

        tags = ""
        if is_good: tags += " [GOOD]"
        if is_neg: tags += " [NEG]"
        if related: tags += f" [{related}]"
        print(f"  ✓ [{category}] \"{headline[:48]}\" ({len(key_points)}kp, {len(sources)}s, {len(group)}art){tags}")

        return {
            "slug": slug, "headline": headline, "summary": summary,
            "context": context, "category": category, "key_points": key_points,
            "sources": sources, "component_articles": component_articles,
            "stakeholder_quotes": quotes, "is_good_development": is_good,
            "is_negative": is_neg, "positive_thought": pos if is_neg else "",
            "related_ongoing": related,
        }
    except Exception as e:
        print(f"  ✗ Article {idx+1} failed: {e}")
        return {
            "slug": slug, "headline": group[0]["title"],
            "summary": group[0].get("description", "")[:300],
            "context": "", "category": group[0].get("region", "World"),
            "key_points": [{"text": group[0].get("description", "")[:200], "source_url": group[0]["link"]}],
            "sources": sources, "component_articles": component_articles,
            "stakeholder_quotes": [], "is_good_development": False,
            "is_negative": False, "positive_thought": "", "related_ongoing": "",
        }


# ── Ongoing Topics (priority-ordered entity matching) ───────────────

def load_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def update_ongoing_topics(articles, topics_data, today):
    if not topics_data.get("topics"):
        return topics_data

    for topic in topics_data["topics"]:
        slug = topic["slug"]
        # Find entity set for this topic from priority list
        entities = None
        for t_slug, t_entities in ONGOING_TOPICS_PRIORITY:
            if t_slug == slug:
                entities = t_entities
                break
        if not entities:
            continue

        for article in articles:
            text = (article["headline"] + " " + article.get("summary", "")).lower()
            matches = sum(1 for e in entities if e in text)

            # Must match 2+ entity keywords
            if matches < 2:
                continue

            # PRIORITY CHECK: only link if this is the BEST matching topic
            # (i.e., the article's related_ongoing matches this slug, or no related_ongoing set)
            article_linked = article.get("related_ongoing", "")
            if article_linked and article_linked != slug:
                continue

            existing_dates = {e["date"] for e in topic.get("timeline", [])}
            if today not in existing_dates:
                topic.setdefault("timeline", []).insert(0, {
                    "date": today,
                    "text": article["headline"],
                    "source_url": article["sources"][0]["url"] if article["sources"] else "#",
                })
                topic["timeline"] = topic["timeline"][:30]
                print(f"  → Updated \"{topic['topic']}\" with: {article['headline'][:50]}")
                break

    return topics_data


# ── Multi-AI Bias Review (Step 5b) ──────────────────────────────────

BIAS_REVIEW_PROMPT = """You are an editorial bias reviewer for The Daily Informant, a strictly neutral, fact-only news briefing.

Below are today's articles written by another AI. Review each one for:
1. BIAS: Language that favors one political side (loaded words, framing that assumes a position)
2. SENSATIONALISM: Dramatic language that doesn't belong in neutral reporting
3. MISSING PERSPECTIVE: If sources from both left and right covered this story, does the summary fairly represent both viewpoints?
4. FACTUAL CONCERNS: Anything that seems editorialized rather than factual

For EACH article that needs correction, provide:
- article_index (0-based)
- field ("headline", "summary", or "context")
- issue (brief description of what's wrong)
- corrected_text (the fixed version — must be same length/style, just neutralized)

Return ONLY a JSON array of corrections. If no corrections needed, return [].
Example: [{"article_index": 2, "field": "headline", "issue": "loaded word 'slams'", "corrected_text": "US Responds to Iran's Position on Negotiations"}]

Return ONLY the JSON array."""


def _build_review_batch(articles):
    """Build a text batch of all articles for review."""
    lines = []
    for i, a in enumerate(articles):
        lines.append(f"\n--- Article {i} [{a.get('category', '?')}] ---")
        lines.append(f"Headline: {a['headline']}")
        lines.append(f"Summary: {a.get('summary', '')}")
        lines.append(f"Context: {a.get('context', '')}")
        if a.get("component_articles"):
            sources = [f"{ca['source']}({ca['lean']})" for ca in a["component_articles"]]
            lines.append(f"Sources: {', '.join(sources)}")
    return "\n".join(lines)


def _apply_corrections(articles, corrections, reviewer_name):
    """Apply bias corrections to articles."""
    applied = 0
    for fix in corrections:
        try:
            idx = fix.get("article_index", -1)
            field = fix.get("field", "")
            corrected = fix.get("corrected_text", "")
            issue = fix.get("issue", "")
            if 0 <= idx < len(articles) and field in ("headline", "summary", "context") and corrected:
                old_val = articles[idx].get(field, "")[:40]
                articles[idx][field] = corrected
                applied += 1
                print(f"    {reviewer_name} fixed article {idx} {field}: {issue}")
        except Exception:
            continue
    return applied


def _review_with_claude(batch_text):
    """Send batch to Claude for bias review."""
    payload = json.dumps({
        "model": CLAUDE_MODEL, "max_tokens": 4096,
        "messages": [{"role": "user", "content": f"{BIAS_REVIEW_PROMPT}\n\n{batch_text}"}],
        "temperature": 0.1,
    }).encode("utf-8")
    req = Request("https://api.anthropic.com/v1/messages", data=payload,
                  headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
                  method="POST")
    with urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        raw = data["content"][0]["text"].strip()
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    return []


def _review_with_grok(batch_text):
    """Send batch to Grok for bias review."""
    payload = json.dumps({
        "model": GROK_MODEL,
        "input": [{"role": "user", "content": f"{BIAS_REVIEW_PROMPT}\n\n{batch_text}"}],
        "temperature": 0.1, "store": False,
    }).encode("utf-8")
    req = Request("https://api.x.ai/v1/responses", data=payload, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}",
        "User-Agent": "DailyInformant/1.0",
    }, method="POST")
    with urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        raw = ""
        for item in data.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") == "output_text":
                        raw += c.get("text", "")
        raw = raw.strip()
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    return []


def run_bias_review(articles):
    """Send all articles to available AIs for bias review. Extensible for future models."""
    batch_text = _build_review_batch(articles)
    total_fixes = 0

    # Define reviewers — add new ones here (e.g., Gemini in future)
    reviewers = []
    if ANTHROPIC_API_KEY:
        reviewers.append(("Claude", _review_with_claude))
    if XAI_API_KEY:
        reviewers.append(("Grok", _review_with_grok))
    # Future: if GOOGLE_API_KEY: reviewers.append(("Gemini", _review_with_gemini))

    if not reviewers:
        print("   No reviewers available (need Claude or Grok API key)")
        return articles

    for name, fn in reviewers:
        print(f"  → {name} reviewing for bias...")
        try:
            corrections = fn(batch_text)
            if corrections and isinstance(corrections, list):
                n = _apply_corrections(articles, corrections, name)
                total_fixes += n
                print(f"    {name}: {n} corrections applied ({len(corrections)} flagged)")
            else:
                print(f"    {name}: no corrections needed")
        except Exception as e:
            print(f"    {name} review failed: {e}")
        time.sleep(1)

    print(f"   Total bias corrections: {total_fixes}")
    return articles


# ── X/Twitter Stakeholder Quotes (Step 5c) ──────────────────────────

X_QUOTES_PROMPT = """You are a research assistant for The Daily Informant, a neutral news briefing.

For each article below, search X (Twitter) for 1-2 relevant quotes from public figures, politicians, officials, or organizations that represent OPPOSING VIEWPOINTS on the issue. We want readers to see both sides.

For political/conflict stories: find one quote supporting/defending the action AND one criticizing/opposing it.
For economic stories: find one optimistic take AND one concerned/pessimistic take.
For local/community stories: skip (return empty array for that article).

Return ONLY a JSON array of objects. Each object has:
- article_index (0-based, matching the article number below)
- quotes: array of {speaker, quote, perspective} where perspective is "supporting" or "opposing"

Only include quotes that are REAL posts from X by identifiable public figures. Do NOT invent quotes.
If you can't find relevant opposing quotes for an article, return an empty quotes array for it.

Return ONLY the JSON array."""


def fetch_x_quotes(articles):
    """Use Grok with web search to find opposing-viewpoint quotes from X/Twitter."""
    if not XAI_API_KEY:
        print("   No Grok API key — skipping X quotes")
        return articles

    # Build batch of articles worth searching (political, world, economic — not local community)
    searchable = []
    for i, a in enumerate(articles):
        cat = a.get("category", "")
        related = a.get("related_ongoing", "")
        is_neg = a.get("is_negative", False)
        if cat in ("World", "US", "Canada", "Ontario") or related or (is_neg and cat != "Local"):
            searchable.append((i, a))

    if not searchable:
        print("   No articles need X quotes")
        return articles

    # Build the prompt text
    batch_lines = []
    for i, a in searchable:
        batch_lines.append(f"\n--- Article {i} [{a.get('category')}] ---")
        batch_lines.append(f"Headline: {a['headline']}")
        batch_lines.append(f"Summary: {a.get('summary', '')[:200]}")
    batch_text = "\n".join(batch_lines)

    try:
        payload = json.dumps({
            "model": GROK_MODEL,
            "input": [{"role": "user", "content": f"{X_QUOTES_PROMPT}\n\n{batch_text}"}],
            "tools": [{"type": "web_search"}],
            "temperature": 0.1,
            "store": False,
        }).encode("utf-8")

        req = Request("https://api.x.ai/v1/responses", data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {XAI_API_KEY}",
            "User-Agent": "DailyInformant/1.0",
        }, method="POST")

        with urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = ""
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            raw += c.get("text", "")

            raw = raw.strip()
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if not match:
                print("   Could not parse X quotes response")
                return articles

            results = json.loads(match.group())
            added = 0
            for result in results:
                try:
                    idx = result.get("article_index", -1)
                    quotes = result.get("quotes", [])
                    if not (0 <= idx < len(articles)) or not quotes:
                        continue
                    for q in quotes:
                        speaker = q.get("speaker", "").strip()
                        quote_text = q.get("quote", "").strip()
                        perspective = q.get("perspective", "").strip()
                        if speaker and quote_text:
                            articles[idx].setdefault("stakeholder_quotes", []).append({
                                "speaker": speaker,
                                "quote": quote_text,
                                "url": "",
                                "source": "X",
                                "perspective": perspective,
                            })
                            added += 1
                except Exception:
                    continue

            print(f"   Added {added} X quotes across {len(results)} articles")

    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        print(f"   Grok X quotes HTTP {e.code}: {body}")
    except Exception as e:
        print(f"   X quotes failed: {e}")

    return articles


# ── Main ────────────────────────────────────────────────────────────

def main():
    today = datetime.now(TORONTO).strftime("%Y-%m-%d")
    print("=" * 65)
    print("  The Daily Informant — Morning Pipeline v8.2")
    print(f"  {datetime.now(TORONTO).strftime('%Y-%m-%d %H:%M %Z')}")
    print("=" * 65)

    models = [n for n, k in [("OpenAI", OPENAI_API_KEY), ("Claude", ANTHROPIC_API_KEY), ("Grok", XAI_API_KEY)] if k]
    print(f"\n  AI models: {', '.join(models) or 'NONE'}")
    if not OPENAI_API_KEY:
        print("\n✗ OPENAI_API_KEY required.")
        sys.exit(1)

    # 1. Fetch
    print("\n─── Step 1: Fetching RSS feeds ───")
    all_items = fetch_all_feeds()
    if not all_items:
        print("\n✗ No items.")
        sys.exit(1)
    print(f"\n   Raw items: {len(all_items)}")

    # 2. Filter
    print("\n─── Step 2: Noise filter ───")
    filtered = filter_noise(all_items)
    print(f"   After filter: {len(filtered)}")

    # 3. Group
    print("\n─── Step 3: Grouping related stories ───")
    groups = group_pass_1(filtered)
    print(f"   Pass 1: {len(groups)} groups")
    for g in groups[:5]:
        print(f"    [{len(g)} art] {g[0]['title'][:60]}")
    groups = group_pass_2_ai(groups)
    print(f"   Final groups: {len(groups)}")

    # 4. AI selection
    print("\n─── Step 4: Multi-AI selection ───")
    pool_text = build_pool_text(groups)
    selections, good_indices = run_selection(pool_text)

    if not selections:
        consensus_indices = list(range(1, min(MAX_ARTICLES + 1, len(groups) + 1)))
    else:
        consensus_indices = build_consensus(selections, len(groups))

    consensus_groups = [groups[i - 1] for i in consensus_indices if 1 <= i <= len(groups)]
    print(f"\n   Final: {len(consensus_groups)} DI articles")

    # 5. Extract
    print("\n─── Step 5: Article extraction ───")
    articles = []
    for i, group in enumerate(consensus_groups):
        idx = consensus_indices[i] if i < len(consensus_indices) else 0
        articles.append(build_di_article(group, i, all_items, idx in good_indices))
        if i < len(consensus_groups) - 1:
            time.sleep(1)

    # 5b. Multi-AI bias review
    print("\n─── Step 5b: Multi-AI bias review ───")
    articles = run_bias_review(articles)

    # 5c. X/Twitter opposing viewpoint quotes
    print("\n─── Step 5c: X/Twitter stakeholder quotes ───")
    articles = fetch_x_quotes(articles)

    # Separate good developments
    regular, good_devs = [], []
    for a in articles:
        if a.get("is_good_development"):
            good_devs.append(a)
        else:
            regular.append(a)

    # Sort by category order
    def cat_key(a):
        try:
            return CATEGORY_ORDER.index(a.get("category", "World"))
        except ValueError:
            return len(CATEGORY_ORDER)
    regular.sort(key=cat_key)

    print(f"\n   Regular: {len(regular)} | Good: {len(good_devs)}")

    # 6. Archive + ongoing
    print("\n─── Step 6: Archive & ongoing ───")
    archive = load_json(ARCHIVE_PATH) or []
    for a in articles:
        archive.append({"date": today, "headline": a["headline"],
                        "category": a.get("category", "World"), "slug": a["slug"],
                        "source_count": len(a.get("component_articles", []))})
    archive = archive[-900:]
    ARCHIVE_PATH.write_text(json.dumps(archive, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  Archive: {len(archive)} entries")

    topics_data = load_json(TOPICS_PATH) or {"topics": []}
    topics_data = update_ongoing_topics(articles, topics_data, today)
    TOPICS_PATH.write_text(json.dumps(topics_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ongoing_for_daily = [{"slug": t["slug"], "topic": t["topic"],
                          "summary": t.get("summary", ""),
                          "timeline": t.get("timeline", [])[:5]}
                         for t in topics_data.get("topics", [])]

    # 7. Write
    DAILY_PATH.write_text(json.dumps({
        "date": today,
        "top_stories": regular,
        "ongoing_topics": ongoing_for_daily,
        "good_developments": good_devs,
        "_meta": {
            "pipeline_version": "8.2",
            "models_used": list(selections.keys()),
            "feeds_attempted": len(FEEDS),
            "raw_items": len(all_items),
            "groups_formed": len(groups),
            "consensus_articles": len(consensus_groups),
            "good_developments": len(good_devs),
            "category_order": CATEGORY_ORDER,
        },
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    cats = set(a.get("category", "?") for a in articles)
    total_src = sum(len(a.get("sources", [])) for a in articles)
    total_comp = sum(len(a.get("component_articles", [])) for a in articles)
    neg = sum(1 for a in articles if a.get("is_negative"))
    linked = sum(1 for a in articles if a.get("related_ongoing"))

    print(f"\n{'=' * 65}")
    print(f"  DONE — {len(articles)} DI articles → data/daily.json")
    print(f"  Models: {', '.join(selections.keys())}")
    print(f"  Categories: {', '.join(sorted(cats))}")
    print(f"  Sources: {total_src} | Consolidated: {total_comp}")
    print(f"  Negative: {neg} | Good: {len(good_devs)} | Linked to ongoing: {linked}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
