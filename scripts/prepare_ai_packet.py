"""Prepare today's Antigravity AI editorial packet from collected RSS articles."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import today_ist_str
from src.editorial.brief_builder import prepare_ai_packet
from src.research.processor import process_and_store_research
from src.research.rss_collector import collect_all_research
from src.storage.local_db import LocalKnowledgeDB


def main() -> None:
    db = LocalKnowledgeDB()
    snapshot = collect_all_research(db=db, max_per_feed=6)
    processed = process_and_store_research(snapshot, db=db)
    packet_path = prepare_ai_packet(processed, db=db, date_str=today_ist_str())
    print(f"AI packet ready at: {packet_path}")


if __name__ == "__main__":
    main()
