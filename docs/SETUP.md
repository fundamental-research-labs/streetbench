# Local setup

The [challenge guide](../CHALLENGE.md) gives the step-by-step path. Start with the [200 fixed cases](../data/cases.jsonl), [forecast template](../data/submission-template.csv), and [benchmark spec](../BENCHMARK_SPEC.md). Every case has an exact `cutoff_iso`. Do not recalculate the cutoff or redraw companies.

Use Python 3.10+ to check a completed forecast file and score it against your own authorized answer file:

```sh
python3 scripts/challenge.py validate path/to/forecasts.csv
python3 scripts/challenge.py score-local path/to/forecasts.csv --answers path/to/local-answers.csv
```

Fill [the local answer template](../data/answers-template.csv) with normalized diluted EPS for all 200 cases. Final Street consensus is optional for local MAE, but needed to calculate error reduction versus Street. The original answer values and licensed historical financial rows are not included in this repository. A different EPS or consensus source can change the local score.

## Historical web evidence

The reference agents used [Exa Snapshot](https://exa.ai/docs/search/snapshot), sending each case's `cutoff_iso` as `snapshotAsOf` on both `/search` and `/contents`. The [request policy](../data/exa-snapshot-policy.json) shows the request shapes. The [portable adapter](../scripts/exa_snapshot_query.py) demonstrates cutoff-bound requests and evidence logging.

You need your own Snapshot access and any separately licensed financial data. Keep credentials and answer values outside the forecasting workspace. Record request times, returned URLs, publication metadata, content hashes, exclusions, and retries. If a results headline or reported value reaches the agent, treat that attempt as exposed and rerun from a clean context. Exa bounds stored page content to the requested time, but its search ranking is not historical. If you use another authorized pre-cutoff source, label that difference when comparing scores.
