#!/usr/bin/env python3
"""
The Daily Informant — Morning Pipeline
=======================================
Fetches RSS feeds, extracts facts via OpenAI, writes data/daily.json.
Designed to run once daily via GitHub Actions at ~6 AM Toronto time.

Usage:
  python scripts/generate_daily.py

Required env vars:
  OPENAI_API_KEY  — OpenAI API key for fact extraction
"""

import json
import os
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

# RSS feeds to ingest. Add more as needed.
FEEDS = [
    {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "Reuters World", "url": "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best"},
    {"name": "CBC News", "url": "https://www.cbc.ca/webfeed/rss/rss-topstories"},
]

# How many stories to publish
MAX_STORIES = 6

# OpenAI model to use (gpt-4o-mini is cheap and fast)
OPENAI_MODEL = "gpt-4o-mini"

# Retry config for API calls
MAX_RETRIES = 3
RETRY_BASE_DELAY = 5  # seconds

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ── RSS Fetching ────────────────────────────────────────────────────


def fetch_feed(url: str, timeout: int = 20) -> bytes:
    """Fetch raw XML from an RSS feed URL."""
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; DailyInformantBot/1.0)"
    })
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_rss(xml_bytes: bytes, source_name: str) -> list[dict]:
    """Parse RSS XML into a list of story dicts."""
    root = ET.fromstring(xml_bytes)
    items = []

    # Standard RSS: channel > item
    for item in root.findall(".//channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()

        if title and link:
            items.append({
                "source_name": source_name,
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "description": description,
            })

    # Atom feeds: entry
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "").strip() if link_el is not None else ""
        pub_date = (entry.findtext("atom:updated", namespaces=ns) or "").strip()
        description = (entry.findtext("atom:summary", namespaces=ns) or "").strip()

        if title and link:
            items.append({
                "source_name": source_name,
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "description": description,
            })

    return items


def fetch_all_feeds() -> list[dict]:
    """Fetch and parse all configured feeds. Tolerates individual feed failures."""
    all_items = []
    for feed in FEEDS:
        try:
            xml_bytes = fetch_feed(feed["url"])
            parsed = parse_rss(xml_bytes, feed["name"])
            # Take a few from each feed to get diversity
            all_items.extend(parsed[:4])
            print(f"  ✓ {feed['name']}: {len(parsed)} items found, using up to 4")
        except Exception as e:
            print(f"  ✗ {feed['name']}: {e}")
    return all_items


def deduplicate(items: list[dict]) -> list[dict]:
    """Remove duplicate stories by link URL."""
    seen = set()
    unique = []
    for item in items:
        if item["link"] not in seen:
            unique.append(item)
            seen.add(item["link"])
    return unique


# ── OpenAI Fact Extraction ──────────────────────────────────────────

SYSTEM_PROMPT = """You write a calm, neutral, facts-only morning news briefing.

Rules:
- Extract ONLY verifiable facts from the provided headline and description
- No sensational words (no "shocking", "devastating", "massive", "historic")
- No opinion or analysis
- No speculation ("could", "might", "reportedly" without sourcing)
- No "experts say" or "experts warn"
- If a politician is mentioned, only include if tied to a concrete action (law, order, ruling)
- Keep bullets short and factual
- If information is very limited, use fewer bullets (minimum 2)
- Write the headline in a neutral, calm tone"""

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "daily_brief_story",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "headline": {"type": "string"},
                "facts": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["headline", "facts"],
        },
        "strict": True,
    },
}


def call_openai(entry: dict) -> dict:
    """Call OpenAI Chat Completions API with structured output."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    user_prompt = f"""Source: {entry["source_name"]}
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
            if e.code == 429:
                wait = RETRY_BASE_DELAY * (attempt + 1)
                print(f"    Rate limited (429). Waiting {wait}s before retry {attempt + 1}/{MAX_RETRIES}...")
                time.sleep(wait)
                continue
            elif e.code >= 500:
                wait = RETRY_BASE_DELAY * (attempt + 1)
                print(f"    Server error ({e.code}). Waiting {wait}s before retry...")
                time.sleep(wait)
                continue
            else:
                raise
        except URLError as e:
            last_error = e
            wait = RETRY_BASE_DELAY
            print(f"    Network error: {e}. Waiting {wait}s...")
            time.sleep(wait)
            continue

    raise RuntimeError(f"OpenAI failed after {MAX_RETRIES} retries: {last_error}")


# ── Story Building ──────────────────────────────────────────────────


def build_story(entry: dict, idx: int) -> dict:
    """Build a story dict from an RSS entry + AI extraction."""
    slug = f"story-{idx + 1}"

    try:
        ai = call_openai(entry)
        headline = ai.get("headline", entry["title"]).strip()
        fact_texts = ai.get("facts", [])

        facts = [
            {"text": f.strip(), "source_url": entry["link"]}
            for f in fact_texts
            if isinstance(f, str) and f.strip()
        ]

        if not facts:
            raise RuntimeError("AI returned no usable facts")

        print(f"  ✓ Story {idx + 1}: \"{headline[:60]}...\" ({len(facts)} facts)")

        return {
            "slug": slug,
            "headline": headline,
            "facts": facts,
            "sources": [{"name": entry["source_name"], "url": entry["link"]}],
        }

    except Exception as e:
        print(f"  ✗ Story {idx + 1} AI failed: {e}")
        print(f"    Falling back to RSS headline for: {entry['title'][:60]}")

        # Graceful fallback: use the raw RSS data
        facts = [
            {"text": entry["description"][:200] if entry.get("description") else "Details available at source.", "source_url": entry["link"]},
        ]
        return {
            "slug": slug,
            "headline": entry["title"],
            "facts": facts,
            "sources": [{"name": entry["source_name"], "url": entry["link"]}],
        }


# ── Main Pipeline ───────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("The Daily Informant — Morning Pipeline")
    print(f"Run time: {datetime.now(TORONTO).strftime('%Y-%m-%d %H:%M %Z')}")
    print("=" * 60)

    # 1. Fetch feeds
    print("\n1. Fetching RSS feeds...")
    all_items = fetch_all_feeds()

    if not all_items:
        print("\n✗ No items fetched from any feed. Exiting without updating.")
        sys.exit(1)

    # 2. Deduplicate and select top stories
    unique_items = deduplicate(all_items)
    top_items = unique_items[:MAX_STORIES]
    print(f"\n2. Selected {len(top_items)} stories from {len(unique_items)} unique items.")

    # 3. AI extraction (with delays between calls to avoid rate limits)
    print("\n3. Running AI fact extraction...")
    stories = []
    for idx, item in enumerate(top_items):
        stories.append(build_story(item, idx))
        # Small delay between API calls to be kind to rate limits
        if idx < len(top_items) - 1:
            time.sleep(2)

    # 4. Load existing data (preserve ongoing topics, good developments, reflection)
    daily_path = Path("data/daily.json")
    existing = {}
    if daily_path.exists():
        try:
            existing = json.loads(daily_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 5. Build the daily edition
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

    # 6. Write to file
    daily_path.write_text(
        json.dumps(daily_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    ai_count = sum(1 for s in stories if not s["headline"].startswith(("Sample:", "Error")))
    fallback_count = len(stories) - ai_count
    print(f"\n4. Wrote {len(stories)} stories to data/daily.json")
    print(f"   AI-extracted: {ai_count} | Fallback: {fallback_count}")
    print(f"\n{'=' * 60}")
    print("Pipeline complete.")


if __name__ == "__main__":
    main()
