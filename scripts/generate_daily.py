#!/usr/bin/env python3
"""
The Daily Informant — Morning Pipeline v5
==========================================

v5 changes:
  - 25+ stories across categories (up from 10)
  - Stakeholder quotes extracted automatically
  - Good news stories auto-detected and separated
  - Source matching threshold lowered to 0.30
  - Sports feeds added (ESPN, BBC Sport)
  - AI selection prompt updated for more stories + category diversity
  - Category targets: World, US, Canada, Business, Science, Health, Tech, Sports

Required env vars:
  OPENAI_API_KEY      — OpenAI API key (required)
  ANTHROPIC_API_KEY   — Anthropic (Claude) API key  (optional)
  XAI_API_KEY         — xAI (Grok) API key          (optional)
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
    # ── Left-leaning ──
    {"name": "NPR News",           "url": "https://feeds.npr.org/1001/rss.xml",                    "lean": "Left"},
    {"name": "NPR World",          "url": "https://feeds.npr.org/1004/rss.xml",                    "lean": "Left"},
    {"name": "NPR Science",        "url": "https://feeds.npr.org/1007/rss.xml",                    "lean": "Left"},
    {"name": "NPR Health",         "url": "https://feeds.npr.org/1128/rss.xml",                    "lean": "Left"},
    {"name": "The Guardian World",  "url": "https://www.theguardian.com/world/rss",                 "lean": "Left"},
    {"name": "The Guardian US",    "url": "https://www.theguardian.com/us-news/rss",                "lean": "Left"},
    {"name": "PBS NewsHour",       "url": "https://www.pbs.org/newshour/feeds/rss/headlines",       "lean": "Left"},

    # ── Center / International ──
    {"name": "BBC World",          "url": "https://feeds.bbci.co.uk/news/world/rss.xml",            "lean": "Center"},
    {"name": "BBC Business",       "url": "https://feeds.bbci.co.uk/news/business/rss.xml",         "lean": "Center"},
    {"name": "BBC Science",        "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "lean": "Center"},
    {"name": "BBC Health",         "url": "https://feeds.bbci.co.uk/news/health/rss.xml",           "lean": "Center"},
    {"name": "BBC Tech",           "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",       "lean": "Center"},
    {"name": "Al Jazeera",         "url": "https://www.aljazeera.com/xml/rss/all.xml",              "lean": "Center"},
    {"name": "France 24",          "url": "https://www.france24.com/en/rss",                        "lean": "Center"},
    {"name": "ABC News",           "url": "https://abcnews.go.com/abcnews/topstories",             "lean": "Center"},
    {"name": "CBS News",           "url": "https://www.cbsnews.com/latest/rss/main",                "lean": "Center"},

    # ── Center-right ──
    {"name": "The Hill",           "url": "https://thehill.com/feed/",                               "lean": "Center-Right"},
    {"name": "RealClearPolitics",  "url": "https://www.realclearpolitics.com/index.xml",            "lean": "Center-Right"},

    # ── Right-leaning ──
    {"name": "Fox News",           "url": "https://moxie.foxnews.com/google-publisher/latest.xml",  "lean": "Right"},
    {"name": "NY Post",            "url": "https://nypost.com/feed/",                                "lean": "Right"},
    {"name": "Daily Wire",         "url": "https://www.dailywire.com/feeds/rss.xml",                "lean": "Right"},
    {"name": "Breitbart",          "url": "https://feeds.feedburner.com/breitbart",                 "lean": "Right"},
    {"name": "Washington Examiner", "url": "https://www.washingtonexaminer.com/feed",               "lean": "Right"},

    # ── Canada ──
    {"name": "Globe and Mail",     "url": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/world/", "lean": "Center"},
    {"name": "National Post",      "url": "https://nationalpost.com/feed/",                          "lean": "Center-Right"},
    {"name": "Toronto Star",       "url": "https://www.thestar.com/search/?f=rss&t=article&c=news*&l=50&s=start_time&sd=desc", "lean": "Center-Left"},

    # ── Science / Tech ──
    {"name": "Ars Technica",       "url": "https://feeds.arstechnica.com/arstechnica/index",        "lean": "Center"},
    {"name": "Phys.org",           "url": "https://phys.org/rss-feed/",                              "lean": "Center"},

    # ── Sports ──
    {"name": "ESPN Top",           "url": "https://www.espn.com/espn/rss/news",                     "lean": "Center"},
    {"name": "BBC Sport",          "url": "https://feeds.bbci.co.uk/sport/rss.xml",                 "lean": "Center"},
    {"name": "TSN",                "url": "https://www.tsn.ca/rss/all",                              "lean": "Center"},

    # ── Good News / Humanitarian / Faith ──
    {"name": "Good News Network",  "url": "https://www.goodnewsnetwork.org/feed/",                "lean": "Center"},
    {"name": "Positive News",      "url": "https://www.positive.news/feed/",                       "lean": "Center"},
    {"name": "Christianity Today", "url": "https://www.christianitytoday.com/feed/",               "lean": "Center"},
    {"name": "Deseret News Faith", "url": "https://www.deseret.com/arc/outboundfeeds/rss/category/faith/", "lean": "Center"},
    {"name": "Catholic News",      "url": "https://www.ncronline.org/feeds/all",                   "lean": "Center"},
    {"name": "Salvation Army",     "url": "https://www.salvationarmy.org/ihq/feed",                "lean": "Center"},
]

ITEMS_PER_FEED = 6
MAX_STORIES = 25
MIN_CONSENSUS = 2

OPENAI_MODEL = "gpt-4o-mini"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
GROK_MODEL = "grok-4-fast-non-reasoning"

MAX_RETRIES = 3
RETRY_BASE_DELAY = 5

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")

DAILY_PATH = Path("data/daily.json")
TOPICS_PATH = Path("data/topics.json")
ARCHIVE_PATH = Path("data/archive.json")

# ── Noise Filter ───────────────────────────────────────────────────

NOISE_PATTERNS = [
    r"\bslam[s]?\b", r"\bblast[s]?\b", r"\bclap[s]? back\b",
    r"\bfires back\b", r"\bgoes (off|viral)\b", r"\bspar[s]?\b",
    r"\boutrage[d]?\b", r"\bbacklash\b", r"\bcalls out\b",
    r"\bdoubles down\b", r"\bmocks?\b", r"\brant[s]?\b",
    r"\bfeud\b", r"\bsparks controversy\b", r"\btrending\b",
    r"\bshocking\b", r"\bexplosive\b", r"\bbombshell\b",
]

ACTION_INDICATORS = [
    r"\bsign[s|ed]?\b", r"\bpass(es|ed)?\b", r"\bapprov(es|ed)?\b",
    r"\brul(es|ed|ing)\b", r"\bveto(es|ed)?\b", r"\bexecutive order\b",
    r"\blaw\b", r"\bregulat(e|ion|ory)\b", r"\bsanction[s]?\b",
    r"\btreaty\b", r"\barrest(s|ed)?\b", r"\bconvict(s|ed|ion)?\b",
    r"\bsentenc(e|ed|ing)\b", r"\bdepl(oy|oyed|oyment)\b",
    r"\bstrike[s]?\b", r"\bbudget\b", r"\brate\b", r"\breport(s|ed)?\b",
    r"\blaunch(es|ed)?\b", r"\bdiscover(y|ed|ies)?\b",
    r"\bvaccine\b", r"\belection\b", r"\bresign(s|ed|ation)?\b",
    r"\bappoint(s|ed|ment)?\b",
]

NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.IGNORECASE)
ACTION_RE = re.compile("|".join(ACTION_INDICATORS), re.IGNORECASE)


def is_politician_noise(title, description=""):
    combined = f"{title} {description}"
    if ACTION_RE.search(combined):
        return False
    return bool(NOISE_RE.search(combined))


# ── RSS Fetching ────────────────────────────────────────────────────

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "is", "are", "was", "were", "be", "been", "has", "have", "had",
    "it", "its", "that", "this", "with", "from", "by", "as", "but",
    "not", "no", "will", "can", "do", "does", "did", "may", "says",
    "said", "new", "over", "after", "how", "why", "what", "who",
    "could", "would", "about", "into", "up", "out", "more", "than",
}


def extract_key_words(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 2}


def fetch_feed(url, timeout=15):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; DailyInformantBot/1.0)"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_rss(xml_bytes, source_name, lean):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall(".//channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = re.sub(r"<[^>]+>", "", (item.findtext("description") or "")).strip()
        if title and link:
            items.append({"source_name": source_name, "lean": lean, "title": title,
                          "link": link, "pub_date": pub_date, "description": description[:400]})
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "").strip() if link_el is not None else ""
        pub_date = (entry.findtext("atom:updated", namespaces=ns) or "").strip()
        description = re.sub(r"<[^>]+>", "", (entry.findtext("atom:summary", namespaces=ns) or "")).strip()
        if title and link:
            items.append({"source_name": source_name, "lean": lean, "title": title,
                          "link": link, "pub_date": pub_date, "description": description[:400]})
    return items


def fetch_all_feeds():
    all_items = []
    success = 0
    for feed in FEEDS:
        try:
            xml_bytes = fetch_feed(feed["url"])
            parsed = parse_rss(xml_bytes, feed["name"], feed["lean"])
            all_items.extend(parsed[:ITEMS_PER_FEED])
            success += 1
            print(f"  ✓ {feed['name']} ({feed['lean']}): {len(parsed)} items")
        except Exception as e:
            print(f"  ✗ {feed['name']}: {e}")
    print(f"\n   Feeds succeeded: {success}/{len(FEEDS)}")
    return all_items


def deduplicate(items):
    seen_links = set()
    accepted = []
    accepted_kw = []
    for item in items:
        if item["link"] in seen_links:
            continue
        kw = extract_key_words(item["title"])
        if len(kw) < 2:
            accepted.append(item)
            seen_links.add(item["link"])
            accepted_kw.append(kw)
            continue
        is_dup = False
        for prev in accepted_kw:
            if len(prev) < 2:
                continue
            overlap = len(kw & prev)
            smaller = min(len(kw), len(prev))
            if smaller > 0 and overlap / smaller >= 0.5:
                is_dup = True
                break
        if not is_dup:
            accepted.append(item)
            seen_links.add(item["link"])
            accepted_kw.append(kw)
    return accepted


def filter_noise(items):
    filtered = []
    n = 0
    for item in items:
        if is_politician_noise(item["title"], item.get("description", "")):
            n += 1
        else:
            filtered.append(item)
    if n:
        print(f"   Filtered {n} politician-noise stories")
    return filtered


# ── Multi-Source Matching ───────────────────────────────────────────


def find_related_sources(primary_item, all_items):
    primary_kw = extract_key_words(primary_item["title"])
    if len(primary_kw) < 2:
        return [{"name": primary_item["source_name"], "url": primary_item["link"]}]
    sources = [{"name": primary_item["source_name"], "url": primary_item["link"]}]
    seen = {primary_item["source_name"]}
    for item in all_items:
        if item["source_name"] in seen:
            continue
        item_kw = extract_key_words(item["title"])
        if len(item_kw) < 2:
            continue
        overlap = len(primary_kw & item_kw)
        smaller = min(len(primary_kw), len(item_kw))
        if smaller > 0 and overlap / smaller >= 0.30:
            sources.append({"name": item["source_name"], "url": item["link"]})
            seen.add(item["source_name"])
    return sources


# ── Multi-AI Story Selection ────────────────────────────────────────

SELECTION_PROMPT = """You are an editorial director for The Daily Informant, a calm, unbiased, fact-only morning news briefing.

Below is a numbered list of today's stories from sources across the political spectrum.

YOUR JOB: Select the 25 most important stories for an informed reader's morning briefing.

CATEGORY TARGETS (aim for this mix):
- 6-8 World/International stories
- 4-6 US domestic stories
- 3-4 Canada stories
- 3-4 Business/Economy stories
- 2-3 Science/Health/Tech stories
- 2-3 Sports stories
- 2-3 stories that are GENUINELY POSITIVE (medical breakthroughs, peace progress, scientific discoveries, community wins) — mark these by adding a + before the number

SELECTION CRITERIA:
1. IMPACT — How many people does this actually affect?
2. ACTION — Prefer stories about things that HAPPENED over things people SAID
3. DIVERSITY — Cover multiple categories, don't let one dominate
4. BALANCE — Don't favor stories from any political lean
5. SKIP politician theater without concrete action
6. SKIP celebrity/entertainment unless it has genuine policy implications
7. DO NOT select multiple stories about the same event — pick the best one

Return ONLY a JSON array of the story numbers. For positive/good-news stories, prefix with + sign.
Example: [4, 17, +2, 31, 8, +22, 11, 45, 3, 29, 14, 38, 7, 55, 19, 62, +33, 41, 26, 50, 12, 48, 9, 36, 15]

Return ONLY the JSON array, nothing else."""


def build_story_pool_text(items):
    lines = []
    for i, item in enumerate(items):
        line = f"{i+1}. [{item['source_name']}] {item['title']}"
        if item.get("description"):
            line += f" — {item['description'][:150]}"
        lines.append(line)
    return "\n".join(lines)


def _call_api(url, headers, payload, model_name, response_path="openai"):
    data_bytes = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data_bytes, headers=headers, method="POST")
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if response_path == "anthropic":
                    raw_text = data["content"][0]["text"]
                else:
                    raw_text = data["choices"][0]["message"]["content"]
                raw_text = raw_text.strip()
                # Parse the array, handling + prefixed numbers for good news
                match = re.search(r'\[([^\]]+)\]', raw_text)
                if match:
                    inner = match.group(1)
                    numbers = []
                    good_news_indices = set()
                    for part in inner.split(","):
                        part = part.strip()
                        is_good = part.startswith("+")
                        part = part.lstrip("+").strip()
                        try:
                            num = int(part)
                            numbers.append(num)
                            if is_good:
                                good_news_indices.add(num)
                        except ValueError:
                            continue
                    return numbers, good_news_indices
                return [], set()
        except HTTPError as e:
            last_error = e
            if e.code in (429, 500, 502, 503):
                wait = RETRY_BASE_DELAY * (attempt + 1)
                print(f"    {model_name} error ({e.code}). Waiting {wait}s... (attempt {attempt + 1})")
                time.sleep(wait)
                continue
            else:
                print(f"    {model_name} HTTP error: {e.code}")
                return [], set()
        except Exception as e:
            last_error = e
            time.sleep(RETRY_BASE_DELAY)
            continue
    print(f"    {model_name} failed after retries: {last_error}")
    return [], set()


def call_openai_selection(pool_text):
    return _call_api(
        url="https://api.openai.com/v1/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
        payload={"model": OPENAI_MODEL, "messages": [
            {"role": "system", "content": SELECTION_PROMPT},
            {"role": "user", "content": pool_text},
        ], "temperature": 0.3},
        model_name="OpenAI",
    )


def call_claude_selection(pool_text):
    return _call_api(
        url="https://api.anthropic.com/v1/messages",
        headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
        payload={"model": CLAUDE_MODEL, "max_tokens": 2048, "messages": [
            {"role": "user", "content": f"{SELECTION_PROMPT}\n\n{pool_text}"},
        ], "temperature": 0.3},
        model_name="Claude",
        response_path="anthropic",
    )


def call_grok_selection(pool_text):
    return _call_api(
        url="https://api.x.ai/v1/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}"},
        payload={"model": GROK_MODEL, "messages": [
            {"role": "system", "content": SELECTION_PROMPT},
            {"role": "user", "content": pool_text},
        ], "temperature": 0.3},
        model_name="Grok",
    )


def run_ai_selection(pool_text):
    results = {}
    all_good_news = set()

    if OPENAI_API_KEY:
        print("  → OpenAI selecting stories...")
        try:
            picks, good = call_openai_selection(pool_text)
            if picks:
                results["OpenAI"] = picks
                all_good_news.update(good)
                print(f"    OpenAI picked {len(picks)} stories, {len(good)} flagged as good news")
        except Exception as e:
            print(f"    OpenAI failed: {e}")

    time.sleep(1)

    if ANTHROPIC_API_KEY:
        print("  → Claude selecting stories...")
        try:
            picks, good = call_claude_selection(pool_text)
            if picks:
                results["Claude"] = picks
                all_good_news.update(good)
                print(f"    Claude picked {len(picks)} stories, {len(good)} flagged as good news")
        except Exception as e:
            print(f"    Claude failed: {e}")

    time.sleep(1)

    if XAI_API_KEY:
        print("  → Grok selecting stories...")
        try:
            picks, good = call_grok_selection(pool_text)
            if picks:
                results["Grok"] = picks
                all_good_news.update(good)
                print(f"    Grok picked {len(picks)} stories, {len(good)} flagged as good news")
        except Exception as e:
            print(f"    Grok failed: {e}")

    return results, all_good_news


def build_consensus(selections, pool_size):
    num_models = len(selections)
    if num_models == 0:
        return []
    if num_models == 1:
        name = list(selections.keys())[0]
        print(f"\n   Only 1 model ({name}). Using its picks.")
        return selections[name][:MAX_STORIES]

    vote_counts = {}
    rank_sums = {}
    for model_name, picks in selections.items():
        for rank, num in enumerate(picks):
            if 1 <= num <= pool_size:
                vote_counts[num] = vote_counts.get(num, 0) + 1
                rank_sums[num] = rank_sums.get(num, 0) + rank

    min_votes = min(MIN_CONSENSUS, num_models)
    consensus = [s for s, v in vote_counts.items() if v >= min_votes]
    consensus.sort(key=lambda s: (-vote_counts[s], rank_sums[s] / vote_counts[s]))

    print(f"\n   Consensus ({num_models} models, min {min_votes} votes): {len(consensus)} stories agreed")

    if len(consensus) < MAX_STORIES:
        remaining = [s for s in vote_counts if s not in consensus]
        remaining.sort(key=lambda s: (-vote_counts[s], rank_sums[s] / max(vote_counts[s], 1)))
        supplement = remaining[:MAX_STORIES - len(consensus)]
        consensus.extend(supplement)
        if supplement:
            print(f"   Added {len(supplement)} supplemental stories")

    return consensus[:MAX_STORIES]


# ── Fact Extraction ─────────────────────────────────────────────────

EXTRACTION_PROMPT = """You are the fact-extraction engine for The Daily Informant, a calm morning news briefing.

For each story, produce:
1. A neutral headline
2. A "context" paragraph (2-3 sentences): brief background explaining WHY this matters and what led to it. Factual, not opinion.
3. 2-4 factual bullet points about what happened
4. A category: one of World, US, Canada, Business, Science, Health, Tech, Sports
5. 0-2 stakeholder quotes: short direct quotes from key people/organizations involved. Only include if the RSS description contains actual quotes. Each needs a speaker name and the quote text.
6. Whether this is a positive/good-news story (true/false)

STRICT RULES:
- FACTS ONLY — every bullet must be verifiable
- NO sensational words
- NO opinion or analysis
- NO speculation
- CALM TONE — short sentences, plain verbs
- Stakeholder quotes must be real quotes from the description, not invented"""

EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "daily_brief_story",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "headline": {"type": "string"},
                "context": {"type": "string"},
                "facts": {"type": "array", "items": {"type": "string"}},
                "category": {"type": "string"},
                "stakeholder_quotes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "speaker": {"type": "string"},
                            "quote": {"type": "string"},
                        },
                        "required": ["speaker", "quote"],
                    },
                },
                "is_good_development": {"type": "boolean"},
            },
            "required": ["headline", "context", "facts", "category", "stakeholder_quotes", "is_good_development"],
        },
        "strict": True,
    },
}


def extract_facts(entry):
    user_prompt = f"""Source: {entry["source_name"]}
Title: {entry["title"]}
Published: {entry["pub_date"]}
Description: {entry["description"]}
Link: {entry["link"]}"""

    payload = json.dumps({
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": EXTRACTION_SCHEMA,
    }).encode("utf-8")

    req = Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
        method="POST",
    )

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except HTTPError as e:
            last_error = e
            if e.code in (429, 500, 502, 503):
                wait = RETRY_BASE_DELAY * (attempt + 1)
                print(f"      Rate limited ({e.code}). Waiting {wait}s...")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            last_error = e
            time.sleep(RETRY_BASE_DELAY)
            continue
    raise RuntimeError(f"Extraction failed: {last_error}")


def build_story(entry, idx, all_items, is_good_news_flagged=False):
    slug = f"story-{idx + 1}"
    sources = find_related_sources(entry, all_items)
    try:
        ai = extract_facts(entry)
        headline = ai.get("headline", entry["title"]).strip()
        context = ai.get("context", "").strip()
        category = ai.get("category", "World").strip()
        is_good = ai.get("is_good_development", False) or is_good_news_flagged

        facts = [{"text": f.strip(), "source_url": entry["link"]}
                 for f in ai.get("facts", []) if isinstance(f, str) and f.strip()]
        if not facts:
            raise RuntimeError("No usable facts")

        # Build stakeholder quotes with source URLs
        quotes = []
        for q in ai.get("stakeholder_quotes", []):
            if q.get("speaker") and q.get("quote"):
                quotes.append({
                    "speaker": q["speaker"],
                    "quote": q["quote"],
                    "url": entry["link"],
                })

        src_count = len(sources)
        q_count = len(quotes)
        good_tag = " [GOOD]" if is_good else ""
        print(f"  ✓ [{category}] \"{headline[:48]}\" ({len(facts)}f, {src_count}s, {q_count}q){good_tag}")

        return {
            "slug": slug, "headline": headline, "context": context,
            "category": category, "facts": facts, "sources": sources,
            "stakeholder_quotes": quotes, "is_good_development": is_good,
        }
    except Exception as e:
        print(f"  ✗ Story {idx+1} extraction failed: {e}")
        desc = entry.get("description", "Details available at source.")[:200]
        return {
            "slug": slug, "headline": entry["title"], "context": "",
            "category": "World", "facts": [{"text": desc, "source_url": entry["link"]}],
            "sources": sources, "stakeholder_quotes": [],
            "is_good_development": is_good_news_flagged,
        }


# ── Archive & Ongoing ──────────────────────────────────────────────

def load_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def update_ongoing_topics(stories, topics_data, today):
    if not topics_data.get("topics"):
        return topics_data
    for topic in topics_data["topics"]:
        topic_kw = extract_key_words(topic["topic"] + " " + topic.get("summary", ""))
        for story in stories:
            story_kw = extract_key_words(story["headline"])
            if len(topic_kw) < 2 or len(story_kw) < 2:
                continue
            overlap = len(topic_kw & story_kw)
            smaller = min(len(topic_kw), len(story_kw))
            if smaller > 0 and overlap / smaller >= 0.25:
                existing_dates = {e["date"] for e in topic.get("timeline", [])}
                if today not in existing_dates:
                    topic.setdefault("timeline", []).insert(0, {
                        "date": today,
                        "text": story["headline"],
                        "source_url": story["sources"][0]["url"] if story["sources"] else "#",
                    })
                    topic["timeline"] = topic["timeline"][:30]
                    print(f"  → Updated \"{topic['topic']}\" with: {story['headline'][:50]}")
                    break
    return topics_data


# ── Main ────────────────────────────────────────────────────────────

def main():
    today = datetime.now(TORONTO).strftime("%Y-%m-%d")

    print("=" * 65)
    print("  The Daily Informant — Morning Pipeline v5")
    print(f"  {datetime.now(TORONTO).strftime('%Y-%m-%d %H:%M %Z')}")
    print("=" * 65)

    models = []
    if OPENAI_API_KEY: models.append("OpenAI")
    if ANTHROPIC_API_KEY: models.append("Claude")
    if XAI_API_KEY: models.append("Grok")
    print(f"\n  AI models: {', '.join(models) or 'NONE'}")

    if not OPENAI_API_KEY:
        print("\n✗ OPENAI_API_KEY required. Exiting.")
        sys.exit(1)

    # Step 1: Fetch
    print("\n─── Step 1: Fetching RSS feeds ───")
    all_items = fetch_all_feeds()
    if not all_items:
        print("\n✗ No items. Exiting.")
        sys.exit(1)
    print(f"\n   Raw items: {len(all_items)}")

    # Step 2: Dedup & filter
    print("\n─── Step 2: Dedup & noise filter ───")
    unique = deduplicate(all_items)
    print(f"   After dedup: {len(unique)}")
    filtered = filter_noise(unique)
    print(f"   After noise filter: {len(filtered)}")

    # Step 3: AI selection
    print("\n─── Step 3: Multi-AI story selection ───")
    pool_text = build_story_pool_text(filtered)
    selections, good_news_indices = run_ai_selection(pool_text)

    if not selections:
        print("\n⚠ No AI returned selections. Fallback.")
        consensus_indices = list(range(1, min(MAX_STORIES + 1, len(filtered) + 1)))
    else:
        consensus_indices = build_consensus(selections, len(filtered))

    consensus_items = [filtered[idx - 1] for idx in consensus_indices if 1 <= idx <= len(filtered)]
    print(f"\n   Final selection: {len(consensus_items)} stories")

    # Step 4: Extract facts
    print("\n─── Step 4: Fact extraction + multi-source ───")
    stories = []
    for i, item in enumerate(consensus_items):
        idx_1based = consensus_indices[i] if i < len(consensus_indices) else 0
        is_flagged_good = idx_1based in good_news_indices
        stories.append(build_story(item, i, all_items, is_flagged_good))
        if i < len(consensus_items) - 1:
            time.sleep(1)

    # Separate good developments
    regular_stories = []
    good_developments = []
    for story in stories:
        if story.get("is_good_development"):
            good_developments.append({
                "headline": story["headline"],
                "context": story.get("context", ""),
                "facts": story["facts"],
                "sources": story["sources"],
            })
        regular_stories.append(story)  # Keep in main list too

    print(f"\n   Good developments found: {len(good_developments)}")

    # Step 5: Archive
    print("\n─── Step 5: Archive & ongoing topics ───")
    archive = load_json(ARCHIVE_PATH) or []
    for story in stories:
        archive.append({
            "date": today, "headline": story["headline"],
            "category": story.get("category", "World"), "slug": story["slug"],
            "source_url": story["sources"][0]["url"] if story["sources"] else "",
        })
    archive = archive[-900:]
    ARCHIVE_PATH.write_text(json.dumps(archive, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  Archive: {len(archive)} stories")

    # Step 6: Ongoing topics
    topics_data = load_json(TOPICS_PATH) or {"topics": []}
    topics_data = update_ongoing_topics(stories, topics_data, today)
    TOPICS_PATH.write_text(json.dumps(topics_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ongoing_for_daily = [{
        "slug": t["slug"], "topic": t["topic"],
        "summary": t.get("summary", ""),
        "timeline": t.get("timeline", [])[:5],
    } for t in topics_data.get("topics", [])]

    # Step 7: Write daily.json
    existing = load_json(DAILY_PATH) or {}

    daily_data = {
        "date": today,
        "top_stories": regular_stories,
        "ongoing_topics": ongoing_for_daily,
        "good_developments": good_developments if good_developments else existing.get("good_developments", []),
        "optional_reflection": existing.get(
            "optional_reflection",
            "In times of uncertainty, may we seek truth with humility and share it with grace. "
            "Lord, grant us wisdom to see clearly, courage to speak honestly, and compassion "
            "for those whose stories we carry today. Amen.",
        ),
        "_meta": {
            "pipeline_version": "5.0",
            "models_used": list(selections.keys()),
            "feeds_attempted": len(FEEDS),
            "raw_items": len(all_items),
            "consensus_stories": len(consensus_items),
            "good_developments_found": len(good_developments),
        },
    }

    DAILY_PATH.write_text(json.dumps(daily_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    categories = set(s.get("category", "?") for s in stories)
    total_sources = sum(len(s.get("sources", [])) for s in stories)
    total_quotes = sum(len(s.get("stakeholder_quotes", [])) for s in stories)

    print(f"\n{'=' * 65}")
    print(f"  DONE — {len(stories)} stories → data/daily.json")
    print(f"  Models: {', '.join(selections.keys()) or 'fallback'}")
    print(f"  Categories: {', '.join(sorted(categories))}")
    print(f"  Sources cited: {total_sources} | Quotes: {total_quotes}")
    print(f"  Good developments: {len(good_developments)}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
