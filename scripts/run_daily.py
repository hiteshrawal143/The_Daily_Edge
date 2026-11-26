"""CLI entry point for the daily LifeTimeLibrary pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.delivery.pipeline import run_daily_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LifeTimeLibrary daily pipeline (₹0 cost).")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip live RSS fetching and use stored research.")
    parser.add_argument("--send-email", action="store_true", help="Trigger email delivery if explicitly approved in .env.")
    args = parser.parse_args()

    result = run_daily_pipeline(skip_fetch=args.skip_fetch, send_email=args.send_email)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
