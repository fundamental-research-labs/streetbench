# How the backtest worked

## Cases and forecasts

All nine configurations forecast the same 200 companies' Q2 2026 normalized diluted EPS in USD per share. Each case has a fixed research cutoff in [the case file](../data/cases.jsonl). We set it to 4 pm New York time two U.S. trading days before the observed earnings report. The exact timestamp in the file takes precedence over recalculating that rule.

Each forecast task included earlier financial history, such as prior EPS and revenue estimates and reported values. It did not include the target quarter's reported EPS or final Street consensus. We kept the answer key separate from the agents. The original histories and answer values are not in this repository because their sharing rights have not been established.

## Web evidence and review

The agents used [Exa Snapshot](https://exa.ai/docs/search/snapshot) to request stored web pages at the case cutoff. Both Search and Contents used the same `snapshotAsOf` value. There was no live search fallback. Exa says Snapshot bounds the page content, while search ranking still uses current retrieval signals. The [benchmark spec](../BENCHMARK_SPEC.md) shows the request shapes.

We checked selected forecasts against the run records and excluded attempts flagged for target-results exposure. Four original Shortcut Astra attempts encountered target-results links. Their forecasts were not scored. Fresh attempts were reviewed and selected under the same case IDs and cutoffs. The original flags remain in the private audit.

We also checked Snapshot provenance metadata for the 200 selected Shortcut Astra attempts. All **14,420 content records** carried the assigned case cutoff. Of those, **5,209** had a provider publication date, and none was after the cutoff. The other **9,211** had no publication date, so their timing rests on Exa's Snapshot contract rather than an independently observed page date.

We screened all 200 selected Shortcut Astra final writeups and their 1,881 cited URLs for target-results wording and dates. We then read the flagged passages and page titles. Seven writeups explicitly said they had not encountered target results. Fifteen same-company links with Q2 results wording led to earnings-date announcements or pre-release previews. None of the 205 cited URLs with a date in its address was dated after its case cutoff. This targeted review is narrower than having an LLM read every retrieved page or every trajectory across all nine configurations. The [aggregate audit counts](../results/snapshot-evidence-audit.json) record its scope.

## Reading the results

We scored one audited usable forecast per company for each configuration. The error for a case is the absolute difference between forecast EPS and reported EPS. The Street comparison uses final uploaded consensus, which was not independently captured at the research cutoff. All nine configurations have 200 selected forecasts, but runs happened at different times and some required retries. This is a comparison of complete agent setups on a retrospective cohort, not a controlled test of model capability alone.

The [case comparison diagnostics](../results/diagnostics.json) count a win when an agent's absolute error is lower than the Street's on the same company. Ties mean the errors differ by no more than `1e-12`. The Shortcut Astra source counts come from links in its final writeups. They show what was cited, not which source changed an estimate. The score file also includes paired bootstrap calculations for readers who want to inspect variability.

OpenAI lists model knowledge cutoffs before these Q2 results for [Sol](https://developers.openai.com/api/docs/models/gpt-6-sol), [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra), and [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna). That lowers the risk that the base models knew the reported figures from training. It does not remove the need to check retrieved web evidence in a backtest run after the reports were public. The results are a useful comparison on these 200 companies, but they do not establish future forecasting skill or investment performance.
