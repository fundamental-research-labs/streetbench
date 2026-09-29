import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import exa_snapshot_query as snapshot


class SnapshotQueryTests(unittest.TestCase):
    def test_fixed_cutoff_filters_late_page_and_enforces_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key_path = root / "key"
            key_path.write_text("fixture")
            task = {"case_id": "TEST-2026-06-30", "cutoff_iso": "2026-07-01T20:00:00Z",
                    "verification_status": "verified"}
            config = {"snapshot_verified": True, "account_id": "fixture",
                      "key_path": str(key_path),
                      "verified_key_sha256": hashlib.sha256(b"fixture").hexdigest(),
                      "evidence_dir": str(root / "evidence"),
                      "max_http_attempts": 1, "max_case_http_attempts": 1}
            response = {"requestId": "fixture-request", "results": [
                {"url": "https://example.test/old", "publishedDate": "2026-06-30",
                 "title": "Old", "text": "Pre-cutoff outlook"},
                {"url": "https://example.test/late", "publishedDate": "2026-07-02",
                 "title": "Late", "text": "Reported EPS"}]}
            with patch.object(snapshot, "request_snapshot", return_value=response) as request:
                result = snapshot.run(task, config, "search", "revenue outlook")
                self.assertEqual([hit["doc_id"] for hit in result["hits"]],
                                 ["https://example.test/old"])
                self.assertEqual(request.call_args.args[1]["contents"]["snapshotAsOf"], task["cutoff_iso"])
                with self.assertRaisesRegex(ValueError, "budget exhausted"):
                    snapshot.run(task, config, "search", "another query")
                self.assertEqual(request.call_count, 1)
            artifact = next((root / "evidence" / task["case_id"]).glob("*.json"))
            self.assertEqual(len(json.loads(artifact.read_text())["documents"]), 1)

    def test_unverified_case_fails_before_http(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = {"case_id": "X", "cutoff_iso": "2026-07-01T20:00:00Z",
                    "verification_status": "unverified"}
            with patch.object(snapshot, "request_snapshot") as request:
                with self.assertRaisesRegex(ValueError, "not verified"):
                    snapshot.run(task, {"snapshot_verified": False}, "search", "outlook")
                request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
