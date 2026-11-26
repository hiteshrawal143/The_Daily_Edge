"""Sunday Weekly Learning Review & 10-Question Knowledge Quiz generator."""

from __future__ import annotations

import json
from typing import Any

from src.config import BRAND_CONFIG, REVIEWS_DIR, ensure_directories, now_ist, today_ist_str
from src.editorial.lesson_formatter import humanize_evidence_label, strip_technical_clutter
from src.storage.local_db import LocalKnowledgeDB


def generate_weekly_quiz(db: LocalKnowledgeDB, week_ending: str) -> list[dict[str, Any]]:
    """Build a 10-question revision quiz grounded in stored Health, Wealth, and Wisdom records."""
    questions: list[dict[str, Any]] = []
    pillars = [
        ("Health", "Health_Research"),
        ("Wealth", "Wealth_Research"),
        ("Wisdom", "Wisdom_Research"),
    ]
    pool: list[tuple[str, dict[str, Any]]] = []
    for pillar_name, tab in pillars:
        rows = db.get_tab_rows(tab, limit=6)
        for r in rows:
            pool.append((pillar_name, r))

    # Build up to 10 grounded questions from collected articles; pad with core curriculum questions if DB is brand new
    for idx in range(10):
        q_no = idx + 1
        if idx < len(pool):
            pillar_name, art = pool[idx]
            title = strip_technical_clutter(art.get("article_title", "Core Principle"))
            source = art.get("source_name", "Research Feed")
            evidence = humanize_evidence_label(art.get("claim_classification", ""))
            other_sources = list(
                dict.fromkeys(
                    p[1].get("source_name", "")
                    for p in pool
                    if p[1].get("source_name") and p[1].get("source_name") != source
                )
            )
            fallback_distractors = [
                "Unverified Social Media Post",
                "Anonymous Forum Rumor",
                "Paid Marketing Brochure",
                "Promotional Newsletter",
            ]
            distractors: list[str] = []
            for cand in other_sources + fallback_distractors:
                if cand != source and cand not in distractors:
                    distractors.append(cand)
                if len(distractors) == 3:
                    break
            options = [source] + distractors
            questions.append(
                {
                    "quiz_id": f"quiz_{week_ending}_q{q_no}",
                    "week_ending": week_ending,
                    "question_no": q_no,
                    "pillar": pillar_name,
                    "question": f"[{pillar_name}] Kis credible source ne '{title[:110]}' ({evidence}) publish kiya?",
                    "options": options,
                    "correct_answer": source,
                    "explanation": (
                        f"Yeh insight {source} ({art.get('publication_date', '')}) dwara publish kiya gaya tha."
                    ),
                    "source_link": art.get("original_article_link", ""),
                }
            )
        else:
            fallback_bank = _core_curriculum_questions(week_ending)
            q = fallback_bank[(idx - len(pool)) % len(fallback_bank)].copy()
            q["question_no"] = q_no
            q["quiz_id"] = f"quiz_{week_ending}_q{q_no}"
            questions.append(q)
    return questions


def _core_curriculum_questions(week_ending: str) -> list[dict[str, Any]]:
    """Evergreen critical-thinking, health, and wealth literacy questions."""
    return [
        {
            "week_ending": week_ending,
            "pillar": "Health",
            "question": "[Health] Sleep aur recovery optimize karne ka sabse strong evidence-based lever kya hai?",
            "options": [
                "Consistent sleep-wake schedule + morning natural light exposure",
                "Late-night bright screens",
                "Weekend par 14 ghante sona",
                "Caffeine ko sone se 1 ghante pehle lena",
            ],
            "correct_answer": "Consistent sleep-wake schedule + morning natural light exposure",
            "explanation": "Circadian rhythm regularity aur subah ki daylight melatonin timing ko anchor karti hai.",
        },
        {
            "week_ending": week_ending,
            "pillar": "Wealth",
            "question": "[Wealth] Long-term compounding mein sabse bada behavioral edge kya hota hai?",
            "options": [
                "Low-cost diversification, emergency fund, aur panic selling se bachna",
                "Daily hot stock tips follow karna",
                "Emergency fund ke bina leverage lena",
                "Har week portfolio churn karna",
            ],
            "correct_answer": "Low-cost diversification, emergency fund, aur panic selling se bachna",
            "explanation": "Behavior gap aur unnecessary fees avoid karne se compounding uninterrupted chalti hai.",
        },
        {
            "week_ending": week_ending,
            "pillar": "Wisdom",
            "question": "[Wisdom] First-principles thinking aur inversion mental model ka kya matlab hai?",
            "options": [
                "Problem ko basic truths mein todna aur fail hone ke reasons pehle avoid karna",
                "Crowd ko blindly copy karna",
                "Sirf first headline padh kar decision lena",
                "Confirmation bias ko ignore karna",
            ],
            "correct_answer": "Problem ko basic truths mein todna aur fail hone ke reasons pehle avoid karna",
            "explanation": "Inversion ('avoid stupidity before chasing brilliance') aur first principles decisions ko sharp banate hain.",
        },
    ]


def build_weekly_review(
    db: LocalKnowledgeDB | None = None,
    week_ending: str | None = None,
) -> dict[str, Any]:
    """Generate Sunday's Weekly Learning Review, top 10 learnings, revision topics, and quiz."""
    ensure_directories()
    db = db or LocalKnowledgeDB()
    target_week = week_ending or today_ist_str()

    briefs = db.get_tab_rows("Daily_Learning", limit=7)
    health_rows = db.get_tab_rows("Health_Research", limit=30)
    wealth_rows = db.get_tab_rows("Wealth_Research", limit=30)
    wisdom_rows = db.get_tab_rows("Wisdom_Research", limit=30)
    quiz_results = db.get_tab_rows("Quiz_Results", limit=30)

    top_10: list[str] = []
    for label, rows in (("Health", health_rows), ("Wealth", wealth_rows), ("Wisdom", wisdom_rows)):
        for art in rows[:4]:
            if len(top_10) < 10:
                clean_t = strip_technical_clutter(art.get("article_title", ""))
                top_10.append(
                    f"[{label}] {clean_t} — Source: {art.get('source_name', '')}"
                )

    quiz_questions = generate_weekly_quiz(db, target_week)

    incorrect_topics = [
        f"{r.get('pillar', '')}: {r.get('question', '')[:80]}"
        for r in quiz_results
        if str(r.get("is_correct", "")).upper() == "FALSE"
    ][:5]
    revision_topics = incorrect_topics or [
        "Health: Sleep regularity & stress physiology",
        "Wealth: Emergency fund sizing & compounding basics",
        "Wisdom: Fact vs expert opinion vs speculation audit",
    ]

    review = {
        "week_ending": target_week,
        "summary": (
            f"Week ending {target_week}: {len(briefs)} daily briefs generated, "
            f"{len(health_rows)} Health, {len(wealth_rows)} Wealth, aur {len(wisdom_rows)} Wisdom research items stored."
        ),
        "top_10_learnings": "\n".join(f"{i+1}. {item}" for i, item in enumerate(top_10)) or "Collect feeds first.",
        "health_progress": f"{len(health_rows)} evidence-based Health items archived.",
        "wealth_progress": f"{len(wealth_rows)} educational Wealth items archived.",
        "wisdom_progress": f"{len(wisdom_rows)} Wisdom & critical-thinking items archived.",
        "revision_topics": "\n".join(f"- {t}" for t in revision_topics),
        "next_week_suggestions": (
            "1. Kam se kam 3 Bookmarks add karein. "
            "2. Weekly 10-question quiz complete karein. "
            "3. Ek Health habit aur ek Financial checklist implement karein."
        ),
        "quiz_questions": quiz_questions,
        "doc_url": "",
        "created_at": now_ist().isoformat(),
    }

    db.save_weekly_review(review)

    out_path = REVIEWS_DIR / f"weekly_{target_week}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(review, fh, indent=2, ensure_ascii=False)

    return review
