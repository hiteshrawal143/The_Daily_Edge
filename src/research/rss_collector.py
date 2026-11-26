"""Free RSS/Atom/podcast collector using feedparser.

Collects only from public feeds defined in config/sources.json.
Never bypasses paywalls, logins, CAPTCHAs, or access controls.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from src.config import COLLECTED_DIR, IST, ensure_directories, load_sources, now_ist, today_ist_str
from src.storage.local_db import LocalKnowledgeDB

REQUEST_TIMEOUT_SEC = 15
USER_AGENT = "LifeTimeLibrary/1.0 (Personal Educational RSS Reader; +https://localhost)"


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and collapse whitespace cleanly."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


TZINFOS = {
    "UTC": 0,
    "GMT": 0,
    "EST": -5 * 3600,
    "EDT": -4 * 3600,
    "CST": -6 * 3600,
    "CDT": -5 * 3600,
    "MST": -7 * 3600,
    "MDT": -6 * 3600,
    "PST": -8 * 3600,
    "PDT": -7 * 3600,
}


def normalize_pub_date(entry: dict[str, Any]) -> str:
    """Convert feed entry publication date to ISO-8601 date string."""
    for field in ("published", "updated", "created"):
        val = entry.get(field)
        if val:
            try:
                dt = date_parser.parse(str(val), tzinfos=TZINFOS)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=IST)
                return dt.astimezone(IST).strftime("%Y-%m-%d")
            except (ValueError, TypeError, OverflowError):
                pass
    struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if struct:
        try:
            dt = datetime(*struct[:6], tzinfo=IST)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
    return today_ist_str()


def make_article_id(link: str, title: str) -> str:
    """Generate a deterministic short ID for deduplication."""
    basis = (link or title).strip().lower().encode("utf-8")
    return hashlib.sha256(basis).hexdigest()[:16]


def fetch_feed(
    source: dict[str, Any], pillar: str, max_items: int = 8
) -> tuple[list[dict[str, Any]], str]:
    """Fetch and parse a single public RSS/Atom feed.

    Returns (articles, status_message).
    """
    url = source["url"]
    headers = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"}
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SEC)
        if resp.status_code in (401, 403):
            return [], f"blocked_http_{resp.status_code}"
        resp.raise_for_status()
    except requests.RequestException as exc:
        return [], f"fetch_error: {type(exc).__name__}"

    parsed = feedparser.parse(resp.content)
    entries = getattr(parsed, "entries", []) or []
    if not entries:
        return [], "empty_feed"

    collected_at = today_ist_str()
    articles: list[dict[str, Any]] = []
    for entry in entries[:max_items]:
        title = clean_html(entry.get("title", ""))
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue

        raw_summary = entry.get("summary") or entry.get("description") or ""
        if not raw_summary and entry.get("content"):
            raw_summary = entry["content"][0].get("value", "")
        summary = clean_html(raw_summary)[:800]

        articles.append(
            {
                "article_id": make_article_id(link, title),
                "source_name": source["name"],
                "source_url": url,
                "publication_date": normalize_pub_date(entry),
                "article_title": title,
                "category": pillar.capitalize(),
                "original_article_link": link,
                "date_collected": collected_at,
                "summary": summary,
                "credibility_weight": int(source.get("credibility_weight", 8)),
                "source_type": source.get("type", "rss"),
                "topics": source.get("topics", []),
            }
        )

    return articles, f"ok ({len(articles)} items)"


def collect_all_research(
    db: LocalKnowledgeDB | None = None,
    max_per_feed: int = 6,
    save_snapshot: bool = True,
) -> dict[str, Any]:
    """Collect public RSS research across Health, Wealth, and Wisdom."""
    ensure_directories()
    db = db or LocalKnowledgeDB()
    sources = load_sources()
    db.upsert_sources(sources)

    results: dict[str, list[dict[str, Any]]] = {"health": [], "wealth": [], "wisdom": []}
    newly_added: dict[str, list[dict[str, Any]]] = {"health": [], "wealth": [], "wisdom": []}
    feed_statuses: list[dict[str, str]] = []

    for pillar in ("health", "wealth", "wisdom"):
        pillar_sources = sources.get(pillar, [])
        for src in pillar_sources:
            items, status = fetch_feed(src, pillar=pillar, max_items=max_per_feed)
            db.update_source_status(src["url"], status)
            feed_statuses.append({"pillar": pillar, "source": src["name"], "status": status})
            results[pillar].extend(items)

    snapshot = {
        "collected_at": now_ist().isoformat(),
        "date": today_ist_str(),
        "feed_statuses": feed_statuses,
        "articles": results,
        "newly_inserted_counts": {k: len(v) for k, v in newly_added.items()},
    }
    if save_snapshot:
        out_path = COLLECTED_DIR / f"{today_ist_str()}.json"
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, indent=2, ensure_ascii=False)

    return snapshot
