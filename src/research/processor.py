"""Research categorization, deduplication, ranking, and claim classification."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from src.config import IST, today_ist_str
from src.storage.local_db import LocalKnowledgeDB

CLICKBAIT_PATTERNS = (
    r"\byou won't believe\b",
    r"\bshocking\b",
    r"\bone weird trick\b",
    r"\bdoctors hate\b",
    r"\bsecret they don't want\b",
    r"\bget rich quick\b",
    r"\bguaranteed returns\b",
    r"\b100x\b",
    r"\bmiracle cure\b",
)

PILLAR_KEYWORDS: dict[str, tuple[str, ...]] = {
    "health": (
        "sleep", "nutrition", "exercise", "fitness", "longevity", "brain", "neuroscience",
        "mental health", "stress", "cortisol", "biology", "diet", "metabolism", "habit",
        "circadian", "cardiovascular", "muscle", "clinical", "study", "therapy",
    ),
    "wealth": (
        "finance", "investing", "economy", "inflation", "interest rate", "startup",
        "business", "revenue", "market", "career", "negotiation", "sales", "ai ",
        "compounding", "capital", "rbi", "monetary", "productivity", "entrepreneur",
    ),
    "wisdom": (
        "philosophy", "thinking", "decision", "mental model", "history", "psychology",
        "leadership", "communication", "relationship", "bias", "cognitive", "ethics",
        "stoic", "scientific method", "reason", "behavior", "behaviour", "society",
    ),
}


def slugify_topic(title: str) -> str:
    """Create a normalized slug to detect repeated topics across days."""
    words = re.findall(r"[a-z0-9]+", title.lower())
    stop = {"the", "a", "an", "and", "or", "of", "in", "on", "to", "for", "with", "how", "why", "what", "is", "are"}
    filtered = [w for w in words if w not in stop][:6]
    return "-".join(filtered) or "general-topic"


def is_clickbait(title: str, summary: str = "") -> bool:
    """Detect sensationalist or clickbait phrasing."""
    blob = f"{title} {summary}".lower()
    return any(re.search(pat, blob) for pat in CLICKBAIT_PATTERNS)


def classify_claim_type(source_type: str, title: str, summary: str) -> str:
    """Distinguish facts, expert opinions, and speculation."""
    blob = f"{title} {summary}".lower()
    if source_type in ("scientific_feed", "official_institution", "official_public_health", "academic_reference", "university_research"):
        if any(w in blob for w in ("randomized", "meta-analysis", "trial", "nih", "who", "rbi", "data", "study found")):
            return "verified_research_or_official_data"
        return "scientific_or_institutional_report"
    if any(w in blob for w in ("might", "could", "prediction", "forecast", "rumor", "speculat")):
        return "speculation_or_forecast"
    return "expert_opinion_or_analysis"


def compute_relevance_score(
    article: dict[str, Any],
    pillar: str,
    recent_slugs: set[str],
    today_str: str | None = None,
) -> float:
    """Rank findings by credibility, recency, topic match, and novelty."""
    today_dt = datetime.strptime(today_str or today_ist_str(), "%Y-%m-%d").replace(tzinfo=IST)
    credibility = float(article.get("credibility_weight", 8))

    try:
        pub_dt = datetime.strptime(article.get("publication_date", today_ist_str()), "%Y-%m-%d").replace(tzinfo=IST)
        age_days = max(0, (today_dt - pub_dt).days)
    except ValueError:
        age_days = 7

    recency_bonus = max(0.0, 5.0 - min(age_days, 10) * 0.5)

    blob = f"{article.get('article_title', '')} {article.get('summary', '')}".lower()
    keyword_hits = sum(1 for kw in PILLAR_KEYWORDS.get(pillar, ()) if kw in blob)
    topic_bonus = min(4.0, keyword_hits * 0.8)

    slug = slugify_topic(article.get("article_title", ""))
    novelty_penalty = -6.0 if slug in recent_slugs else 0.0
    clickbait_penalty = -10.0 if is_clickbait(article.get("article_title", ""), article.get("summary", "")) else 0.0

    return round(credibility + recency_bonus + topic_bonus + novelty_penalty + clickbait_penalty, 2)


def process_and_store_research(
    collected_snapshot: dict[str, Any],
    db: LocalKnowledgeDB | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Filter, deduplicate, rank, classify, and persist research per pillar."""
    db = db or LocalKnowledgeDB()
    recent_slugs = db.get_recent_topic_slugs(days=30)
    raw_by_pillar = collected_snapshot.get("articles", {})
    processed: dict[str, list[dict[str, Any]]] = {"health": [], "wealth": [], "wisdom": []}

    for pillar in ("health", "wealth", "wisdom"):
        seen_links: set[str] = set()
        seen_slugs: set[str] = set()
        candidates: list[dict[str, Any]] = []

        for art in raw_by_pillar.get(pillar, []):
            link = art.get("original_article_link", "").strip()
            title = art.get("article_title", "").strip()
            if not link or not title:
                continue
            if is_clickbait(title, art.get("summary", "")):
                continue

            slug = slugify_topic(title)
            if link in seen_links or slug in seen_slugs:
                continue
            seen_links.add(link)
            seen_slugs.add(slug)

            score = compute_relevance_score(art, pillar, recent_slugs)
            claim_type = classify_claim_type(art.get("source_type", ""), title, art.get("summary", ""))

            row = {
                "article_id": art["article_id"],
                "source_name": art["source_name"],
                "source_url": art["source_url"],
                "publication_date": art["publication_date"],
                "article_title": title,
                "category": pillar.capitalize(),
                "original_article_link": link,
                "date_collected": art["date_collected"],
                "summary": art.get("summary", ""),
                "credibility_score": str(art.get("credibility_weight", 8)),
                "relevance_score": str(score),
                "claim_classification": claim_type,
                "used_in_brief": "FALSE",
                "_score_num": score,
                "_topic_slug": slug,
            }
            candidates.append(row)

        candidates.sort(key=lambda item: item["_score_num"], reverse=True)
        db.insert_research_articles(pillar, candidates)
        processed[pillar] = candidates

    return processed
