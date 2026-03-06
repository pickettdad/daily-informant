#!/usr/bin/env python3
"""
The Daily Informant — Morning Pipeline v2
==========================================
- Broad RSS coverage across categories (World, Business, Science, Canada, etc.)
- Politician-noise filter (skip "X said Y" unless tied to real action)
- Category diversity (no more than 2 stories per category)
- Better deduplication (skip stories about the same event)
- Improved AI prompt with Editorial Constitution rules baked in

Usage:
  python scripts/generate_daily.py

Required env vars:
  OPENAI_API_KEY  — OpenAI API key for fact extraction
"""

import json
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

# ── Config ──────────────────────────────────────────────────────────

TORONTO = ZoneInfo("America/Toronto")

# Curated RSS feeds organized by category
FEEDS = [
    # ── World / Wire Services ──
    {"name": "BBC World",       "url": "https://feeds.bbci.co.uk/news/world/rss.xml",         "category": "World"},
    {"name": "Al Jazeera",      "url": "https://www.aljazeera.com/xml/rss/all.xml",            "category": "World"},
    {"name": "CBC World",       "url": "https://www.cbc.ca/webfeed/rss/rss-world",             "category": "World"},
    {"name": "NPR World",       "url": "https://feeds.npr.org/1004/rss.xml",                   "category": "World"},

    # ── Business / Economy ──
    {"name": "BBC Business",    "url": "https://feeds.bbci.co.uk/news/business/rss.xml",       "category": "Business"},
    {"name": "CBC Business",    "url": "https://www.cbc.ca/webfeed/rss/rss-business",          "category": "Business"},

    # ── Science / Health / Tech ──
    {"name": "BBC Science",     "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "category": "Science"},
    {"name": "BBC Health",      "url": "https://feeds.bbci.co.uk/news/health/rss.xml",         "category": "Health"},
    {"name": "BBC Tech",        "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",     "category": "Tech"},
    {"name": "NPR Science",    "url": "https://feeds.npr.org/1007/rss.xml",                    "category": "Science"},
    {"name": "NPR Health",     "url": "https://feeds.npr.org/1128/rss.xml",                    "category": "Health"},

    # ── Canada ──
    {"name": "CBC Top Stories", "url": "https://www.cbc.ca/webfeed/rss/rss-topstories",        "category": "Canada"},
    {"name": "CBC Politics",    "url": "https://www.cbc.ca/webfeed/rss/rss-politics",          "category": "Canada"},
]

# How many stories in the final daily edition
MAX_STORIES = 8

# Max stories from any single category (ensures diversity)
MAX_PER_CATEGORY = 2

# Max items to pull from each individual feed
ITEMS_PER_FEED = 5

# OpenAI settings
OPENAI_MODEL = "gpt-4o-mini"
MAX_RETRIES = 3
RETRY_BASE_DELAY = 5

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


# ── Politician Noise Filter ────────────────────────────────────────
# Stories whose core is "politician said X" without a concrete action
# get filtered out. These patterns catch the noise.

NOISE_PATTERNS = [
    r"\bslam[s]?\b",
    r"\bblast[s]?\b",
    r"\bclap[s]? back\b",
    r"\bfires back\b",
    r"\bgoes (off|viral)\b",
    r"\bspar[s]?\b",
    r"\boutrage[d]?\b",
    r"\bbacklash\b",
    r"\bcalls out\b",
    r"\brips\b",
    r"\bshut[s]? down\b",
    r"\bdoubles down\b",
    r"\bmocks?\b",
    r"\brant[s]?\b",
    r"\bfeud\b",
    r"\bsparks controversy\b",
    r"\btrending\b",
    r"\bbreaking:\b",
    r"\bshocking\b",
    r"\bexplosive\b",
    r"\bbombshell\b",
]

# These words in a headline suggest the story IS about real action (not just talk)
ACTION_INDICATORS = [
    r"\bsign[s|ed]?\b",
    r"\bpass(es|ed)?\b",
    r"\bapprov(es|ed)?\b",
    r"\brul(es|ed|ing)\b",
    r"\bveto(es|ed)?\b",
    r"\bexecutive order\b",
    r"\bbill\b",
    r"\blaw\b",
    r"\bregulat(e|ion|ory)\b",
    r"\bsanction[s]?\b",
    r"\btreaty\b",
    r"\bindic[t]?\b",
    r"\barrest(s|ed)?\b",
    r"\bconvict(s|ed|ion)?\b",
    r"\bsentenc(e|ed|ing)\b",
    r"\bdepl(oy|oyed|oyment)\b",
    r"\bstrike[s]?\b",
    r"\bbudget\b",
    r"\brate\b",
    r"\breport(s|ed)?\b",
    r"\brecall(s|ed)?\b",
    r"\blaunch(es|ed)?\b",
    r"\bdiscover(y|ed|ies)?\b",
    r"\bvaccine\b",
    r"\belection\b",
    r"\bresign(s|ed|ation)?\b",
    r"\bappoint(s|ed|ment)?\b",
]

NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.IGNORECASE)
ACTION_RE = re.compile("|".join(ACTION_INDICATORS), re.IGNORECASE)


def is_politician_noise(title: str, description: str = "") -> bool:
    """
    Returns True if the story appears to be political theater
    rather than a concrete policy action.
    """
    combined = f"{title} {description}"

    # If the headline has action indicators, it's probably real news
    if ACTION_RE.search(combined):
        return False

    # If it matches noise patterns, skip it
    if NOISE_RE.search(combined):
        return True

    return False


# ── RSS Fetching ────────────────────────────────────────────────────


def fetch_feed(url: str, timeout: int = 20) -> bytes:
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; DailyInformantBot/1.0)"
    })
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_rss(xml_bytes: bytes, source_name: str, category: str) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    items = []

    # Standard RSS
    for item in root.findall(".//channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()
        # Strip HTML tags from description
        description = re.sub(r"<[^>]+>", "", description).strip()

        if title and link:
            items.append({
                "source_name": source_name,
                "category": category,
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "description": description[:500],  # Cap description length
            })

    # Atom feeds
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "").strip() if link_el is not None else ""
        pub_date = (entry.findtext("atom:updated", namespaces=ns) or "").strip()
        description = (entry.findtext("atom:summary", namespaces=ns) or "").strip()
        description = re.sub(r"<[^>]+>", "", description).strip()

        if title and link:
            items.append({
                "source_name": source_name,
                "category": category,
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "description": description[:500],
            })

    return items


def fetch_all_feeds() -> list[dict]:
    all_items = []
    for feed in FEEDS:
        try:
            xml_bytes = fetch_feed(feed["url"])
            parsed = parse_rss(xml_bytes, feed["name"], feed["category"])
            all_items.extend(parsed[:ITEMS_PER_FEED])
            print(f"  ✓ {feed['name']}: {len(parsed)} items found, using up to {ITEMS_PER_FEED}")
        except Exception as e:
            print(f"  ✗ {feed['name']}: {e}")
    return all_items


def deduplicate(items: list[dict]) -> list[dict]:
    """Remove duplicate stories by URL and similar headlines."""
    seen_links = set()
    seen_titles = []
    unique = []

    for item in items:
        # Skip exact URL duplicates
        if item["link"] in seen_links:
            continue

        # Skip very similar headlines (same event from different sources)
        title_lower = item["title"].lower()
        # Simple similarity: if >60% of words overlap with an existing title, skip
        title_words = set(title_lower.split())
        is_duplicate = False
        for prev_title in seen_titles:
            prev_words = set(prev_title.split())
            if len(title_words) > 0 and len(prev_words) > 0:
                overlap = len(title_words & prev_words) / min(len(title_words), len(prev_words))
                if overlap > 0.6:
                    is_duplicate = True
                    break

        if not is_duplicate:
            unique.append(item)
            seen_links.add(item["link"])
            seen_titles.append(title_lower)

    return unique


def select_stories(items: list[dict]) -> list[dict]:
    """
    Select the best stories with category diversity.
    Applies the politician-noise filter.
    """
    # Filter out politician noise
    filtered = []
    noise_count = 0
    for item in items:
        if is_politician_noise(item["title"], item.get("description", "")):
            noise_count += 1
            print(f"  ⊘ Filtered (politician noise): {item['title'][:70]}")
        else:
            filtered.append(item)

    if noise_count > 0:
        print(f"  Filtered {noise_count} politician-noise stories")

    # Select with category diversity
    selected = []
    category_counts = {}

    for item in filtered:
        cat = item["category"]
        if category_counts.get(cat, 0) >= MAX_PER_CATEGORY:
            continue
        selected.append(item)
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if len(selected) >= MAX_STORIES:
            break

    return selected


# ── OpenAI Fact Extraction ──────────────────────────────────────────

SYSTEM_PROMPT = """You are the editorial engine for The Daily Informant, a calm, fact-only morning news briefing.

Your job: rewrite each story as a neutral, verified summary.

STRICT RULES:
1. FACTS ONLY — every bullet must be something verifiable
2. NO sensational words: never use "shocking", "devastating", "massive", "explosive", "bombshell", "historic", "unprecedented"
3. NO opinion or analysis: no "experts warn", no "critics say", no "raising concerns"
4. NO speculation: no "could", "might", "may" unless quoting a scheduled future event
5. NO loaded framing: no "regime", "radical", "far-left/right" unless in a direct quote
6. CALM TONE: short sentences, plain verbs, measured language
7. If a politician is mentioned, focus on the ACTION (what was signed, passed, ruled) not the rhetoric
8. If information is limited, use fewer bullets (minimum 2) — do NOT pad with speculation

Write as if the reader is an intelligent adult who wants facts, not feelings."""

RESPONSE_SCHEMA = {
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


def call_openai(entry: dict) -> dict:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    user_prompt = f"""Source: {entry["source_name"]}
Category: {entry["category"]}
Title: {entry["title"]}
Published: {entry["pub_date"]}
Description: {entry["description"]}
Link: {entry["link"]}"""

    payload = json.dumps({
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": RESPONSE_SCHEMA,
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
                print(f"    API error ({e.code}). Waiting {wait}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            raise
        except URLError as e:
            last_error = e
            time.sleep(RETRY_BASE_DELAY)
            continue

    raise RuntimeError(f"OpenAI failed after {MAX_RETRIES} retries: {last_error}")


# ── Story Building ──────────────────────────────────────────────────


def build_story(entry: dict, idx: int) -> dict:
    slug = f"story-{idx + 1}"

    try:
        ai = call_openai(entry)
        headline = ai.get("headline", entry["title"]).strip()
        category = ai.get("category", entry["category"]).strip()
        fact_texts = ai.get("facts", [])

        facts = [
            {"text": f.strip(), "source_url": entry["link"]}
            for f in fact_texts
            if isinstance(f, str) and f.strip()
        ]

        if not facts:
            raise RuntimeError("AI returned no usable facts")

        print(f"  ✓ [{category}] \"{headline[:60]}\" ({len(facts)} facts)")

        return {
            "slug": slug,
            "headline": headline,
            "category": category,
            "facts": facts,
            "sources": [{"name": entry["source_name"], "url": entry["link"]}],
        }

    except Exception as e:
        print(f"  ✗ Story {idx + 1} AI failed: {e}")
        print(f"    Fallback: {entry['title'][:60]}")

        desc = entry.get("description", "")
        fallback_text = desc[:200] if desc else "Details available at source."

        return {
            "slug": slug,
            "headline": entry["title"],
            "category": entry["category"],
            "facts": [{"text": fallback_text, "source_url": entry["link"]}],
            "sources": [{"name": entry["source_name"], "url": entry["link"]}],
        }


# ── Main Pipeline ───────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("The Daily Informant — Morning Pipeline v2")
    print(f"Run time: {datetime.now(TORONTO).strftime('%Y-%m-%d %H:%M %Z')}")
    print("=" * 60)

    # 1. Fetch all feeds
    print("\n1. Fetching RSS feeds...")
    all_items = fetch_all_feeds()

    if not all_items:
        print("\n✗ No items fetched from any feed. Exiting.")
        sys.exit(1)

    print(f"\n   Total raw items: {len(all_items)}")

    # 2. Deduplicate
    print("\n2. Deduplicating...")
    unique_items = deduplicate(all_items)
    print(f"   After dedup: {unique_items.__len__()} unique stories")

    # 3. Select with filters + category diversity
    print("\n3. Applying filters & selecting stories...")
    selected = select_stories(unique_items)
    print(f"   Selected {len(selected)} stories for today's edition")

    if not selected:
        print("\n✗ No stories passed filters. Exiting.")
        sys.exit(1)

    # 4. AI extraction
    print("\n4. Running AI fact extraction...")
    stories = []
    for idx, item in enumerate(selected):
        stories.append(build_story(item, idx))
        if idx < len(selected) - 1:
            time.sleep(1.5)  # Gentle delay between API calls

    # 5. Load existing data (preserve ongoing topics, reflection, etc.)
    daily_path = Path("data/daily.json")
    existing = {}
    if daily_path.exists():
        try:
            existing = json.loads(daily_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 6. Assemble the daily edition
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
    }

    # 7. Write
    daily_path.write_text(
        json.dumps(daily_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Summary
    ai_count = sum(1 for s in stories if len(s["facts"]) > 1 or s["facts"][0]["text"] != "Details available at source.")
    categories_used = set(s.get("category", "?") for s in stories)

    print(f"\n{'=' * 60}")
    print(f"5. DONE — Wrote {len(stories)} stories to data/daily.json")
    print(f"   AI-extracted: {ai_count} | Categories: {', '.join(sorted(categories_used))}")
    print(f"   Date: {daily_data['date']}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
