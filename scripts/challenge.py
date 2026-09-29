#!/usr/bin/env python3
"""Validate Streetbench forecasts and score them against local EPS answers."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "data/cases.jsonl"
REFERENCE_SCORES = ROOT / "results/scores.json"


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def cases_by_id(path: Path) -> dict[str, dict]:
    rows = read_jsonl(path)
    cases = {row["case_id"]: row for row in rows}
    if not rows or len(cases) != len(rows):
        raise ValueError("Case manifest is empty or contains duplicate IDs")
    return cases


def finite_number(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def read_submission(path: Path, cases: dict[str, dict]) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["case_id", "forecast_eps"]:
            raise ValueError("Submission columns must be case_id,forecast_eps")
        predictions = {}
        for line, row in enumerate(reader, start=2):
            case_id = (row["case_id"] or "").strip()
            if case_id not in cases:
                raise ValueError(f"Line {line}: unknown case_id {case_id!r}")
            if case_id in predictions:
                raise ValueError(f"Line {line}: duplicate case_id {case_id!r}")
            predictions[case_id] = finite_number(row["forecast_eps"], f"Line {line} forecast_eps")
    missing = set(cases) - set(predictions)
    if missing:
        raise ValueError(f"Submission missing {len(missing)} cases; first: {sorted(missing)[0]}")
    return predictions


def read_answers(path: Path, cases: dict[str, dict]) -> dict[str, dict]:
    rows = read_jsonl(path)
    answers = {row["case_id"]: row for row in rows}
    if len(answers) != len(rows) or set(answers) != set(cases):
        raise ValueError("Answer key must contain each frozen case exactly once")
    for case_id, row in answers.items():
        finite_number(row["actual_eps"], f"{case_id} actual_eps")
        finite_number(row["consensus_eps"], f"{case_id} consensus_eps")
    return answers


def read_local_answers(path: Path, cases: dict[str, dict]) -> dict[str, dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["case_id", "actual_eps", "consensus_eps"]:
            raise ValueError("Local answer columns must be case_id,actual_eps,consensus_eps")
        answers = {}
        for line, row in enumerate(reader, start=2):
            case_id = (row["case_id"] or "").strip()
            if case_id not in cases or case_id in answers:
                raise ValueError(f"Line {line}: unknown or duplicate case_id {case_id!r}")
            answers[case_id] = {
                "actual_eps": finite_number(row["actual_eps"], f"Line {line} actual_eps"),
                "consensus_eps": (finite_number(row["consensus_eps"], f"Line {line} consensus_eps")
                                  if row["consensus_eps"] not in (None, "") else None),
            }
    missing = set(cases) - set(answers)
    if missing:
        raise ValueError(f"Local answers missing {len(missing)} cases; first: {sorted(missing)[0]}")
    return answers


def score_local(predictions: dict[str, float], answers: dict[str, dict], baseline: float) -> dict:
    ordered = sorted(predictions)
    actuals = {case_id: float(answers[case_id]["actual_eps"]) for case_id in ordered}
    model_mae = sum(abs(predictions[case_id] - actuals[case_id]) for case_id in ordered) / len(ordered)
    street_mae = None
    if all(answers[case_id]["consensus_eps"] is not None for case_id in ordered):
        street_mae = sum(abs(float(answers[case_id]["consensus_eps"]) - actuals[case_id])
                         for case_id in ordered) / len(ordered)
    return {
        "cases": len(ordered),
        "forecast_mae": model_mae,
        "street_mae": street_mae,
        "error_reduction_pct": 100 * (street_mae - model_mae) / street_mae if street_mae else None,
        "shortcut_astra_reference_mae": baseline,
        "mae_gap_vs_shortcut_astra": model_mae - baseline,
        "answer_source": "user_supplied_unverified",
        "comparison_note": "Exact comparability requires the same normalized EPS and final-consensus definitions as Streetbench.",
    }


def reference_mae(path: Path = REFERENCE_SCORES) -> float:
    rows = json.loads(path.read_text())["rows"]
    matching = [row for row in rows if row["harness"] == "Shortcut" and row["model"] == "Astra"]
    if len(matching) != 1 or matching[0]["valid"] != matching[0]["cases"]:
        raise ValueError("Shortcut Astra reference must have one complete score row")
    return finite_number(matching[0]["model_mae"], "Shortcut Astra reference MAE")


def score(predictions: dict[str, float], answers: dict[str, dict], baseline: float) -> dict:
    ordered = sorted(predictions)
    errors = [abs(predictions[case_id] - float(answers[case_id]["actual_eps"]))
              for case_id in ordered]
    street_errors = [abs(float(answers[case_id]["consensus_eps"]) - float(answers[case_id]["actual_eps"]))
                     for case_id in ordered]
    model_mae = sum(errors) / len(ordered)
    street_mae = sum(street_errors) / len(ordered)
    improvements = [street - model for street, model in zip(street_errors, errors)]
    rng = random.Random(20260924)
    draws = sorted(sum(rng.choices(improvements, k=len(improvements))) / len(improvements)
                   for _ in range(2000))

    def percentile(probability: float) -> float:
        index = (len(draws) - 1) * probability
        low = math.floor(index)
        high = math.ceil(index)
        return draws[low] + (draws[high] - draws[low]) * (index - low)

    return {
        "cases": len(ordered),
        "submission_mae": model_mae,
        "street_mae": street_mae,
        "improvement_over_street": street_mae - model_mae,
        "error_reduction_pct": 100 * (street_mae - model_mae) / street_mae,
        "improvement_95pct_bootstrap": [percentile(.025), percentile(.975)],
        "shortcut_astra_mae": baseline,
        "mae_gap_vs_shortcut_astra": model_mae - baseline,
        "beats_shortcut_astra_on_mae": model_mae < baseline,
        "status": "exploratory_retrospective",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "score", "score-local"))
    parser.add_argument("submission", type=Path)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--answers", type=Path,
                        help="Required for score: private JSONL key; for score-local: your own CSV answer file")
    args = parser.parse_args()
    try:
        cases = cases_by_id(args.cases)
        predictions = read_submission(args.submission, cases)
        if args.command == "validate":
            result = {"valid": True, "cases": len(predictions)}
        elif args.command == "score-local":
            if args.answers is None:
                parser.error("score-local requires --answers with your own 200-row CSV")
            answers = read_local_answers(args.answers, cases)
            result = score_local(predictions, answers, reference_mae())
        else:
            if args.answers is None:
                parser.error("score requires --answers")
            release = json.loads((ROOT / "results/release-manifest.json").read_text())
            digest = hashlib.sha256(args.answers.read_bytes()).hexdigest()
            if digest != release["answer_key_sha256"]:
                raise ValueError("Answer key does not match the frozen release commitment")
            result = score(predictions, read_answers(args.answers, cases), reference_mae())
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Invalid forecast or answer file: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
