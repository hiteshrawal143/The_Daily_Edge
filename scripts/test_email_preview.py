"""Generate a local HTML email preview without sending any email."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import EXPORTS_DIR, ensure_directories
from src.delivery.email_renderer import render_newsletter_html
from src.storage.local_db import LocalKnowledgeDB


def main() -> None:
    ensure_directories()
    db = LocalKnowledgeDB()
    rows = db.get_tab_rows("Daily_Learning", limit=1)
    if not rows:
        print("No brief in database yet. Run scripts/run_daily.py first.")
        return

    html_out = render_newsletter_html(rows[0], doc_url=rows[0].get("doc_url", ""), db=db)
    out_path = EXPORTS_DIR / "preview_email.html"
    out_path.write_text(html_out, encoding="utf-8")
    print(f"Local email preview written to: {out_path} (no email sent)")


if __name__ == "__main__":
    main()
