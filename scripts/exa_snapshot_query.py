#!/usr/bin/env python3
"""Case-scoped Exa Snapshot search/read with a fixed cutoff and HTTP budget.

The config stays on the host. This is a research adapter, not an OS sandbox or
independent proof of a provider's stored-page timestamp.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path


API = "https://api.exa.ai/"


def instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("cutoff must include a time zone")
    return parsed.astimezone(timezone.utc)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def published_after_cutoff(value: str, cutoff: datetime) -> bool:
    # A date-only value has no time; exclude the whole cutoff day.
    if len(value) == 10:
        return datetime.fromisoformat(value).date() >= cutoff.date()
    return instant(value) > cutoff


def validate(config: dict, task: dict) -> tuple[str, str, Path]:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", str(task.get("case_id", ""))):
        raise ValueError("invalid case ID")
    cutoff = task.get("cutoff_iso")
    if not cutoff or instant(cutoff) > datetime.now(timezone.utc):
        raise ValueError("case needs a past, timezone-aware cutoff_iso")
    if task.get("verification_status") != "verified" and not config.get("allow_unverified_case", False):
        raise ValueError("case eligibility is not verified; set allow_unverified_case only for an exploratory run")
    if not config.get("snapshot_verified") or not config.get("account_id"):
        raise ValueError("Exa Snapshot account verification is missing")
    key_path = Path(config["key_path"]).expanduser().resolve()
    key = key_path.read_text().strip()
    if not key or sha256(key) != config.get("verified_key_sha256"):
        raise ValueError("Exa key does not match the verified account fingerprint")
    limit = int(config.get("max_http_attempts", 0))
    per_case = int(config.get("max_case_http_attempts", 0))
    if not 0 < limit <= 100000 or not 0 < per_case <= limit:
        raise ValueError("positive total and per-case HTTP budgets are required")
    evidence_dir = Path(config["evidence_dir"]).expanduser().resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    return cutoff, key, evidence_dir


def reserve(evidence_dir: Path, case_id: str, total_limit: int, case_limit: int, endpoint: str) -> None:
    lock_path = evidence_dir / "budget.lock"
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        log_path = evidence_dir / "http-attempts.jsonl"
        rows = [json.loads(line) for line in log_path.read_text().splitlines()] if log_path.exists() else []
        if len(rows) >= total_limit or sum(row["case_id"] == case_id for row in rows) >= case_limit:
            raise ValueError("Exa Snapshot HTTP budget exhausted")
        with log_path.open("a") as log:
            log.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(),
                                  "case_id": case_id, "endpoint": endpoint}) + "\n")
            log.flush()
            os.fsync(log.fileno())


def request_snapshot(endpoint: str, payload: dict, key: str) -> dict:
    request = urllib.request.Request(
        API + endpoint, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            data = json.load(response)
            if not isinstance(data, dict):
                raise ValueError("Exa Snapshot response is not an object")
            return data
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Exa Snapshot HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError("Exa Snapshot transport unavailable") from exc


def admitted(response: dict, cutoff: datetime) -> list[dict]:
    rows = response.get("results")
    if not isinstance(rows, list):
        raise ValueError("Exa response has no results array")
    docs = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("url") or not row.get("text"):
            continue
        published = row.get("publishedDate")
        if published and published_after_cutoff(published, cutoff):
            continue
        docs.append(row)
    return docs


def record(evidence_dir: Path, task: dict, endpoint: str, payload: dict,
           response: dict, docs: list[dict]) -> None:
    case_dir = evidence_dir / task["case_id"]
    case_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    artifact = {
        "case_id": task["case_id"], "cutoff_iso": task["cutoff_iso"],
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "provider": "exa-snapshot", "provider_request_id": response.get("requestId"),
        "provider_asof_guarantee": True, "capture_timestamp": None,
        "historical_search_ranking": False, "endpoint": endpoint,
        "request_sha256": sha256(json.dumps(payload, sort_keys=True)),
        "provider_cost_usd": response.get("costDollars"),
        "documents": [{"url": doc["url"], "title": doc.get("title"),
                       "published_at": doc.get("publishedDate"), "text": doc["text"],
                       "text_sha256": sha256(doc["text"])} for doc in docs],
    }
    path = case_dir / (uuid.uuid4().hex + ".json")
    with path.open("x") as handle:
        os.fchmod(handle.fileno(), 0o600)
        json.dump(artifact, handle, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def run(task: dict, config: dict, action: str, value: str) -> dict:
    cutoff_text, key, evidence_dir = validate(config, task)
    cutoff = instant(cutoff_text)
    if action == "search":
        if not value.strip() or len(value) > 4000:
            raise ValueError("search query must contain 1..4000 characters")
        endpoint = "search"
        payload = {"query": value, "type": "auto", "numResults": 5,
                   "contents": {"snapshotAsOf": cutoff_text, "text": True}}
    else:
        url = urllib.parse.urlparse(value)
        if url.scheme not in ("http", "https") or not url.netloc or len(value) > 4000:
            raise ValueError("read requires an HTTP(S) URL returned by search")
        endpoint = "contents"
        payload = {"ids": [value], "snapshotAsOf": cutoff_text, "text": True}
    reserve(evidence_dir, task["case_id"], int(config["max_http_attempts"]),
            int(config["max_case_http_attempts"]), endpoint)
    response = request_snapshot(endpoint, payload, key)
    docs = admitted(response, cutoff)
    record(evidence_dir, task, endpoint, payload, response, docs)
    if action == "search":
        return {"cutoff_iso": cutoff_text, "provider": "exa-snapshot",
                "ranking_is_historical": False,
                "hits": [{"doc_id": doc["url"], "title": doc.get("title"),
                          "source_url": doc["url"], "published_at": doc.get("publishedDate"),
                          "snippet": doc["text"][:500]} for doc in docs]}
    if len(docs) != 1 or docs[0]["url"] != value:
        raise ValueError("document unavailable in Snapshot at cutoff")
    doc = docs[0]
    return {"doc_id": value, "title": doc.get("title"), "source_url": value,
            "published_at": doc.get("publishedDate"), "cutoff_iso": cutoff_text,
            "text_sha256": sha256(doc["text"]), "text": doc["text"][:30000]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--snapshot-config", type=Path, required=True)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("search").add_argument("query")
    actions.add_parser("read").add_argument("doc_id")
    args = parser.parse_args()
    try:
        task = json.loads(args.task.read_text())
        config = json.loads(args.snapshot_config.read_text())
        value = args.query if args.action == "search" else args.doc_id
        print(json.dumps(run(task, config, args.action, value), sort_keys=True))
    except (KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()
