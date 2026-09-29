#!/usr/bin/env python3
"""Minimal stdio MCP adapter for the case-scoped as-of search/read service."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


TOOLS = [
    {"name": "asof_search", "description": "Search archived case evidence available before the forecast cutoff.",
     "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False, "idempotentHint": True},
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}},
                     "required": ["query"], "additionalProperties": False}},
    {"name": "asof_read", "description": "Read an archived document returned by asof_search.",
     "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False, "idempotentHint": True},
     "inputSchema": {"type": "object", "properties": {"doc_id": {"type": "string"}},
                     "required": ["doc_id"], "additionalProperties": False}},
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--documents", type=Path)
    source.add_argument("--snapshot-config", type=Path)
    parser.add_argument("--prefetch-limit", type=int, default=0,
                        help="for research agents, read top Snapshot hits before returning search")
    args = parser.parse_args()
    if args.prefetch_limit < 0 or args.prefetch_limit > 3:
        parser.error("prefetch-limit must be 0..3")
    if args.prefetch_limit and not args.snapshot_config:
        parser.error("prefetch requires Exa Snapshot")
    query_script = Path(__file__).with_name("exa_snapshot_query.py" if args.snapshot_config else "asof_query.py")
    source_args = (["--snapshot-config", str(args.snapshot_config)] if args.snapshot_config else
                   ["--documents", str(args.documents)])
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method = request.get("method")
            if "id" not in request:
                continue
            if method == "initialize":
                result = {"protocolVersion": request.get("params", {}).get("protocolVersion", "2025-06-18"),
                          "capabilities": {"tools": {}},
                          "serverInfo": {"name": "streetbench-asof", "version": "0.1.0"}}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "ping":
                result = {}
            elif method == "tools/call":
                params = request.get("params") or {}
                name = params.get("name")
                values = params.get("arguments") or {}
                if name == "asof_search":
                    command = ["search", str(values["query"])]
                elif name == "asof_read":
                    command = ["read", str(values["doc_id"])]
                else:
                    raise ValueError("unknown tool")
                base = [sys.executable, str(query_script), "--task", str(args.task), *source_args]
                proc = subprocess.run([*base, *command], capture_output=True, text=True, timeout=60)
                if proc.returncode == 0 and name == "asof_search" and args.prefetch_limit:
                    search = json.loads(proc.stdout)
                    for hit in search.get("hits", [])[:args.prefetch_limit]:
                        read = subprocess.run([*base, "read", hit["doc_id"]], capture_output=True,
                                              text=True, timeout=60)
                        if read.returncode:
                            raise ValueError("Snapshot historical page read failed: " + read.stderr.strip())
                        page = json.loads(read.stdout)
                        hit["historical_text"] = page["text"][:12000]
                        hit["historical_text_sha256"] = page["text_sha256"]
                    proc.stdout = json.dumps(search)
                result = {"content": [{"type": "text", "text": (proc.stdout if proc.returncode == 0 else proc.stderr).strip()}],
                          "isError": proc.returncode != 0}
            else:
                raise ValueError("unknown method")
            response = {"jsonrpc": "2.0", "id": request["id"], "result": result}
        except (ValueError, KeyError, subprocess.TimeoutExpired) as exc:
            response = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                        "error": {"code": -32602, "message": str(exc)}}
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
