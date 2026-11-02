# Appendix

Two supporting tables. The first restates the published scores for all eleven configurations. The second lists the forecasting skill changes we tested. They are separate studies and should not be pooled.

## All eleven configurations

Each configuration forecast the same 200 companies. The Street's mean error is $0.1467. Cut is the share of that error removed. The last column counts companies closer than the Street, tied, and farther. This table is built from [scores](../results/scores.json), [Sol 6.1 and Opus 5.5 scores](../results/newer-models.json), and [case comparisons](../results/diagnostics.json).

| Harness | Model | Mean error | Cut vs Street | Closer-tied-farther |
| --- | --- | --- | --- | --- |
| Shortcut | Opus 5.5 | $0.1125 | 23.3% | 126-19-55 |
| Shortcut | Sol 6.1 | $0.1183 | 19.4% | 124-0-76 |
| Shortcut | Astra | $0.1203 | 18.0% | 121-0-79 |
| Codex | Sol | $0.1258 | 14.2% | 104-26-70 |
| Codex + GPT Researcher | Sol | $0.1270 | 13.4% | 109-23-68 |
| Codex + GPT Researcher | Astra | $0.1271 | 13.3% | 108-26-66 |
| Shortcut | Sol | $0.1274 | 13.1% | 120-3-77 |
| Codex | Astra | $0.1290 | 12.1% | 101-32-67 |
| Shortcut | Luna | $0.1316 | 10.3% | 113-9-78 |
| Codex | Luna | $0.1322 | 9.9% | 100-28-72 |
| Codex + GPT Researcher | Luna | $0.1413 | 3.7% | 84-31-85 |

## Forecasting skill changes

Between September 22 and October 8, 2026, we tested a naive skill evolution workflow: read training cases, prompt for a change to the forecasting skill, and test it against the incumbent. It did not work through simple prompting, and none of the 13 changes held up. These tests ran on a separate pool of historical Q2 2026 cases on GPT-5.6 Luna and Sol, a generation before the models above, so they say nothing direct about the scores in the first table.

Each change ran against the incumbent skill on the same companies, with the same model, inputs, and cutoff. Three tests reused earlier baseline runs, so run timing differed in those. The incumbent was the original skill, except for three changes tested against the EPS bridge.

A screen is a cheap first test on a handful of training cases. Validation uses 20 cases kept away from the writing of each change and scored in aggregate only. W-T-L counts wins, ties, and losses against the incumbent. Cases repeat across tests, so the counts should not be summed into one result.

| Change | What it asked for | Model | Furthest test | Pairs | W-T-L | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| Prior-EPS bridge | A sourced bridge to the consensus EPS basis | Sol | Validation | 19 | 8-2-9 | Rejected |
| Guidance | Match guidance to the period and accounting basis | Luna | Validation | 17 | 7-2-8 | Rejected, more invalid runs |
| EPS bridge | Reconcile the adjusted numerator, tax and shares | Luna, Sol | All training cases | 67 | 29-6-32 | Cleared validation, then failed |
| Driver evidence | Use supported drivers, no back-solving | Luna | Screen | 4 | 1-0-3 | Rejected |
| Guidance + EPS | Add conditional guidance to the EPS bridge | Luna | Screen | 3 | 0-0-3 | Rejected |
| Fiscal period | Map evidence to fiscal dates and week counts | Luna | Screen | 3 | 2-1-0 | Rejected, candidate run failed |
| Independent bridge | Derive EPS from separately supported inputs | Sol | Screen | 2 | 0-0-2 | Rejected |
| Share basis | Reconcile weighted-average shares | Sol | Screen | 1 | 0-0-1 | Stopped early |
| Beat prior | A small beat cushion near zero consensus | Sol | Screen | 3 | 0-1-2 | Rejected |
| Model gap | Check gaps to consensus for scale and source | Luna | Screen | 11 | 4-1-6 | Rejected |
| Unit consistency | Reconcile units in formulas | Luna | Screen | 3 | 1-1-1 | Rejected |
| Income signs | One sign convention down to pre-tax income | Luna | Validation | 18 | 7-0-11 | Rejected |
| Clinical calendar | Separate trial starts, activity and closeouts | Luna | Larger screen | 13 | 6-1-6 | Not promoted, search stopped |
