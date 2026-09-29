#!/usr/bin/env python3
"""Exploratory two-stage baseline: GPT Researcher/Exa Snapshot, then Codex EPS.

One task JSON on stdin, one forecast JSON on stdout. The answer key must never
be mounted into this process. This adapter is not a model-training cutoff proof.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PINNED_RESEARCHER_COMMIT = "6f998577d547b1e54ec662dac63583aa11e3b84b"
sys.path.insert(0, str(ROOT / "scripts"))
from exa_snapshot_query import validate  # noqa: E402


def checked_task(task: dict) -> None:
    if not isinstance(task, dict) or not task.get("case_id") or not task.get("cutoff_iso"):
        raise ValueError("case_id and cutoff_iso are required")
    if task.get("consensus_eps") is not None:
        raise ValueError("target consensus must stay outside the forecast task")
    forbidden = {"actual_eps", "target_actual_eps", "target_consensus_eps", "answer"}
    if forbidden.intersection(task):
        raise ValueError("answer field found in forecast task")


def successful_evidence(case_dir: Path, old_names: set[str], task: dict) -> list[dict]:
    rows = [json.loads(path.read_text()) for path in case_dir.glob("*.json")
            if path.name not in old_names]
    admitted = [row for row in rows if row.get("case_id") == task["case_id"]
                and row.get("cutoff_iso") == task["cutoff_iso"]
                and row.get("provider") == "exa-snapshot" and row.get("documents")]
    if not {"search", "contents"}.issubset({r["endpoint"] for r in admitted}):
        raise RuntimeError("research needs successful Snapshot search and historical page read")
    return admitted


async def research(task: dict, snapshot_config: Path, checkout: Path, model: str,
                   task_path: Path) -> tuple[str, float]:
    # GPT Researcher's upstream default retriever is live Tavily. Set this
    # before constructing the agent and then check its resolved retriever list.
    os.environ["RETRIEVER"] = "mcp"
    for name in ("FAST_LLM", "SMART_LLM", "STRATEGIC_LLM"):
        os.environ[name] = "openai:" + model
    os.environ["MCP_STRATEGY"] = "deep"
    os.environ["CURATE_SOURCES"] = "false"
    os.environ["IMAGE_GENERATION_ENABLED"] = "false"
    sys.path.insert(0, str(checkout))
    from gpt_researcher import GPTResearcher
    from gpt_researcher.skills.browser import BrowserManager

    async def snapshot_only_browse(_self: BrowserManager, urls: list[str]) -> list[dict]:
        if urls:
            raise RuntimeError("live crawler forbidden in Streetbench")
        return []

    # The MCP-only path calls browse_urls([]). Reject any future upstream
    # change that tries to fetch a URL through the ordinary crawler.
    BrowserManager.browse_urls = snapshot_only_browse
    mcp = [{"name": "streetbench_snapshot", "command": sys.executable,
            "args": [str(ROOT / "scripts/asof_mcp.py"), "--task", str(task_path),
                     "--snapshot-config", str(snapshot_config), "--prefetch-limit", "2"]}]
    agent = GPTResearcher(
        query=(f"Research {task['company']} ({task['ticker']}) for a forecast of "
               f"normalized diluted EPS for the quarter ending {task['period_end_date']}. "
               f"Use the Snapshot tools to search and read source pages as they existed "
               f"by {task['cutoff_iso']}. Return evidence and citations; do not look "
               "for the subsequently reported EPS."),
        report_source="web", source_urls=None, complement_source_urls=False,
        mcp_configs=mcp, mcp_strategy="deep", verbose=False,
    )
    if [r.__name__ for r in agent.retrievers] != ["MCPRetriever"]:
        raise RuntimeError("GPT Researcher enabled a non-Snapshot retriever")
    if agent.source_urls or agent.document_urls or agent.complement_source_urls:
        raise RuntimeError("GPT Researcher enabled a direct document fetch path")
    context = await agent.conduct_research()
    if not isinstance(context, str) or not context.strip():
        raise RuntimeError("GPT Researcher returned no research context")
    return context, float(agent.get_costs())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-config", type=Path, required=True)
    parser.add_argument("--researcher-checkout", type=Path, required=True)
    parser.add_argument("--research-model", default="gpt-6-sol")
    parser.add_argument("--codex-model", default="gpt-6-sol")
    parser.add_argument("--codex-effort", choices=("low", "medium", "high"), default="high")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--research-timeout", type=int, default=900)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    args = parser.parse_args()
    task = json.load(sys.stdin)
    checked_task(task)
    config_path = args.snapshot_config.resolve(strict=True)
    config = json.loads(config_path.read_text())
    validate(config, task)
    checkout = args.researcher_checkout.resolve(strict=True)
    if not (checkout / "gpt_researcher" / "agent.py").is_file():
        raise SystemExit("researcher checkout is missing gpt_researcher/agent.py")
    commit = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                                     text=True).strip()
    if commit != PINNED_RESEARCHER_COMMIT:
        raise SystemExit("GPT Researcher checkout differs from audited commit")
    artifacts = args.artifacts_dir.resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    case_dir = artifacts / task["case_id"]
    case_dir.mkdir(mode=0o700, exist_ok=True)
    evidence_case_dir = Path(config["evidence_dir"]).expanduser().resolve() / task["case_id"]
    previous_evidence = {path.name for path in evidence_case_dir.glob("*.json")}
    attempts = Path(config["evidence_dir"]).expanduser().resolve() / "http-attempts.jsonl"
    before = len(attempts.read_text().splitlines()) if attempts.exists() else 0
    with tempfile.TemporaryDirectory(prefix="streetbench-gptr-") as temp:
        task_path = Path(temp) / "task.json"
        task_path.write_text(json.dumps(task, sort_keys=True))
        context, research_cost = asyncio.run(asyncio.wait_for(
            research(task, config_path, checkout, args.research_model, task_path),
            timeout=args.research_timeout))
        # The attempt ledger counts requests even when the provider fails. Demand
        # fresh, admitted provider records for both operations before forecasting.
        rows = [json.loads(line) for line in attempts.read_text().splitlines()[before:]]
        case_rows = [r for r in rows if r["case_id"] == task["case_id"]]
        admitted = successful_evidence(evidence_case_dir, previous_evidence, task)
        (case_dir / "research.txt").write_text(context)
        (case_dir / "research-manifest.json").write_text(json.dumps({
            "case_id": task["case_id"], "cutoff_iso": task["cutoff_iso"],
            "research_model": args.research_model, "research_model_reported_cost_usd": research_cost,
            "researcher_commit": commit,
            "snapshot_attempt_count": len(case_rows),
            "snapshot_endpoints": [r["endpoint"] for r in case_rows],
            "successful_evidence_records": len(admitted),
            "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
            "status": "exploratory",
        }, indent=2) + "\n")
        enriched = dict(task, snapshot_research=context[:60000])
        codex = [sys.executable, str(ROOT / "harnesses/codex_cli.py"),
                 "--model", args.codex_model, "--effort", args.codex_effort,
                 "--timeout", str(args.timeout)]
        result = subprocess.run(codex, input=json.dumps(enriched), text=True,
                                capture_output=True, timeout=args.timeout + 30)
        if result.returncode:
            raise SystemExit(f"Codex forecast failed: {result.stderr[-500:]}")
        forecast = json.loads(result.stdout)
        print(json.dumps({"eps_prediction": float(forecast["eps_prediction"])}))


if __name__ == "__main__":
    main()
