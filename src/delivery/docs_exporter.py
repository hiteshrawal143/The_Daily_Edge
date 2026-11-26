"""Report exporter creating local Markdown/HTML files and Google Docs/PDF copies."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config import BRAND_CONFIG, EXPORTS_DIR, ensure_directories
from src.delivery.email_renderer import render_newsletter_html
from src.editorial.citations import resolve_citations
from src.editorial.lesson_formatter import strip_technical_clutter
from src.storage.google_sync import GoogleWorkspaceSync
from src.storage.local_db import LocalKnowledgeDB


def brief_to_markdown(brief: dict[str, Any], db: LocalKnowledgeDB | None = None) -> str:
    """Format a Daily Growth Brief dict into clean editorial Markdown for Google Docs & PDF."""
    is_ai = str(brief.get("is_ai_verified", False)).lower() == "true" or brief.get("is_ai_verified") is True
    status_label = "Editorially Verified" if is_ai else "Curated Source Digest"

    citations = resolve_citations(brief.get("source_links", []), db=db)
    links_md = (
        "\n".join(f"- **Source: {c['source_name']}** – [{c['title']}]({c['url']})" for c in citations)
        or "- Sources archived in Life Time Library."
    )

    return (
        f"# {BRAND_CONFIG['brand_name']} – {BRAND_CONFIG['main_title']}\n"
        f"*{BRAND_CONFIG['tagline']}*\n\n"
        f"**Date:** {brief.get('date', '')}  \n"
        f"**Edition Status:** {status_label}  \n"
        f"**Language:** {brief.get('language', 'Hinglish')}\n\n"
        f"---\n\n"
        f"## 1. Health Lesson\n{strip_technical_clutter(str(brief.get('health_lesson', '')))}\n\n"
        f"## 2. Wealth Lesson (Educational Only)\n{strip_technical_clutter(str(brief.get('wealth_lesson', '')))}\n\n"
        f"## 3. Wisdom Lesson\n{strip_technical_clutter(str(brief.get('wisdom_lesson', '')))}\n\n"
        f"## 4. Deep Dive\n{strip_technical_clutter(str(brief.get('deep_dive', '')))}\n\n"
        f"## 5. Surprising Discovery\n{strip_technical_clutter(str(brief.get('surprising_discovery', '')))}\n\n"
        f"## 6. Mental Model of the Day\n{strip_technical_clutter(str(brief.get('mental_model', '')))}\n\n"
        f"## 7. Today's Action\n{strip_technical_clutter(str(brief.get('todays_action', '')))}\n\n"
        f"## 8. Reflection Question\n{strip_technical_clutter(str(brief.get('reflection_question', '')))}\n\n"
        f"## 9. Original Sources\n{links_md}\n\n"
        f"---\n\n"
        f"{BRAND_CONFIG['compact_signature']}  \n"
        f"[Connect with me on LinkedIn ↗]({BRAND_CONFIG['creator_linkedin_url']})\n"
    )


def export_daily_report(
    brief: dict[str, Any],
    sync_client: GoogleWorkspaceSync | None = None,
    db: LocalKnowledgeDB | None = None,
) -> dict[str, str]:
    """Export Daily_Growth_Brief_YYYY_MM_DD locally (.md + .html) and to Google Docs/PDF if configured."""
    ensure_directories()
    date_underscored = str(brief.get("date", "")).replace("-", "_")
    doc_title = f"Daily_Growth_Brief_{date_underscored}"

    md_text = brief_to_markdown(brief, db=db)
    md_path: Path = EXPORTS_DIR / f"{doc_title}.md"
    md_path.write_text(md_text, encoding="utf-8")

    cloud_result = {"doc_url": "", "pdf_url": "", "status": "local_only"}
    sync_client = sync_client or GoogleWorkspaceSync()
    if sync_client.is_configured():
        cloud_result = sync_client.create_google_doc_and_pdf(
            title=doc_title,
            markdown_body=md_text,
            folder_subpath="Daily Reports",
        )

    html_text = render_newsletter_html(brief, doc_url=cloud_result.get("doc_url", ""), db=db)
    html_path: Path = EXPORTS_DIR / f"{doc_title}.html"
    html_path.write_text(html_text, encoding="utf-8")

    return {
        "doc_title": doc_title,
        "local_md": str(md_path),
        "local_html": str(html_path),
        "doc_url": cloud_result.get("doc_url", ""),
        "pdf_url": cloud_result.get("pdf_url", ""),
        "cloud_status": cloud_result.get("status", "local_only"),
    }
