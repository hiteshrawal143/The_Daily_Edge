"""CLI entry point for Sunday Weekly Review, 10-question Quiz, and Monthly Rollup."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.delivery.pipeline import run_weekly_pipeline


def main() -> None:
    result = run_weekly_pipeline()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
