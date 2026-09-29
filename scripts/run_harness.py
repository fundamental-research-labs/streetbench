#!/usr/bin/env python3
"""Run any command-line harness once per case (JSON task on stdin, JSON forecast on stdout)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--timeout", type=int, default=600)
    if "--" not in sys.argv:
        parser.error("put the harness command after --")
    separator = sys.argv.index("--")
    args = parser.parse_args(sys.argv[1:separator])
    command = sys.argv[separator + 1:]
    if not command:
        parser.error("a harness command is required after --")
    lines = args.tasks.read_text().splitlines()
    cases = [json.loads(line) for line in lines if line.strip()]
    if len({case["case_id"] for case in cases}) != len(cases):
        raise SystemExit("Duplicate case IDs in tasks")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as handle:
        for case in cases:
            row = {"run_id": args.run_id, "case_id": case["case_id"], "status": "failed"}
            started = time.monotonic()
            try:
                result = subprocess.run(command, input=json.dumps(case), text=True,
                                        capture_output=True, timeout=args.timeout)
                if result.returncode:
                    raise ValueError(f"exit {result.returncode}: {result.stderr[-300:]}")
                forecast = json.loads(result.stdout)
                eps = float(forecast["eps_prediction"])
                if not math.isfinite(eps):
                    raise ValueError("nonfinite EPS")
                row.update(status="ok", eps_prediction=eps)
            except (subprocess.TimeoutExpired, ValueError, KeyError, json.JSONDecodeError) as exc:
                row["error"] = str(exc)[:500]
            row["latency_seconds"] = round(time.monotonic() - started, 3)
            row["submitted_at"] = datetime.now(timezone.utc).isoformat()
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    manifest = {"run_id": args.run_id, "command": command,
                "task_sha256": hashlib.sha256(args.tasks.read_bytes()).hexdigest(),
                "forecast_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                "case_count": len(cases), "status": "self_reported_exploratory"}
    args.output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(cases)} forecasts to {args.output}")


if __name__ == "__main__":
    main()
