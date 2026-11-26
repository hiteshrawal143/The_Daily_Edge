"""Automated verification tests for Life Time Library – The Daily Edge."""

from __future__ import annotations

from pathlib import Path

from src.config import BRAND_CONFIG, SHEET_SCHEMAS, load_settings, load_sources
from src.delivery.docs_exporter import brief_to_markdown
from src.delivery.email_renderer import render_newsletter_html
from src.editorial.brief_builder import (
    build_rss_fallback_brief,
    prepare_ai_packet,
    validate_and_save_brief,
)
from src.editorial.citations import resolve_citations
from src.editorial.lesson_formatter import (
    format_structured_lesson,
    parse_structured_lesson,
    strip_technical_clutter,
)
from src.editorial.monthly_builder import build_monthly_review
from src.editorial.weekly_builder import build_weekly_review
from src.research.processor import (
    classify_claim_type,
    is_clickbait,
    process_and_store_research,
    slugify_topic,
)
from src.storage.local_db import LocalKnowledgeDB


def test_brand_identity_and_linkedin_config() -> None:
    assert BRAND_CONFIG["brand_name"] == "Life Time Library"
    assert BRAND_CONFIG["main_title"] == "The Daily Edge"
    assert BRAND_CONFIG["creator_name"] == "Hitesh Rawal"
    assert BRAND_CONFIG["creator_linkedin_url"] == "https://www.linkedin.com/in/rawalhitesh/"
    assert "₹0" not in BRAND_CONFIG["tagline"]
    assert "₹0" not in BRAND_CONFIG["supporting_description"]


def test_sources_minimum_five_per_pillar() -> None:
    sources = load_sources()
    for pillar in ("health", "wealth", "wisdom"):
        assert len(sources[pillar]) >= 5, f"{pillar} must have at least 5 credible sources"


def test_zero_cost_defaults() -> None:
    settings = load_settings()
    assert settings["budget_inr"] == 0
    assert settings["allow_paid_apis"] is False
    assert settings["allow_ai_credit_overages"] is False
    assert settings["allow_email_send"] is False


def test_db_twelve_tabs_progress_and_deduplication(tmp_path: Path) -> None:
    db = LocalKnowledgeDB(db_path=tmp_path / "test.db")
    counts = db.get_counts()
    assert set(counts.keys()) == set(SHEET_SCHEMAS.keys())
    assert len(counts) == 12

    sample = [
        {
            "article_id": "abc123",
            "source_name": "NIH News",
            "source_url": "https://www.nih.gov/feed.xml",
            "publication_date": "2026-11-26",
            "article_title": "Sleep Regularity Improves Cognitive Recovery",
            "category": "Health",
            "original_article_link": "https://www.nih.gov/example-1",
            "date_collected": "2026-11-26",
            "summary": "Randomized trial found regular sleep schedules improved memory.",
            "credibility_score": "10",
            "relevance_score": "14.0",
            "claim_classification": "verified_research_or_official_data",
            "used_in_brief": "FALSE",
        }
    ]
    assert len(db.insert_research_articles("health", sample)) == 1
    assert len(db.insert_research_articles("health", sample)) == 0

    # Test bookmark deduplication and lesson completion tracking
    bm = {
        "bookmark_id": "bm1",
        "date_saved": "2026-11-26",
        "pillar": "Health",
        "title": "Sleep Regularity",
        "lesson_text": "Keep wake-up time steady.",
        "source_link": "https://www.nih.gov/example-1",
        "notes": "Test",
    }
    assert db.add_bookmark_if_new(bm) is True
    assert db.add_bookmark_if_new(bm) is False

    db.set_lesson_progress("2026-11-26", "Health", "Sleep Regularity", completed=True, read_later=True)
    stats = db.get_learning_stats("2026-11-26")
    assert stats["today_completed"] == 1
    assert stats["total_completed"] == 1
    assert stats["learning_streak"] == 1
    assert stats["read_later_count"] == 1


def test_lesson_formatter_clutter_stripping_and_citations(tmp_path: Path) -> None:
    dirty = "[RSS-Only Digest – Not AI-Verified] Classification: scientific_or_institutional_report https://example.com/raw"
    cleaned = strip_technical_clutter(dirty)
    assert "RSS-Only" not in cleaned
    assert "scientific_or_institutional_report" not in cleaned
    assert "https://" not in cleaned

    structured = format_structured_lesson(
        title="Sleep Timing & Brain Clarity",
        core_idea="Fixed wake time circadian clock ko reset karta hai.",
        why_it_matters="Subah focus aur mood stable rehta hai.",
        what_research_says="Peer-reviewed studies circadian regularity ko support karti hain.",
        real_life_example="7:00 AM daily wake-up even on Sundays.",
        practical_application="Aaj alarm 7:00 AM par set karein aur 10 min sunlight lein.",
        key_takeaway="Consistency beats sleeping extra hours on weekends.",
    )
    parsed = parse_structured_lesson(structured, "Health")
    assert parsed["is_structured"] is True
    assert parsed["title"] == "Sleep Timing & Brain Clarity"
    assert "Consistency beats" in parsed["takeaway"]

    db = LocalKnowledgeDB(db_path=tmp_path / "cite.db")
    db.insert_research_articles(
        "health",
        [
            {
                "article_id": "n1",
                "source_name": "Nature - Neuroscience",
                "source_url": "https://www.nature.com/neuro.rss",
                "publication_date": "2026-11-23",
                "article_title": "Shared meaning component across languages",
                "category": "Health",
                "original_article_link": "https://www.nature.com/articles/s41593-026-02523-6",
                "date_collected": "2026-11-26",
                "summary": "fMRI study across 21 languages.",
                "credibility_score": "10",
                "relevance_score": "15.0",
                "claim_classification": "verified_research_or_official_data",
                "used_in_brief": "FALSE",
            }
        ],
    )
    cites = resolve_citations(
        [
            "https://www.nature.com/articles/s41593-026-02523-6",
            "https://www.nature.com/articles/s41593-026-02523-6",
        ],
        db=db,
    )
    assert len(cites) == 1
    assert cites[0]["source_name"] == "Nature - Neuroscience"
    assert cites[0]["title"] == "Shared meaning component across languages"


def test_processor_clickbait_and_classification(tmp_path: Path) -> None:
    assert is_clickbait("10 Shocking Tricks Doctors Hate!") is True
    assert is_clickbait("Randomized Trial on Resistance Training and Longevity") is False
    assert classify_claim_type("scientific_feed", "NIH study found", "data shows") == "verified_research_or_official_data"
    assert classify_claim_type("educational_blog", "Market forecast", "Stocks might rally") == "speculation_or_forecast"

    db = LocalKnowledgeDB(db_path=tmp_path / "proc.db")
    snapshot = {
        "articles": {
            "health": [
                {
                    "article_id": "h1",
                    "source_name": "NIH",
                    "source_url": "https://nih.gov/rss",
                    "publication_date": "2026-11-26",
                    "article_title": "Circadian Rhythm and Sleep Recovery",
                    "category": "Health",
                    "original_article_link": "https://nih.gov/sleep-1",
                    "date_collected": "2026-11-26",
                    "summary": "Study found consistent morning light supports circadian rhythm.",
                    "credibility_weight": 10,
                    "source_type": "scientific_feed",
                },
                {
                    "article_id": "h2",
                    "source_name": "Spam",
                    "source_url": "https://spam.example/rss",
                    "publication_date": "2026-11-26",
                    "article_title": "One Weird Trick Doctors Hate",
                    "category": "Health",
                    "original_article_link": "https://spam.example/1",
                    "date_collected": "2026-11-26",
                    "summary": "Miracle cure!",
                    "credibility_weight": 1,
                    "source_type": "blog",
                },
            ],
            "wealth": [],
            "wisdom": [],
        }
    }
    processed = process_and_store_research(snapshot, db=db)
    assert len(processed["health"]) == 1
    assert slugify_topic("Inversion Mental Model for Better Decisions") == "inversion-mental-model-better-decisions"


def test_fallback_brief_html_branding_and_weekly_quiz(tmp_path: Path) -> None:
    db = LocalKnowledgeDB(db_path=tmp_path / "brief.db")
    processed = {
        "health": [
            {
                "article_id": "h1",
                "source_name": "Nature - Neuroscience",
                "source_url": "https://www.nature.com/neuro.rss",
                "publication_date": "2026-11-25",
                "article_title": "Morning Daylight Improves Sleep",
                "category": "Health",
                "original_article_link": "https://www.nature.com/articles/demo-1",
                "date_collected": "2026-11-26",
                "summary": "Morning light anchors circadian clocks.",
                "credibility_score": "10",
                "relevance_score": "15",
                "claim_classification": "verified_research_or_official_data",
                "used_in_brief": "FALSE",
            }
        ],
        "wealth": [],
        "wisdom": [],
    }
    db.insert_research_articles("health", processed["health"])
    packet_path = prepare_ai_packet(processed, db=db, date_str="2026-11-26", output_dir=tmp_path)
    assert packet_path.exists()

    brief = build_rss_fallback_brief(processed, db=db, date_str="2026-11-26")
    assert brief["is_ai_verified"] is False
    assert "RSS-Only" not in brief["health_lesson"]
    assert "https://" not in brief["health_lesson"]

    validate_and_save_brief(
        brief,
        db=db,
        doc_url="https://docs.google.com/document/d/demo/edit",
        output_dir=tmp_path,
    )
    html_out = render_newsletter_html(brief, doc_url="https://docs.google.com/document/d/demo/edit", db=db)
    assert "Life Time Library" in html_out
    assert "The Daily Edge" in html_out
    assert "Created by Hitesh Rawal" in html_out
    assert "https://www.linkedin.com/in/rawalhitesh/" in html_out
    assert "Source: Nature - Neuroscience" in html_out
    assert "₹0" not in html_out

    md_out = brief_to_markdown(brief, db=db)
    assert "Created by Hitesh Rawal | Life Time Library – The Daily Edge" in md_out
    assert "https://www.linkedin.com/in/rawalhitesh/" in md_out

    weekly = build_weekly_review(db=db, week_ending="2026-11-26")
    assert len(weekly["quiz_questions"]) == 10
    for q in weekly["quiz_questions"]:
        assert len(set(q["options"])) == 4, f"Quiz question {q['question_no']} has duplicate options"
    monthly = build_monthly_review(db=db, month_str="2026-11")
    assert monthly["month"] == "2026-11"
