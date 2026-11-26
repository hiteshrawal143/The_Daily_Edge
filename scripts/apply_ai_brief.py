"""Validate and ingest an Antigravity AI-generated Hinglish brief JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.delivery.docs_exporter import export_daily_report
from src.editorial.brief_builder import validate_and_save_brief
from src.storage.google_sync import GoogleWorkspaceSync
from src.storage.local_db import LocalKnowledgeDB


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply an AI-verified Hinglish brief JSON.")
    parser.add_argument("brief_json", type=Path, help="Path to AI-generated brief JSON.")
    parser.add_argument("--send-email", action="store_true", help="Sync and trigger email if approved.")
    args = parser.parse_args()

    with args.brief_json.open("r", encoding="utf-8") as fh:
        brief = json.load(fh)

    db = LocalKnowledgeDB()
    sync_client = GoogleWorkspaceSync()
    export_info = export_daily_report(brief, sync_client=sync_client, db=db)
    validate_and_save_brief(
        brief,
        db=db,
        doc_url=export_info.get("doc_url", ""),
        pdf_url=export_info.get("pdf_url", ""),
    )
    sync_res = sync_client.sync_all(db, send_email=args.send_email)
    db.log_automation("apply_ai_brief", "success", "antigravity_ai_verified", str(args.brief_json))
    print(json.dumps({"export": export_info, "sync": sync_res}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
