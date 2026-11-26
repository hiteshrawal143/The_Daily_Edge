"""Monthly Knowledge Review generator."""

from __future__ import annotations

import json
from typing import Any

from src.config import BRAND_CONFIG, REVIEWS_DIR, ensure_directories, now_ist
from src.storage.local_db import LocalKnowledgeDB


def build_monthly_review(
    db: LocalKnowledgeDB | None = None,
    month_str: str | None = None,
) -> dict[str, Any]:
    """Generate a Monthly Knowledge Review from Daily_Learning, research tabs, and Quiz_Results."""
    ensure_directories()
    db = db or LocalKnowledgeDB()
    target_month = month_str or now_ist().strftime("%Y-%m")

    counts = db.get_counts()
    quiz_rows = db.get_tab_rows("Quiz_Results", limit=200)
    total_q = len(quiz_rows)
    correct_q = sum(1 for r in quiz_rows if str(r.get("is_correct", "")).upper() == "TRUE")
    accuracy = f"{(correct_q / total_q * 100):.1f}% ({correct_q}/{total_q})" if total_q else "No quiz attempts yet"

    bookmarks = db.get_tab_rows("Bookmarks", limit=10)
    top_insights = "\n".join(
        f"- [{b.get('pillar', '')}] {b.get('title', '')}" for b in bookmarks
    ) or "No bookmarks saved yet — bookmark high-value lessons in the Streamlit dashboard."

    review = {
        "month": target_month,
        "summary": (
            f"Monthly Knowledge Review ({target_month}) — {BRAND_CONFIG['brand_name']} ({BRAND_CONFIG['main_title']}): "
            f"{counts.get('Daily_Learning', 0)} daily briefs, {counts.get('Weekly_Reviews', 0)} weekly reviews, "
            f"and {counts.get('Bookmarks', 0)} saved lessons. {BRAND_CONFIG['compact_signature']}"
        ),
        "top_insights": top_insights,
        "pillar_breakdown": (
            f"Health: {counts.get('Health_Research', 0)} | "
            f"Wealth: {counts.get('Wealth_Research', 0)} | "
            f"Wisdom: {counts.get('Wisdom_Research', 0)}"
        ),
        "quiz_accuracy": accuracy,
        "doc_url": "",
        "created_at": now_ist().isoformat(),
    }

    db.save_monthly_review(review)

    out_path = REVIEWS_DIR / f"monthly_{target_month}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(review, fh, indent=2, ensure_ascii=False)

    return review
