# Life Time Library – The Daily Edge

**10 Minutes. Learn Daily. Live Intentionally. Evolve Continuously.**

Build a healthier body, a stronger financial mind, and deeper wisdom through consistent daily learning across **Health**, **Wealth**, and **Wisdom** in natural Hinglish.

Created by **Hitesh Rawal** ([Connect on LinkedIn ↗](https://www.linkedin.com/in/rawalhitesh/)).

---

## Key Features

- **Editorial 13-Page Streamlit Platform**:
  - Warm ivory & deep navy editorial design system with muted gold accents (`src/dashboard/theme.py`, `src/dashboard/components.py`, `src/dashboard/app.py`).
  - **Home Page**: IST greeting, Health/Wealth/Wisdom daily overview cards, Featured Insight spotlight, real DB-backed Daily Progress & learning streak, Today's Action, Reflection of the Day, and Recent Learning.
  - **Structured 7-Part Hinglish Lessons**: Interesting Title, The Core Idea, Why It Matters, What Science & Research Say, Real-Life Example, Practical Application, and Key Takeaway (`src/editorial/lesson_formatter.py`).
  - **Descriptive Source Citations**: Replaces raw URLs with readable `Source: <Publication> – <Article Title>` links everywhere (`src/editorial/citations.py`).
  - **Interactive Learning Tools**: Mark lessons completed, Save to Bookmarks, Read Later queue, Knowledge Library search & pillar filter, Related Previous Lessons, Weekly/Monthly Reviews, and 10-question Knowledge Quiz.
  - **System Diagnostics & Settings**: Keeps Topic History, automation logs, database diagnostics, and feed sync separated cleanly inside Settings.
- **Automated Research Pipeline**:
  - 23 curated public RSS/podcast sources (`config/sources.json`).
  - Deduplication, clickbait filtering, claim evidence labeling, and 12-tab local SQLite database + `Lesson_Progress` tracking (`src/storage/local_db.py`).
  - Google Workspace sync (`apps_script/` & `src/storage/google_sync.py`) for Google Sheets, Google Docs (`Daily_Growth_Brief_YYYY_MM_DD`), PDF exports, and Gmail HTML newsletters.
- **Zero-Extra-Cost Architecture**:
  - Runs locally and via free Google Workspace services without paid AI APIs, paid databases, or credit overages.

## Quick Commands (Windows PowerShell)

```powershell
# Launch the redesigned 13-page Streamlit platform
d:\LifeTimeLibrary\.venv\Scripts\streamlit.exe run d:\LifeTimeLibrary\src\dashboard\app.py

# Collect today's research and update local database / exports
d:\LifeTimeLibrary\.venv\Scripts\python.exe d:\LifeTimeLibrary\scripts\run_daily.py

# Prepare today's Antigravity editorial packet
d:\LifeTimeLibrary\.venv\Scripts\python.exe d:\LifeTimeLibrary\scripts\prepare_ai_packet.py

# Apply an editorially verified Hinglish brief JSON
d:\LifeTimeLibrary\.venv\Scripts\python.exe d:\LifeTimeLibrary\scripts\apply_ai_brief.py d:\LifeTimeLibrary\data\briefs\2026-11-26.json

# Generate Weekly Review & 10-question Quiz
d:\LifeTimeLibrary\.venv\Scripts\python.exe d:\LifeTimeLibrary\scripts\run_weekly.py

# Generate local HTML email preview (no email sent)
d:\LifeTimeLibrary\.venv\Scripts\python.exe d:\LifeTimeLibrary\scripts\test_email_preview.py

# Run automated test suite
d:\LifeTimeLibrary\.venv\Scripts\python.exe -m pytest d:\LifeTimeLibrary\tests\test_pipeline.py -v
```

See [NEXT_STEPS.md](NEXT_STEPS.md) to authorize Google Sheets, Google Docs/PDF export, Gmail delivery, and daily scheduling.
