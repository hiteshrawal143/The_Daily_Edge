"""End-to-end daily and weekly pipeline orchestrators."""

from __future__ import annotations

import time
from typing import Any

from src.config import load_settings, today_ist_str
from src.delivery.docs_exporter import export_daily_report
from src.editorial.brief_builder import (
    build_rss_fallback_brief,
    load_existing_ai_brief,
    prepare_ai_packet,
    validate_and_save_brief,
)
from src.editorial.monthly_builder import build_monthly_review
from src.editorial.weekly_builder import build_weekly_review
from src.research.processor import process_and_store_research
from src.research.rss_collector import collect_all_research
from src.storage.google_sync import GoogleWorkspaceSync
from src.storage.local_db import LocalKnowledgeDB


def run_daily_pipeline(
    skip_fetch: bool = False,
    send_email: bool = False,
) -> dict[str, Any]:
    """Execute the full daily LifeTimeLibrary workflow with zero-cost safeguards."""
    start = time.monotonic()
    db = LocalKnowledgeDB()
    settings = load_settings()
    sync_client = GoogleWorkspaceSync(settings)
    today_str = today_ist_str()

    snapshot = {"articles": {"health": [], "wealth": [], "wisdom": []}, "feed_statuses": []}
    if not skip_fetch:
        snapshot = collect_all_research(db=db, max_per_feed=6)
        processed = process_and_store_research(snapshot, db=db)
    else:
        processed = {
            pillar: db.get_tab_rows(f"{pillar.capitalize()}_Research", limit=10)
            for pillar in ("health", "wealth", "wisdom")
        }

    packet_path = prepare_ai_packet(processed, db=db, date_str=today_str)

    # Use AI-verified brief if Antigravity already produced today's brief; otherwise use labeled RSS fallback
    ai_brief = load_existing_ai_brief(today_str)
    if ai_brief is not None:
        brief = ai_brief
        ai_mode = "antigravity_ai_verified"
    else:
        brief = build_rss_fallback_brief(processed, db=db, date_str=today_str)
        ai_mode = "rss_only_fallback_not_ai_verified"

    export_info = export_daily_report(brief, sync_client=sync_client, db=db)

    email_status = "not_sent_pending_approval"
    if send_email and settings.get("allow_email_send") and settings.get("recipient_email"):
        email_status = "delegated_to_google_sync"
    elif send_email:
        email_status = "blocked_missing_recipient_or_approval"

    validate_and_save_brief(
        brief,
        db=db,
        doc_url=export_info.get("doc_url", ""),
        pdf_url=export_info.get("pdf_url", ""),
        email_status=email_status,
    )

    sync_result = sync_client.sync_all(db, send_email=send_email)
    duration = time.monotonic() - start

    db.log_automation(
        workflow="daily_pipeline",
        status="success",
        ai_mode=ai_mode,
        details=f"doc={export_info['local_md']} | sync={sync_result.get('status')}",
        duration_sec=duration,
    )

    return {
        "date": today_str,
        "ai_mode": ai_mode,
        "ai_packet_path": str(packet_path),
        "export": export_info,
        "sync": sync_result,
        "counts": db.get_counts(),
        "feed_statuses": snapshot.get("feed_statuses", []),
        "duration_sec": round(duration, 2),
    }


def run_weekly_pipeline() -> dict[str, Any]:
    """Execute Sunday's Weekly Review, 10-question quiz, and Monthly rollup."""
    start = time.monotonic()
    db = LocalKnowledgeDB()
    review = build_weekly_review(db=db)
    monthly = build_monthly_review(db=db)
    sync_client = GoogleWorkspaceSync()
    sync_res = sync_client.sync_all(db=db, send_email=False)
    duration = time.monotonic() - start

    db.log_automation(
        workflow="weekly_review",
        status="success",
        ai_mode="deterministic_summary_and_quiz",
        details=f"week={review['week_ending']} | sync={sync_res.get('status')}",
        duration_sec=duration,
    )
    return {"weekly_review": review, "monthly_review": monthly, "sync": sync_res}
