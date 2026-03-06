#!/usr/bin/env python3
"""
The Daily Informant — Morning Pipeline v3.1 (Multi-AI Consensus)
=================================================================

Architecture:
  1. WIDE NET — 30+ RSS feeds spanning left-to-right political spectrum
  2. STORY POOL — Deduplicated, filtered list of ~100+ raw headlines
  3. AI EDITORS — Same pool sent to 3 AI models independently
     Each picks the top stories for a balanced morning briefing
  4. CONSENSUS — Stories picked by 2+ models get published
  5. EXTRACTION — Detailed fact extraction for each consensus story
  6. OUTPUT — data/daily.json

v3.1 changes:
  - Fixed broken feeds (Reuters, AP, CBC replaced with working URLs)
  - Smarter dedup that catches same-event-different-headline duplicates
  - Grok model name fix
  - Each AI model failure is fully isolated (can never crash the pipeline)

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

# ── Config ──────────────────────────────────────────────────────────

TORONTO = ZoneInfo("America/Toronto")

# ┌─────────────────────────────────────────────────────────────────┐
# │  RSS FEEDS — Deliberately broad, left-to-right spectrum        │
# │  The feeds are raw material. The AI consensus is the editor.   │
# └─────────────────────────────────────────────────────────────────┘

FEEDS = [
    # ── Left-leaning ──
    {"name": "NPR News",           "url": "https://feeds.npr.org/1001/rss.xml",                                      "lean": "Left"},
    {"name": "NPR World",          "url": "https://feeds.npr.org/1004/rss.xml",                                      "lean": "Left"},
    {"name": "NPR Science",        "url": "https://feeds.npr.org/1007/rss.xml",                                      "lean": "Left"},
    {"name": "NPR Health",         "url": "https://feeds.npr.org/1128/rss.xml",                                      "lean": "Left"},
    {"name": "The Guardian World",  "url": "https://www.theguardian.com/world/rss",                                   "lean": "Left"},
    {"name": "The Guardian US",    "url": "https://www.theguardian.com/us-news/rss",                                  "lean": "Left"},
    {"name": "PBS NewsHour",       "url": "https://www.pbs.org/newshour/feeds/rss/headlines",                         "lean": "Left"},

    # ── Center / International ──
    {"name": "BBC World",          "url": "https://feeds.bbci.co.uk/news/world/rss.xml",                              "lean": "Center"},
    {"name": "BBC Business",       "url": "https://feeds.bbci.co.uk/news/business/rss.xml",                           "lean": "Center"},
    {"name": "BBC Science",        "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",             "lean": "Center"},
    {"name": "BBC Health",         "url": "https://feeds.bbci.co.uk/news/health/rss.xml",                              "lean": "Center"},
    {"name": "BBC Tech",           "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",                          "lean": "Center"},
    {"name": "Al Jazeera",         "url": "https://www.aljazeera.com/xml/rss/all.xml",                                 "lean": "Center"},
    {"name": "France 24",          "url": "https://www.france24.com/en/rss",                                           "lean": "Center"},
    {"name": "ABC News",           "url": "https://abcnews.go.com/abcnews/topstories",                                "lean": "Center"},
    {"name": "CBS News",           "url": "https://www.cbsnews.com/latest/rss/main",                                   "lean": "Center"},

    # ── Center-right ──
    {"name": "The Hill",           "url": "https://thehill.com/feed/",                                                  "lean": "Center-Right"},
    {"name": "RealClearPolitics",  "url": "https://www.realclearpolitics.com/index.xml",                               "lean": "Center-Right"},

    # ── Right-leaning ──
    {"name": "Fox News",           "url": "https://moxie.foxnews.com/google-publisher/latest.xml",                     "lean": "Right"},
    {"name": "NY Post",            "url": "https://nypost.com/feed/",                                                  "lean": "Right"},
    {"name": "Daily Wire",         "url": "https://www.dailywire.com/feeds/rss.xml",                                   "lean": "Right"},
    {"name": "Breitbart",          "url": "https://feeds.feedburner.com/breitbart",                                    "lean": "Right"},
    {"name": "Washington Examiner", "url": "https://www.washingtonexaminer.com/feed",                                  "lean": "Right"},

    # ── Canada ──
    {"name": "Globe and Mail",     "url": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/world/",     "lean": "Center"},
    {"name": "National Post",      "url": "https://nationalpost.com/feed/",                                             "lean": "Center-Right"},
    {"name": "CTV News",           "url": "https://www.ctvnews.ca/rss/ctvnews-ca-top-stories-public-rss-1.822009",     "lean": "Center"},
    {"name": "Toronto Star",       "url": "https://www.thestar.com/search/?f=rss&t=article&c=news*&l=50&s=start_time&sd=desc", "lean": "Center-Left"},

    # ── Science / Tech (non-partisan) ──
    {"name": "Ars Technica",       "url": "https://feeds.arstechnica.com/arstechnica/index",                           "lean": "Center"},
    {"name": "Phys.org",           "url": "https://phys.org/rss-feed/",                                                "lean": "Center"},
]

ITEMS_PER_FEED = 5        # Max items from each feed
MAX_STORIES = 10          # Final stories in the edition
MIN_CONSENSUS = 2         # Minimum AI models that must agree on a story

# AI model configs
OPENAI_MODEL = "gpt-4o-mini"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
GROK_MODEL = "grok-2-1212"

MAX_RETRIES = 3
RETRY_BASE_DELAY = 5

# API keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")


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


def is_politician_noise(title: str, description: str = "") -> bool:
    combined = f"{title} {description}"
    if ACTION_RE.search(combined):
        return False
    if NOISE_RE.search(combined):
        return True
    return False


# ── RSS Fetching ────────────────────────────────────────────────────


def fetch_feed(url: str, timeout: int = 15) -> bytes:
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; DailyInformantBot/1.0)"
    })
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_rss(xml_bytes: bytes, source_name: str, lean: str) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    items = []

    for item in root.findall(".//channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = re.sub(r"<[^>]+>", "", (item.findtext("description") or "")).strip()
        if title and link:
            items.append({
                "source_name": source_name, "lean": lean,
                "title": title, "link": link,
                "pub_date": pub_date, "description": description[:400],
            })

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "").strip() if link_el is not None else ""
        pub_date = (entry.findtext("atom:updated", namespaces=ns) or "").strip()
        description = re.sub(r"<[^>]+>", "", (entry.findtext("atom:summary", namespaces=ns) or "")).strip()
        if title and link:
            items.append({
                "source_name": source_name, "lean": lean,
                "title": title, "link": link,
                "pub_date": pub_date, "description": description[:400],
            })

    return items


def fetch_all_feeds() -> list[dict]:
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


# ── Deduplication ───────────────────────────────────────────────────

# Common filler words to ignore when comparing headlines
STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "is", "are", "was", "were", "be", "been", "has", "have", "had",
    "it", "its", "that", "this", "with", "from", "by", "as", "but",
    "not", "no", "will", "can", "do", "does", "did", "may", "says",
    "said", "new", "over", "after", "how", "why", "what", "who",
    "could", "would", "about", "into", "up", "out", "more", "than",
}


def extract_key_words(title: str) -> set[str]:
    """Extract meaningful words from a headline, ignoring stop words."""
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 2}


def deduplicate(items: list[dict]) -> list[dict]:
    """
    Remove duplicate stories using:
    1. Exact URL match
    2. High keyword overlap in headlines (catches same event, different wording)
    """
    seen_links = set()
    accepted = []
    accepted_keywords = []

    for item in items:
        # Skip exact URL duplicates
        if item["link"] in seen_links:
            continue

        # Extract meaningful keywords from this headline
        keywords = extract_key_words(item["title"])

        if len(keywords) < 2:
            # Very short headline, just check URL
            accepted.append(item)
            seen_links.add(item["link"])
            accepted_keywords.append(keywords)
            continue

        # Check against all accepted headlines for keyword overlap
        is_duplicate = False
        for prev_kw in accepted_keywords:
            if len(prev_kw) < 2:
                continue
            # Calculate overlap as fraction of the smaller set
            overlap = len(keywords & prev_kw)
            smaller = min(len(keywords), len(prev_kw))
            if smaller > 0 and overlap / smaller >= 0.5:
                is_duplicate = True
                break

        if not is_duplicate:
            accepted.append(item)
            seen_links.add(item["link"])
            accepted_keywords.append(keywords)

    return accepted


def filter_noise(items: list[dict]) -> list[dict]:
    filtered = []
    noise_count = 0
    for item in items:
        if is_politician_noise(item["title"], item.get("description", "")):
            noise_count += 1
        else:
            filtered.append(item)
    if noise_count:
        print(f"   Filtered {noise_count} politician-noise stories")
    return filtered


# ── Multi-AI Story Selection ────────────────────────────────────────

SELECTION_PROMPT = """You are an editorial director for The Daily Informant, a calm, unbiased, fact-only morning news briefing.

Below is a numbered list of today's stories from sources across the political spectrum (left, center, right).

YOUR JOB: Select the 12 most important stories for an informed reader's morning briefing.

SELECTION CRITERIA:
1. IMPACT — How many people does this actually affect?
2. ACTION — Prefer stories about things that HAPPENED (laws, rulings, events, data releases) over things people SAID
3. DIVERSITY — Cover multiple topics: world affairs, economy, science, health, tech. Don't let one topic dominate.
4. BALANCE — Don't favor stories from any political lean. A Fox News story and an NPR story about the same event both validate its importance.
5. SKIP politician theater — "X slams Y" or "X fires back" without concrete action is noise, not news
6. SKIP celebrity/entertainment unless it has genuine policy or public safety implications
7. DO NOT select multiple stories about the same event — pick the best one

Return ONLY a JSON array of the story numbers you selected, ranked by importance.
Example: [4, 17, 2, 31, 8, 22, 11, 45, 3, 29, 14, 38]

Return ONLY the JSON array, nothing else."""


def build_story_pool_text(items: list[dict]) -> str:
    lines = []
    for i, item in enumerate(items):
        line = f"{i+1}. [{item['source_name']}] {item['title']}"
        if item.get("description"):
            line += f" — {item['description'][:150]}"
        lines.append(line)
    return "\n".join(lines)


def _call_api(url: str, headers: dict, payload: dict, model_name: str, response_path: str = "openai") -> list[int]:
    """Generic API caller with retry logic. Returns list of story numbers."""
    data_bytes = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data_bytes, headers=headers, method="POST")

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))

                if response_path == "anthropic":
                    raw_text = data["content"][0]["text"]
                else:
                    raw_text = data["choices"][0]["message"]["content"]

                raw_text = raw_text.strip()
                match = re.search(r'\[[\d\s,]+\]', raw_text)
                if match:
                    numbers = json.loads(match.group())
                    return [int(n) for n in numbers if isinstance(n, (int, float))]
                else:
                    print(f"    {model_name}: Could not parse selection from response")
                    return []

        except HTTPError as e:
            last_error = e
            if e.code in (429, 500, 502, 503):
                wait = RETRY_BASE_DELAY * (attempt + 1)
                print(f"    {model_name} error ({e.code}). Waiting {wait}s... (attempt {attempt + 1})")
                time.sleep(wait)
                continue
            else:
                print(f"    {model_name} HTTP error: {e.code}")
                return []
        except Exception as e:
            last_error = e
            time.sleep(RETRY_BASE_DELAY)
            continue

    print(f"    {model_name} failed after {MAX_RETRIES} retries: {last_error}")
    return []


def call_openai_selection(pool_text: str) -> list[int]:
    return _call_api(
        url="https://api.openai.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        payload={
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": SELECTION_PROMPT},
                {"role": "user", "content": pool_text},
            ],
            "temperature": 0.3,
        },
        model_name="OpenAI",
    )


def call_claude_selection(pool_text: str) -> list[int]:
    return _call_api(
        url="https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        payload={
            "model": CLAUDE_MODEL,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": f"{SELECTION_PROMPT}\n\n{pool_text}"},
            ],
            "temperature": 0.3,
        },
        model_name="Claude",
        response_path="anthropic",
    )


def call_grok_selection(pool_text: str) -> list[int]:
    return _call_api(
        url="https://api.x.ai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {XAI_API_KEY}",
        },
        payload={
            "model": GROK_MODEL,
            "messages": [
                {"role": "system", "content": SELECTION_PROMPT},
                {"role": "user", "content": pool_text},
            ],
            "temperature": 0.3,
        },
        model_name="Grok",
    )


def run_ai_selection(pool_text: str) -> dict[str, list[int]]:
    """Run story selection across all available AI models. Fully fault-tolerant."""
    results = {}

    # OpenAI (required for extraction, so must work for selection too)
    if OPENAI_API_KEY:
        print("  → OpenAI selecting stories...")
        try:
            picks = call_openai_selection(pool_text)
            if picks:
                results["OpenAI"] = picks
                print(f"    OpenAI picked {len(picks)} stories: {picks[:5]}...")
            else:
                print("    OpenAI returned no picks")
        except Exception as e:
            print(f"    OpenAI selection failed: {e}")
    else:
        print("  ✗ OpenAI: no API key")

    time.sleep(1)

    # Claude
    if ANTHROPIC_API_KEY:
        print("  → Claude selecting stories...")
        try:
            picks = call_claude_selection(pool_text)
            if picks:
                results["Claude"] = picks
                print(f"    Claude picked {len(picks)} stories: {picks[:5]}...")
            else:
                print("    Claude returned no picks")
        except Exception as e:
            print(f"    Claude selection failed: {e}")
    else:
        print("  ○ Claude: no API key (skipping)")

    time.sleep(1)

    # Grok
    if XAI_API_KEY:
        print("  → Grok selecting stories...")
        try:
            picks = call_grok_selection(pool_text)
            if picks:
                results["Grok"] = picks
                print(f"    Grok picked {len(picks)} stories: {picks[:5]}...")
            else:
                print("    Grok returned no picks")
        except Exception as e:
            print(f"    Grok selection failed: {e}")
    else:
        print("  ○ Grok: no API key (skipping)")

    return results


def build_consensus(selections: dict[str, list[int]], pool_size: int) -> list[int]:
    """
    Find stories that multiple AIs agree on.
    Returns story indices sorted by consensus strength then average rank.
    """
    num_models = len(selections)

    if num_models == 0:
        return []

    # If only 1 model available, use its picks directly
    if num_models == 1:
        model_name = list(selections.keys())[0]
        print(f"\n   Only 1 model available ({model_name}). Using its picks directly.")
        return selections[model_name][:MAX_STORIES]

    # Count how many models picked each story + track ranks
    vote_counts: dict[int, int] = {}
    rank_sums: dict[int, float] = {}

    for model_name, picks in selections.items():
        for rank, story_num in enumerate(picks):
            if 1 <= story_num <= pool_size:
                vote_counts[story_num] = vote_counts.get(story_num, 0) + 1
                rank_sums[story_num] = rank_sums.get(story_num, 0) + rank

    # Filter to stories with minimum consensus
    min_votes = min(MIN_CONSENSUS, num_models)
    consensus_stories = [
        s for s, votes in vote_counts.items()
        if votes >= min_votes
    ]

    # Sort by: most votes first, then by average rank (lower = more important)
    consensus_stories.sort(key=lambda s: (-vote_counts[s], rank_sums[s] / vote_counts[s]))

    print(f"\n   Consensus results ({num_models} models, min {min_votes} votes):")
    for s in consensus_stories[:MAX_STORIES]:
        avg_rank = rank_sums[s] / vote_counts[s]
        print(f"    Story #{s}: {vote_counts[s]}/{num_models} votes, avg rank {avg_rank:.1f}")

    # If consensus is too thin, supplement with highest-voted remaining stories
    if len(consensus_stories) < MAX_STORIES:
        remaining = [
            s for s in vote_counts.keys()
            if s not in consensus_stories
        ]
        remaining.sort(key=lambda s: (-vote_counts[s], rank_sums[s] / max(vote_counts[s], 1)))
        supplement = remaining[:MAX_STORIES - len(consensus_stories)]
        consensus_stories.extend(supplement)
        if supplement:
            print(f"   Added {len(supplement)} supplemental stories (single-model picks)")

    return consensus_stories[:MAX_STORIES]


# ── Fact Extraction ─────────────────────────────────────────────────

EXTRACTION_PROMPT = """You are the fact-extraction engine for The Daily Informant, a calm morning news briefing.

STRICT RULES:
1. FACTS ONLY — every bullet must be verifiable
2. NO sensational words (no "shocking", "devastating", "massive", "explosive")
3. NO opinion (no "experts warn", "critics say", "raising concerns")
4. NO speculation (no "could", "might" unless quoting a scheduled future event)
5. CALM TONE — short sentences, plain verbs
6. If a politician is mentioned, focus on the ACTION not the rhetoric
7. Minimum 2 bullets, maximum 4
8. Assign a category: World, Business, Science, Health, Tech, or Canada"""

EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "daily_brief_story",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "headline": {
                    "type": "string",
                    "description": "Neutral, calm headline. No clickbait. No sensational adjectives."
                },
                "facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-4 short factual bullet points. Each must be verifiable."
                },
                "category": {
                    "type": "string",
                    "description": "One of: World, Business, Science, Health, Tech, Canada"
                },
            },
            "required": ["headline", "facts", "category"],
        },
        "strict": True,
    },
}


def extract_facts(entry: dict) -> dict:
    """Use OpenAI to extract structured facts from a story."""
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
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
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


def build_story(entry: dict, idx: int) -> dict:
    """Build final story dict with AI-extracted facts."""
    slug = f"story-{idx + 1}"
    try:
        ai = extract_facts(entry)
        headline = ai.get("headline", entry["title"]).strip()
        category = ai.get("category", "World").strip()
        facts = [
            {"text": f.strip(), "source_url": entry["link"]}
            for f in ai.get("facts", [])
            if isinstance(f, str) and f.strip()
        ]
        if not facts:
            raise RuntimeError("No usable facts")

        print(f"  ✓ [{category}] \"{headline[:55]}\" ({len(facts)} facts)")
        return {
            "slug": slug, "headline": headline, "category": category,
            "facts": facts,
            "sources": [{"name": entry["source_name"], "url": entry["link"]}],
        }
    except Exception as e:
        print(f"  ✗ Story {idx+1} extraction failed: {e}")
        desc = entry.get("description", "Details available at source.")[:200]
        return {
            "slug": slug, "headline": entry["title"], "category": "World",
            "facts": [{"text": desc, "source_url": entry["link"]}],
            "sources": [{"name": entry["source_name"], "url": entry["link"]}],
        }


# ── Main Pipeline ───────────────────────────────────────────────────


def main():
    print("=" * 65)
    print("  The Daily Informant — Morning Pipeline v3.1")
    print(f"  {datetime.now(TORONTO).strftime('%Y-%m-%d %H:%M %Z')}")
    print("=" * 65)

    # Check which AI models are available
    models_available = []
    if OPENAI_API_KEY:
        models_available.append("OpenAI")
    if ANTHROPIC_API_KEY:
        models_available.append("Claude")
    if XAI_API_KEY:
        models_available.append("Grok")

    print(f"\n  AI models: {', '.join(models_available) or 'NONE'}")

    if not OPENAI_API_KEY:
        print("\n✗ OPENAI_API_KEY is required. Exiting.")
        sys.exit(1)

    # ── Step 1: Fetch ──
    print("\n─── Step 1: Fetching RSS feeds ───")
    all_items = fetch_all_feeds()
    if not all_items:
        print("\n✗ No items fetched. Exiting.")
        sys.exit(1)
    print(f"\n   Raw items: {len(all_items)}")

    # ── Step 2: Deduplicate & filter ──
    print("\n─── Step 2: Dedup & noise filter ───")
    unique = deduplicate(all_items)
    print(f"   After dedup: {len(unique)}")
    filtered = filter_noise(unique)
    print(f"   After noise filter: {len(filtered)}")

    # ── Step 3: AI selection ──
    print("\n─── Step 3: Multi-AI story selection ───")
    pool_text = build_story_pool_text(filtered)
    selections = run_ai_selection(pool_text)

    if not selections:
        print("\n⚠ No AI model returned selections. Using first stories as fallback.")
        consensus_indices = list(range(1, min(MAX_STORIES + 1, len(filtered) + 1)))
    else:
        consensus_indices = build_consensus(selections, len(filtered))

    # Map indices back to items (1-based)
    consensus_items = []
    for idx in consensus_indices:
        if 1 <= idx <= len(filtered):
            consensus_items.append(filtered[idx - 1])

    print(f"\n   Final selection: {len(consensus_items)} stories")

    # ── Step 4: Extract facts ──
    print("\n─── Step 4: Fact extraction ───")
    stories = []
    for i, item in enumerate(consensus_items):
        stories.append(build_story(item, i))
        if i < len(consensus_items) - 1:
            time.sleep(1.5)

    # ── Step 5: Assemble ──
    daily_path = Path("data/daily.json")
    existing = {}
    if daily_path.exists():
        try:
            existing = json.loads(daily_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    daily_data = {
        "date": datetime.now(TORONTO).strftime("%Y-%m-%d"),
        "top_stories": stories,
        "ongoing_topics": existing.get("ongoing_topics", []),
        "good_developments": existing.get("good_developments", []),
        "optional_reflection": existing.get(
            "optional_reflection",
            "In times of uncertainty, may we seek truth with humility and share it with grace. "
            "Lord, grant us wisdom to see clearly, courage to speak honestly, and compassion "
            "for those whose stories we carry today. Amen.",
        ),
        "_meta": {
            "pipeline_version": "3.1",
            "models_used": list(selections.keys()),
            "feeds_attempted": len(FEEDS),
            "raw_items": len(all_items),
            "after_dedup": len(unique),
            "after_filter": len(filtered),
            "consensus_stories": len(consensus_items),
        },
    }

    daily_path.write_text(
        json.dumps(daily_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Summary
    categories = set(s.get("category", "?") for s in stories)
    source_leans = set()
    for idx in consensus_indices:
        if 1 <= idx <= len(filtered):
            source_leans.add(filtered[idx - 1]["lean"])

    print(f"\n{'=' * 65}")
    print(f"  DONE — {len(stories)} stories written to data/daily.json")
    print(f"  Models: {', '.join(selections.keys()) or 'fallback'}")
    print(f"  Categories: {', '.join(sorted(categories))}")
    print(f"  Source spectrum: {', '.join(sorted(source_leans))}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
