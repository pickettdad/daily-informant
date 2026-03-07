#!/usr/bin/env python3
"""
The Daily Informant — Morning Pipeline v6
==========================================

MAJOR CHANGES from v5:
  - STORY CONSOLIDATION: Related articles grouped into single "DI Articles"
    (no more 6 Iran stories — one consolidated Iran article with all sources)
  - LOCAL FEEDS: Quinte News, inQuinte, CTV Belleville for local coverage
  - ONTARIO FEEDS: CTV, Ontario-specific sources
  - SOURCE REBALANCING: More right-leaning sources prioritized in extraction
  - ARTICLE DETAIL: Each DI article includes component_articles listing all
    source articles that were merged
  - POSITIVE THOUGHTS: Negative stories get a specific uplifting thought
  - NO SPORTS: Removed from selection
  - CATEGORY ORDER: Local, Ontario, Canada, US, World, Health, Science, Tech
  - ONGOING LINKS: Articles linked to related ongoing situations

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
    # ── Local (Bay of Quinte / Belleville) ──
    {"name": "Quinte News",        "url": "https://www.quintenews.com/feed/",                      "lean": "Center",       "region": "Local"},
    {"name": "inQuinte",           "url": "https://inquinte.ca/feed",                               "lean": "Center",       "region": "Local"},

    # ── Ontario ──
    {"name": "CTV Toronto",       "url": "https://toronto.ctvnews.ca/rss/ctv-news-toronto-1.822319", "lean": "Center",    "region": "Ontario"},
    {"name": "CTV Ottawa",        "url": "https://ottawa.ctvnews.ca/rss/ctv-news-ottawa-1.822325",   "lean": "Center",    "region": "Ontario"},
    {"name": "Toronto Star",      "url": "https://www.thestar.com/search/?f=rss&t=article&c=news*&l=50&s=start_time&sd=desc", "lean": "Center-Left", "region": "Ontario"},
    {"name": "Toronto Sun",       "url": "https://torontosun.com/feed",                             "lean": "Right",        "region": "Ontario"},

    # ── Canada ──
    {"name": "Globe and Mail",    "url": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/world/", "lean": "Center", "region": "Canada"},
    {"name": "National Post",     "url": "https://nationalpost.com/feed/",                           "lean": "Center-Right", "region": "Canada"},
    {"name": "CBC Top Stories",   "url": "https://www.cbc.ca/webfeed/rss/rss-topstories",           "lean": "Center-Left",  "region": "Canada"},

    # ── US: Left-leaning ──
    {"name": "NPR News",          "url": "https://feeds.npr.org/1001/rss.xml",                      "lean": "Left",         "region": "US"},
    {"name": "NPR World",         "url": "https://feeds.npr.org/1004/rss.xml",                      "lean": "Left",         "region": "US"},
    {"name": "The Guardian US",   "url": "https://www.theguardian.com/us-news/rss",                  "lean": "Left",         "region": "US"},
    {"name": "PBS NewsHour",      "url": "https://www.pbs.org/newshour/feeds/rss/headlines",         "lean": "Left",         "region": "US"},

    # ── US/World: Center ──
    {"name": "BBC World",         "url": "https://feeds.bbci.co.uk/news/world/rss.xml",              "lean": "Center",       "region": "World"},
    {"name": "BBC Business",      "url": "https://feeds.bbci.co.uk/news/business/rss.xml",           "lean": "Center",       "region": "World"},
    {"name": "Al Jazeera",        "url": "https://www.aljazeera.com/xml/rss/all.xml",                "lean": "Center",       "region": "World"},
    {"name": "France 24",         "url": "https://www.france24.com/en/rss",                          "lean": "Center",       "region": "World"},
    {"name": "ABC News",          "url": "https://abcnews.go.com/abcnews/topstories",               "lean": "Center",       "region": "US"},
    {"name": "CBS News",          "url": "https://www.cbsnews.com/latest/rss/main",                  "lean": "Center",       "region": "US"},

    # ── US: Right-leaning ──
    {"name": "Fox News",          "url": "https://moxie.foxnews.com/google-publisher/latest.xml",    "lean": "Right",        "region": "US"},
    {"name": "NY Post",           "url": "https://nypost.com/feed/",                                  "lean": "Right",        "region": "US"},
    {"name": "Daily Wire",        "url": "https://www.dailywire.com/feeds/rss.xml",                  "lean": "Right",        "region": "US"},
    {"name": "Breitbart",         "url": "https://feeds.feedburner.com/breitbart",                   "lean": "Right",        "region": "US"},
    {"name": "Washington Examiner", "url": "https://www.washingtonexaminer.com/feed",                "lean": "Right",        "region": "US"},
    {"name": "The Hill",          "url": "https://thehill.com/feed/",                                 "lean": "Center-Right", "region": "US"},
    {"name": "RealClearPolitics", "url": "https://www.realclearpolitics.com/index.xml",              "lean": "Center-Right", "region": "US"},
    {"name": "Newsmax",           "url": "https://www.newsmax.com/rss/Newsfront/1/",                 "lean": "Right",        "region": "US"},

    # ── Science / Health / Tech ──
    {"name": "BBC Science",       "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "lean": "Center", "region": "World"},
    {"name": "BBC Health",        "url": "https://feeds.bbci.co.uk/news/health/rss.xml",             "lean": "Center",       "region": "World"},
    {"name": "BBC Tech",          "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",         "lean": "Center",       "region": "World"},
    {"name": "NPR Science",      "url": "https://feeds.npr.org/1007/rss.xml",                       "lean": "Left",         "region": "World"},
    {"name": "NPR Health",       "url": "https://feeds.npr.org/1128/rss.xml",                       "lean": "Left",         "region": "World"},
    {"name": "Ars Technica",     "url": "https://feeds.arstechnica.com/arstechnica/index",           "lean": "Center",       "region": "World"},
    {"name": "Phys.org",         "url": "https://phys.org/rss-feed/",                                "lean": "Center",       "region": "World"},

    # ── Good News / Humanitarian / Faith ──
    {"name": "Good News Network",  "url": "https://www.goodnewsnetwork.org/feed/",                   "lean": "Center",       "region": "World"},
    {"name": "Positive News",      "url": "https://www.positive.news/feed/",                          "lean": "Center",       "region": "World"},
    {"name": "Christianity Today", "url": "https://www.christianitytoday.com/feed/",                  "lean": "Center",       "region": "World"},
    {"name": "Deseret News Faith", "url": "https://www.deseret.com/arc/outboundfeeds/rss/category/faith/", "lean": "Center", "region": "World"},
]

ITEMS_PER_FEED = 6
MAX_ARTICLES = 15  # Final DI articles (consolidated, not individual stories)
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

# ── Category order for display ──
CATEGORY_ORDER = ["Local", "Ontario", "Canada", "US", "World", "Health", "Science", "Tech"]

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


def parse_rss(xml_bytes, source_name, lean, region):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall(".//channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = re.sub(r"<[^>]+>", "", (item.findtext("description") or "")).strip()
        if title and link:
            items.append({"source_name": source_name, "lean": lean, "region": region,
                          "title": title, "link": link, "pub_date": pub_date,
                          "description": description[:500]})
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "").strip() if link_el is not None else ""
        pub_date = (entry.findtext("atom:updated", namespaces=ns) or "").strip()
        description = re.sub(r"<[^>]+>", "", (entry.findtext("atom:summary", namespaces=ns) or "")).strip()
        if title and link:
            items.append({"source_name": source_name, "lean": lean, "region": region,
                          "title": title, "link": link, "pub_date": pub_date,
                          "description": description[:500]})
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


# ── Story Grouping (the key v6 change) ─────────────────────────────


def group_related_stories(items):
    """
    Group related RSS items into clusters about the same event/topic.
    Each group becomes one DI Article.
    Returns list of groups, where each group is a list of RSS items.
    """
    groups = []
    used = set()

    for i, item in enumerate(items):
        if i in used:
            continue

        group = [item]
        used.add(i)
        item_kw = extract_key_words(item["title"] + " " + item.get("description", "")[:200])

        if len(item_kw) < 2:
            groups.append(group)
            continue

        # Find all related items
        for j, other in enumerate(items):
            if j in used:
                continue
            other_kw = extract_key_words(other["title"] + " " + other.get("description", "")[:200])
            if len(other_kw) < 2:
                continue
            overlap = len(item_kw & other_kw)
            smaller = min(len(item_kw), len(other_kw))
            if smaller > 0 and overlap / smaller >= 0.35:
                group.append(other)
                used.add(j)

        groups.append(group)

    # Sort groups by size (largest = most covered = most important)
    groups.sort(key=lambda g: -len(g))
    return groups


# ── Multi-AI Topic Selection ────────────────────────────────────────

SELECTION_PROMPT = """You are the editorial director for The Daily Informant, a calm, unbiased, fact-only morning news briefing based in the Bay of Quinte region of Ontario, Canada.

Below is a numbered list of STORY GROUPS. Each group contains related articles from multiple sources about the same event or topic. The number in brackets [N articles] shows how many sources covered it.

YOUR JOB: Select the 15 most important story groups for today's edition.

CATEGORY TARGETS:
- 1-2 Local (Bay of Quinte / Belleville area) if available
- 1-2 Ontario stories
- 2-3 Canada stories
- 3-4 US stories
- 3-4 World/International stories
- 1-2 Health/Science/Tech stories
- 1-2 GENUINELY POSITIVE humanitarian/community stories (mark with +)

DO NOT select sports stories.

SELECTION CRITERIA:
1. IMPACT — How many people does this actually affect?
2. ACTION — Prefer things that HAPPENED over things people SAID
3. DIVERSITY — Mix of categories, don't let one dominate
4. SOURCE BALANCE — Groups covered by BOTH left and right sources are more important
5. SKIP politician theater without concrete action

Return ONLY a JSON array of group numbers. Prefix positive/good-news groups with +.
Example: [1, 3, +7, 2, 11, 4, +15, 8, 6, 12, 9, 14, 5, 10, 13]

Return ONLY the JSON array."""


def build_group_pool_text(groups):
    lines = []
    for i, group in enumerate(groups):
        sources = set(item["source_name"] for item in group)
        leans = set(item["lean"] for item in group)
        regions = set(item["region"] for item in group)
        primary = group[0]
        line = f"{i+1}. [{len(group)} articles, {', '.join(sorted(leans))}] "
        line += f"[{', '.join(sorted(regions))}] "
        line += f"{primary['title']}"
        if primary.get("description"):
            line += f" — {primary['description'][:120]}"
        if len(sources) > 1:
            line += f" (Also covered by: {', '.join(sorted(sources - {primary['source_name']}))})"
        lines.append(line)
    return "\n".join(lines)


def _call_openai_style_api(url, headers, payload, model_name, response_path="openai"):
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
                print(f"    {model_name} error ({e.code}). Waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                body = ""
                try:
                    body = e.read().decode("utf-8", "replace")[:300]
                except Exception:
                    pass
                print(f"    {model_name} HTTP {e.code}: {body}")
                return [], set()
        except Exception as e:
            last_error = e
            time.sleep(RETRY_BASE_DELAY)
            continue
    print(f"    {model_name} failed: {last_error}")
    return [], set()


def _call_grok_responses_api(pool_text):
    payload = json.dumps({
        "model": GROK_MODEL,
        "input": [
            {"role": "system", "content": SELECTION_PROMPT},
            {"role": "user", "content": pool_text},
        ],
        "temperature": 0.3,
        "store": False,
    }).encode("utf-8")

    req = Request(
        "https://api.x.ai/v1/responses",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {XAI_API_KEY}",
            "User-Agent": "DailyInformant/1.0",
        },
        method="POST",
    )

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_text = ""
                for item in data.get("output", []):
                    if item.get("type") == "message":
                        for content in item.get("content", []):
                            if content.get("type") == "output_text":
                                raw_text += content.get("text", "")
                raw_text = raw_text.strip()
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
                else:
                    print(f"    Grok: Could not parse. Raw: {raw_text[:200]}")
                    return [], set()
        except HTTPError as e:
            last_error = e
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            if e.code in (429, 500, 502, 503):
                wait = RETRY_BASE_DELAY * (attempt + 1)
                print(f"    Grok error ({e.code}). Waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                print(f"    Grok HTTP {e.code}: {body}")
                return [], set()
        except Exception as e:
            last_error = e
            time.sleep(RETRY_BASE_DELAY)
            continue
    print(f"    Grok failed: {last_error}")
    return [], set()


def run_ai_selection(pool_text):
    results = {}
    all_good_news = set()

    if OPENAI_API_KEY:
        print("  → OpenAI...")
        try:
            picks, good = _call_openai_style_api(
                url="https://api.openai.com/v1/chat/completions",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
                payload={"model": OPENAI_MODEL, "messages": [
                    {"role": "system", "content": SELECTION_PROMPT},
                    {"role": "user", "content": pool_text},
                ], "temperature": 0.3},
                model_name="OpenAI",
            )
            if picks:
                results["OpenAI"] = picks
                all_good_news.update(good)
                print(f"    OpenAI: {len(picks)} groups, {len(good)} good news")
        except Exception as e:
            print(f"    OpenAI failed: {e}")

    time.sleep(1)

    if ANTHROPIC_API_KEY:
        print("  → Claude...")
        try:
            picks, good = _call_openai_style_api(
                url="https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
                payload={"model": CLAUDE_MODEL, "max_tokens": 2048, "messages": [
                    {"role": "user", "content": f"{SELECTION_PROMPT}\n\n{pool_text}"},
                ], "temperature": 0.3},
                model_name="Claude",
                response_path="anthropic",
            )
            if picks:
                results["Claude"] = picks
                all_good_news.update(good)
                print(f"    Claude: {len(picks)} groups, {len(good)} good news")
        except Exception as e:
            print(f"    Claude failed: {e}")

    time.sleep(1)

    if XAI_API_KEY:
        print("  → Grok...")
        try:
            picks, good = _call_grok_responses_api(pool_text)
            if picks:
                results["Grok"] = picks
                all_good_news.update(good)
                print(f"    Grok: {len(picks)} groups, {len(good)} good news")
        except Exception as e:
            print(f"    Grok failed: {e}")

    return results, all_good_news


def build_consensus(selections, pool_size):
    num_models = len(selections)
    if num_models == 0:
        return []
    if num_models == 1:
        name = list(selections.keys())[0]
        return selections[name][:MAX_ARTICLES]

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

    print(f"\n   Consensus ({num_models} models): {len(consensus)} groups agreed")
    for s in consensus[:10]:
        avg = rank_sums[s] / vote_counts[s]
        print(f"    Group #{s}: {vote_counts[s]}/{num_models} votes, avg rank {avg:.1f}")

    if len(consensus) < MAX_ARTICLES:
        remaining = [s for s in vote_counts if s not in consensus]
        remaining.sort(key=lambda s: (-vote_counts[s], rank_sums[s] / max(vote_counts[s], 1)))
        consensus.extend(remaining[:MAX_ARTICLES - len(consensus)])

    return consensus[:MAX_ARTICLES]


# ── Consolidated Article Extraction ─────────────────────────────────

EXTRACTION_PROMPT = """You are the article writer for The Daily Informant (DI), a calm, unbiased morning news briefing.

You are given a GROUP of related articles from multiple sources about the same event/topic. Your job is to write ONE consolidated DI Article that combines all the information.

Produce:
1. headline: A neutral, informative headline for this consolidated article
2. summary: A 3-5 sentence summary combining information from ALL the source articles. Write in a calm, neutral tone. Include key facts, numbers, and context. This should read like a well-written briefing paragraph, not a list.
3. context: 2-3 sentences of background — what led to this, why it matters
4. key_points: 3-6 bullet points capturing the most important facts across all sources
5. category: One of Local, Ontario, Canada, US, World, Health, Science, Tech
6. stakeholder_quotes: 0-3 direct quotes from key people/organizations (only real quotes from the articles)
7. is_good_development: ONLY true for humanitarian aid, disaster relief, volunteers, missionary work, charitable giving, community rebuilding, faith-based service
8. is_negative: true if the story involves conflict, death, economic hardship, disaster, or suffering
9. positive_thought: If is_negative is true, write one short, specific, uplifting thought related to this story. No mentions of God or Amen. Focus on hope, resilience, compassion, or human strength specific to this situation. If not negative, leave empty.
10. related_ongoing: If this story relates to a known ongoing situation (Iran Conflict, Ukraine-Russia, Economy & Inflation, U.S. Tariffs & Trade, Israel & Gaza, Sudan & South Sudan, AI Regulation, Climate & Environment), list the slug. Otherwise empty string.

RULES:
- FACTS ONLY — verifiable information from the provided articles
- NO sensational words
- NO opinion or analysis
- CALM TONE — measured language
- Use information from ALL provided articles, not just the first one
- The summary should be comprehensive enough that a reader doesn't need to click through"""

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


def extract_consolidated_article(group):
    """Send a group of related articles to OpenAI for consolidated extraction."""
    articles_text = ""
    for i, item in enumerate(group):
        articles_text += f"\n--- Article {i+1} [{item['source_name']}, {item['lean']}] ---\n"
        articles_text += f"Title: {item['title']}\n"
        articles_text += f"Published: {item['pub_date']}\n"
        articles_text += f"Description: {item['description']}\n"
        articles_text += f"Link: {item['link']}\n"

    payload = json.dumps({
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": articles_text},
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
            with urlopen(req, timeout=90) as resp:
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


def build_di_article(group, idx, is_good_flagged=False):
    """Build a consolidated DI Article from a group of related RSS items."""
    slug = f"article-{idx + 1}"

    # Collect all sources from the group
    sources = []
    seen_names = set()
    component_articles = []
    for item in group:
        component_articles.append({
            "source": item["source_name"],
            "lean": item["lean"],
            "title": item["title"],
            "url": item["link"],
        })
        if item["source_name"] not in seen_names:
            sources.append({"name": item["source_name"], "url": item["link"]})
            seen_names.add(item["source_name"])

    try:
        ai = extract_consolidated_article(group)
        headline = ai.get("headline", group[0]["title"]).strip()
        summary = ai.get("summary", "").strip()
        context = ai.get("context", "").strip()
        category = ai.get("category", "World").strip()
        is_good = ai.get("is_good_development", False) or is_good_flagged
        is_negative = ai.get("is_negative", False)
        positive_thought = ai.get("positive_thought", "").strip()
        related_ongoing = ai.get("related_ongoing", "").strip()

        key_points = [
            {"text": kp.strip(), "source_url": group[0]["link"]}
            for kp in ai.get("key_points", [])
            if isinstance(kp, str) and kp.strip()
        ]

        quotes = []
        for q in ai.get("stakeholder_quotes", []):
            if q.get("speaker") and q.get("quote"):
                quotes.append({
                    "speaker": q["speaker"],
                    "quote": q["quote"],
                    "url": group[0]["link"],
                })

        good_tag = " [GOOD]" if is_good else ""
        neg_tag = " [NEG]" if is_negative else ""
        print(f"  ✓ [{category}] \"{headline[:48]}\" ({len(key_points)}kp, {len(sources)}s, {len(group)}art){good_tag}{neg_tag}")

        return {
            "slug": slug,
            "headline": headline,
            "summary": summary,
            "context": context,
            "category": category,
            "key_points": key_points,
            "sources": sources,
            "component_articles": component_articles,
            "stakeholder_quotes": quotes,
            "is_good_development": is_good,
            "is_negative": is_negative,
            "positive_thought": positive_thought if is_negative else "",
            "related_ongoing": related_ongoing,
        }

    except Exception as e:
        print(f"  ✗ Article {idx+1} failed: {e}")
        return {
            "slug": slug,
            "headline": group[0]["title"],
            "summary": group[0].get("description", "")[:300],
            "context": "",
            "category": group[0].get("region", "World"),
            "key_points": [{"text": group[0].get("description", "")[:200], "source_url": group[0]["link"]}],
            "sources": sources,
            "component_articles": component_articles,
            "stakeholder_quotes": [],
            "is_good_development": is_good_flagged,
            "is_negative": False,
            "positive_thought": "",
            "related_ongoing": "",
        }


# ── Archive & Ongoing ──────────────────────────────────────────────

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
        topic_kw = extract_key_words(topic["topic"] + " " + topic.get("summary", ""))
        for article in articles:
            article_kw = extract_key_words(article["headline"] + " " + article.get("summary", ""))
            if len(topic_kw) < 2 or len(article_kw) < 2:
                continue
            overlap = len(topic_kw & article_kw)
            smaller = min(len(topic_kw), len(article_kw))
            if smaller > 0 and overlap / smaller >= 0.25:
                existing_dates = {e["date"] for e in topic.get("timeline", [])}
                if today not in existing_dates:
                    topic.setdefault("timeline", []).insert(0, {
                        "date": today,
                        "text": article["headline"],
                        "source_url": article["sources"][0]["url"] if article["sources"] else "#",
                    })
                    topic["timeline"] = topic["timeline"][:30]
                    print(f"  → Updated \"{topic['topic']}\"")
                    break
    return topics_data


# ── Main ────────────────────────────────────────────────────────────

def main():
    today = datetime.now(TORONTO).strftime("%Y-%m-%d")

    print("=" * 65)
    print("  The Daily Informant — Morning Pipeline v6")
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

    # Step 2: Filter noise
    print("\n─── Step 2: Noise filter ───")
    filtered = filter_noise(all_items)
    print(f"   After noise filter: {len(filtered)}")

    # Step 3: Group related stories
    print("\n─── Step 3: Grouping related stories ───")
    groups = group_related_stories(filtered)
    print(f"   Story groups formed: {len(groups)}")
    for i, g in enumerate(groups[:10]):
        sources = set(item["source_name"] for item in g)
        print(f"    Group {i+1}: {len(g)} articles — {g[0]['title'][:60]}")

    # Step 4: AI selection (on groups, not individual stories)
    print("\n─── Step 4: Multi-AI group selection ───")
    pool_text = build_group_pool_text(groups)
    selections, good_news_indices = run_ai_selection(pool_text)

    if not selections:
        print("\n⚠ No AI returned selections. Fallback.")
        consensus_indices = list(range(1, min(MAX_ARTICLES + 1, len(groups) + 1)))
    else:
        consensus_indices = build_consensus(selections, len(groups))

    consensus_groups = [groups[idx - 1] for idx in consensus_indices if 1 <= idx <= len(groups)]
    print(f"\n   Final selection: {len(consensus_groups)} DI articles")

    # Step 5: Extract consolidated articles
    print("\n─── Step 5: Consolidated article extraction ───")
    articles = []
    for i, group in enumerate(consensus_groups):
        idx_1based = consensus_indices[i] if i < len(consensus_indices) else 0
        is_flagged_good = idx_1based in good_news_indices
        articles.append(build_di_article(group, i, is_flagged_good))
        if i < len(consensus_groups) - 1:
            time.sleep(1)

    # Separate good developments
    regular_articles = []
    good_developments = []
    for article in articles:
        if article.get("is_good_development"):
            good_developments.append(article)
        else:
            regular_articles.append(article)

    # Sort by category order
    def cat_sort_key(article):
        cat = article.get("category", "World")
        try:
            return CATEGORY_ORDER.index(cat)
        except ValueError:
            return len(CATEGORY_ORDER)

    regular_articles.sort(key=cat_sort_key)

    print(f"\n   Regular articles: {len(regular_articles)}")
    print(f"   Good developments: {len(good_developments)}")

    # Step 6: Archive
    print("\n─── Step 6: Archive & ongoing topics ───")
    archive = load_json(ARCHIVE_PATH) or []
    for article in articles:
        archive.append({
            "date": today, "headline": article["headline"],
            "category": article.get("category", "World"), "slug": article["slug"],
            "source_count": len(article.get("component_articles", [])),
        })
    archive = archive[-900:]
    ARCHIVE_PATH.write_text(json.dumps(archive, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  Archive: {len(archive)} entries")

    # Step 7: Ongoing topics
    topics_data = load_json(TOPICS_PATH) or {"topics": []}
    topics_data = update_ongoing_topics(articles, topics_data, today)
    TOPICS_PATH.write_text(json.dumps(topics_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ongoing_for_daily = [{
        "slug": t["slug"], "topic": t["topic"],
        "summary": t.get("summary", ""),
        "timeline": t.get("timeline", [])[:5],
    } for t in topics_data.get("topics", [])]

    # Step 8: Write daily.json
    daily_data = {
        "date": today,
        "top_stories": regular_articles,
        "ongoing_topics": ongoing_for_daily,
        "good_developments": good_developments,
        "_meta": {
            "pipeline_version": "6.0",
            "models_used": list(selections.keys()),
            "feeds_attempted": len(FEEDS),
            "raw_items": len(all_items),
            "groups_formed": len(groups),
            "consensus_articles": len(consensus_groups),
            "good_developments_found": len(good_developments),
            "category_order": CATEGORY_ORDER,
        },
    }

    DAILY_PATH.write_text(json.dumps(daily_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    categories = set(a.get("category", "?") for a in articles)
    total_sources = sum(len(a.get("sources", [])) for a in articles)
    total_component = sum(len(a.get("component_articles", [])) for a in articles)
    negative_count = sum(1 for a in articles if a.get("is_negative"))

    print(f"\n{'=' * 65}")
    print(f"  DONE — {len(articles)} DI articles → data/daily.json")
    print(f"  Models: {', '.join(selections.keys()) or 'fallback'}")
    print(f"  Categories: {', '.join(sorted(categories))}")
    print(f"  Sources cited: {total_sources} | Articles consolidated: {total_component}")
    print(f"  Negative (with positive thoughts): {negative_count}")
    print(f"  Good developments: {len(good_developments)}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
