#!/usr/bin/env python3
"""Build a portable NeuroDaily profile from a guided topic description."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_WINDOWS = {
    "daily_paper_hours": 36,
    "manual_paper_hours": 240,
    "trials_hours": 36,
    "funding_hours": 168,
    "news_hours": 36,
    "other_lookback_days": 7,
}


def clean(value) -> str:
    return " ".join(str(value or "").split())


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(value).casefold()).strip("-")[:60] or "topic"


def quote(term: str) -> str:
    term = clean(term).replace('"', "")
    return f'"{term}"' if " " in term else term


def unique(values) -> list[str]:
    out, seen = [], set()
    for value in values or []:
        value = clean(value)
        if value and value.casefold() not in seen:
            seen.add(value.casefold())
            out.append(value)
    return out


def build(topic: dict) -> dict:
    name = clean(topic.get("topic"))
    if not name:
        raise ValueError("topic is required")
    aliases = unique([name, *(topic.get("aliases") or [])])
    subtopics = unique(topic.get("subtopics") or [])
    mesh = unique(topic.get("mesh_terms") or [])
    exclude = unique(topic.get("exclude") or [])
    terms = unique([*aliases, *subtopics])
    query = " OR ".join(quote(term) for term in terms[:8])
    if exclude:
        query = f"({query}) AND NOT (" + " OR ".join(quote(term) for term in exclude) + ")"
    journals = []
    for row in topic.get("journals") or []:
        row = {"name": row} if isinstance(row, str) else dict(row)
        if clean(row.get("name")):
            journals.append({"name": clean(row["name"]), "url": row.get("url", ""),
                             "rss": row.get("rss", ""), "category": row.get("category", "topic"),
                             "impact_factor": row.get("impact_factor"),
                             "jcr": row.get("jcr", ""), "cas": row.get("cas", ""),
                             "metric_year": row.get("metric_year"),
                             "aliases": list(row.get("aliases") or []),
                             "issns": list(row.get("issns") or [])})
    sources = topic.get("sources") or {
        "journal": {"enabled": True, "max_results": 200, "lookback_days": 2},
        "pubmed": {"enabled": True, "max_results": 500, "lookback_days": 2},
        "biorxiv": {"enabled": True, "max_results": 200, "lookback_days": 2},
        "arxiv": {"enabled": False},
        "trials": {"enabled": True, "max_results": 100, "lookback_days": 2},
        "policy": {"enabled": True, "max_results": 100, "lookback_days": 2},
    }
    config = {
        "profile": clean(topic.get("profile")) or slug(name),
        "disciplines": [{"name": name, "keywords": terms, "mesh_terms": mesh,
                         "arxiv_cats": [], "bio_cats": [], "enabled": True}],
        "global_keywords": terms,
        "search": {"query": query, "sets": {}, "journal_mode": "prefer",
                   "journals": [row["name"] for row in journals], "sort": "relevance"},
        "sources": sources,
        "windows": dict(DEFAULT_WINDOWS, **(topic.get("windows") or {})),
        "policy_feeds": unique(topic.get("policy_feeds") or []),
        "journals": journals,
    }
    return {"format": "neurodaily.profile", "version": 1, "config": config}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic")
    parser.add_argument("--out", default="neurodaily-topic.json")
    args = parser.parse_args()
    try:
        data = json.loads(Path(args.topic).read_text(encoding="utf-8"))
        profile = build(data)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    Path(args.out).write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    print(f"{profile['config']['profile']}: {len(profile['config']['global_keywords'])} terms, "
          f"{len(profile['config']['journals'])} journals -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
