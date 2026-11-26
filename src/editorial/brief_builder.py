"""Daily 10-minute Hinglish Growth Brief builder (AI-verified packet + clean RSS fallback)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.config import BRIEFS_DIR, ensure_directories, now_ist, today_ist_str
from src.editorial.lesson_formatter import (
    format_structured_lesson,
    humanize_evidence_label,
    strip_technical_clutter,
)
from src.research.processor import slugify_topic
from src.storage.local_db import LocalKnowledgeDB

REQUIRED_BRIEF_FIELDS = (
    "date",
    "title",
    "language",
    "is_ai_verified",
    "health_lesson",
    "wealth_lesson",
    "wisdom_lesson",
    "deep_dive",
    "surprising_discovery",
    "mental_model",
    "todays_action",
    "reflection_question",
    "source_links",
)


def brief_json_path(date_str: str | None = None, output_dir: Path | None = None) -> Path:
    """Return path to today's brief JSON artifact."""
    base = output_dir or BRIEFS_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{date_str or today_ist_str()}.json"


def ai_packet_path(date_str: str | None = None, output_dir: Path | None = None) -> Path:
    """Return path to the Antigravity AI editorial input packet."""
    base = output_dir or BRIEFS_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{date_str or today_ist_str()}_ai_packet.json"


def _pick_top_unused(
    processed_by_pillar: dict[str, list[dict[str, Any]]],
    pillar: str,
    recent_slugs: set[str],
) -> list[dict[str, Any]]:
    """Select top 2 articles for a pillar avoiding recent topic slugs when possible."""
    items = processed_by_pillar.get(pillar, [])
    fresh = [a for a in items if slugify_topic(a.get("article_title", "")) not in recent_slugs]
    return fresh[:2] if fresh else items[:2]


def prepare_ai_packet(
    processed_by_pillar: dict[str, list[dict[str, Any]]],
    db: LocalKnowledgeDB | None = None,
    date_str: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Create a structured JSON packet for Antigravity's included Gemini model."""
    db = db or LocalKnowledgeDB()
    target_date = date_str or today_ist_str()
    recent_slugs = sorted(db.get_recent_topic_slugs(days=30))

    candidates = {
        pillar: [
            {
                "article_title": item["article_title"],
                "source_name": item["source_name"],
                "publication_date": item["publication_date"],
                "original_article_link": item["original_article_link"],
                "summary": item["summary"],
                "evidence_tier": humanize_evidence_label(item.get("claim_classification", "")),
                "relevance_score": item["relevance_score"],
            }
            for item in processed_by_pillar.get(pillar, [])[:5]
        ]
        for pillar in ("health", "wealth", "wisdom")
    }

    lesson_format_guide = (
        "Title: <Compelling Title>\n\n"
        "**The Core Idea**\n<Simple Hinglish explanation>\n\n"
        "**Why It Matters**\n<Real-life relevance>\n\n"
        "**What Science & Research Say**\n<Evidence from cited sources; separate fact vs expert opinion vs speculation>\n\n"
        "**Real-Life Example**\n<Practical relatable example>\n\n"
        "**Practical Application**\n<How to apply today>\n\n"
        "**Key Takeaway**\n<One memorable line>"
    )

    packet = {
        "brand": "Life Time Library – The Daily Edge",
        "date": target_date,
        "target_language": "Natural Hinglish (warm teacher-like Hindi + English mix, keep technical terms intact)",
        "target_reading_time_minutes": 10,
        "recently_covered_topic_slugs": recent_slugs[:60],
        "editorial_rules": [
            "Use ONLY facts grounded in the candidate articles below and verify claims against their source summaries/links.",
            "Every health_lesson, wealth_lesson, and wisdom_lesson MUST follow the 7-part structure shown in lesson_format_guide.",
            "NEVER insert raw URLs, classification enums, or '[RSS-Only...]' tags inside lesson text.",
            "Distinguish peer-reviewed research / official data from expert opinion and speculation naturally in prose.",
            "Avoid clickbait and avoid repeating topics in recently_covered_topic_slugs.",
            "Wealth section must be strictly educational—no personalized buy/sell advice or guaranteed return claims.",
            "Output valid JSON matching output_schema and save to target_output_path.",
        ],
        "lesson_format_guide": lesson_format_guide,
        "target_output_path": str(brief_json_path(target_date, output_dir=output_dir)),
        "output_schema": {
            "date": target_date,
            "title": f"The Daily Edge – Health, Wealth & Wisdom – {target_date}",
            "language": "Hinglish",
            "is_ai_verified": True,
            "health_lesson": "7-part structured Hinglish lesson grounded in Health sources",
            "wealth_lesson": "7-part structured Hinglish educational lesson grounded in Wealth sources",
            "wisdom_lesson": "7-part structured Hinglish lesson grounded in Wisdom sources",
            "deep_dive": "Connecting insight across science, money, or decision-making (no raw URLs)",
            "surprising_discovery": "One counter-intuitive finding with publication name",
            "mental_model": "One practical mental model + daily application",
            "todays_action": "Concrete 10-minute action for today",
            "reflection_question": "One sharp critical-thinking question for journaling",
            "source_links": ["https://..."],
            "topics_covered": [
                {"pillar": "Health", "topic_title": "...", "article_link": "https://..."}
            ],
        },
        "candidates": candidates,
    }

    out = ai_packet_path(target_date, output_dir=output_dir)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(packet, fh, indent=2, ensure_ascii=False)
    return out


def build_rss_fallback_brief(
    processed_by_pillar: dict[str, list[dict[str, Any]]],
    db: LocalKnowledgeDB | None = None,
    date_str: str | None = None,
) -> dict[str, Any]:
    """Generate a clean 7-part Hinglish source digest when AI editorial pass hasn't run.

    Honesty guarantee: sets is_ai_verified=False without cluttering lesson prose with raw URLs or enums.
    """
    db = db or LocalKnowledgeDB()
    target_date = date_str or today_ist_str()
    recent_slugs = db.get_recent_topic_slugs(days=30)

    selected = {
        pillar: _pick_top_unused(processed_by_pillar, pillar, recent_slugs)
        for pillar in ("health", "wealth", "wisdom")
    }

    pillar_defaults = {
        "health": (
            "Sehat aur Brain Recovery ke Core Principles",
            "Aaj Health pillar mein hamara focus evidence-based habits aur biological recovery par hai.",
            "Daily energy, cognitive clarity aur long-term longevity seedhe aapki daily routines se judi hoti hai.",
            "Original medical aur neuroscience journals se collected summaries niche Sources section mein linked hain.",
            "Ek fixed wake-up time aur morning daylight exposure aapke circadian rhythm ko stabilize karta hai.",
            "Aaj apni sleep timing, hydration aur 20-minute movement par dhyaan dein.",
            "Chhoti daily biological habits long-term health ka sabse reliable foundation banati hain.",
        ),
        "wealth": (
            "Financial Clarity aur Smart Decision-Making",
            "Wealth creation sirf zyada kamane se nahi, balki risk aur cashflow ko samajhne se hoti hai.",
            "Macroeconomics aur personal finance ke fundamentals samajhne se impulsive financial mistakes kam hoti hain.",
            "Official institutional releases aur data-driven financial blogs se collected readings Sources mein available hain.",
            "Kisi bhi big purchase ya investment se pehle opportunity cost aur emergency buffer calculate karna zaroori hai.",
            "Aaj apne top 3 monthly expenses ya saving rate par 10 minute ka calm review karein.",
            "Financial intelligence ka matlab hai clarity over hype — hamesha data aur time-horizon dekhein.",
        ),
        "wisdom": (
            "Clear Thinking aur Better Decisions",
            "Acchi zindagi ka base sharp thinking aur emotions ke beech clear judgment lena hota hai.",
            "Mental models aur philosophy humein noise ke beech sahi signal pehchanne mein madad karte hain.",
            "Credible philosophy, science journalism aur decision-making publications se readings curated hain.",
            "Kisi bade decision se pehle inversion use karein: 'Kaunsi cheez is plan ko fail kar sakti hai?'",
            "Aaj kisi ek important belief ko test karne ke liye opposite perspective calmly padhein.",
            "Better questions puchna hamesha ready-made answers ratne se zyada valuable hota hai.",
        ),
    }

    def format_pillar_clean(pillar: str) -> str:
        items = selected[pillar]
        d_title, d_core, d_why, d_sci, d_ex, d_app, d_key = pillar_defaults[pillar]
        if not items:
            return format_structured_lesson(d_title, d_core, d_why, d_sci, d_ex, d_app, d_key)

        lead = items[0]
        second = items[1] if len(items) > 1 else None
        clean_title = strip_technical_clutter(lead.get("article_title", d_title))
        src_name = lead.get("source_name", "Credible Publication")
        evidence = humanize_evidence_label(lead.get("claim_classification", ""))
        snippet = strip_technical_clutter(lead.get("summary", ""))[:360]

        sci_text = (
            f"{src_name} ({lead.get('publication_date', target_date)}) ke mutabik — yeh ek {evidence.lower()} hai. "
            f"{snippet}"
        )
        if second:
            sec_title = strip_technical_clutter(second.get("article_title", ""))
            sec_src = second.get("source_name", "")
            sci_text += f"\n\nSaath hi {sec_src} mein '{sec_title}' par bhi relevant insight publish hua hai."

        return format_structured_lesson(
            title=clean_title,
            core_idea=f"{d_core} Aaj ki key reading '{clean_title}' is topic par focused hai.",
            why_it_matters=d_why,
            what_research_says=sci_text,
            real_life_example=d_ex,
            practical_application=d_app,
            key_takeaway=d_key,
        )

    all_selected = selected["health"] + selected["wealth"] + selected["wisdom"]
    source_links = list(
        dict.fromkeys(a["original_article_link"] for a in all_selected if a.get("original_article_link"))
    )

    top_item = all_selected[0] if all_selected else None
    deep_dive = (
        f"Aaj ki featured reading '{strip_technical_clutter(top_item['article_title'])}' "
        f"({top_item['source_name']}) ko neeche Sources section se open karke padhein. "
        "Padhte waqt note karein ki kaunsa point direct data par based hai aur kaunsa interpretation par."
        if top_item
        else "Aaj ke teeno pillars mein se ek topic chunein aur uske original source par 10 minute deep reading karein."
    )

    surprising = (
        f"{all_selected[1]['source_name']} ki report: '{strip_technical_clutter(all_selected[1]['article_title'])}' "
        "— primary evidence aur context samajhne ke liye worth reading hai."
        if len(all_selected) > 1
        else "Har claim ke piche ka sample size aur baseline context check karna aksar headline se zyada batata hai."
    )

    return {
        "date": target_date,
        "title": f"The Daily Edge – Health, Wealth & Wisdom – {target_date}",
        "language": "Hinglish",
        "is_ai_verified": False,
        "health_lesson": format_pillar_clean("health"),
        "wealth_lesson": format_pillar_clean("wealth"),
        "wisdom_lesson": format_pillar_clean("wisdom"),
        "deep_dive": deep_dive,
        "surprising_discovery": surprising,
        "mental_model": (
            "First-Principles Verification: Har claim ko padhte waqt poochein — "
            "kya yeh verified data hai, expert opinion hai, ya sirf speculation?"
        ),
        "todays_action": (
            "Aaj ke Sources section se kam se kam ek original article poora padhein aur "
            "uska ek practical takeaway Bookmarks mein save karein."
        ),
        "reflection_question": (
            "Aaj jo maine padha, usmein se kaunsa idea mere purane belief ko challenge karta hai, aur kyun?"
        ),
        "source_links": source_links,
        "topics_covered": [
            {
                "pillar": a["category"],
                "topic_title": a["article_title"],
                "article_link": a["original_article_link"],
            }
            for a in all_selected
        ],
    }


def validate_and_save_brief(
    brief: dict[str, Any],
    db: LocalKnowledgeDB | None = None,
    doc_url: str = "",
    pdf_url: str = "",
    email_status: str = "not_sent_pending_approval",
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Validate brief fields, save JSON file, and persist to Daily_Learning + Topic_History."""
    db = db or LocalKnowledgeDB()
    missing = [f for f in REQUIRED_BRIEF_FIELDS if f not in brief]
    if missing:
        raise ValueError(f"Brief is missing required fields: {missing}")

    target_date = str(brief["date"])
    is_ai = bool(brief.get("is_ai_verified", False))
    source_links = brief.get("source_links", [])
    if isinstance(source_links, list):
        links_str = "\n".join(str(x) for x in list(dict.fromkeys(source_links)))
    else:
        links_str = str(source_links)

    row = {
        "date": target_date,
        "title": str(brief["title"]),
        "language": str(brief.get("language", "Hinglish")),
        "is_ai_verified": "TRUE" if is_ai else "FALSE",
        "health_lesson": str(brief["health_lesson"]),
        "wealth_lesson": str(brief["wealth_lesson"]),
        "wisdom_lesson": str(brief["wisdom_lesson"]),
        "deep_dive": str(brief["deep_dive"]),
        "surprising_discovery": str(brief["surprising_discovery"]),
        "mental_model": str(brief["mental_model"]),
        "todays_action": str(brief["todays_action"]),
        "reflection_question": str(brief["reflection_question"]),
        "source_links": links_str,
        "doc_url": doc_url,
        "pdf_url": pdf_url,
        "email_status": email_status,
        "created_at": now_ist().isoformat(),
    }

    db.save_daily_brief(row)

    topics_covered = brief.get("topics_covered", [])
    history_rows = []
    for item in topics_covered:
        pillar = str(item.get("pillar", "Wisdom"))
        title = str(item.get("topic_title", ""))
        link = str(item.get("article_link", ""))
        if title:
            history_rows.append(
                {
                    "date": target_date,
                    "pillar": pillar,
                    "topic_slug": slugify_topic(title),
                    "topic_title": title,
                    "article_link": link,
                    "brief_date": target_date,
                }
            )
            db.mark_articles_used(pillar, [link] if link else [])
    db.record_topic_history(history_rows)

    out_path = brief_json_path(target_date, output_dir=output_dir)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(brief, fh, indent=2, ensure_ascii=False)

    return row


def load_existing_ai_brief(date_str: str | None = None, output_dir: Path | None = None) -> dict[str, Any] | None:
    """Return today's brief JSON if an AI-verified brief already exists."""
    path = brief_json_path(date_str, output_dir=output_dir)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("is_ai_verified") is True:
            return data
    except (OSError, json.JSONDecodeError):
        return None
    return None
