"""Central configuration, brand identity, schemas, and zero-cost guardrails for Life Time Library."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"
COLLECTED_DIR = DATA_DIR / "collected"
BRIEFS_DIR = DATA_DIR / "briefs"
REVIEWS_DIR = DATA_DIR / "reviews"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "lifetimelibrary.db"

SOURCES_PATH = CONFIG_DIR / "sources.json"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
SETTINGS_EXAMPLE_PATH = CONFIG_DIR / "settings.example.json"

IST = ZoneInfo("Asia/Kolkata")

# Central Brand & Personal Creator Identity (single source of truth)
BRAND_CONFIG: dict[str, Any] = {
    "brand_name": "Life Time Library",
    "main_title": "The Daily Edge",
    "tagline": "10 Minutes. Learn Daily. Live Intentionally. Evolve Continuously.",
    "supporting_description": (
        "Build a healthier body, a stronger financial mind, and deeper wisdom "
        "through consistent daily learning."
    ),
    "pillars": {
        "Health": "Build a healthier body and mind.",
        "Wealth": "Develop financial intelligence and wealth-building knowledge.",
        "Wisdom": "Improve critical thinking, decision-making and understanding of life.",
    },
    "creator_name": "Hitesh Rawal",
    "creator_linkedin_url": "https://www.linkedin.com/in/rawalhitesh/",
    "compact_signature": "Created by Hitesh Rawal | Life Time Library – The Daily Edge",
    "copyright_year": "2026",
    "footer_closing": "Built to learn. Designed to grow. Created for life.",
}

# Exact 12-tab schema for "LifeTimeLibrary Knowledge Database" in Google Sheets
SHEET_SCHEMAS: dict[str, list[str]] = {
    "Daily_Learning": [
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
        "doc_url",
        "pdf_url",
        "email_status",
        "created_at",
    ],
    "Health_Research": [
        "article_id",
        "source_name",
        "source_url",
        "publication_date",
        "article_title",
        "category",
        "original_article_link",
        "date_collected",
        "summary",
        "credibility_score",
        "relevance_score",
        "claim_classification",
        "used_in_brief",
    ],
    "Wealth_Research": [
        "article_id",
        "source_name",
        "source_url",
        "publication_date",
        "article_title",
        "category",
        "original_article_link",
        "date_collected",
        "summary",
        "credibility_score",
        "relevance_score",
        "claim_classification",
        "used_in_brief",
    ],
    "Wisdom_Research": [
        "article_id",
        "source_name",
        "source_url",
        "publication_date",
        "article_title",
        "category",
        "original_article_link",
        "date_collected",
        "summary",
        "credibility_score",
        "relevance_score",
        "claim_classification",
        "used_in_brief",
    ],
    "Sources": [
        "pillar",
        "source_name",
        "source_url",
        "source_type",
        "credibility_weight",
        "topics",
        "active",
        "last_checked",
        "last_status",
    ],
    "Topic_History": [
        "date",
        "pillar",
        "topic_slug",
        "topic_title",
        "article_link",
        "brief_date",
    ],
    "Bookmarks": [
        "bookmark_id",
        "date_saved",
        "pillar",
        "title",
        "lesson_text",
        "source_link",
        "notes",
    ],
    "Quiz_Results": [
        "quiz_id",
        "week_ending",
        "question_no",
        "pillar",
        "question",
        "user_answer",
        "correct_answer",
        "is_correct",
        "explanation",
        "submitted_at",
    ],
    "Weekly_Reviews": [
        "week_ending",
        "summary",
        "top_10_learnings",
        "health_progress",
        "wealth_progress",
        "wisdom_progress",
        "revision_topics",
        "next_week_suggestions",
        "doc_url",
        "created_at",
    ],
    "Monthly_Reviews": [
        "month",
        "summary",
        "top_insights",
        "pillar_breakdown",
        "quiz_accuracy",
        "doc_url",
        "created_at",
    ],
    "Automation_Logs": [
        "timestamp",
        "workflow",
        "status",
        "ai_mode",
        "details",
        "duration_sec",
    ],
    "Settings": [
        "key",
        "value",
        "updated_at",
    ],
}

PILLAR_TO_TAB = {
    "health": "Health_Research",
    "wealth": "Wealth_Research",
    "wisdom": "Wisdom_Research",
}


def ensure_directories() -> None:
    """Create all local runtime data directories if missing."""
    for folder in (DATA_DIR, COLLECTED_DIR, BRIEFS_DIR, REVIEWS_DIR, EXPORTS_DIR, LOGS_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def now_ist() -> datetime:
    """Return current timezone-aware datetime in Asia/Kolkata."""
    return datetime.now(IST)


def today_ist_str() -> str:
    """Return today's date string (YYYY-MM-DD) in Asia/Kolkata."""
    return now_ist().strftime("%Y-%m-%d")


def ist_greeting() -> str:
    """Return time-appropriate greeting in Asia/Kolkata."""
    hour = now_ist().hour
    if hour < 12:
        return "Good Morning"
    if hour < 17:
        return "Good Afternoon"
    return "Good Evening"


def load_settings() -> dict[str, Any]:
    """Load runtime settings from .env and config/settings.json."""
    load_dotenv(ROOT_DIR / ".env", override=False)

    settings_file = SETTINGS_PATH if SETTINGS_PATH.exists() else SETTINGS_EXAMPLE_PATH
    with settings_file.open("r", encoding="utf-8") as fh:
        settings: dict[str, Any] = json.load(fh)

    settings["recipient_email"] = os.getenv("RECIPIENT_EMAIL", settings.get("recipient_email", "")).strip()
    settings["sender_name"] = os.getenv("SENDER_NAME", "Life Time Library – The Daily Edge")
    settings["google_sync_mode"] = os.getenv("GOOGLE_SYNC_MODE", "local_only").strip().lower()
    settings["apps_script_webapp_url"] = os.getenv("APPS_SCRIPT_WEBAPP_URL", "").strip()
    settings["apps_script_shared_secret"] = os.getenv("APPS_SCRIPT_SHARED_SECRET", "").strip()
    settings["google_credentials_path"] = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json").strip()
    settings["google_token_path"] = os.getenv("GOOGLE_TOKEN_PATH", "token.json").strip()
    settings["google_spreadsheet_name"] = os.getenv(
        "GOOGLE_SPREADSHEET_NAME", "LifeTimeLibrary Knowledge Database"
    ).strip()
    settings["google_drive_root_folder"] = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER", "LifeTimeLibrary").strip()
    settings["allow_email_send"] = os.getenv("ALLOW_EMAIL_SEND", "false").strip().lower() == "true"

    # Hard zero-cost safety guards (cannot be overridden)
    settings["budget_inr"] = 0
    settings["allow_paid_apis"] = False
    settings["allow_ai_credit_overages"] = False
    return settings


def load_sources() -> dict[str, list[dict[str, Any]]]:
    """Load curated free RSS/podcast sources grouped by pillar."""
    with SOURCES_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)
