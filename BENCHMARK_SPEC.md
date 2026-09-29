# Streetbench benchmark spec

Streetbench measures how closely an agent can estimate a company's Q2 2026 normalized diluted EPS before its earnings report. The test has [200 fixed companies](data/cases.jsonl). Each of the nine reference configurations produced one audited forecast per company. We compare those forecasts with reported EPS and with the final Street consensus on the same cases.

The reference to beat is Shortcut Astra: **$0.1203/share** mean absolute error (MAE), compared with **$0.1467/share** for the Street. These are rounded displays. The scorer uses the unrounded values in [the results file](results/scores.json).

## Cases and cutoff

Each row in `data/cases.jsonl` supplies the company, fiscal period, EPS target, and exact `cutoff_iso`. The cutoffs were assigned at 4 pm New York time two U.S. trading days before the observed report date. For this cohort they fall between July 10 and August 11, 2026, all at 4 pm EDT. Use each row's timestamp as given rather than recalculating it.

The original forecasting task included earlier-quarter history: period end, normalized EPS consensus and actual, revenue consensus and actual, and report date. It did not include the target-quarter reported EPS, final consensus, or target-or-later history. Those numeric historical rows are not in this repository because their redistribution rights have not been established. The case file includes hashes of the original prompts and histories, so their identities can be checked without publishing the underlying data. A run built from a different authorized history source should disclose that difference.

The forecast is one finite number in USD per share for each case. Keep the company, quarter, EPS definition, and cutoff fixed. The [forecast template](data/submission-template.csv) contains the 200 required IDs.

## Replaying the web evidence

The reference agents used [Exa Snapshot](https://exa.ai/docs/search/snapshot). The case's exact `cutoff_iso` was passed as `snapshotAsOf` on both Search and Contents. Search used `auto`, returned up to five results, and requested stored page text:

```json
{
  "query": "<agent query>",
  "type": "auto",
  "numResults": 5,
  "contents": {"snapshotAsOf": "<case cutoff_iso>", "text": true}
}
```

A page read used the same cutoff:

```json
{
  "ids": ["<one HTTP(S) URL>"],
  "snapshotAsOf": "<same case cutoff_iso>",
  "text": true
}
```

The endpoints were `POST https://api.exa.ai/search` and `POST https://api.exa.ai/contents`. The reference runs did not fall back to live web search. The [machine-readable request policy](data/exa-snapshot-policy.json) and [portable adapter](scripts/exa_snapshot_query.py) show how to pass the cutoff and log evidence.

Snapshot returns stored page content at or before the requested time, but [Exa says its search ranking uses current retrieval signals](https://exa.ai/docs/search/snapshot). It is not a historical ranking replay. We rejected provider publication dates after the cutoff and excluded attempts flagged for target-results exposure. Four Shortcut Astra cases needed clean retries. Keep a record of request time, cutoff, returned URL, publication metadata, content hash, and any exclusion so you can inspect your own evidence boundary. Snapshot access and lookback may also change, so check that your account can reach these dates before starting.

To compare web setups, use the same case cutoffs and Snapshot request shapes, avoid live fallback, and quarantine results exposure. You can test another archived evidence source, but label the difference. Research volume, prompts, historical financial data, and agent architecture can all affect the result, so record what you changed.

## Scoring

For each case, absolute error is `|forecast EPS − reported EPS|`. MAE is the average error over all 200 cases. The Street comparison uses the same reported EPS values and the **final** uploaded consensus, not an analyst consensus captured independently at each forecast cutoff. The original 200-case answer key is held outside Git. Its hash is recorded in the [release manifest](results/release-manifest.json).

You can [run the evaluation locally](CHALLENGE.md) with your own authorized normalized EPS values. The scorer checks that all 200 IDs have finite forecasts and reports MAE and the gap from Shortcut Astra. If you also provide final-consensus values, it reports error reduction versus Street. If your answer source applies a different EPS definition or consensus treatment, its score is not directly identical to ours.

OpenAI's published knowledge cutoffs for [Sol](https://developers.openai.com/api/docs/models/gpt-6-sol), [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra), and [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) precede these earnings reports. That lowers the risk that the base models memorized the target results. This is still a retrospective test run after the reports were public. Source leakage, differences in historical input timing, and the use of final consensus limit what the result can prove about live forecasting or investment performance.
