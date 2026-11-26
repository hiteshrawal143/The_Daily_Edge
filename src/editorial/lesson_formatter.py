"""Editorial lesson formatter & sanitizer (7-section Hinglish structure, zero technical clutter)."""

from __future__ import annotations

import re
from typing import Any

SECTION_ORDER = [
    ("core_idea", "The Core Idea"),
    ("why_it_matters", "Why It Matters"),
    ("what_research_says", "What Science & Research Say"),
    ("real_life_example", "Real-Life Example"),
    ("practical_application", "Practical Application"),
    ("key_takeaway", "Key Takeaway"),
]

# Patterns of internal/technical clutter that must never appear inside educational prose
_CLUTTER_PATTERNS = (
    r"\[RSS-Only Digest\s*[–-]\s*Not AI-Verified\]\s*",
    r"\[Verified Scientific Research[^\]]*\]\s*",
    r"\[Educational Only[^\]]*\]\s*",
    r"\[Verified Science Journalism[^\]]*\]\s*",
    r"\|\s*Classification:\s*[a-z_]+",
    r"Classification:\s*[a-z_]+",
    r"https?://\S+",
    r"(?im)^\s*Source:\s*$",
    r"(?im)^\s*Summary:\s*",
)

_EVIDENCE_LABELS = {
    "verified_research_or_official_data": "Peer-reviewed research / official institutional data",
    "scientific_or_institutional_report": "Scientific or institutional report",
    "expert_opinion_or_analysis": "Expert analysis & commentary",
    "speculation_or_forecast": "Forward-looking opinion / forecast (treat cautiously)",
}


def humanize_evidence_label(raw_classification: str) -> str:
    """Convert internal claim enum into clean, human-readable editorial language."""
    return _EVIDENCE_LABELS.get(raw_classification, "Public research report")


def strip_technical_clutter(text: str) -> str:
    """Remove internal RSS flags, classification enums, and raw URLs from lesson prose."""
    cleaned = str(text or "")
    for pat in _CLUTTER_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def estimate_reading_minutes(text: str) -> int:
    """Estimate reading time in minutes (minimum 2 min per pillar lesson)."""
    words = len(re.findall(r"\w+", text or ""))
    return max(2, round(words / 160))


def extract_lesson_title_and_takeaway(lesson_text: str, pillar: str) -> tuple[str, str]:
    """Extract a clean topic title and a crisp one-line takeaway from structured or prose lessons."""
    cleaned = strip_technical_clutter(lesson_text)
    if not cleaned:
        return f"Today's {pillar} Perspective", f"Build daily clarity in {pillar.lower()}."

    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    title = f"Today's {pillar} Lesson"
    takeaway = ""

    for ln in lines:
        if ln.lower().startswith("title:"):
            title = ln.split(":", 1)[1].strip()
            break
        if ln.startswith("### "):
            title = ln.removeprefix("### ").strip()
            break

    for idx, ln in enumerate(lines):
        if "key takeaway" in ln.lower():
            if ":" in ln and ln.split(":", 1)[1].strip():
                takeaway = ln.split(":", 1)[1].strip()
            elif idx + 1 < len(lines):
                takeaway = lines[idx + 1]
            break

    if title == f"Today's {pillar} Lesson":
        # Fallback: derive concise headline from first meaningful content line
        for candidate_line in lines:
            cand = re.sub(r"^(?:1\.\s*)?(?:Aaj ke .*?:|The Core Idea:?)\s*", "", candidate_line, flags=re.IGNORECASE)
            cand = re.sub(r"^\d+\.\s*", "", cand).strip()
            if len(cand) >= 8:
                words = cand.split()
                title = " ".join(words[:10]).rstrip(".,;:") + ("..." if len(words) > 10 else "")
                break

    if not takeaway:
        meaningful_lines = [ln for ln in lines if len(ln.strip()) >= 12 and not ln.strip().lower().startswith("source:")]
        chosen = meaningful_lines[-1] if meaningful_lines else lines[-1]
        takeaway = chosen[:140].rstrip("., ") + ("..." if len(chosen) > 140 else "")

    return title, takeaway


def parse_structured_lesson(lesson_text: str, pillar: str) -> dict[str, Any]:
    """Parse a structured 7-part lesson (or gracefully adapt legacy prose into readable sections)."""
    cleaned = strip_technical_clutter(lesson_text)
    title, takeaway = extract_lesson_title_and_takeaway(cleaned, pillar)

    sections: dict[str, str] = {}
    heading_map = {
        "the core idea": "core_idea",
        "core idea": "core_idea",
        "why it matters": "why_it_matters",
        "what science / research says": "what_research_says",
        "what science & research say": "what_research_says",
        "what research says": "what_research_says",
        "real-life example": "real_life_example",
        "real life example": "real_life_example",
        "practical application": "practical_application",
        "key takeaway": "key_takeaway",
    }

    current_key: str | None = None
    buffer: list[str] = []

    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        normalized = re.sub(r"^[#*>\d.\s]+", "", line).rstrip("*:# ").strip().lower()
        if normalized in heading_map:
            if current_key and buffer:
                sections[current_key] = "\n".join(buffer).strip()
            current_key = heading_map[normalized]
            buffer = []
        elif line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
        else:
            if current_key is not None:
                buffer.append(raw_line)
    if current_key and buffer:
        sections[current_key] = "\n".join(buffer).strip()

    # If the lesson was saved as clean narrative paragraphs without explicit headings, keep it crisp
    is_structured = len(sections) >= 3
    return {
        "title": title,
        "takeaway": sections.get("key_takeaway", takeaway),
        "reading_minutes": estimate_reading_minutes(cleaned),
        "is_structured": is_structured,
        "sections": sections,
        "clean_prose": cleaned,
    }


def format_structured_lesson(
    title: str,
    core_idea: str,
    why_it_matters: str,
    what_research_says: str,
    real_life_example: str,
    practical_application: str,
    key_takeaway: str,
) -> str:
    """Format a lesson into the standard 7-section editorial layout."""
    return (
        f"Title: {title.strip()}\n\n"
        f"**The Core Idea**\n{core_idea.strip()}\n\n"
        f"**Why It Matters**\n{why_it_matters.strip()}\n\n"
        f"**What Science & Research Say**\n{what_research_says.strip()}\n\n"
        f"**Real-Life Example**\n{real_life_example.strip()}\n\n"
        f"**Practical Application**\n{practical_application.strip()}\n\n"
        f"**Key Takeaway**\n{key_takeaway.strip()}"
    )
