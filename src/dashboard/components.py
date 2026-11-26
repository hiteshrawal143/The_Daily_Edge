"""Reusable UI components (headers, lesson cards, descriptive sources, and creator footer)."""

from __future__ import annotations

import html
import uuid
from typing import Any

import streamlit as st

from src.config import BRAND_CONFIG, today_ist_str
from src.editorial.citations import resolve_citations
from src.editorial.lesson_formatter import parse_structured_lesson, strip_technical_clutter
from src.storage.local_db import LocalKnowledgeDB

LINKEDIN_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
    'fill="#0A66C2" style="background:#FFFFFF;border-radius:3px;padding:1px;flex-shrink:0;">'
    '<path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 '
    '15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-'
    '.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-'
    '.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 '
    '9.94v-8.37H5.5v8.37h2.77z"/></svg>'
)


def render_page_hero(eyebrow: str, title: str, subtitle: str, badge_text: str = "") -> None:
    """Render a consistent navy-and-gold editorial header."""
    badge_html = f'<div class="ltl-date-pill">{html.escape(badge_text)}</div>' if badge_text else ""
    st.markdown(
        f"""
        <div class="ltl-hero">
            <div class="ltl-hero-eyebrow">{html.escape(eyebrow)}</div>
            <div class="ltl-hero-title">{html.escape(title)}</div>
            <p class="ltl-hero-sub">{html.escape(subtitle)}</p>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sources_block(
    source_links: list[str] | str,
    db: LocalKnowledgeDB | None = None,
    pillar_filter: str | None = None,
    heading: str = "Sources & References",
) -> None:
    """Render descriptive clickable source links (never raw URLs)."""
    citations = resolve_citations(source_links, db=db, pillar_filter=pillar_filter)
    st.markdown(f"#### {heading}")
    if not citations:
        st.caption("Sources for this section are archived in your Knowledge Library.")
        return

    items_html = "".join(
        f'<li style="margin-bottom:8px;line-height:1.5;">'
        f'<strong style="color:#0B162C;">Source: {html.escape(c["source_name"])}</strong> &ndash; '
        f'<a href="{html.escape(c["url"])}" target="_blank" rel="noopener noreferrer" '
        f'style="color:#1D4ED8;text-decoration:none;font-weight:600;">{html.escape(c["title"])} &#8599;</a>'
        f"</li>"
        for c in citations
    )
    st.markdown(
        f'<div class="ltl-card" style="padding:16px 22px;"><ul style="margin:0;padding-left:18px;">{items_html}</ul></div>',
        unsafe_allow_html=True,
    )


def render_structured_lesson_card(
    db: LocalKnowledgeDB,
    brief_date: str,
    pillar: str,
    raw_lesson: str,
    source_links: list[str] | str,
    key_prefix: str = "brief",
) -> None:
    """Render a 7-part structured Hinglish lesson with completion, bookmark, and read-later controls."""
    parsed = parse_structured_lesson(raw_lesson, pillar)
    badge_cls = f"ltl-badge-{pillar.lower()}"
    pillar_desc = BRAND_CONFIG["pillars"].get(pillar, "")

    progress_rows = {
        (r["brief_date"], r["pillar"].lower()): r
        for r in db.get_lesson_progress(limit=200)
    }
    state = progress_rows.get((brief_date, pillar.lower()), {})
    is_completed = state.get("completed") == "TRUE"
    is_later = state.get("read_later") == "TRUE"

    status_chip = "✓ Completed" if is_completed else ("🕒 Saved for Later" if is_later else f"~{parsed['reading_minutes']} min read")

    sections_html = ""
    if parsed["is_structured"]:
        label_map = [
            ("core_idea", "The Core Idea"),
            ("why_it_matters", "Why It Matters"),
            ("what_research_says", "What Science & Research Say"),
            ("real_life_example", "Real-Life Example"),
            ("practical_application", "Practical Application"),
        ]
        for key, label in label_map:
            body = parsed["sections"].get(key)
            if body:
                safe_body = html.escape(body).replace("\n", "<br>")
                sections_html += (
                    f'<div class="ltl-section-label">{label}</div>'
                    f'<div class="ltl-section-body">{safe_body}</div>'
                )
        takeaway = parsed["sections"].get("key_takeaway", parsed["takeaway"])
        sections_html += f'<div class="ltl-takeaway-box"><strong>Key Takeaway:</strong> {html.escape(takeaway)}</div>'
    else:
        safe_prose = html.escape(parsed["clean_prose"]).replace("\n", "<br>")
        sections_html = (
            f'<div class="ltl-section-body">{safe_prose}</div>'
            f'<div class="ltl-takeaway-box"><strong>Key Takeaway:</strong> {html.escape(parsed["takeaway"])}</div>'
        )

    st.markdown(
        f"""
        <div class="ltl-lesson-shell">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <span class="ltl-badge {badge_cls}">{html.escape(pillar)} &bull; {html.escape(pillar_desc)}</span>
                <span class="ltl-meta">{html.escape(status_chip)}</span>
            </div>
            <h2 class="ltl-serif" style="margin:4px 0 12px 0;color:#0B162C;font-size:1.55rem;">{html.escape(parsed["title"])}</h2>
            {sections_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, _ = st.columns([1.2, 1.2, 1.2, 2.4])
    comp_label = "Completed ✓ (Undo)" if is_completed else "Mark as Completed"
    if c1.button(comp_label, key=f"{key_prefix}_comp_{brief_date}_{pillar}", use_container_width=True):
        db.set_lesson_progress(brief_date, pillar, parsed["title"], completed=not is_completed)
        st.rerun()

    if c2.button("Save to Bookmarks", key=f"{key_prefix}_bm_{brief_date}_{pillar}", use_container_width=True):
        first_cite = resolve_citations(source_links, db=db, pillar_filter=pillar)
        added = db.add_bookmark_if_new(
            {
                "bookmark_id": str(uuid.uuid4())[:8],
                "date_saved": today_ist_str(),
                "pillar": pillar,
                "title": parsed["title"],
                "lesson_text": parsed["takeaway"],
                "source_link": first_cite[0]["url"] if first_cite else "",
                "notes": f"Saved from {brief_date} brief",
            }
        )
        if added:
            st.success("Lesson saved to Bookmarks.")
        else:
            st.info("Already in your Bookmarks.")

    later_label = "Remove Read Later" if is_later else "Read Later"
    if c3.button(later_label, key=f"{key_prefix}_later_{brief_date}_{pillar}", use_container_width=True):
        db.set_lesson_progress(brief_date, pillar, parsed["title"], read_later=not is_later)
        st.rerun()


def render_related_lessons(db: LocalKnowledgeDB, pillar: str, exclude_date: str) -> None:
    """Show up to 3 related previous briefs for the selected pillar."""
    rows = [r for r in db.get_tab_rows("Daily_Learning", limit=10) if r.get("date") != exclude_date]
    if not rows:
        return
    col_key = f"{pillar.lower()}_lesson"
    st.markdown(f"#### Related Previous {pillar} Lessons")
    cols = st.columns(min(3, len(rows)))
    for idx, row in enumerate(rows[:3]):
        parsed = parse_structured_lesson(row.get(col_key, ""), pillar)
        with cols[idx]:
            st.markdown(
                f"""
                <div class="ltl-card">
                    <div class="ltl-meta">{html.escape(row.get("date", ""))} &bull; {html.escape(pillar)}</div>
                    <div class="ltl-card-title" style="font-size:1rem;margin-top:4px;">{html.escape(parsed["title"])}</div>
                    <p class="ltl-card-text" style="font-size:0.85rem;">{html.escape(strip_technical_clutter(parsed["takeaway"])[:120])}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_premium_footer() -> None:
    """Render the signature Hitesh Rawal & LinkedIn footer once per page."""
    brand = html.escape(BRAND_CONFIG["brand_name"])
    title = html.escape(BRAND_CONFIG["main_title"])
    creator = html.escape(BRAND_CONFIG["creator_name"])
    linkedin_url = html.escape(BRAND_CONFIG["creator_linkedin_url"])
    year = html.escape(BRAND_CONFIG["copyright_year"])
    closing = html.escape(BRAND_CONFIG["footer_closing"])

    st.markdown(
        f"""
        <div class="ltl-footer">
            <div class="ltl-footer-brand">{brand}</div>
            <div class="ltl-footer-sub">{title}</div>
            <div class="ltl-footer-creator">Created with passion by <strong>{creator}</strong></div>
            <div style="width:84px;height:1px;background:rgba(197,155,56,0.5);margin:16px auto;"></div>
            <div>
                <a class="ltl-linkedin-cta" href="{linkedin_url}" target="_blank" rel="noopener noreferrer">
                    {LINKEDIN_SVG}
                    <span>Connect with me on LinkedIn &#8599;</span>
                </a>
            </div>
            <div class="ltl-footer-copy">&copy; {year} {creator}. All rights reserved.</div>
            <div class="ltl-footer-closing">{closing}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
