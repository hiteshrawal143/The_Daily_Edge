"""Life Time Library – The Daily Edge (Redesigned 13-Page Streamlit Learning Platform)."""

from __future__ import annotations

import html
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import (
    BRAND_CONFIG,
    REVIEWS_DIR,
    ist_greeting,
    load_settings,
    load_sources,
    now_ist,
    today_ist_str,
)
from src.dashboard.components import (
    render_page_hero,
    render_premium_footer,
    render_related_lessons,
    render_sources_block,
    render_structured_lesson_card,
)
from src.dashboard.theme import inject_theme_css
from src.delivery.email_renderer import render_newsletter_html
from src.delivery.pipeline import run_daily_pipeline, run_weekly_pipeline
from src.editorial.lesson_formatter import humanize_evidence_label, parse_structured_lesson, strip_technical_clutter
from src.editorial.monthly_builder import build_monthly_review
from src.editorial.weekly_builder import build_weekly_review, generate_weekly_quiz
from src.storage.google_sync import GoogleWorkspaceSync
from src.storage.local_db import LocalKnowledgeDB

st.set_page_config(
    page_title=f"{BRAND_CONFIG['brand_name']} – {BRAND_CONFIG['main_title']}",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAV_ITEMS = [
    "🏠 Home",
    "☀️ Today's Brief",
    "💚 Health",
    "💼 Wealth",
    "🧠 Wisdom",
    "📚 Knowledge Library",
    "🔖 Bookmarks",
    "📅 Weekly Review",
    "🗓️ Monthly Review",
    "🎯 Knowledge Quiz",
    "📈 Learning Analytics",
    "🌐 Research Sources",
    "⚙️ Settings",
]


@st.cache_resource
def get_db() -> LocalKnowledgeDB:
    return LocalKnowledgeDB()


def _navigate_to(page_label: str, focus_pillar: str | None = None, brief_date: str | None = None) -> None:
    st.session_state["active_page"] = page_label
    if focus_pillar:
        st.session_state["focus_pillar"] = focus_pillar
    if brief_date:
        st.session_state["selected_brief_date"] = brief_date
    st.rerun()


def render_home_page(db: LocalKnowledgeDB) -> None:
    """Premium editorial Home Page — strictly focused on today's learning & real progress."""
    formatted_date = now_ist().strftime("%A, %d %B %Y")
    greeting = ist_greeting()

    render_page_hero(
        eyebrow=f"{BRAND_CONFIG['brand_name']} • {BRAND_CONFIG['tagline']}",
        title=f"{greeting}. Welcome to {BRAND_CONFIG['main_title']}.",
        subtitle="Your daily journey towards better Health, Wealth and Wisdom.",
        badge_text=f"{formatted_date} • 10-Minute Daily Edition",
    )

    briefs = db.get_tab_rows("Daily_Learning", limit=6)
    today_brief = briefs[0] if briefs else None

    st.markdown("### Daily Learning Overview")
    if not today_brief:
        st.info("Your first daily edition is waiting. Open Settings to run today's collection.")
    else:
        brief_date = today_brief.get("date", today_ist_str())
        progress_map = {
            (r["brief_date"], r["pillar"].lower()): r
            for r in db.get_lesson_progress(limit=50)
        }

        cols = st.columns(3)
        for idx, pillar in enumerate(("Health", "Wealth", "Wisdom")):
            raw_text = today_brief.get(f"{pillar.lower()}_lesson", "")
            parsed = parse_structured_lesson(raw_text, pillar)
            state = progress_map.get((brief_date, pillar.lower()), {})
            done_tag = "✓ Completed" if state.get("completed") == "TRUE" else f"~{parsed['reading_minutes']} min read"
            badge_cls = f"ltl-badge-{pillar.lower()}"
            card_cls = f"ltl-pillar-{pillar.lower()}"

            with cols[idx]:
                short_title = parsed["title"][:78] + ("..." if len(parsed["title"]) > 78 else "")
                short_takeaway = parsed["takeaway"][:115] + ("..." if len(parsed["takeaway"]) > 115 else "")
                st.markdown(
                    f"""
                    <div class="ltl-card ltl-pillar-card {card_cls}">
                        <div>
                            <span class="ltl-badge {badge_cls}">{pillar.upper()}</span>
                            <div class="ltl-card-title">{html.escape(short_title)}</div>
                            <p class="ltl-card-text">{html.escape(short_takeaway)}</p>
                        </div>
                        <div class="ltl-meta">{html.escape(done_tag)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"Read {pillar} Lesson →", key=f"home_read_{pillar}", use_container_width=True):
                    _navigate_to("☀️ Today's Brief", focus_pillar=pillar, brief_date=brief_date)

        # C. Today's Featured Insight
        featured = strip_technical_clutter(
            today_brief.get("surprising_discovery") or today_brief.get("deep_dive") or ""
        )
        st.markdown(
            f"""
            <div class="ltl-spotlight">
                <span class="ltl-badge ltl-badge-gold">Today's Featured Insight</span>
                <div class="ltl-card-title" style="font-size:1.25rem;margin-bottom:6px;">Spotlight Discovery</div>
                <p style="margin:0;font-size:0.98rem;line-height:1.65;color:#1E293B;">{html.escape(featured)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # D. Daily Progress (Real database metrics only)
    stats = db.get_learning_stats(today_ist_str())
    st.markdown("### Daily Progress")
    m1, m2, m3, m4 = st.columns(4)
    metrics = [
        ("Daily Lessons Completed", f"{stats['today_completed']} / 3"),
        ("Learning Streak", f"{stats['learning_streak']} day{'s' if stats['learning_streak'] != 1 else ''}"),
        ("Total Lessons Studied", str(stats["total_completed"])),
        ("Weekly Progress", f"{stats['weekly_completed']} lessons"),
    ]
    for col, (label, val) in zip((m1, m2, m3, m4), metrics):
        col.markdown(
            f'<div class="ltl-stat"><div class="ltl-stat-label">{label}</div><div class="ltl-stat-val">{val}</div></div>',
            unsafe_allow_html=True,
        )

    # E & F. Today's Action + Reflection of the Day
    if today_brief:
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        a_col, r_col = st.columns(2)
        with a_col:
            action_txt = strip_technical_clutter(today_brief.get("todays_action", ""))
            st.markdown(
                f"""
                <div class="ltl-card" style="background:#FFFDF7;">
                    <span class="ltl-badge ltl-badge-gold">Today's Action</span>
                    <div class="ltl-card-title" style="font-size:1.08rem;">10-Minute Real-Life Practice</div>
                    <p class="ltl-card-text" style="color:#1E293B;margin-bottom:0;">{html.escape(action_txt)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r_col:
            refl_txt = strip_technical_clutter(today_brief.get("reflection_question", ""))
            st.markdown(
                f"""
                <div class="ltl-card">
                    <span class="ltl-badge ltl-badge-wisdom">Reflection of the Day</span>
                    <div class="ltl-card-title" style="font-size:1.08rem;">Critical Thinking Prompt</div>
                    <p class="ltl-card-text" style="color:#1E293B;margin-bottom:0;">{html.escape(refl_txt)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # G. Recent Learning (Last 3-5 lessons from Daily_Learning & curated pillars)
    st.markdown("### Recent Learning")
    recent_cards: list[dict[str, str]] = []
    for b in briefs[:2]:
        b_date = b.get("date", "")
        for p in ("Health", "Wealth", "Wisdom"):
            parsed = parse_structured_lesson(b.get(f"{p.lower()}_lesson", ""), p)
            recent_cards.append(
                {
                    "title": parsed["title"][:62] + ("..." if len(parsed["title"]) > 62 else ""),
                    "pillar": p,
                    "desc": parsed["takeaway"][:88] + ("..." if len(parsed["takeaway"]) > 88 else ""),
                    "date": b_date,
                }
            )
    recent_cards = recent_cards[:4]

    if recent_cards:
        r_cols = st.columns(len(recent_cards))
        for idx, item in enumerate(recent_cards):
            with r_cols[idx]:
                st.markdown(
                    f"""
                    <div class="ltl-card ltl-recent-card">
                        <div>
                            <span class="ltl-badge ltl-badge-{item['pillar'].lower()}">{item['pillar']}</span>
                            <div class="ltl-card-title" style="font-size:1rem;">{html.escape(item['title'])}</div>
                            <p class="ltl-card-text" style="font-size:0.84rem;">{html.escape(item['desc'])}</p>
                        </div>
                        <div class="ltl-meta">{html.escape(item['date'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Read More →", key=f"recent_{idx}_{item['pillar']}", use_container_width=True):
                    _navigate_to("☀️ Today's Brief", focus_pillar=item["pillar"], brief_date=item["date"])


def render_todays_brief_page(db: LocalKnowledgeDB) -> None:
    """Editorial digital publication view of Today's Brief."""
    briefs = db.get_tab_rows("Daily_Learning", limit=30)
    if not briefs:
        render_page_hero("Today's Brief", BRAND_CONFIG["main_title"], BRAND_CONFIG["supporting_description"])
        st.info("No brief available yet. Open Settings to generate your first Daily Brief.")
        return

    dates = [b["date"] for b in briefs if b.get("date")]
    selected_date = st.session_state.get("selected_brief_date")
    default_idx = dates.index(selected_date) if selected_date in dates else 0

    chosen_date = st.selectbox("Select Edition Date", dates, index=default_idx)
    b = next((x for x in briefs if x["date"] == chosen_date), briefs[0])

    is_ai = str(b.get("is_ai_verified", "FALSE")).upper() == "TRUE"
    edition_badge = (
        f"{chosen_date} • Editorially Verified"
        if is_ai
        else f"{chosen_date} • Curated Source Digest"
    )

    render_page_hero(
        eyebrow=f"{BRAND_CONFIG['brand_name']} • Daily Edition",
        title=BRAND_CONFIG["main_title"],
        subtitle=BRAND_CONFIG["tagline"],
        badge_text=edition_badge,
    )

    if not is_ai:
        st.caption(
            "Note: This edition is a structured digest from your curated publications and has not yet undergone a full editorial verification pass."
        )

    focus_pillar = st.session_state.get("focus_pillar", "All")
    view_choice = st.radio(
        "Filter Pillars",
        ["All", "Health", "Wealth", "Wisdom"],
        index=["All", "Health", "Wealth", "Wisdom"].index(focus_pillar) if focus_pillar in ("All", "Health", "Wealth", "Wisdom") else 0,
        horizontal=True,
    )
    st.session_state["focus_pillar"] = view_choice

    pillars_to_show = ("Health", "Wealth", "Wisdom") if view_choice == "All" else (view_choice,)
    for pillar in pillars_to_show:
        render_structured_lesson_card(
            db=db,
            brief_date=chosen_date,
            pillar=pillar,
            raw_lesson=b.get(f"{pillar.lower()}_lesson", ""),
            source_links=b.get("source_links", ""),
            key_prefix="todays_brief",
        )

    # Deep Dive, Surprising Discovery, Mental Model, Action, Reflection
    st.markdown("### Synthesis & Critical Thinking")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div class="ltl-card">
                <span class="ltl-badge ltl-badge-gold">Deep Dive</span>
                <p class="ltl-section-body">{html.escape(strip_technical_clutter(b.get("deep_dive", ""))).replace(chr(10), "<br>")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="ltl-card">
                <span class="ltl-badge ltl-badge-wisdom">Surprising Discovery</span>
                <p class="ltl-section-body">{html.escape(strip_technical_clutter(b.get("surprising_discovery", ""))).replace(chr(10), "<br>")}</p>
                <hr style="border:none;border-top:1px solid #E8E2D5;margin:12px 0;" />
                <span class="ltl-badge ltl-badge-wealth">Mental Model of the Day</span>
                <p class="ltl-section-body">{html.escape(strip_technical_clutter(b.get("mental_model", ""))).replace(chr(10), "<br>")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    c_act, c_ref = st.columns(2)
    with c_act:
        st.markdown(
            f"""
            <div class="ltl-card" style="background:#FFFDF7;">
                <span class="ltl-badge ltl-badge-gold">Today's Action</span>
                <p class="ltl-section-body">{html.escape(strip_technical_clutter(b.get("todays_action", "")))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_ref:
        st.markdown(
            f"""
            <div class="ltl-card">
                <span class="ltl-badge ltl-badge-health">Reflection Question</span>
                <p class="ltl-section-body">{html.escape(strip_technical_clutter(b.get("reflection_question", "")))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    render_sources_block(b.get("source_links", ""), db=db, heading="Original Sources")

    render_related_lessons(db, pillars_to_show[0], exclude_date=chosen_date)

    with st.expander("Preview Email Newsletter Edition"):
        st.components.v1.html(render_newsletter_html(b, b.get("doc_url", ""), db=db), height=680, scrolling=True)


def render_pillar_department_page(db: LocalKnowledgeDB, pillar: str, tab_name: str) -> None:
    """Clean editorial archive for Health, Wealth, or Wisdom."""
    subtitle = BRAND_CONFIG["pillars"][pillar]
    render_page_hero(
        eyebrow=f"{BRAND_CONFIG['brand_name']} • Learning Department",
        title=f"{pillar} Department",
        subtitle=subtitle,
    )

    # Show today's brief lesson for this pillar first
    briefs = db.get_tab_rows("Daily_Learning", limit=1)
    if briefs:
        latest = briefs[0]
        render_structured_lesson_card(
            db=db,
            brief_date=latest.get("date", today_ist_str()),
            pillar=pillar,
            raw_lesson=latest.get(f"{pillar.lower()}_lesson", ""),
            source_links=latest.get("source_links", ""),
            key_prefix=f"dept_{pillar}",
        )

    rows = db.get_tab_rows(tab_name, limit=120)
    st.markdown(f"### Curated {pillar} Readings")
    if not rows:
        st.info(f"No {pillar} readings archived yet. Visit Settings to refresh feeds.")
        return

    df = pd.DataFrame(rows)
    search = st.text_input(f"Search {pillar} readings", placeholder="Search topics, studies, or publications...", key=f"search_{pillar}")
    if search:
        mask = df["article_title"].str.contains(search, case=False, na=False) | df["summary"].str.contains(search, case=False, na=False)
        df = df[mask]

    for idx, row in df.head(15).iterrows():
        title = strip_technical_clutter(row.get("article_title", "Untitled"))
        source_name = row.get("source_name", "Research Source")
        pub_date = row.get("publication_date", "")
        evidence = humanize_evidence_label(row.get("claim_classification", ""))
        summary = strip_technical_clutter(row.get("summary", ""))
        link = row.get("original_article_link", "")

        with st.expander(f"{title} — {source_name} ({pub_date})"):
            st.caption(f"Evidence Type: {evidence}")
            st.write(summary or "Read the full publication for complete details.")
            if link:
                st.markdown(f"**Source: {source_name}** – [{title} ↗]({link})")
            if st.button("Save to Bookmarks", key=f"dept_bm_{pillar}_{idx}"):
                added = db.add_bookmark_if_new(
                    {
                        "bookmark_id": str(uuid.uuid4())[:8],
                        "date_saved": today_ist_str(),
                        "pillar": pillar,
                        "title": title,
                        "lesson_text": summary[:380],
                        "source_link": link,
                        "notes": f"Saved from {pillar} Department",
                    }
                )
                st.success("Saved to Bookmarks.") if added else st.info("Already in Bookmarks.")


def render_knowledge_library_page(db: LocalKnowledgeDB) -> None:
    """Searchable archive of all Daily Briefs and curated lessons with pillar filtering."""
    render_page_hero(
        eyebrow=BRAND_CONFIG["brand_name"],
        title="Knowledge Library",
        subtitle="Search and revisit every lesson across Health, Wealth, and Wisdom.",
    )

    c_search, c_filter = st.columns([2, 1])
    query = c_search.text_input("Search lessons", placeholder="Keyword, concept, or mental model...")
    pillar_filter = c_filter.selectbox("Filter by Pillar", ["All", "Health", "Wealth", "Wisdom"])

    briefs = db.get_tab_rows("Daily_Learning", limit=60)
    progress_rows = db.get_lesson_progress(limit=200)
    completed_keys = {(r["brief_date"], r["pillar"].lower()) for r in progress_rows if r["completed"] == "TRUE"}
    later_keys = {(r["brief_date"], r["pillar"].lower()) for r in progress_rows if r["read_later"] == "TRUE"}

    if not briefs:
        st.info("No lessons stored in your Knowledge Library yet.")
        return

    pillars = ("Health", "Wealth", "Wisdom") if pillar_filter == "All" else (pillar_filter,)
    matched = 0
    for b in briefs:
        b_date = b.get("date", "")
        for p in pillars:
            raw = b.get(f"{p.lower()}_lesson", "")
            parsed = parse_structured_lesson(raw, p)
            blob = f"{parsed['title']} {parsed['clean_prose']}".lower()
            if query and query.lower() not in blob:
                continue
            matched += 1
            tags = []
            if (b_date, p.lower()) in completed_keys:
                tags.append("✓ Completed")
            if (b_date, p.lower()) in later_keys:
                tags.append("🕒 Read Later")
            tag_str = " • ".join(tags) if tags else f"~{parsed['reading_minutes']} min read"

            st.markdown(
                f"""
                <div class="ltl-card" style="margin-bottom:12px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span class="ltl-badge ltl-badge-{p.lower()}">{p} &bull; {html.escape(b_date)}</span>
                        <span class="ltl-meta">{html.escape(tag_str)}</span>
                    </div>
                    <div class="ltl-card-title">{html.escape(parsed['title'])}</div>
                    <p class="ltl-card-text" style="margin-bottom:0;">{html.escape(parsed['takeaway'])}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Open Full Lesson →", key=f"lib_open_{b_date}_{p}"):
                _navigate_to("☀️ Today's Brief", focus_pillar=p, brief_date=b_date)

    if matched == 0:
        st.info("No lessons matched your search filter.")


def render_bookmarks_page(db: LocalKnowledgeDB) -> None:
    """Bookmarks & Read Later queue."""
    render_page_hero(
        eyebrow=BRAND_CONFIG["brand_name"],
        title="Bookmarks & Read Later",
        subtitle="Your personal collection of high-value insights and saved lessons.",
    )

    later_items = [r for r in db.get_lesson_progress(limit=100) if r.get("read_later") == "TRUE"]
    if later_items:
        st.markdown("### Read Later Queue")
        for item in later_items:
            col_a, col_b = st.columns([4, 1])
            col_a.markdown(f"**[{item['pillar']}]** {item['title']} *({item['brief_date']})*")
            if col_b.button("Open →", key=f"rl_{item['progress_key']}"):
                _navigate_to("☀️ Today's Brief", focus_pillar=item["pillar"], brief_date=item["brief_date"])

    st.markdown("### Add Personal Note or Bookmark")
    with st.form("add_bookmark_form"):
        pillar = st.selectbox("Pillar", ["Health", "Wealth", "Wisdom"])
        title = st.text_input("Lesson Title")
        lesson_text = st.text_area("Key Takeaway")
        source_link = st.text_input("Source Link (optional)")
        notes = st.text_input("Personal Reflection / Notes")
        if st.form_submit_button("Save Bookmark") and title:
            added = db.add_bookmark_if_new(
                {
                    "bookmark_id": str(uuid.uuid4())[:8],
                    "date_saved": today_ist_str(),
                    "pillar": pillar,
                    "title": title.strip(),
                    "lesson_text": lesson_text.strip(),
                    "source_link": source_link.strip(),
                    "notes": notes.strip(),
                }
            )
            if added:
                st.success("Saved to Bookmarks.")
                st.rerun()
            else:
                st.info("A bookmark with this title already exists.")

    st.markdown("### Saved Lessons")
    bms = db.get_tab_rows("Bookmarks", limit=100)
    if not bms:
        st.info("No bookmarks saved yet. Use 'Save to Bookmarks' on any lesson to build your library.")
        return

    for bm in bms:
        link = bm.get("source_link", "")
        link_html = (
            f' &bull; <a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer" style="color:#1D4ED8;font-weight:600;text-decoration:none;">Read Original Research &#8599;</a>'
            if link.startswith(("http://", "https://"))
            else ""
        )
        st.markdown(
            f"""
            <div class="ltl-card" style="margin-bottom:10px;">
                <span class="ltl-badge ltl-badge-{bm.get('pillar', 'wisdom').lower()}">{html.escape(bm.get('pillar', ''))} &bull; {html.escape(bm.get('date_saved', ''))}</span>
                <div class="ltl-card-title" style="font-size:1.05rem;">{html.escape(bm.get('title', ''))}</div>
                <p class="ltl-card-text">{html.escape(bm.get('lesson_text', ''))}</p>
                <div class="ltl-meta">{html.escape(bm.get('notes', ''))}{link_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_weekly_review_page(db: LocalKnowledgeDB) -> None:
    render_page_hero(
        eyebrow=BRAND_CONFIG["brand_name"],
        title="Weekly Learning Review",
        subtitle="Consolidate your top insights, track pillar momentum, and plan revision.",
    )
    if st.button("Refresh Weekly Review", type="primary"):
        build_weekly_review(db=db)
        st.rerun()

    reviews = db.get_tab_rows("Weekly_Reviews", limit=12)
    if not reviews:
        st.info("No weekly review generated yet. Click 'Refresh Weekly Review' above.")
        return

    r = reviews[0]
    st.markdown(
        f"""
        <div class="ltl-card" style="margin-bottom:16px;">
            <span class="ltl-badge ltl-badge-gold">Week Ending {html.escape(r.get('week_ending', ''))}</span>
            <p class="ltl-section-body">{html.escape(r.get('summary', ''))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Top 10 Weekly Learnings")
        st.markdown(
            f'<div class="ltl-card"><pre style="white-space:pre-wrap;font-family:inherit;margin:0;line-height:1.6;">{html.escape(r.get("top_10_learnings", ""))}</pre></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown("#### Weekly Revision Suggestions")
        st.markdown(
            f'<div class="ltl-card"><pre style="white-space:pre-wrap;font-family:inherit;margin:0;line-height:1.6;">{html.escape(r.get("revision_topics", ""))}</pre>'
            f'<hr style="border:none;border-top:1px solid #E8E2D5;margin:12px 0;" />'
            f'<strong>Next Week Focus:</strong><br>{html.escape(r.get("next_week_suggestions", ""))}</div>',
            unsafe_allow_html=True,
        )


def render_monthly_review_page(db: LocalKnowledgeDB) -> None:
    render_page_hero(
        eyebrow=BRAND_CONFIG["brand_name"],
        title="Monthly Knowledge Review",
        subtitle="Long-horizon reflection on consistency, retention, and personal growth.",
    )
    if st.button("Refresh Monthly Review", type="primary"):
        build_monthly_review(db=db)
        st.rerun()

    rows = db.get_tab_rows("Monthly_Reviews", limit=12)
    if not rows:
        st.info("No monthly review generated yet.")
        return
    for r in rows:
        st.markdown(
            f"""
            <div class="ltl-card" style="margin-bottom:12px;">
                <span class="ltl-badge ltl-badge-gold">Month: {html.escape(r.get('month', ''))}</span>
                <p class="ltl-section-body">{html.escape(r.get('summary', ''))}</p>
                <div class="ltl-meta">{html.escape(r.get('pillar_breakdown', ''))} &bull; Quiz Accuracy: {html.escape(r.get('quiz_accuracy', ''))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_quiz_page(db: LocalKnowledgeDB) -> None:
    render_page_hero(
        eyebrow=BRAND_CONFIG["brand_name"],
        title="Knowledge Quiz",
        subtitle="Reinforce retention with a 10-question weekly review quiz.",
    )
    week_str = today_ist_str()
    quiz_file = REVIEWS_DIR / f"weekly_{week_str}.json"
    if quiz_file.exists():
        questions = json.loads(quiz_file.read_text(encoding="utf-8")).get("quiz_questions", [])
    else:
        questions = generate_weekly_quiz(db, week_str)

    with st.form("weekly_quiz_form"):
        answers = {}
        for q in questions:
            st.markdown(f"**Q{q['question_no']} ({q['pillar']}):** {q['question']}")
            answers[q["question_no"]] = st.radio(
                "Select one option:",
                q["options"],
                key=f"quiz_q_{q['question_no']}",
                label_visibility="collapsed",
            )
            st.divider()
        submitted = st.form_submit_button("Submit Quiz", type="primary")

    if submitted:
        score = 0
        result_rows = []
        for q in questions:
            user_ans = answers[q["question_no"]]
            correct = user_ans == q["correct_answer"]
            if correct:
                score += 1
            result_rows.append(
                {
                    "quiz_id": q["quiz_id"],
                    "week_ending": q["week_ending"],
                    "question_no": str(q["question_no"]),
                    "pillar": q["pillar"],
                    "question": q["question"],
                    "user_answer": user_ans,
                    "correct_answer": q["correct_answer"],
                    "is_correct": "TRUE" if correct else "FALSE",
                    "explanation": q["explanation"],
                    "submitted_at": now_ist().isoformat(),
                }
            )
        db.save_quiz_results(result_rows)
        st.success(f"Quiz Score: {score} / {len(questions)}")
        for r in result_rows:
            if r["is_correct"] == "FALSE":
                st.warning(f"Q{r['question_no']}: Correct = {r['correct_answer']} — {r['explanation']}")


def render_analytics_page(db: LocalKnowledgeDB) -> None:
    render_page_hero(
        eyebrow=BRAND_CONFIG["brand_name"],
        title="Learning Analytics",
        subtitle="Track real study progress, pillar balance, and quiz mastery.",
    )
    stats = db.get_learning_stats(today_ist_str())
    counts = db.get_counts()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Completed Lessons", stats["total_completed"])
    c2.metric("Current Streak", f"{stats['learning_streak']} days")
    c3.metric("Saved Bookmarks", counts.get("Bookmarks", 0))
    c4.metric("Daily Editions", counts.get("Daily_Learning", 0))

    chart_df = pd.DataFrame(
        [
            {"Pillar": "Health", "Archived Studies": counts.get("Health_Research", 0)},
            {"Pillar": "Wealth", "Archived Studies": counts.get("Wealth_Research", 0)},
            {"Pillar": "Wisdom", "Archived Studies": counts.get("Wisdom_Research", 0)},
        ]
    )
    fig = px.bar(
        chart_df,
        x="Pillar",
        y="Archived Studies",
        color="Pillar",
        color_discrete_map={"Health": "#1F7A5C", "Wealth": "#1D4ED8", "Wisdom": "#6D28D9"},
        title="Knowledge Archive by Pillar",
    )
    fig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    quiz_rows = db.get_tab_rows("Quiz_Results", limit=200)
    if quiz_rows:
        qdf = pd.DataFrame(quiz_rows)
        qdf["correct_num"] = qdf["is_correct"].str.upper().eq("TRUE").astype(int)
        acc = qdf.groupby("pillar")["correct_num"].mean().reset_index()
        acc["Accuracy (%)"] = (acc["correct_num"] * 100).round(1)
        qfig = px.bar(acc, x="pillar", y="Accuracy (%)", title="Quiz Accuracy by Pillar")
        qfig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
        st.plotly_chart(qfig, use_container_width=True)


def render_research_sources_page(db: LocalKnowledgeDB) -> None:
    render_page_hero(
        eyebrow=BRAND_CONFIG["brand_name"],
        title="Research Sources",
        subtitle="Curated scientific journals, institutional releases, and educational publications.",
    )
    sources_cfg = load_sources()
    db.upsert_sources(sources_cfg)

    for pillar in ("health", "wealth", "wisdom"):
        st.markdown(f"### {pillar.capitalize()} Publications")
        items = sources_cfg.get(pillar, [])
        cols = st.columns(2)
        for idx, src in enumerate(items):
            with cols[idx % 2]:
                topics_str = ", ".join(src.get("topics", []))
                st.markdown(
                    f"""
                    <div class="ltl-card" style="margin-bottom:12px;">
                        <span class="ltl-badge ltl-badge-{pillar}">{pillar.capitalize()}</span>
                        <div class="ltl-card-title" style="font-size:1.05rem;">{html.escape(src['name'])}</div>
                        <p class="ltl-card-text">{html.escape(src.get('notes', ''))}</p>
                        <div class="ltl-meta">Topics: {html.escape(topics_str)} &bull; <a href="{html.escape(src['url'])}" target="_blank" rel="noopener noreferrer" style="color:#1D4ED8;text-decoration:none;font-weight:600;">Visit Feed &#8599;</a></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_settings_page(db: LocalKnowledgeDB, settings: dict[str, Any]) -> None:
    """Backend controls, Google sync, Topic History (Duplicate Prevention), and System Diagnostics."""
    render_page_hero(
        eyebrow="Platform Administration",
        title="Settings & System Diagnostics",
        subtitle="Manage research collection, Google Workspace sync, duplicate prevention, and diagnostics.",
    )

    st.markdown("### Pipeline Actions")
    col_a, col_b, col_c = st.columns(3)
    if col_a.button("Collect Research & Build Today's Brief", type="primary", use_container_width=True):
        with st.spinner("Collecting curated publications and building today's brief..."):
            res = run_daily_pipeline(skip_fetch=False, send_email=False)
        st.success(f"Completed in {res['duration_sec']}s.")
        st.rerun()

    if col_b.button("Generate Weekly Review & Quiz", use_container_width=True):
        with st.spinner("Building weekly review and 10-question quiz..."):
            run_weekly_pipeline()
        st.success("Weekly Review and Quiz updated.")
        st.rerun()

    if col_c.button("Sync to Google Sheets", use_container_width=True):
        sync_res = GoogleWorkspaceSync(settings).sync_all(db, send_email=False)
        st.info(f"Sync status: {sync_res.get('status')} — {sync_res.get('message', '')}")

    st.markdown("### System Configuration & Guardrails")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Google Sync", settings.get("google_sync_mode", "local_only"))
    c2.metric("Email Auto-Send", "Approved" if settings.get("allow_email_send") else "Off (Safe)")
    c3.metric("Additional Budget", f"₹{settings.get('budget_inr', 0)}")
    c4.metric("AI Overages", "Never")

    st.caption(
        f"Creator Attribution: {BRAND_CONFIG['creator_name']} • LinkedIn: {BRAND_CONFIG['creator_linkedin_url']}"
    )

    with st.expander("Database Table Counts & Diagnostics"):
        st.json(db.get_counts())

    with st.expander("Topic History (Duplicate Prevention)"):
        topics = db.get_tab_rows("Topic_History", limit=100)
        if topics:
            st.dataframe(pd.DataFrame(topics), use_container_width=True)
        else:
            st.info("No topic history recorded yet.")

    with st.expander("Automation Logs"):
        logs = db.get_tab_rows("Automation_Logs", limit=25)
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else:
            st.info("No automation runs logged yet.")


def main() -> None:
    inject_theme_css()
    db = get_db()
    settings = load_settings()

    if "active_page" not in st.session_state or st.session_state["active_page"] not in NAV_ITEMS:
        st.session_state["active_page"] = NAV_ITEMS[0]

    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding:8px 4px 14px 4px;border-bottom:1px solid #1E2E4D;margin-bottom:12px;">
                <div style="font-size:0.7rem;letter-spacing:0.16em;text-transform:uppercase;color:#C59B38;font-weight:700;">{html.escape(BRAND_CONFIG['brand_name'])}</div>
                <div style="font-family:'Playfair Display',Georgia,serif;font-size:1.35rem;font-weight:700;color:#FFFFFF;margin-top:2px;">{html.escape(BRAND_CONFIG['main_title'])}</div>
                <div style="font-size:0.78rem;color:#94A3B8;margin-top:4px;line-height:1.4;">{html.escape(BRAND_CONFIG['tagline'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected_page = st.radio(
            "Navigation",
            NAV_ITEMS,
            index=NAV_ITEMS.index(st.session_state["active_page"]),
            label_visibility="collapsed",
        )
        if selected_page != st.session_state["active_page"]:
            st.session_state["active_page"] = selected_page
            st.rerun()

        st.markdown("---")
        stats = db.get_learning_stats(today_ist_str())
        st.markdown(
            f"""
            <div style="font-size:0.78rem;color:#CBD5E1;line-height:1.6;">
                <div><strong>Today's Progress:</strong> {stats['today_completed']} / 3 lessons</div>
                <div><strong>Streak:</strong> {stats['learning_streak']} day{'s' if stats['learning_streak'] != 1 else ''}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    active = st.session_state["active_page"]
    if active == "🏠 Home":
        render_home_page(db)
    elif active == "☀️ Today's Brief":
        render_todays_brief_page(db)
    elif active == "💚 Health":
        render_pillar_department_page(db, "Health", "Health_Research")
    elif active == "💼 Wealth":
        render_pillar_department_page(db, "Wealth", "Wealth_Research")
    elif active == "🧠 Wisdom":
        render_pillar_department_page(db, "Wisdom", "Wisdom_Research")
    elif active == "📚 Knowledge Library":
        render_knowledge_library_page(db)
    elif active == "🔖 Bookmarks":
        render_bookmarks_page(db)
    elif active == "📅 Weekly Review":
        render_weekly_review_page(db)
    elif active == "🗓️ Monthly Review":
        render_monthly_review_page(db)
    elif active == "🎯 Knowledge Quiz":
        render_quiz_page(db)
    elif active == "📈 Learning Analytics":
        render_analytics_page(db)
    elif active == "🌐 Research Sources":
        render_research_sources_page(db)
    elif active == "⚙️ Settings":
        render_settings_page(db, settings)

    # Display the signature Hitesh Rawal footer cleanly on all main learning pages (once per page)
    if active != "⚙️ Settings":
        render_premium_footer()


if __name__ == "__main__":
    main()
