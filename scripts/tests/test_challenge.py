"""Submission boundary checks for the public challenge."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from challenge import cases_by_id, read_answers, read_local_answers, read_submission, score, score_local  # noqa: E402


class ChallengeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        self.cases_file = root / "cases.jsonl"
        self.answers_file = root / "answers.jsonl"
        self.submission_file = root / "submission.csv"
        self.local_answers_file = root / "local-answers.csv"
        self.cases_file.write_text(
            "".join(json.dumps({"case_id": case_id}) + "\n" for case_id in ("A", "B")))
        self.answers_file.write_text(
            "".join(json.dumps(row) + "\n" for row in (
                {"case_id": "A", "actual_eps": 1.0, "consensus_eps": 1.4},
                {"case_id": "B", "actual_eps": -0.5, "consensus_eps": -0.2},
            )))

    def submission(self, rows):
        with self.submission_file.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(("case_id", "forecast_eps"))
            writer.writerows(rows)

    def test_complete_submission_scores_against_same_cases(self):
        self.submission((("A", "1.1"), ("B", "-0.4")))
        cases = cases_by_id(self.cases_file)
        result = score(read_submission(self.submission_file, cases),
                       read_answers(self.answers_file, cases), .12)
        self.assertAlmostEqual(result["submission_mae"], .1)
        self.assertAlmostEqual(result["street_mae"], .35)
        self.assertTrue(result["beats_shortcut_astra_on_mae"])

    def test_missing_duplicate_or_nonfinite_forecast_is_rejected(self):
        cases = cases_by_id(self.cases_file)
        for rows in (
            (("A", "1.0"),),
            (("A", "1.0"), ("A", "1.1"), ("B", "-0.5")),
            (("A", "nan"), ("B", "-0.5")),
        ):
            with self.subTest(rows=rows):
                self.submission(rows)
                with self.assertRaises(ValueError):
                    read_submission(self.submission_file, cases)

    def test_answer_key_must_match_frozen_ids(self):
        cases = cases_by_id(self.cases_file)
        self.answers_file.write_text(
            json.dumps({"case_id": "A", "actual_eps": 1, "consensus_eps": 1}) + "\n")
        with self.assertRaises(ValueError):
            read_answers(self.answers_file, cases)

    def test_local_answers_require_exact_ids_and_finite_values(self):
        cases = cases_by_id(self.cases_file)
        self.local_answers_file.write_text(
            "case_id,actual_eps,consensus_eps\nA,1.0,1.4\nB,-0.5,-0.2\n")
        answers = read_local_answers(self.local_answers_file, cases)
        self.assertEqual(len(answers), 2)
        result = score_local({"A": 1.1, "B": -0.4}, answers, .12)
        self.assertAlmostEqual(result["forecast_mae"], .1)
        self.assertAlmostEqual(result["street_mae"], .35)
        self.local_answers_file.write_text(
            "case_id,actual_eps,consensus_eps\nA,1.0,\nB,-0.5,\n")
        self.assertIsNone(score_local({"A": 1.1, "B": -0.4},
                                       read_local_answers(self.local_answers_file, cases), .12)["street_mae"])
        for bad_rows in ("A,1.0,1.4\n", "A,1.0,1.4\nA,1.1,1.4\nB,-0.5,-0.2\n",
                         "A,nan,1.4\nB,-0.5,-0.2\n"):
            with self.subTest(bad_rows=bad_rows):
                self.local_answers_file.write_text("case_id,actual_eps,consensus_eps\n" + bad_rows)
                with self.assertRaises(ValueError):
                    read_local_answers(self.local_answers_file, cases)


if __name__ == "__main__":
    unittest.main()
