"""Aggregate results/latest/comparison.json + community YAMLs into website data.

Writes two files consumed by the Next.js leaderboard:
  - website/public/results.json : per-test rows for every model
  - website/public/models.json  : model metadata (provider, pricing, contributor)

Run locally or in CI before `next build`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
RESULTS_LATEST = ROOT / "results" / "latest" / "comparison.json"
RESULTS_LEGACY = ROOT / "results" / "latest" / "summary.json"
WEBSITE_PUBLIC = ROOT / "website" / "public"
SUBMISSIONS_DIR = ROOT / "results" / "submissions"

sys.path.insert(0, str(ROOT / "scripts"))
from community_models import registry_entries  # noqa: E402


def _load_rows() -> List[Dict[str, Any]]:
    candidates = [RESULTS_LATEST, RESULTS_LEGACY]
    for path in candidates:
        if path.exists():
            with path.open("r") as handle:
                rows = json.load(handle)
            if isinstance(rows, list):
                return rows
    return []


def _load_submissions() -> List[Dict[str, Any]]:
    """Load any contributor-submitted results from results/submissions/<model-id>.json."""
    if not SUBMISSIONS_DIR.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for path in sorted(SUBMISSIONS_DIR.glob("*.json")):
        try:
            with path.open("r") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            print(f"warn: skipping malformed submission {path}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, list):
            rows.extend(data)
        elif isinstance(data, dict) and "results" in data:
            rows.extend(data["results"])
    return rows


def _thin_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Drop heavy fields (prompt/response/reasoning) — the website doesn't render them."""
    return {
        "model": row.get("model"),
        "test_id": row.get("test_id"),
        "category": row.get("category"),
        "subcategory": row.get("subcategory"),
        "score": row.get("score"),
        "passed": row.get("passed"),
        "latency_ms": row.get("latency_ms"),
    }


def main() -> int:
    rows = _load_rows() + _load_submissions()
    if not rows:
        print("warn: no result rows found. Leaderboard will be empty.", file=sys.stderr)

    thinned = [_thin_row(row) for row in rows if row.get("model")]

    WEBSITE_PUBLIC.mkdir(parents=True, exist_ok=True)

    results_path = WEBSITE_PUBLIC / "results.json"
    with results_path.open("w") as handle:
        json.dump(thinned, handle, separators=(",", ":"))
    print(f"Wrote {len(thinned)} rows → {results_path.relative_to(ROOT)}")

    models = registry_entries(include_premium=True)
    models_path = WEBSITE_PUBLIC / "models.json"
    with models_path.open("w") as handle:
        json.dump(models, handle, indent=2, default=str)
    print(f"Wrote {len(models)} model configs → {models_path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
