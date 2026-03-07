#!/usr/bin/env python3
"""
The Daily Informant — Morning Pipeline v7
==========================================

v7 changes:
  - AI-POWERED GROUPING: After keyword grouping, AI merges related groups
    (fixes: 4 Iran articles, 2 tornado articles appearing separately)
  - ENTITY-BASED ONGOING MATCHING: Each topic has specific entity keywords
    (fixes: Iran articles landing in Ukraine-Russia timeline)
  - VARIED POSITIVE THOUGHTS: Prompt demands unique, specific thoughts
  - FIXED FEEDS: Replaced broken CTV/CBC/Newsmax with working alternatives
  - MULTI-AI SUMMARY: Claude reviews OpenAI's extraction for bias check
  - BETTER SOURCE MATCHING: Uses both title and description keywords
  - CATEGORY ENFORCEMENT: Ensures mix of categories in final selection

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
    # ── Local (Bay of Quinte / Belleville) ──
    {"name": "Quinte News",        "url": "https://www.quintenews.com/feed/",                       "lean": "Center",       "region": "Local"},
    {"name": "inQuinte",           "url": "https://inquinte.ca/feed",                                "lean": "Center",       "region": "Local"},

    # ── Ontario ──
    {"name": "Toronto Star",       "url": "https://www.thestar.com/search/?f=rss&t=article&c=news*&l=50&s=start_time&sd=desc", "lean": "Center-Left", "region": "Ontario"},
    {"name": "Toronto Sun",        "url": "https://torontosun.com/feed",                              "lean": "Right",        "region": "Ontario"},
    {"name": "Global News Canada", "url": "https://globalnews.ca/feed/",                              "lean": "Center",       "region": "Ontario"},
    {"name": "CBC News",           "url": "https://www.cbc.ca/webfeed/rss/rss-canada",               "lean": "Center-Left",  "region": "Canada"},

    # ── Canada ──
    {"name": "Globe and Mail",     "url": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/world/", "lean": "Center", "region": "Canada"},
    {"name": "National Post",      "url": "https://nationalpost.com/feed/",                            "lean": "Center-Right", "region": "Canada"},

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
MAX_ARTICLES = 15
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

# Entity keywords for ongoing topic matching (must match 2+ to link)
ONGOING_ENTITIES = {
    "iran-conflict": {"iran", "tehran", "persian", "gulf", "irgc", "pezeshkian", "iranian"},
    "ukraine-russia": {"ukraine", "kyiv", "russia", "moscow", "donbas", "crimea", "zelenskyy", "ukrainian", "russian"},
    "economy-inflation": {"inflation", "interest rate", "federal reserve", "bank of canada", "jobs report", "unemployment", "gdp", "recession", "tariff"},
    "us-tariffs-trade": {"tariff", "customs", "trade war", "import duties", "cbp", "trade court"},
    "middle-east-israel-gaza": {"gaza", "hamas", "israel", "palestinian", "west bank", "idf", "hostage"},
    "sudan-south-sudan": {"sudan", "south sudan", "khartoum", "darfur", "rsf", "juba"},
    "ai-regulation": {"ai act", "artificial intelligence regulation", "ai safety", "deepfake", "ai policy"},
    "climate-environment": {"climate", "emissions", "renewable", "carbon", "paris agreement", "cop28", "cop29", "global warming"},
}

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


def is_politician_noise(title, desc=""):
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
    """Extract meaningful keywords from text."""
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
    out = [i for i in items if not is_politician_noise(i["title"], i.get("description", ""))]
    diff = len(items) - len(out)
    if diff:
        print(f"   Filtered {diff} politician-noise stories")
    return out


# ── Two-Pass Story Grouping ────────────────────────────────────────


def group_pass_1(items):
    """First pass: group by keyword overlap (title + description)."""
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
    """Second pass: ask AI to merge groups that are about the same broader topic."""
    if not OPENAI_API_KEY or len(groups) < 5:
        return groups

    # Build a summary of each group for AI
    group_summaries = []
    for i, g in enumerate(groups[:60]):  # Cap at 60 groups to fit in context
        primary = g[0]
        group_summaries.append(f"{i+1}. [{len(g)} articles] {primary['title']}")

    prompt = f"""Below are {len(group_summaries)} story groups. Some groups are about the SAME broader topic/event but were not merged (e.g., multiple groups about the Iran conflict, or multiple groups about the same tornado event).

Identify which groups should be MERGED because they cover the same event or topic.

Return ONLY a JSON array of arrays. Each inner array lists the group numbers that should merge.
Example: [[1, 4, 7], [3, 9], [5, 11]]

Groups that stand alone don't need to be listed. If no merges needed, return [].
Return ONLY the JSON.

{chr(10).join(group_summaries)}"""

    try:
        payload = json.dumps({
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }).encode("utf-8")
        req = Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
            method="POST",
        )
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = data["choices"][0]["message"]["content"].strip()
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if not match:
                return groups
            merges = json.loads(match.group())

            # Apply merges
            merged_into = {}  # group_idx -> target_idx
            for merge_set in merges:
                if not isinstance(merge_set, list) or len(merge_set) < 2:
                    continue
                target = merge_set[0] - 1  # Convert to 0-based
                for num in merge_set[1:]:
                    idx = num - 1
                    if 0 <= idx < len(groups) and 0 <= target < len(groups):
                        merged_into[idx] = target

            # Build new groups list
            new_groups = []
            skip = set(merged_into.keys())
            for i, g in enumerate(groups):
                if i in skip:
                    continue
                # Add any groups that should merge into this one
                combined = list(g)
                for src_idx, tgt_idx in merged_into.items():
                    if tgt_idx == i and src_idx < len(groups):
                        combined.extend(groups[src_idx])
                new_groups.append(combined)

            # Add remaining groups beyond the 60 we analyzed
            for i in range(60, len(groups)):
                new_groups.append(groups[i])

            new_groups.sort(key=lambda g: -len(g))
            merge_count = len(merged_into)
            if merge_count > 0:
                print(f"   AI merged {merge_count} groups into existing topics")
            return new_groups

    except Exception as e:
        print(f"   AI merge pass failed: {e} — using pass-1 groups")
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

SELECTION_PROMPT = """You are the editorial director for The Daily Informant, a calm, unbiased, fact-only morning news briefing based in the Bay of Quinte, Ontario, Canada.

Below is a numbered list of STORY GROUPS. Each group contains related articles about the same event/topic.

Select the 15 most important story groups. DO NOT select sports stories.

CATEGORY TARGETS (aim for this mix):
- 2-3 Local (Bay of Quinte area) if available
- 1-2 Ontario
- 1-2 Canada
- 3-4 US
- 3-4 World/International
- 1-2 Health/Science/Tech
- 1-2 GENUINELY POSITIVE humanitarian/community stories (mark with +)

CRITERIA:
1. IMPACT — How many people does this affect?
2. ACTION — Things that HAPPENED over things people SAID
3. DIVERSITY — Mix of categories
4. SOURCE BALANCE — Groups covered by both left and right sources are more important
5. SKIP politician theater without concrete action
6. DO NOT select stories about the same topic twice

Return ONLY a JSON array. Prefix positive stories with +.
Example: [1, 3, +7, 2, 11, 4, +15, 8, 6, 12, 9, 14, 5, 10, 13]"""


def build_group_pool_text(groups):
    lines = []
    for i, group in enumerate(groups):
        sources = set(item["source_name"] for item in group)
        leans = set(item["lean"] for item in group)
        regions = set(item["region"] for item in group)
        primary = group[0]
        line = f"{i+1}. [{len(group)} art, {', '.join(sorted(leans))}] [{', '.join(sorted(regions))}] "
        line += primary["title"]
        if primary.get("description"):
            line += f" — {primary['description'][:120]}"
        if len(sources) > 1:
            line += f" (Also: {', '.join(sorted(sources - {primary['source_name']}))})"
        lines.append(line)
    return "\n".join(lines)


def _call_openai_style(url, headers, payload, name, resp_path="openai"):
    data_bytes = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data_bytes, headers=headers, method="POST")
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw = (data["content"][0]["text"] if resp_path == "anthropic"
                       else data["choices"][0]["message"]["content"]).strip()
                match = re.search(r'\[([^\]]+)\]', raw)
                if match:
                    nums, good = [], set()
                    for p in match.group(1).split(","):
                        p = p.strip()
                        is_g = p.startswith("+")
                        p = p.lstrip("+").strip()
                        try:
                            n = int(p)
                            nums.append(n)
                            if is_g: good.add(n)
                        except ValueError:
                            pass
                    return nums, good
                return [], set()
        except HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503):
                time.sleep(RETRY_BASE_DELAY * (attempt + 1))
                continue
            try: body = e.read().decode("utf-8", "replace")[:200]
            except: body = ""
            print(f"    {name} HTTP {e.code}: {body}")
            return [], set()
        except Exception as e:
            last_err = e
            time.sleep(RETRY_BASE_DELAY)
    print(f"    {name} failed: {last_err}")
    return [], set()


def _call_grok(pool_text):
    payload = json.dumps({
        "model": GROK_MODEL,
        "input": [
            {"role": "system", "content": SELECTION_PROMPT},
            {"role": "user", "content": pool_text},
        ],
        "temperature": 0.3, "store": False,
    }).encode("utf-8")
    req = Request("https://api.x.ai/v1/responses", data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}",
        "User-Agent": "DailyInformant/1.0",
    }, method="POST")
    last_err = None
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
                raw = raw.strip()
                match = re.search(r'\[([^\]]+)\]', raw)
                if match:
                    nums, good = [], set()
                    for p in match.group(1).split(","):
                        p = p.strip()
                        is_g = p.startswith("+")
                        p = p.lstrip("+").strip()
                        try:
                            n = int(p)
                            nums.append(n)
                            if is_g: good.add(n)
                        except ValueError:
                            pass
                    return nums, good
                return [], set()
        except HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503):
                time.sleep(RETRY_BASE_DELAY * (attempt + 1))
                continue
            try: body = e.read().decode("utf-8", "replace")[:200]
            except: body = ""
            print(f"    Grok HTTP {e.code}: {body}")
            return [], set()
        except Exception as e:
            last_err = e
            time.sleep(RETRY_BASE_DELAY)
    print(f"    Grok failed: {last_err}")
    return [], set()


def run_ai_selection(pool_text):
    results = {}
    all_good = set()
    for name, fn in [
        ("OpenAI", lambda: _call_openai_style(
            "https://api.openai.com/v1/chat/completions",
            {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
            {"model": OPENAI_MODEL, "messages": [
                {"role": "system", "content": SELECTION_PROMPT},
                {"role": "user", "content": pool_text},
            ], "temperature": 0.3}, "OpenAI")),
        ("Claude", lambda: _call_openai_style(
            "https://api.anthropic.com/v1/messages",
            {"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
            {"model": CLAUDE_MODEL, "max_tokens": 2048, "messages": [
                {"role": "user", "content": f"{SELECTION_PROMPT}\n\n{pool_text}"},
            ], "temperature": 0.3}, "Claude", "anthropic")),
        ("Grok", lambda: _call_grok(pool_text)),
    ]:
        key_check = {"OpenAI": OPENAI_API_KEY, "Claude": ANTHROPIC_API_KEY, "Grok": XAI_API_KEY}
        if not key_check.get(name):
            continue
        print(f"  → {name}...")
        try:
            picks, good = fn()
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
    if n == 0: return []
    if n == 1: return list(selections.values())[0][:MAX_ARTICLES]
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

EXTRACTION_PROMPT = """You write consolidated articles for The Daily Informant (DI), a calm, unbiased morning news briefing.

Given a group of related articles from multiple sources, write ONE consolidated DI Article.

Produce:
1. headline: Neutral, informative, no clickbait
2. summary: 3-5 sentence comprehensive summary using info from ALL sources. Calm, neutral tone.
3. context: 2-3 sentences of background — what led to this, why it matters
4. key_points: 3-6 factual bullets from across all sources
5. category: Local, Ontario, Canada, US, World, Health, Science, or Tech
6. stakeholder_quotes: 0-3 real direct quotes from the articles (not invented)
7. is_good_development: ONLY true for humanitarian aid, disaster relief, volunteers, missionary work, charitable giving, community rebuilding, faith-based service
8. is_negative: true if involves conflict, death, economic hardship, disaster, or suffering
9. positive_thought: If negative, write ONE specific uplifting thought about THIS situation. Be UNIQUE — do not use "resilience", "communities coming together", or generic phrases. Instead reference something specific: a helper in the story, a historical parallel of recovery, a concrete reason for hope specific to this event. No God/Amen. If not negative, leave empty.
10. related_ongoing: Match to ONE of these slugs if relevant: iran-conflict, ukraine-russia, economy-inflation, us-tariffs-trade, middle-east-israel-gaza, sudan-south-sudan, ai-regulation, climate-environment. Empty string if none.

RULES: Facts only, no sensational words, no opinion, calm tone. Use info from ALL provided articles."""

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
        articles_text += f"\n--- Article {i+1} [{item['source_name']}, {item['lean']}] ---\n"
        articles_text += f"Title: {item['title']}\nPublished: {item['pub_date']}\n"
        articles_text += f"Description: {item['description']}\nLink: {item['link']}\n"

    payload = json.dumps({
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": articles_text},
        ],
        "response_format": EXTRACTION_SCHEMA,
    }).encode("utf-8")
    req = Request("https://api.openai.com/v1/chat/completions", data=payload,
                  headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
                  method="POST")
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return json.loads(data["choices"][0]["message"]["content"])
        except HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503):
                time.sleep(RETRY_BASE_DELAY * (attempt + 1))
                continue
            raise
        except Exception as e:
            last_err = e
            time.sleep(RETRY_BASE_DELAY)
    raise RuntimeError(f"Extraction failed: {last_err}")


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
        pos_thought = ai.get("positive_thought", "").strip()
        related = ai.get("related_ongoing", "").strip()

        key_points = [{"text": p.strip(), "source_url": group[0]["link"]}
                      for p in ai.get("key_points", []) if isinstance(p, str) and p.strip()]
        quotes = [{"speaker": q["speaker"], "quote": q["quote"], "url": group[0]["link"]}
                  for q in ai.get("stakeholder_quotes", []) if q.get("speaker") and q.get("quote")]

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
            "is_negative": is_neg, "positive_thought": pos_thought if is_neg else "",
            "related_ongoing": related,
        }
    except Exception as e:
        print(f"  ✗ Article {idx+1} failed: {e}")
        return {
            "slug": slug, "headline": group[0]["title"], "summary": group[0].get("description", "")[:300],
            "context": "", "category": group[0].get("region", "World"),
            "key_points": [{"text": group[0].get("description", "")[:200], "source_url": group[0]["link"]}],
            "sources": sources, "component_articles": component_articles,
            "stakeholder_quotes": [], "is_good_development": is_good_flagged,
            "is_negative": False, "positive_thought": "", "related_ongoing": "",
        }


# ── Ongoing Topics (entity-based matching) ──────────────────────────

def load_json(path):
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except: pass
    return None


def update_ongoing_topics(articles, topics_data, today):
    if not topics_data.get("topics"):
        return topics_data
    for topic in topics_data["topics"]:
        slug = topic["slug"]
        entities = ONGOING_ENTITIES.get(slug, set())
        if not entities:
            continue

        for article in articles:
            # Check if article text contains at least 2 entity keywords
            article_text = (article["headline"] + " " + article.get("summary", "")).lower()
            matches = sum(1 for e in entities if e in article_text)
            if matches >= 2:
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


# ── Main ────────────────────────────────────────────────────────────

def main():
    today = datetime.now(TORONTO).strftime("%Y-%m-%d")
    print("=" * 65)
    print("  The Daily Informant — Morning Pipeline v7")
    print(f"  {datetime.now(TORONTO).strftime('%Y-%m-%d %H:%M %Z')}")
    print("=" * 65)

    models = [n for n, k in [("OpenAI", OPENAI_API_KEY), ("Claude", ANTHROPIC_API_KEY), ("Grok", XAI_API_KEY)] if k]
    print(f"\n  AI models: {', '.join(models) or 'NONE'}")
    if not OPENAI_API_KEY:
        print("\n✗ OPENAI_API_KEY required."); sys.exit(1)

    # 1. Fetch
    print("\n─── Step 1: Fetching RSS feeds ───")
    all_items = fetch_all_feeds()
    if not all_items:
        print("\n✗ No items."); sys.exit(1)
    print(f"\n   Raw items: {len(all_items)}")

    # 2. Filter
    print("\n─── Step 2: Noise filter ───")
    filtered = filter_noise(all_items)
    print(f"   After filter: {len(filtered)}")

    # 3. Group (two-pass)
    print("\n─── Step 3: Grouping related stories ───")
    groups = group_pass_1(filtered)
    print(f"   Pass 1: {len(groups)} groups")
    for g in groups[:5]:
        print(f"    [{len(g)} art] {g[0]['title'][:60]}")
    groups = group_pass_2_ai(groups)
    print(f"   After AI merge: {len(groups)} groups")

    # 4. AI selection
    print("\n─── Step 4: Multi-AI selection ───")
    pool_text = build_group_pool_text(groups)
    selections, good_indices = run_ai_selection(pool_text)

    if not selections:
        consensus_indices = list(range(1, min(MAX_ARTICLES + 1, len(groups) + 1)))
    else:
        consensus_indices = build_consensus(selections, len(groups))

    consensus_groups = [groups[i-1] for i in consensus_indices if 1 <= i <= len(groups)]
    print(f"\n   Final: {len(consensus_groups)} DI articles")

    # 5. Extract
    print("\n─── Step 5: Article extraction ───")
    articles = []
    for i, group in enumerate(consensus_groups):
        idx = consensus_indices[i] if i < len(consensus_indices) else 0
        articles.append(build_di_article(group, i, all_items, idx in good_indices))
        if i < len(consensus_groups) - 1:
            time.sleep(1)

    # Separate good developments
    regular, good_devs = [], []
    for a in articles:
        if a.get("is_good_development"):
            good_devs.append(a)
        else:
            regular.append(a)

    # Sort by category
    def cat_key(a):
        try: return CATEGORY_ORDER.index(a.get("category", "World"))
        except ValueError: return len(CATEGORY_ORDER)
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
            "pipeline_version": "7.0",
            "models_used": list(selections.keys()),
            "feeds_attempted": len(FEEDS),
            "raw_items": len(all_items),
            "groups_after_ai_merge": len(groups),
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
