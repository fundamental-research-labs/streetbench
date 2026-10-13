import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import rewind_query as rewind


def fixture_config(root: Path, attempts: int = 1) -> dict:
    key_path = root / "key"
    key_path.write_text("fixture")
    return {"key_path": str(key_path),
            "verified_key_sha256": hashlib.sha256(b"fixture").hexdigest(),
            "evidence_dir": str(root / "evidence"),
            "max_http_attempts": attempts, "max_case_http_attempts": attempts}


class RewindQueryTests(unittest.TestCase):
    task = {"case_id": "TEST-2026-06-30", "cutoff_iso": "2026-07-01T16:00:00-04:00",
            "verification_status": "verified"}

    def test_as_of_is_last_full_utc_day_before_cutoff(self):
        self.assertEqual(rewind.as_of_day(rewind.instant("2026-07-01T16:00:00-04:00")), "2026-06-30")
        self.assertEqual(rewind.as_of_day(rewind.instant("2026-07-01T00:00:00Z")), "2026-06-30")
        self.assertEqual(rewind.as_of_day(rewind.instant("2026-07-01T23:30:00-04:00")), "2026-07-01")

    def test_search_drops_late_revision_and_enforces_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = fixture_config(root)
            response = {"asOf": "2026-06-30", "results": [
                {"url": "https://example.test/old", "name": "Old", "content": "Pre-cutoff outlook",
                 "validFrom": "2026-06-12", "validTo": None},
                {"url": "https://example.test/late", "name": "Late", "content": "Reported EPS",
                 "validFrom": "2026-07-02", "validTo": None}]}
            with patch.object(rewind, "request_rewind", return_value=response) as request:
                result = rewind.run(self.task, config, "search", "revenue outlook")
                self.assertEqual([hit["doc_id"] for hit in result["hits"]], ["https://example.test/old"])
                self.assertTrue(result["ranking_is_historical"])
                self.assertEqual(request.call_args.args[1], {"q": "revenue outlook", "asOf": "2026-06-30"})
                with self.assertRaisesRegex(ValueError, "budget exhausted"):
                    rewind.run(self.task, config, "search", "another query")
                self.assertEqual(request.call_count, 1)
            artifact = json.loads(next((root / "evidence" / self.task["case_id"]).glob("*.json")).read_text())
            self.assertEqual(artifact["provider"], "linkup-rewind")
            self.assertEqual([doc["valid_from"] for doc in artifact["documents"]], ["2026-06-12"])

    def test_read_without_revision_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            config = fixture_config(Path(directory))
            with patch.object(rewind, "request_rewind", return_value={}):
                with self.assertRaisesRegex(ValueError, "unavailable in Rewind"):
                    rewind.run(self.task, config, "read", "https://example.test/missing")

    def test_unverified_case_fails_before_http(self):
        task = {"case_id": "X", "cutoff_iso": "2026-07-01T20:00:00Z", "verification_status": "unverified"}
        with patch.object(rewind, "request_rewind") as request:
            with self.assertRaisesRegex(ValueError, "not verified"):
                rewind.run(task, {}, "search", "outlook")
            request.assert_not_called()

    def test_keyless_request_sends_no_authorization(self):
        with tempfile.TemporaryDirectory() as directory:
            config = fixture_config(Path(directory))
            del config["key_path"], config["verified_key_sha256"]
            response = io.BytesIO(json.dumps({"asOf": "2026-06-30", "results": []}).encode())
            with patch.dict(os.environ, {}, clear=True), \
                    patch.object(rewind.urllib.request, "urlopen", return_value=response) as urlopen:
                rewind.run(self.task, config, "search", "outlook")
            self.assertIsNone(urlopen.call_args.args[0].get_header("Authorization"))

    def test_wrong_key_fails_before_http(self):
        with tempfile.TemporaryDirectory() as directory:
            config = fixture_config(Path(directory))
            config["verified_key_sha256"] = hashlib.sha256(b"other").hexdigest()
            with patch.object(rewind, "request_rewind") as request:
                with self.assertRaisesRegex(ValueError, "fingerprint"):
                    rewind.run(self.task, config, "search", "outlook")
                request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
