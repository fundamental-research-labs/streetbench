"""Fail-closed checks for the GPT Researcher historical evidence boundary."""
from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SnapshotBoundaryTests(unittest.TestCase):
    def test_pilot_input_whitelist_drops_final_consensus(self):
        prepare = load("prepare_gptr_pilot", "scripts/prepare_gpt_researcher_pilot.py")
        source = {"case_id": "FOXF-2026-06-30", "ticker": "FOXF", "company": "Fox Factory",
                  "quarter": "Q2 2026", "period_end_date": "2026-06-30",
                  "eps_basis": "normalized diluted", "cutoff_iso": "2026-08-05T20:00:00Z",
                  "verification_status": "exploratory", "history": [],
                  "consensus_eps": 0.12, "actual_eps": 0.25, "report_date": "2026-08-07"}
        task = prepare.prepare(source)
        self.assertFalse({"consensus_eps", "actual_eps", "report_date"}.intersection(task))

    def test_rejects_target_answers(self):
        adapter = load("codex_gptr", "harnesses/codex_gpt_researcher.py")
        task = {"case_id": "FOXF-2026-06-30", "cutoff_iso": "2026-08-05T20:00:00Z",
                "consensus_eps": None}
        adapter.checked_task(task)
        for key, value in (("actual_eps", 1), ("consensus_eps", 1), ("answer", {})):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    adapter.checked_task(dict(task, **{key: value}))

    def test_requires_successful_search_and_historical_read(self):
        adapter = load("codex_gptr_evidence", "harnesses/codex_gpt_researcher.py")
        task = {"case_id": "FOXF-2026-06-30", "cutoff_iso": "2026-08-05T20:00:00Z"}
        with tempfile.TemporaryDirectory() as root:
            case_dir = Path(root)
            search = {**task, "provider": "exa-snapshot", "endpoint": "search",
                      "documents": [{"url": "https://example.org/a"}]}
            (case_dir / "search.json").write_text(json.dumps(search))
            with self.assertRaisesRegex(RuntimeError, "successful Snapshot"):
                adapter.successful_evidence(case_dir, set(), task)
            read = {**search, "endpoint": "contents", "documents": []}
            (case_dir / "read.json").write_text(json.dumps(read))
            with self.assertRaisesRegex(RuntimeError, "successful Snapshot"):
                adapter.successful_evidence(case_dir, set(), task)
            read["documents"] = [{"url": "https://example.org/a"}]
            (case_dir / "read.json").write_text(json.dumps(read))
            self.assertEqual(len(adapter.successful_evidence(case_dir, set(), task)), 2)
            with self.assertRaisesRegex(RuntimeError, "successful Snapshot"):
                adapter.successful_evidence(case_dir, {"read.json"}, task)

    def test_mcp_search_prefetches_historical_contents(self):
        mcp = load("asof_mcp_boundary", "scripts/asof_mcp.py")
        calls = []

        def fake_run(command, **_kwargs):
            calls.append(command[-2:])
            if command[-2] == "search":
                payload = {"hits": [{"doc_id": "https://example.org/a", "title": "A"}]}
            elif command[-2] == "read":
                payload = {"text": "historical page", "text_sha256": "abc"}
            else:
                raise AssertionError(command)
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": "asof_search", "arguments": {"query": "FOXF"}}}
        with tempfile.TemporaryDirectory() as root:
            argv = ["asof_mcp.py", "--task", str(Path(root) / "task.json"),
                    "--snapshot-config", str(Path(root) / "config.json"),
                    "--prefetch-limit", "2"]
            output = io.StringIO()
            with patch.object(sys, "argv", argv), patch.object(sys, "stdin", io.StringIO(json.dumps(request)+"\n")), \
                    patch.object(mcp.subprocess, "run", side_effect=fake_run), redirect_stdout(output):
                mcp.main()
        response = json.loads(output.getvalue())
        self.assertEqual(calls, [["search", "FOXF"], ["read", "https://example.org/a"]])
        result = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(result["hits"][0]["historical_text"], "historical page")

    def test_prefetch_read_error_fails_closed(self):
        mcp = load("asof_mcp_error", "scripts/asof_mcp.py")

        def fake_run(command, **_kwargs):
            if command[-2] == "search":
                return subprocess.CompletedProcess(command, 0,
                    json.dumps({"hits": [{"doc_id": "https://example.org/a"}]}), "")
            return subprocess.CompletedProcess(command, 1, "", "not in historical index")

        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": "asof_search", "arguments": {"query": "FOXF"}}}
        output = io.StringIO()
        with patch.object(sys, "argv", ["asof_mcp.py", "--task", "task.json",
                                       "--snapshot-config", "config.json", "--prefetch-limit", "2"]), \
                patch.object(sys, "stdin", io.StringIO(json.dumps(request)+"\n")), \
                patch.object(mcp.subprocess, "run", side_effect=fake_run), redirect_stdout(output):
            mcp.main()
        response = json.loads(output.getvalue())
        self.assertIn("Snapshot historical page read failed", response["error"]["message"])


if __name__ == "__main__":
    unittest.main()
