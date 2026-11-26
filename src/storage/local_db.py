"""Local SQLite knowledge database mirroring all 12 Google Sheets tabs.

Ensures deduplicated, zero-cost persistence even when offline or before Google OAuth is configured.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from src.config import DB_PATH, PILLAR_TO_TAB, SHEET_SCHEMAS, ensure_directories, now_ist


class LocalKnowledgeDB:
    """SQLite mirror of the 12-tab LifeTimeLibrary Knowledge Database."""

    def __init__(self, db_path: Path | None = None) -> None:
        ensure_directories()
        self.db_path = db_path or DB_PATH
        self._init_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self._connect() as conn:
            for tab_name, columns in SHEET_SCHEMAS.items():
                col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
                conn.execute(
                    f'CREATE TABLE IF NOT EXISTS "{tab_name}" ({col_defs})'
                )
            # Unique indexes to guarantee zero duplicate rows
            for tab in ("Health_Research", "Wealth_Research", "Wisdom_Research"):
                conn.execute(
                    f'CREATE UNIQUE INDEX IF NOT EXISTS "idx_{tab}_link" '
                    f'ON "{tab}" ("original_article_link")'
                )
            conn.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS "idx_daily_date" ON "Daily_Learning" ("date")'
            )
            conn.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS "idx_sources_url" ON "Sources" ("source_url")'
            )
            conn.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS "idx_topic_slug_date" '
                'ON "Topic_History" ("topic_slug", "brief_date")'
            )
            conn.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS "idx_settings_key" ON "Settings" ("key")'
            )
            conn.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS "idx_weekly_date" ON "Weekly_Reviews" ("week_ending")'
            )
            conn.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS "idx_monthly_month" ON "Monthly_Reviews" ("month")'
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS "Lesson_Progress" (
                    "progress_key" TEXT PRIMARY KEY,
                    "brief_date" TEXT,
                    "pillar" TEXT,
                    "title" TEXT,
                    "completed" TEXT,
                    "read_later" TEXT,
                    "completed_at" TEXT,
                    "updated_at" TEXT
                )
                """
            )

    def get_tab_rows(self, tab_name: str, limit: int | None = None) -> list[dict[str, Any]]:
        """Fetch rows from a tab ordered newest-first by rowid."""
        if tab_name not in SHEET_SCHEMAS:
            raise ValueError(f"Unknown tab: {tab_name}")
        query = f'SELECT * FROM "{tab_name}" ORDER BY rowid DESC'
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]

    def upsert_sources(self, sources: dict[str, list[dict[str, Any]]]) -> int:
        """Sync curated sources from config/sources.json into the Sources tab."""
        inserted = 0
        now_iso = now_ist().isoformat()
        with self._connect() as conn:
            for pillar, items in sources.items():
                for src in items:
                    cur = conn.execute(
                        """
                        INSERT INTO "Sources" (
                            pillar, source_name, source_url, source_type,
                            credibility_weight, topics, active, last_checked, last_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(source_url) DO UPDATE SET
                            pillar=excluded.pillar,
                            source_name=excluded.source_name,
                            source_type=excluded.source_type,
                            credibility_weight=excluded.credibility_weight,
                            topics=excluded.topics
                        """,
                        (
                            pillar,
                            src["name"],
                            src["url"],
                            src.get("type", "rss"),
                            str(src.get("credibility_weight", 8)),
                            ", ".join(src.get("topics", [])),
                            "TRUE",
                            now_iso,
                            "configured",
                        ),
                    )
                    inserted += cur.rowcount
        return inserted

    def update_source_status(self, source_url: str, status: str) -> None:
        """Update last_checked and last_status for a feed URL."""
        with self._connect() as conn:
            conn.execute(
                'UPDATE "Sources" SET last_checked = ?, last_status = ? WHERE source_url = ?',
                (now_ist().isoformat(), status, source_url),
            )

    def insert_research_articles(self, pillar: str, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Insert deduplicated research articles into Health/Wealth/Wisdom_Research.

        Returns only the newly inserted articles.
        """
        tab = PILLAR_TO_TAB[pillar.lower()]
        columns = SHEET_SCHEMAS[tab]
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(f'"{c}"' for c in columns)
        newly_inserted: list[dict[str, Any]] = []

        with self._connect() as conn:
            for art in articles:
                values = [str(art.get(col, "")) for col in columns]
                cur = conn.execute(
                    f'INSERT OR IGNORE INTO "{tab}" ({col_list}) VALUES ({placeholders})',
                    values,
                )
                if cur.rowcount > 0:
                    newly_inserted.append(art)
        return newly_inserted

    def mark_articles_used(self, pillar: str, links: list[str]) -> None:
        """Mark articles as used in a daily brief."""
        if not links:
            return
        tab = PILLAR_TO_TAB[pillar.lower()]
        with self._connect() as conn:
            for link in links:
                conn.execute(
                    f'UPDATE "{tab}" SET used_in_brief = "TRUE" WHERE original_article_link = ?',
                    (link,),
                )

    def get_recent_topic_slugs(self, days: int = 30) -> set[str]:
        """Return topic slugs covered recently to avoid repeating topics."""
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT topic_slug FROM "Topic_History" ORDER BY rowid DESC LIMIT ?',
                (days * 10,),
            ).fetchall()
            return {r["topic_slug"] for r in rows if r["topic_slug"]}

    def get_existing_article_links(self, pillar: str) -> set[str]:
        """Return all stored article URLs for a pillar."""
        tab = PILLAR_TO_TAB[pillar.lower()]
        with self._connect() as conn:
            rows = conn.execute(f'SELECT original_article_link FROM "{tab}"').fetchall()
            return {r["original_article_link"] for r in rows if r["original_article_link"]}

    def save_daily_brief(self, brief_row: dict[str, Any]) -> None:
        """Insert or update a row in Daily_Learning."""
        columns = SHEET_SCHEMAS["Daily_Learning"]
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(f'"{c}"' for c in columns)
        updates = ", ".join(f'"{c}"=excluded."{c}"' for c in columns if c != "date")
        values = [str(brief_row.get(c, "")) for c in columns]

        with self._connect() as conn:
            conn.execute(
                f'INSERT INTO "Daily_Learning" ({col_list}) VALUES ({placeholders}) '
                f'ON CONFLICT(date) DO UPDATE SET {updates}',
                values,
            )

    def record_topic_history(self, items: list[dict[str, str]]) -> None:
        """Record covered topics in Topic_History without duplicates."""
        with self._connect() as conn:
            for item in items:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO "Topic_History"
                    (date, pillar, topic_slug, topic_title, article_link, brief_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.get("date", ""),
                        item.get("pillar", ""),
                        item.get("topic_slug", ""),
                        item.get("topic_title", ""),
                        item.get("article_link", ""),
                        item.get("brief_date", ""),
                    ),
                )

    def add_bookmark(self, bookmark: dict[str, str]) -> None:
        """Save a lesson bookmark into Bookmarks."""
        columns = SHEET_SCHEMAS["Bookmarks"]
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(f'"{c}"' for c in columns)
        with self._connect() as conn:
            conn.execute(
                f'INSERT INTO "Bookmarks" ({col_list}) VALUES ({placeholders})',
                [str(bookmark.get(c, "")) for c in columns],
            )

    def save_quiz_results(self, rows: list[dict[str, str]]) -> None:
        """Persist quiz answers and scores into Quiz_Results."""
        columns = SHEET_SCHEMAS["Quiz_Results"]
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(f'"{c}"' for c in columns)
        with self._connect() as conn:
            for row in rows:
                conn.execute(
                    f'INSERT INTO "Quiz_Results" ({col_list}) VALUES ({placeholders})',
                    [str(row.get(c, "")) for c in columns],
                )

    def save_weekly_review(self, review: dict[str, Any]) -> None:
        """Insert or update a Weekly_Reviews record."""
        columns = SHEET_SCHEMAS["Weekly_Reviews"]
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(f'"{c}"' for c in columns)
        updates = ", ".join(f'"{c}"=excluded."{c}"' for c in columns if c != "week_ending")
        with self._connect() as conn:
            conn.execute(
                f'INSERT INTO "Weekly_Reviews" ({col_list}) VALUES ({placeholders}) '
                f'ON CONFLICT(week_ending) DO UPDATE SET {updates}',
                [str(review.get(c, "")) for c in columns],
            )

    def save_monthly_review(self, review: dict[str, Any]) -> None:
        """Insert or update a Monthly_Reviews record."""
        columns = SHEET_SCHEMAS["Monthly_Reviews"]
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(f'"{c}"' for c in columns)
        updates = ", ".join(f'"{c}"=excluded."{c}"' for c in columns if c != "month")
        with self._connect() as conn:
            conn.execute(
                f'INSERT INTO "Monthly_Reviews" ({col_list}) VALUES ({placeholders}) '
                f'ON CONFLICT(month) DO UPDATE SET {updates}',
                [str(review.get(c, "")) for c in columns],
            )

    def log_automation(
        self, workflow: str, status: str, ai_mode: str, details: str, duration_sec: float = 0.0
    ) -> None:
        """Append an execution record to Automation_Logs."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO "Automation_Logs"
                (timestamp, workflow, status, ai_mode, details, duration_sec)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now_ist().isoformat(), workflow, status, ai_mode, details, f"{duration_sec:.2f}"),
            )

    def set_setting(self, key: str, value: str) -> None:
        """Upsert a setting in the Settings tab."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO "Settings" (key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, now_ist().isoformat()),
            )

    def get_counts(self) -> dict[str, int]:
        """Return row counts for all 12 tabs."""
        counts: dict[str, int] = {}
        with self._connect() as conn:
            for tab in SHEET_SCHEMAS:
                row = conn.execute(f'SELECT COUNT(*) AS c FROM "{tab}"').fetchone()
                counts[tab] = int(row["c"]) if row else 0
        return counts

    def add_bookmark_if_new(self, bookmark: dict[str, str]) -> bool:
        """Save a bookmark only if the same title+pillar does not already exist."""
        title = bookmark.get("title", "").strip()
        pillar = bookmark.get("pillar", "").strip()
        with self._connect() as conn:
            existing = conn.execute(
                'SELECT 1 FROM "Bookmarks" WHERE lower(title) = lower(?) AND lower(pillar) = lower(?) LIMIT 1',
                (title, pillar),
            ).fetchone()
            if existing:
                return False
        self.add_bookmark(bookmark)
        return True

    def set_lesson_progress(
        self,
        brief_date: str,
        pillar: str,
        title: str,
        completed: bool | None = None,
        read_later: bool | None = None,
    ) -> None:
        """Upsert lesson completion or read-later state without creating duplicates."""
        key = f"{brief_date}::{pillar.lower()}"
        now_iso = now_ist().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                'SELECT completed, read_later, completed_at FROM "Lesson_Progress" WHERE progress_key = ?',
                (key,),
            ).fetchone()
            cur_completed = (row["completed"] == "TRUE") if row else False
            cur_later = (row["read_later"] == "TRUE") if row else False
            cur_comp_at = row["completed_at"] if row else ""

            new_completed = cur_completed if completed is None else completed
            new_later = cur_later if read_later is None else read_later
            if new_completed and not cur_comp_at:
                cur_comp_at = now_iso
            elif not new_completed:
                cur_comp_at = ""

            conn.execute(
                """
                INSERT INTO "Lesson_Progress" (
                    progress_key, brief_date, pillar, title, completed, read_later, completed_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(progress_key) DO UPDATE SET
                    title=excluded.title,
                    completed=excluded.completed,
                    read_later=excluded.read_later,
                    completed_at=excluded.completed_at,
                    updated_at=excluded.updated_at
                """,
                (
                    key,
                    brief_date,
                    pillar.capitalize(),
                    title,
                    "TRUE" if new_completed else "FALSE",
                    "TRUE" if new_later else "FALSE",
                    cur_comp_at,
                    now_iso,
                ),
            )

    def get_lesson_progress(self, limit: int = 200) -> list[dict[str, Any]]:
        """Fetch lesson completion & read-later records."""
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT * FROM "Lesson_Progress" ORDER BY brief_date DESC, updated_at DESC LIMIT ?',
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_learning_stats(self, reference_date: str | None = None) -> dict[str, int]:
        """Compute real learning metrics from Lesson_Progress and Daily_Learning (never fabricated)."""
        from datetime import datetime, timedelta

        ref_str = reference_date or now_ist().strftime("%Y-%m-%d")
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT brief_date, pillar, completed, read_later FROM "Lesson_Progress"'
            ).fetchall()
            daily_count_row = conn.execute('SELECT COUNT(*) AS c FROM "Daily_Learning"').fetchone()

        completed_rows = [r for r in rows if r["completed"] == "TRUE"]
        today_completed = sum(1 for r in completed_rows if r["brief_date"] == ref_str)
        read_later_count = sum(1 for r in rows if r["read_later"] == "TRUE")

        completed_dates = sorted({r["brief_date"] for r in completed_rows if r["brief_date"]}, reverse=True)
        streak = 0
        if completed_dates:
            ref_dt = datetime.strptime(ref_str, "%Y-%m-%d").date()
            # Streak counts consecutive days ending today or yesterday if today isn't completed yet
            check_dt = ref_dt if ref_str in completed_dates else (ref_dt - timedelta(days=1))
            date_set = {datetime.strptime(d, "%Y-%m-%d").date() for d in completed_dates}
            while check_dt in date_set:
                streak += 1
                check_dt -= timedelta(days=1)

        ref_dt = datetime.strptime(ref_str, "%Y-%m-%d").date()
        week_start = ref_dt - timedelta(days=6)
        weekly_completed = sum(
            1
            for r in completed_rows
            if r["brief_date"] and week_start <= datetime.strptime(r["brief_date"], "%Y-%m-%d").date() <= ref_dt
        )

        return {
            "today_completed": today_completed,
            "total_completed": len(completed_rows),
            "learning_streak": streak,
            "weekly_completed": weekly_completed,
            "read_later_count": read_later_count,
            "total_briefs": int(daily_count_row["c"]) if daily_count_row else 0,
        }
