#!/usr/bin/env python3
"""Normalize Shortcut or another external harness's CSV into the shared forecast JSONL."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path


def instant(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp needs a timezone")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", type=Path)
    parser.add_argument("csv_file", type=Path, help="columns: case_id,eps_prediction,submitted_at")
    parser.add_argument("output", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", choices=["retrospective", "prospective"], required=True)
    args = parser.parse_args()
    tasks = {row["case_id"]: row for row in (json.loads(line) for line in args.tasks.read_text().splitlines() if line.strip())}
    with args.csv_file.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not {"case_id", "eps_prediction", "submitted_at"} <= set(reader.fieldnames or []):
            raise SystemExit("CSV must have case_id,eps_prediction,submitted_at columns")
        source_rows = list(reader)
    seen = set()
    out = []
    for row in source_rows:
        case_id = row["case_id"]
        if case_id not in tasks or case_id in seen:
            raise SystemExit(f"unknown or duplicate case ID: {case_id}")
        seen.add(case_id)
        try:
            eps = float(row["eps_prediction"])
            if not math.isfinite(eps):
                raise ValueError("EPS is not finite")
            submitted = instant(row["submitted_at"])
            if args.mode == "prospective":
                cutoff_text = tasks[case_id].get("cutoff_iso")
                if not cutoff_text:
                    raise ValueError("prospective case has no frozen cutoff")
                if submitted > instant(cutoff_text):
                    raise ValueError("forecast arrived after cutoff")
        except ValueError as exc:
            raise SystemExit(f"{case_id}: {exc}") from exc
        out.append({"case_id": case_id, "run_id": args.run_id, "eps_prediction": eps,
                    "submitted_at": submitted.isoformat(), "status": "ok"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in sorted(out, key=lambda r: r["case_id"])))
    manifest = {"run_id": args.run_id, "mode": args.mode, "status": "self_reported_pending_review",
                "source_sha256": hashlib.sha256(args.csv_file.read_bytes()).hexdigest(),
                "task_sha256": hashlib.sha256(args.tasks.read_bytes()).hexdigest(),
                "forecast_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                "submitted_cases": len(out), "expected_cases": len(tasks)}
    args.output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Imported {len(out)}/{len(tasks)} forecasts to {args.output}; pending maintainer review")


if __name__ == "__main__":
    main()
