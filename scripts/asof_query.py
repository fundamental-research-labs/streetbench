#!/usr/bin/env python3
"""Search/read an immutable, case-scoped document JSONL using a frozen cutoff."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


def instant(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timezone required")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--documents", type=Path, required=True)
    sub = parser.add_subparsers(dest="action", required=True)
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)
    read = sub.add_parser("read")
    read.add_argument("doc_id")
    args = parser.parse_args()
    task = json.loads(args.task.read_text())
    if not task.get("cutoff_iso"):
        raise SystemExit("case cutoff is missing")
    cutoff = instant(task["cutoff_iso"])
    docs = [json.loads(line) for line in args.documents.read_text().splitlines() if line.strip()]
    allowed = []
    for doc in docs:
        if doc.get("case_id") != task["case_id"]:
            continue
        declared_hash = doc.get("text_sha256")
        if declared_hash and declared_hash != hashlib.sha256(str(doc.get("text") or "").encode("utf-8")).hexdigest():
            continue
        try:
            if instant(doc["published_at"]) <= cutoff and instant(doc["captured_at"]) <= cutoff:
                allowed.append(doc)
        except (KeyError, ValueError):
            continue
    if args.action == "read":
        matched = [doc for doc in allowed if doc.get("doc_id") == args.doc_id]
        if len(matched) != 1:
            raise SystemExit("document unavailable at cutoff or doc_id not unique")
        doc = matched[0]
        result = {key: doc.get(key) for key in ("doc_id", "title", "source_url", "published_at", "captured_at")}
        result["text"] = str(doc.get("text") or "")[:30000]
    else:
        tokens = set(re.findall(r"[a-z0-9]+", args.query.lower()))
        if not tokens or args.limit < 1 or args.limit > 20:
            raise SystemExit("query must contain words and limit must be 1..20")
        hits = []
        for doc in allowed:
            text = str(doc.get("text") or "")
            haystack = (str(doc.get("title") or "") + " " + text).lower()
            score = sum(haystack.count(token) for token in tokens)
            if score:
                hits.append((score, doc))
        hits.sort(key=lambda pair: (-pair[0], str(pair[1].get("doc_id"))))
        result = {"cutoff_iso": task["cutoff_iso"], "hits": [
            {"doc_id": doc.get("doc_id"), "title": doc.get("title"),
             "published_at": doc.get("published_at"), "source_url": doc.get("source_url"),
             "score": score, "snippet": str(doc.get("text") or "")[:500]}
            for score, doc in hits[:args.limit]]}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
