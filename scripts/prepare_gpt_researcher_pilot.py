#!/usr/bin/env python3
"""Make outcome-free pilot inputs from the ignored exploratory draw."""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path


TASK_FIELDS = ("case_id", "ticker", "company", "quarter", "period_end_date",
               "eps_basis", "cutoff_iso", "verification_status", "history")


def prepare(source: dict) -> dict:
    task = {field: source[field] for field in TASK_FIELDS}
    cutoff = datetime.fromisoformat(task["cutoff_iso"].replace("Z", "+00:00"))
    target = date.fromisoformat(task["period_end_date"])
    if cutoff.tzinfo is None:
        raise ValueError("pilot cutoff must include time zone")
    for row in task["history"]:
        period = date.fromisoformat(row["period_end_date"])
        reported = date.fromisoformat(row["report_date"])
        if period >= target or reported > cutoff.date():
            raise ValueError(f"post-cutoff history in {task['case_id']}")
    return task


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case-id", action="append", required=True)
    args = parser.parse_args()
    rows = {row["case_id"]: row for row in
            (json.loads(line) for line in args.source.read_text().splitlines())}
    cases = list(dict.fromkeys(args.case_id))
    tasks = [prepare(rows[case_id]) for case_id in cases]
    args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with args.output.open("w") as output:
        for task in tasks:
            output.write(json.dumps(task, sort_keys=True) + "\n")
    args.output.chmod(0o600)
    print(f"prepared {len(tasks)} pilot cases: {', '.join(cases)}")


if __name__ == "__main__":
    main()
