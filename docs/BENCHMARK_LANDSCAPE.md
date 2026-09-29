# How related benchmarks are built

Reviewed September 28, 2026. These are methodological comparisons, not claims that the tasks or scores are interchangeable with Streetbench.

| Benchmark | How its authors set it up | Useful lesson for Streetbench |
| --- | --- | --- |
| [ForecastBench](https://www.forecastbench.org/docs/) ([code](https://github.com/forecastingresearch/forecastbench)) | Continuously collects questions and resolutions, samples dated forecasting rounds, separates baseline and tool-augmented leaderboards, and scores forecasts made before future events resolve. It uses a difficulty-adjusted Brier method when participants answer different question sets. | The strongest next Streetbench version would seal forecasts before earnings releases, record the exact forecast time and consensus available then, and version each cohort. Streetbench's numeric EPS MAE is a different scoring problem. ForecastBench's Brier score should not be substituted for it. |
| [LiveBench](https://github.com/LiveBench/LiveBench) | Adds fresh questions regularly, keeps release identifiers, uses verifiable ground truth rather than an LLM judge where possible, and provides a runner with explicit model, concurrency, retry, and release options. | Preserve a frozen release manifest and deterministic scorer. Rotate future cohorts so a model cannot rely on published historical outcomes. Keep a private answer set until resolution. |
| [Finance Agent Benchmark](https://arxiv.org/abs/2508.00828) | Uses expert-authored financial research tasks across nine categories, validates questions, and evaluates agents with a specified Google Search and EDGAR tool harness. | Record the whole system configuration: model, effort, research stage, tool access, research limits, and source provenance. Separate agent setup effects from model-name comparisons. |
| [FinanceBench](https://github.com/patronus-ai/financebench) | Publishes an annotated financial-QA sample with question IDs, gold answers, justifications, evidence text, document names, pages, and document metadata. Its task is answering questions about existing filings. | Keep an evidence trail and explicit source dates for each EPS forecast. FinanceBench is financial QA, so its accuracy is not a direct baseline for predicting unreleased quarterly EPS. |
| [τ-bench](https://github.com/sierra-research/tau-bench) | Publishes the agent environment, historical trajectories, and tooling to classify whether a failure came from the agent, user simulation, or environment. | Retain every attempt and distinguish forecast error, target-results exposure, and infrastructure failure. Document retry paths alongside the selected audited result. |

## What the current Streetbench package makes inspectable

- One frozen 200-company cohort and the same reported-EPS/Street-consensus key for all nine completed configurations.
- A deterministic scoring rule: mean absolute EPS error and paired company bootstrap intervals for all nine configurations, with attempt and retry audits kept separately.
- 200/200 coverage for each configuration, selected valid forecasts, and attempt audits.
- The system contract, portable adapters, aggregate scores, graph, method limits, and synthetic scoring examples. Licensed histories, the real answer key, raw trajectories, credentials, and provider artifacts are intentionally absent.

## What a stronger next release needs

1. **Prospective sealing.** Register companies, EPS basis, exclusions, forecast deadlines, and every system configuration before reports. Timestamp each submitted forecast and commit its hash before the outcome is known. This addresses the largest gap with ForecastBench.
2. **Point-in-time baseline.** Save the analyst consensus actually available at each forecast cutoff, with vendor snapshot ID, timestamp, EPS definition, currency/share basis, and revision history. The current final uploaded consensus is post-report and cannot establish a live beat-the-Street result.
3. **Evidence availability.** For each historical input and retrieved page, record publication time, capture time, URL, content hash, admission decision, and any target-results flag. Periodically audit the Snapshot boundary against released filings and live search contamination.
4. **Predeclared scoring.** Keep numeric EPS MAE versus the same as-of Street baseline as the primary measure. Publish valid coverage, fallback treatment, paired company differences and intervals, plus direct system-to-system contrasts. Report failed attempts separately from accuracy.
5. **Versioned releases.** Freeze a manifest binding cohort IDs, case cutoffs, prompts, histories, evidence policy, model and effort, scorer revision, and result artifact hashes. A later retry or runtime repair becomes a new result version. It never rewrites the original attempt.

These are proposals inferred from the referenced benchmarks and from Streetbench's documented limitations. They are not claims that the present retrospective comparison has already passed prospective or point-in-time validation.
