# The 200 cases

[cases.jsonl](cases.jsonl) lists the companies in the backtest. Each row gives the company, Q2 2026 period, EPS target, and exact time when research had to stop. Keep those case IDs and cutoffs unchanged when you try your own model.

Start with [the forecast template](submission-template.csv). It has one blank EPS estimate for each company. To score a run on your own computer, fill [the answer template](answers-template.csv) with reported normalized diluted EPS from a source you may use. Final Street consensus is optional if you only want your model's average error.

The original runs also used earlier financial history and [Exa Snapshot](https://exa.ai/docs/search/snapshot) web pages bounded by each case's cutoff. We have not included the historical numbers, archived pages, or answer values because their sharing rights have not been established. The [challenge guide](../CHALLENGE.md) shows how to run and score a new attempt. The [benchmark spec](../BENCHMARK_SPEC.md) explains the research cutoff and Snapshot requests.

These reports are already public. A local score is useful for comparing ideas, but it does not by itself show how a system would perform before future reports arrive.
