"""Descriptive source citation resolver (replaces raw URLs with readable source titles)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from src.storage.local_db import LocalKnowledgeDB


def _friendly_domain_label(url: str) -> str:
    """Turn a URL hostname into a clean publication label when DB metadata is absent."""
    host = urlparse(url).netloc.lower().removeprefix("www.")
    mapping = {
        "nature.com": "Nature Neuroscience",
        "journals.plos.org": "PLOS Medicine",
        "medicalxpress.com": "Medical Xpress",
        "sciencedaily.com": "ScienceDaily",
        "who.int": "World Health Organization",
        "peterattiamd.com": "The Drive (Peter Attia)",
        "rbi.org.in": "Reserve Bank of India",
        "finshots.in": "Finshots",
        "ofdollarsanddata.com": "Of Dollars And Data",
        "ycombinator.com": "Y Combinator",
        "marginalrevolution.com": "Marginal Revolution",
        "paulgraham.com": "Paul Graham Essays",
        "fred.stlouisfed.org": "Federal Reserve Economic Data (FRED)",
        "blog.google": "Google AI Blog",
        "fs.blog": "Farnam Street",
        "aeon.co": "Aeon Magazine",
        "news.mit.edu": "MIT News",
        "quantamagazine.org": "Quanta Magazine",
        "plato.stanford.edu": "Stanford Encyclopedia of Philosophy",
        "waitbutwhy.com": "Wait But Why",
    }
    for domain, label in mapping.items():
        if domain in host:
            return label
    return host.split(".")[0].capitalize() if host else "Research Source"


def resolve_citations(
    source_links: list[str] | str,
    db: LocalKnowledgeDB | None = None,
    pillar_filter: str | None = None,
) -> list[dict[str, str]]:
    """Resolve raw URLs into deduplicated {source_name, title, url, pillar} citation dicts."""
    if isinstance(source_links, str):
        raw_urls = [line.strip() for line in source_links.splitlines() if line.strip()]
    else:
        raw_urls = [str(u).strip() for u in source_links if str(u).strip()]

    deduped_urls = list(dict.fromkeys(raw_urls))
    lookup: dict[str, dict[str, str]] = {}

    if db is not None:
        for tab, pillar in (
            ("Health_Research", "Health"),
            ("Wealth_Research", "Wealth"),
            ("Wisdom_Research", "Wisdom"),
        ):
            for row in db.get_tab_rows(tab, limit=250):
                url = str(row.get("original_article_link", "")).strip()
                if url:
                    lookup[url] = {
                        "source_name": str(row.get("source_name", "")).strip(),
                        "title": str(row.get("article_title", "")).strip(),
                        "url": url,
                        "pillar": pillar,
                    }

    citations: list[dict[str, str]] = []
    for url in deduped_urls:
        if not url.startswith(("http://", "https://")):
            continue
        meta = lookup.get(url)
        if meta:
            item = meta
        else:
            item = {
                "source_name": _friendly_domain_label(url),
                "title": "Read Original Research",
                "url": url,
                "pillar": "General",
            }
        if pillar_filter and item["pillar"] not in (pillar_filter, "General"):
            continue
        citations.append(item)

    return citations
