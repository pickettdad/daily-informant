#!/usr/bin/env python3
"""
The Daily Informant — Data Schema Validator
============================================

Validates data/*.json artifacts against required schemas.
Run standalone:  python scripts/validate_schemas.py
Import:          from validate_schemas import validate_all

Exit code 0 = all valid, 1 = errors found.
"""

import json
import sys
from pathlib import Path

DATA_DIR = Path("data")

# ── Schema Definitions ──────────────────────────────────────────────

STORY_REQUIRED_KEYS = {"slug", "headline", "sources"}
STORY_EXPECTED_KEYS = {"bottom_line", "body", "category", "key_points",
                       "component_articles", "stakeholder_quotes",
                       "is_good_development", "is_negative", "positive_thought"}

ONGOING_TOPIC_REQUIRED_KEYS = {"slug", "topic", "summary", "timeline"}

DAILY_REQUIRED_KEYS = {"date", "top_stories"}
DAILY_EXPECTED_KEYS = {"need_to_know", "ongoing_topics", "good_developments", "_meta"}

META_REQUIRED_KEYS = {"pipeline_version", "models_used", "feeds_attempted",
                      "raw_items", "groups_formed", "consensus_articles"}

TOPICS_REQUIRED_KEYS = {"topics"}

ARCHIVE_ENTRY_REQUIRED_KEYS = {"date", "headline", "slug"}


# ── Validators ──────────────────────────────────────────────────────

def validate_story(story, index, context="top_stories"):
    """Validate a single story/article object. Returns list of error strings."""
    errors = []
    prefix = f"{context}[{index}]"

    if not isinstance(story, dict):
        return [f"{prefix}: expected object, got {type(story).__name__}"]

    missing = STORY_REQUIRED_KEYS - set(story.keys())
    if missing:
        errors.append(f"{prefix}: missing required keys: {missing}")

    if story.get("slug") and not isinstance(story["slug"], str):
        errors.append(f"{prefix}.slug: expected string")

    if story.get("headline") and not isinstance(story["headline"], str):
        errors.append(f"{prefix}.headline: expected string")

    if story.get("headline") and len(story["headline"].strip()) < 5:
        errors.append(f"{prefix}.headline: suspiciously short ({story['headline']!r})")

    sources = story.get("sources", [])
    if not isinstance(sources, list):
        errors.append(f"{prefix}.sources: expected array")
    elif len(sources) == 0:
        errors.append(f"{prefix}.sources: empty — every story needs at least one source")
    else:
        for si, src in enumerate(sources):
            if not isinstance(src, dict):
                errors.append(f"{prefix}.sources[{si}]: expected object")
            elif not src.get("name") or not src.get("url"):
                errors.append(f"{prefix}.sources[{si}]: missing name or url")

    body = story.get("body", "")
    if isinstance(body, str) and len(body.split()) < 20:
        errors.append(f"{prefix}.body: only {len(body.split())} words (expected 50+)")

    return errors


def validate_ongoing_topic(topic, index):
    """Validate a single ongoing topic object."""
    errors = []
    prefix = f"topics[{index}]"

    if not isinstance(topic, dict):
        return [f"{prefix}: expected object, got {type(topic).__name__}"]

    missing = ONGOING_TOPIC_REQUIRED_KEYS - set(topic.keys())
    if missing:
        errors.append(f"{prefix}: missing required keys: {missing}")

    timeline = topic.get("timeline", [])
    if not isinstance(timeline, list):
        errors.append(f"{prefix}.timeline: expected array")
    else:
        for ti, entry in enumerate(timeline):
            if not isinstance(entry, dict):
                errors.append(f"{prefix}.timeline[{ti}]: expected object")
            elif not entry.get("date") or not entry.get("text"):
                errors.append(f"{prefix}.timeline[{ti}]: missing date or text")

    return errors


def validate_daily(data):
    """Validate daily.json structure. Returns (errors, warnings)."""
    errors, warnings = [], []

    if not isinstance(data, dict):
        return [f"daily.json: expected object, got {type(data).__name__}"], []

    missing = DAILY_REQUIRED_KEYS - set(data.keys())
    if missing:
        errors.append(f"daily.json: missing required keys: {missing}")

    missing_expected = DAILY_EXPECTED_KEYS - set(data.keys())
    if missing_expected:
        warnings.append(f"daily.json: missing expected keys: {missing_expected}")

    # Validate date format
    date = data.get("date", "")
    if date and (len(date) != 10 or date.count("-") != 2):
        errors.append(f"daily.json.date: invalid format ({date!r}), expected YYYY-MM-DD")

    # Validate stories
    stories = data.get("top_stories", [])
    if not isinstance(stories, list):
        errors.append("daily.json.top_stories: expected array")
    elif len(stories) == 0:
        errors.append("daily.json.top_stories: empty — no stories in edition")
    else:
        for i, story in enumerate(stories):
            errors.extend(validate_story(story, i, "top_stories"))

    # Validate _meta
    meta = data.get("_meta", {})
    if isinstance(meta, dict):
        missing_meta = META_REQUIRED_KEYS - set(meta.keys())
        if missing_meta:
            warnings.append(f"daily.json._meta: missing keys: {missing_meta}")
    else:
        warnings.append("daily.json._meta: expected object")

    # Validate need_to_know
    ntk = data.get("need_to_know", [])
    if isinstance(ntk, list):
        for i, item in enumerate(ntk):
            if isinstance(item, dict):
                if not item.get("headline"):
                    warnings.append(f"daily.json.need_to_know[{i}]: missing headline")
            else:
                errors.append(f"daily.json.need_to_know[{i}]: expected object")

    return errors, warnings


def validate_topics(data):
    """Validate topics.json structure."""
    errors, warnings = [], []

    if not isinstance(data, dict):
        return [f"topics.json: expected object, got {type(data).__name__}"], []

    missing = TOPICS_REQUIRED_KEYS - set(data.keys())
    if missing:
        errors.append(f"topics.json: missing required keys: {missing}")

    topics = data.get("topics", [])
    if not isinstance(topics, list):
        errors.append("topics.json.topics: expected array")
    else:
        slugs = set()
        for i, topic in enumerate(topics):
            errors.extend(validate_ongoing_topic(topic, i))
            slug = topic.get("slug", "")
            if slug in slugs:
                warnings.append(f"topics.json: duplicate slug {slug!r}")
            slugs.add(slug)

    return errors, warnings


def validate_archive(data):
    """Validate archive.json structure."""
    errors, warnings = [], []

    if not isinstance(data, list):
        return [f"archive.json: expected array, got {type(data).__name__}"], []

    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            errors.append(f"archive[{i}]: expected object")
            continue
        missing = ARCHIVE_ENTRY_REQUIRED_KEYS - set(entry.keys())
        if missing:
            errors.append(f"archive[{i}]: missing required keys: {missing}")

    return errors, warnings


def validate_manifest(data):
    """Validate edition_manifest.json structure."""
    errors, warnings = [], []

    if not isinstance(data, dict):
        return [f"edition_manifest.json: expected object, got {type(data).__name__}"], []

    required = {"date", "pipeline_version", "run_timestamp", "feeds", "selection", "articles"}
    missing = required - set(data.keys())
    if missing:
        errors.append(f"edition_manifest.json: missing required keys: {missing}")

    return errors, warnings


# ── Main Runner ─────────────────────────────────────────────────────

def validate_all(data_dir=None):
    """Run all validators. Returns (total_errors, total_warnings)."""
    if data_dir is None:
        data_dir = DATA_DIR

    total_errors, total_warnings = 0, 0

    files = {
        "daily.json": (validate_daily, True),
        "topics.json": (validate_topics, True),
        "archive.json": (validate_archive, True),
        "edition_manifest.json": (validate_manifest, False),
    }

    for filename, (validator, required) in files.items():
        filepath = data_dir / filename
        if not filepath.exists():
            if required:
                print(f"  ✗ {filename}: FILE NOT FOUND")
                total_errors += 1
            else:
                print(f"  ○ {filename}: not present (optional)")
            continue

        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  ✗ {filename}: INVALID JSON — {e}")
            total_errors += 1
            continue

        errors, warnings = validator(data)
        total_errors += len(errors)
        total_warnings += len(warnings)

        if errors:
            print(f"  ✗ {filename}: {len(errors)} errors, {len(warnings)} warnings")
            for err in errors[:10]:
                print(f"    ERROR: {err}")
            for warn in warnings[:5]:
                print(f"    WARN:  {warn}")
        elif warnings:
            print(f"  ⚠ {filename}: OK ({len(warnings)} warnings)")
            for warn in warnings[:5]:
                print(f"    WARN:  {warn}")
        else:
            print(f"  ✓ {filename}: valid")

    return total_errors, total_warnings


if __name__ == "__main__":
    print("\n─── Data Schema Validation ───")
    errors, warnings = validate_all()
    print(f"\n  Total: {errors} errors, {warnings} warnings")
    if errors:
        print("  VALIDATION FAILED")
        sys.exit(1)
    else:
        print("  ALL VALID")
        sys.exit(0)
