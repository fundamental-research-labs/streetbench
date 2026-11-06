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

[Linkup Rewind](../data/linkup-rewind-policy.json) is an alternative source with historical ranking: matches and their order are computed only from pages crawled by the requested UTC day, and each result reports the day its revision was first captured. Rewind is day-granular, so the [Rewind adapter](../scripts/rewind_query.py) uses the last full UTC day before each `cutoff_iso`. Pass `--rewind-config` instead of `--snapshot-config` to `harnesses/codex_cli.py` or `scripts/asof_mcp.py`. The config takes the same budget and evidence fields as the Snapshot config, plus an optional `key_path` (or `LINKUP_API_KEY` in the environment). Without a key, requests use Linkup's shared, rate-limited keyless tier. Label Rewind runs separately when comparing scores.
