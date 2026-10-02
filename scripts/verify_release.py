#!/usr/bin/env python3
"""Verify the aggregate Streetbench release without access to private cases."""
import hashlib
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'results/release-manifest.json').read_text())
    for relative, expected in manifest['sha256'].items():
        path = ROOT / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Hash mismatch: {relative}')
    current = json.loads((ROOT / 'results/scores.json').read_text())
    diagnostics = json.loads((ROOT / 'results/diagnostics.json').read_text())
    cohort = json.loads((ROOT / 'results/frozen-cohort-metadata.json').read_text())
    evidence = json.loads((ROOT / 'results/snapshot-evidence-audit.json').read_text())
    rows = current['rows']
    if len(rows) != 9 or len({(row['harness'], row['model']) for row in rows}) != 9:
        raise ValueError('Current scores need nine distinct configurations')
    if any(row['cases'] != 200 or row['valid'] != 200 or row['failures'] != 0 for row in rows):
        raise ValueError('Current coverage differs from the completed 200-case release')
    newer = json.loads((ROOT / 'results/newer-models.json').read_text())['rows']
    if ({(row['harness'], row['model']) for row in newer} != {('Shortcut', 'Sol 6.1'), ('Shortcut', 'Opus 5.5')}
            or len(newer) != 2
            or any(row['cases'] != 200 or row['valid'] != 200 or row['failures'] != 0
                   or abs(row['street_mae'] - rows[0]['street_mae']) > 1e-12
                   or row['closer_than_street'] + row['same_absolute_error'] + row['farther_than_street'] != 200
                   for row in newer)):
        raise ValueError('Newer Shortcut scores differ from the completed 200-case basis')
    if diagnostics['cohort_cases'] != 200 or diagnostics['answer_key_sha256'] != manifest['answer_key_sha256']:
        raise ValueError('Case diagnostics differ from the frozen score key')
    scored = {(row['harness'], row['model']): row for row in rows}
    counted = {(row['harness'], row['model']): row for row in diagnostics['rows']}
    if set(counted) != set(scored) or len(diagnostics['rows']) != 9:
        raise ValueError('Case diagnostics need the nine scored configurations')
    for key, row in counted.items():
        if (sum(row[name] for name in ('closer_than_street', 'same_absolute_error', 'farther_than_street')) != 200
                or abs(row['mean_absolute_error'] - scored[key]['model_mae']) > 1e-10):
            raise ValueError(f'Case diagnostics mismatch: {key}')
    if len(cohort['cases']) != 200:
        raise ValueError('Frozen cohort is not 200 cases')
    if (evidence['selected_cases'] != 200
            or evidence['all_provenance_records'] != evidence['content_provenance_records'] + evidence['no_eligible_snapshot_state_records']
            or evidence['content_provenance_records'] != evidence['records_with_exact_case_cutoff']
            or evidence['content_provenance_records'] != evidence['records_with_provider_publication_date'] + evidence['records_without_provider_publication_date']
            or evidence['records_published_after_cutoff'] != 0
            or evidence['selected_final_writeups_screened'] != 200
            or evidence['cited_source_urls_dated_after_cutoff'] != 0
            or evidence['flagged_writeups_reviewed'] != evidence['writeups_flagged_for_target_actual_wording']
            or evidence['flagged_url_titles_and_openings_reviewed'] != evidence['same_company_q2_results_wording_urls_flagged']):
        raise ValueError('Selected Snapshot metadata audit counts are inconsistent')
    challenge = [json.loads(line) for line in (ROOT / 'data/cases.jsonl').read_text().splitlines() if line.strip()]
    if len(challenge) != 200 or len({row['case_id'] for row in challenge}) != 200:
        raise ValueError('Challenge case list must have 200 distinct IDs')
    cutoffs = {row['cutoff_iso'] for row in challenge}
    if (len(cutoffs) != 21 or min(cutoffs) != '2026-07-10T16:00:00-04:00'
            or max(cutoffs) != '2026-08-11T16:00:00-04:00'
            or any((datetime.fromisoformat(value).hour, datetime.fromisoformat(value).minute,
                    datetime.fromisoformat(value).utcoffset()) != (16, 0, timedelta(hours=-4))
                   for value in cutoffs)):
        raise ValueError('Frozen case cutoffs differ from the documented 4 pm New York boundary')
    snapshot = json.loads((ROOT / 'data/exa-snapshot-policy.json').read_text())
    if (snapshot['case_count'] != len(challenge)
            or snapshot['search']['contents']['snapshotAsOf'] != '<case cutoff_iso>'
            or snapshot['contents']['snapshotAsOf'] != '<same case cutoff_iso>'
            or not snapshot['admission']['no_live_web_fallback']):
        raise ValueError('Snapshot policy differs from the documented replay boundary')
    for public, frozen in zip(challenge, cohort['cases']):
        for public_key, frozen_key in (('case_id', 'case_id'), ('ticker', 'ticker'),
                                       ('cutoff_iso', 'cutoff'), ('prompt_sha256', 'prompt_sha256'),
                                       ('history_sha256', 'history_sha256')):
            if public[public_key] != frozen[frozen_key]:
                raise ValueError(f'Challenge case mismatch: {public_key}')
    with (ROOT / 'data/submission-template.csv').open(newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ['case_id', 'forecast_eps'] or [row['case_id'] for row in reader] != [row['case_id'] for row in challenge]:
            raise ValueError('Submission template does not match the frozen case list')
    with (ROOT / 'data/answers-template.csv').open(newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ['case_id', 'actual_eps', 'consensus_eps'] or [row['case_id'] for row in reader] != [row['case_id'] for row in challenge]:
            raise ValueError('Local answer template does not match the frozen case list')
    print('Release verified: nine 200/200 scores plus two newer Shortcut models, 200 frozen challenge cases, Snapshot audit and artifact hashes match.')


if __name__ == '__main__':
    main()
