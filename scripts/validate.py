#!/usr/bin/env python3
"""Validate a NeuroDaily profile/config before import.

This validator is deliberately stricter than a JSON parser: a file can be valid
JSON and still be an invalid NeuroDaily config (wrong enum, bad URL, wrong type,
private delivery field). Errors include a field path so the fix is obvious.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

FORMAT = "neurodaily.profile"
VERSION = 1
SEARCH_MODES = {"any", "only", "prefer"}
SEARCH_SORTS = {"default", "latest", "relevance", "journal"}
FEED_KINDS = {"paper", "news", "policy", "funding", "conference"}
PRIVATE_FIELDS = {
    "email", "smtp", "password", "api_key", "apikey", "token", "secret",
    "credential", "webhook", "webhooks", "recipient", "recipients",
}
SECRET_QUERY_KEYS = {
    "key", "apikey", "token", "accesstoken", "authtoken", "secret",
    "password", "signature", "sig", "credential", "jwt",
}
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class ProfileError(Exception):
    """A load or schema error suitable for display, without a traceback."""


def _clean(value) -> str:
    return " ".join(str(value or "").split())


def _url_problem(value) -> str:
    if not isinstance(value, str) or not value.strip():
        return "must be a non-empty URL string"
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return "must be http(s) with a host"
    for key, _ in parse_qsl(parts.query, keep_blank_values=True):
        if re.sub(r"[^a-z]", "", key.casefold()) in SECRET_QUERY_KEYS:
            return f"URL query contains secret-like parameter {key!r}"
    return ""


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _list_of_strings(errors: list[str], value, path: str) -> None:
    if value is None:
        return
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{path} must be an array of strings")


def _private_fields(errors: list[str], value, path: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else key
            if key.casefold() in PRIVATE_FIELDS:
                errors.append(f"{child} is private and must not be in a shared profile")
            _private_fields(errors, item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _private_fields(errors, item, f"{path}[{index}]")


def _validate_config(config: dict, errors: list[str], warnings: list[str]) -> None:
    profile = config.get("profile")
    if profile is None:
        warnings.append("config.profile is missing; NeuroDaily may use a fallback name")
    elif not isinstance(profile, str) or not _clean(profile):
        errors.append("config.profile must be a non-empty string")
    elif not SLUG.fullmatch(profile):
        warnings.append("config.profile is not a lowercase slug; import may rename it")

    disciplines = config.get("disciplines")
    if not isinstance(disciplines, list) or not disciplines:
        errors.append("config.disciplines must contain at least one discipline")
    else:
        for index, row in enumerate(disciplines):
            path = f"config.disciplines[{index}]"
            if not isinstance(row, dict):
                errors.append(f"{path} must be an object")
                continue
            if not isinstance(row.get("name"), str) or not _clean(row.get("name")):
                errors.append(f"{path}.name is required")
            for key in ("keywords", "mesh_terms", "arxiv_cats", "bio_cats"):
                _list_of_strings(errors, row.get(key), f"{path}.{key}")
            enabled = row.get("enabled", True)
            if not isinstance(enabled, bool):
                errors.append(f"{path}.enabled must be boolean")
            elif enabled and not any(row.get(key) for key in
                                     ("keywords", "mesh_terms", "arxiv_cats", "bio_cats")):
                errors.append(f"{path} needs keywords/mesh_terms/arxiv_cats/bio_cats")

    _list_of_strings(errors, config.get("global_keywords"), "config.global_keywords")

    search = config.get("search")
    if search is not None:
        if not isinstance(search, dict):
            errors.append("config.search must be an object")
        else:
            if search.get("query") is not None and not isinstance(search.get("query"), str):
                errors.append("config.search.query must be a string")
            _list_of_strings(errors, search.get("authors"), "config.search.authors")
            if search.get("author_mode") not in (None, "intersect", "track"):
                errors.append("config.search.author_mode must be intersect/track")
            if search.get("journal_mode") not in (None, *SEARCH_MODES):
                errors.append("config.search.journal_mode must be any/only/prefer")
            if search.get("sort") not in (None, *SEARCH_SORTS):
                errors.append("config.search.sort must be default/latest/relevance/journal")
            _list_of_strings(errors, search.get("journals"), "config.search.journals")
            for key in ("sets", "rules"):
                value = search.get(key)
                if value is not None and not isinstance(value, dict):
                    errors.append(f"config.search.{key} must be an object")
                elif isinstance(value, dict) and any(not isinstance(item, str) for item in value.values()):
                    errors.append(f"config.search.{key} values must be strings")

    sources = config.get("sources")
    if sources is not None:
        if not isinstance(sources, dict):
            errors.append("config.sources must be an object")
        else:
            for name, options in sources.items():
                path = f"config.sources.{name}"
                if not isinstance(name, str) or not name:
                    errors.append("config.sources keys must be non-empty strings")
                    continue
                if not isinstance(options, dict):
                    errors.append(f"{path} must be an object")
                    continue
                if "enabled" in options and not isinstance(options["enabled"], bool):
                    errors.append(f"{path}.enabled must be boolean")
                for key in ("max_results", "lookback_days"):
                    if key in options and (not isinstance(options[key], int) or isinstance(options[key], bool)
                                           or options[key] < 1):
                        errors.append(f"{path}.{key} must be a positive integer")
                if options.get("type") in {"rss", "json_api", "json"}:
                    if not options.get("url"):
                        errors.append(f"{path}.url is required for type={options['type']}")
                    else:
                        problem = _url_problem(options["url"])
                        if problem:
                            errors.append(f"{path}.url: {problem}")
                if "url" in options and options["url"] is not None:
                    problem = _url_problem(options["url"])
                    if problem:
                        errors.append(f"{path}.url: {problem}")
                feed_kinds = options.get("feed_kinds")
                if feed_kinds is not None:
                    if not isinstance(feed_kinds, dict):
                        errors.append(f"{path}.feed_kinds must be an object")
                    else:
                        for feed_url, kind in feed_kinds.items():
                            if _url_problem(feed_url):
                                errors.append(f"{path}.feed_kinds key {feed_url!r}: {_url_problem(feed_url)}")
                            if kind not in FEED_KINDS:
                                errors.append(f"{path}.feed_kinds[{feed_url!r}] must be one of "
                                              f"{sorted(FEED_KINDS)}")

    feeds = config.get("policy_feeds")
    if feeds is not None:
        if not isinstance(feeds, list):
            errors.append("config.policy_feeds must be an array")
        else:
            if not feeds:
                warnings.append("config.policy_feeds is empty; policy/news will stay empty")
            for index, url in enumerate(feeds):
                problem = _url_problem(url)
                if problem:
                    errors.append(f"config.policy_feeds[{index}]: {problem}")

    windows = config.get("windows")
    if windows is not None:
        if not isinstance(windows, dict):
            errors.append("config.windows must be an object")
        else:
            for key, value in windows.items():
                if not _number(value) or value < 1:
                    errors.append(f"config.windows.{key} must be a positive number")

    journals = config.get("journals") or []
    if not isinstance(journals, list):
        errors.append("config.journals must be an array")
    else:
        seen = set()
        for index, row in enumerate(journals):
            path = f"config.journals[{index}]"
            if not isinstance(row, dict):
                errors.append(f"{path} must be an object")
                continue
            name = row.get("name")
            if not isinstance(name, str) or not _clean(name):
                errors.append(f"{path}.name is required")
            else:
                key = name.casefold()
                if key in seen:
                    warnings.append(f"duplicate journal: {name}")
                seen.add(key)
            for key in ("url", "rss"):
                value = row.get(key)
                if value:
                    problem = _url_problem(value)
                    if problem:
                        errors.append(f"{path}.{key}: {problem}")
            for key in ("impact_factor", "year"):
                if row.get(key) is not None and not _number(row[key]):
                    errors.append(f"{path}.{key} must be a number or null")

    _private_fields(errors, config, "config")


def validate_document(document) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(document, dict):
        return ["document must be a JSON object"], warnings
    if "format" in document or "version" in document or "config" in document:
        if document.get("format") != FORMAT:
            errors.append(f"format must be {FORMAT!r}")
        if document.get("version") != VERSION:
            errors.append("version must be 1")
        config = document.get("config")
        if not isinstance(config, dict):
            return errors + ["config must be an object"], warnings
    else:
        warnings.append("plain config detected; expected the portable wrapper")
        config = document
    _validate_config(config, errors, warnings)
    return errors, warnings


def load(path: str):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ProfileError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON number {value}")))
    except json.JSONDecodeError as exc:
        raise ProfileError(f"invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}") from exc
    except ValueError as exc:
        raise ProfileError(str(exc)) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="profile or config JSON")
    parser.add_argument("--json", action="store_true", help="machine-readable result")
    args = parser.parse_args()
    try:
        document = load(args.path)
        errors, warnings = validate_document(document)
    except ProfileError as exc:
        errors, warnings = [str(exc)], []
    result = {"ok": not errors, "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        if not errors:
            print("OK: profile is valid")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
