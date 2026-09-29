#!/usr/bin/env python3
"""Audit case cutoffs, declared document times, and document text hashes.

This checks timestamps, not the truth of a document's publication date or hidden
model training data. Use --strict for an official candidate bundle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", type=Path)
    parser.add_argument("--documents", type=Path, help="JSONL with case_id, doc_id, published_at, captured_at")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    tasks = read_jsonl(args.tasks)
    ids = {t["case_id"] for t in tasks}
    if len(ids) != len(tasks):
        raise SystemExit("duplicate case IDs")
    docs = read_jsonl(args.documents) if args.documents else []
    issues = []
    cutoffs = {}
    for task in tasks:
        case_id = task["case_id"]
        cutoff_text = task.get("cutoff_iso")
        if not cutoff_text:
            issues.append({"case_id": case_id, "severity": "unverified", "issue": "cutoff_missing"})
            continue
        try:
            cutoff = instant(cutoff_text)
        except ValueError as exc:
            issues.append({"case_id": case_id, "severity": "fail", "issue": f"bad_cutoff: {exc}"})
            continue
        cutoffs[case_id] = cutoff
        if task.get("verification_status") != "verified":
            issues.append({"case_id": case_id, "severity": "unverified", "issue": "eligibility_unverified"})
        for item in task.get("history", []):
            when = item.get("report_date")
            if not when:
                issues.append({"case_id": case_id, "severity": "unverified", "issue": "history_date_missing"})
            elif when > cutoff.date().isoformat():
                issues.append({"case_id": case_id, "severity": "fail", "issue": "history_after_cutoff",
                               "report_date": when})
    seen_docs = set()
    for doc in docs:
        case_id = doc.get("case_id")
        doc_id = doc.get("doc_id")
        key = (case_id, doc_id)
        if case_id not in ids or not doc_id or key in seen_docs:
            issues.append({"case_id": case_id, "severity": "fail", "issue": "unknown_or_duplicate_document",
                           "doc_id": doc_id})
            continue
        seen_docs.add(key)
        declared_hash = doc.get("text_sha256")
        if not declared_hash:
            issues.append({"case_id": case_id, "severity": "unverified", "issue": "text_sha256_missing",
                           "doc_id": doc_id})
        elif declared_hash != hashlib.sha256(str(doc.get("text") or "").encode("utf-8")).hexdigest():
            issues.append({"case_id": case_id, "severity": "fail", "issue": "text_sha256_mismatch",
                           "doc_id": doc_id})
        cutoff = cutoffs.get(case_id)
        if cutoff is None:
            continue
        for field in ("published_at", "captured_at"):
            value = doc.get(field)
            if not value:
                issues.append({"case_id": case_id, "severity": "unverified", "issue": f"{field}_missing",
                               "doc_id": doc_id})
                continue
            try:
                if instant(value) > cutoff:
                    issues.append({"case_id": case_id, "severity": "fail", "issue": f"{field}_after_cutoff",
                                   "doc_id": doc_id})
            except ValueError as exc:
                issues.append({"case_id": case_id, "severity": "fail", "issue": f"bad_{field}: {exc}",
                               "doc_id": doc_id})
    failed = sum(i["severity"] == "fail" for i in issues)
    unverified = sum(i["severity"] == "unverified" for i in issues)
    status = "fail" if failed else ("unverified" if unverified else "pass")
    report = {"status": status, "tasks": len(tasks), "documents": len(docs), "failed": failed,
              "unverified": unverified, "issues": issues}
    body = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body)
    print(body, end="")
    if failed or (args.strict and unverified):
        sys.exit(1)


if __name__ == "__main__":
    main()
