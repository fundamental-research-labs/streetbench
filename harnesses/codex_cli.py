#!/usr/bin/env python3
"""Exploratory Codex CLI harness adapter; one JSON task on stdin, one JSON forecast on stdout.

The CLI is open source, but a local historical replay is NOT leakage certified:
the model may have learned public outcomes, and a local read-only sandbox does not
prove it could not access other historical files or the web.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from common import forecast_prompt


SCHEMA = {
    "type": "object",
    "properties": {"eps_prediction": {"type": "number"}},
    "required": ["eps_prediction"],
    "additionalProperties": False,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--effort", choices=("low", "medium", "high"), default="medium")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--documents", type=Path, help="enables archived as-of MCP tools")
    parser.add_argument("--snapshot-config", type=Path, help="enables Exa Snapshot search/read via MCP")
    args = parser.parse_args()
    if args.documents and args.snapshot_config:
        parser.error("choose only one of --documents or --snapshot-config")
    task = json.load(sys.stdin)
    with tempfile.TemporaryDirectory(prefix="streetbench-codex-") as directory:
        root = Path(directory)
        (root / "task.json").write_text(json.dumps(task, indent=2))
        (root / "schema.json").write_text(json.dumps(SCHEMA))
        tool_mode = bool(args.documents or args.snapshot_config)
        prompt = forecast_prompt(task, asof_tools=tool_mode)
        command = ["codex", "exec", "--json", "--ephemeral", "--ignore-user-config",
                   "--skip-git-repo-check", "--sandbox", "read-only",
                   "--disable", "shell_tool", "--disable", "unified_exec",
                   "-c", "tools.web_search=false", "--strict-config",
                   "-c", f'model_reasoning_effort="{args.effort}"',
                   "--cd", str(root), "--model", args.model,
                   "--output-schema", str(root / "schema.json"),
                   "--output-last-message", str(root / "result.json")]
        if tool_mode:
            if not task.get("cutoff_iso"):
                raise SystemExit("as-of mode requires a frozen cutoff_iso")
            server = Path(__file__).resolve().parents[1] / "scripts/asof_mcp.py"
            mcp_args = [str(server), "--task", str(root / "task.json")]
            mcp_args += (["--snapshot-config", str(args.snapshot_config.resolve())] if args.snapshot_config else
                         ["--documents", str(args.documents.resolve())])
            command += ["-c", 'mcp_servers.streetbench.command="python3"',
                        "-c", "mcp_servers.streetbench.args=" + json.dumps(mcp_args)]
        command.append("-")
        result = subprocess.run(command, input=prompt, text=True, capture_output=True,
                                timeout=args.timeout)
        if result.returncode:
            raise SystemExit(f"codex exited {result.returncode}: {result.stderr[-500:]}")
        events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        tool_events = [event.get("item", {}) for event in events
                       if event.get("type") == "item.completed" and
                       event.get("item", {}).get("type") == "mcp_tool_call"]
        if tool_mode:
            if not any(item.get("server") == "streetbench" and
                       item.get("tool") == "asof_search" and
                       item.get("status") == "completed" and not item.get("error")
                       for item in tool_events):
                raise SystemExit("Codex did not complete the required asof_search call")
            if any(item.get("server") != "streetbench" or item.get("error") for item in tool_events):
                raise SystemExit("unexpected or failed MCP tool call")
        elif tool_events:
            raise SystemExit("prompt-only Codex run made an MCP tool call")
        forecast = json.loads((root / "result.json").read_text())
        print(json.dumps({"eps_prediction": float(forecast["eps_prediction"])}))


if __name__ == "__main__":
    main()
