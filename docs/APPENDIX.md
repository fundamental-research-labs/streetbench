# Appendix

Supporting tables for the StreetBench results and the [Beat the Street](https://beatthestreet.live/) published record. They are separate studies and should not be pooled.

## All thirteen configurations

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
| Codex | Sol 6.1 | $0.1296 | 11.6% | 106-23-71 |
| Codex + GPT Researcher | Sol 6.1 | $0.1300 | 11.4% | 112-29-59 |
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

## Do moves away from the Street carry information?

Share of forecasts closer than the Street, by size of the move. Ties are left out. The published record and StreetBench are never pooled, and StreetBench uses the 150 companies outside the held-back 50.

| Dataset | Move from the Street | Closer | Farther | Share |
| --- | --- | --- | --- | --- |
| StreetBench, Opus 5.5 | Under 2% | 14 | 14 | 50% |
| StreetBench, Opus 5.5 | 2–5% | 32 | 13 | 71% |
| StreetBench, Opus 5.5 | 5–10% | 18 | 4 | 82% |
| StreetBench, Opus 5.5 | 10–20% | 11 | 4 | 73% |
| StreetBench, Opus 5.5 | Over 20% | 22 | 3 | 88% |
| StreetBench, Sol 6.1 | Under 2% | 22 | 20 | 52% |
| StreetBench, Sol 6.1 | 2–5% | 29 | 17 | 63% |
| StreetBench, Sol 6.1 | 5–10% | 15 | 8 | 65% |
| StreetBench, Sol 6.1 | 10–20% | 9 | 6 | 60% |
| StreetBench, Sol 6.1 | Over 20% | 20 | 4 | 83% |
| Published record | Under 0.5% | 8 | 7 | 53% |
| Published record | 0.5–1% | 26 | 9 | 74% |
| Published record | 1–2% | 29 | 6 | 83% |
| Published record | 2–5% | 33 | 12 | 73% |
| Published record | Over 5% | 23 | 4 | 85% |

How often the company then fell short of the Street, after a move up or down.

| Dataset | After a move up | After a move down | Rank correlation, move and surprise | Fisher exact, one-sided |
| --- | --- | --- | --- | --- |
| Published record | 10 of 120 (8%) | 11 of 37 (30%) | 0.479 (0.33 to 0.62) | p = 0.002 |
| StreetBench, Opus 5.5 | 14 of 83 (17%) | 36 of 53 (68%) | 0.658 (0.52 to 0.76) | p < 0.0001 |
| StreetBench, Sol 6.1 | 19 of 89 (21%) | 35 of 61 (57%) | 0.506 (0.34 to 0.65) | p < 0.0001 |

## Gain by the Street's past error

Share of the Street's capped % error removed on StreetBench, by thirds of a company's median Street miss in earlier quarters. The split was chosen after seeing results.

| Harness | Model | Street had been accurate | Middle | Street had missed most |
| --- | --- | --- | --- | --- |
| Codex | Astra | 1.3% | 13.8% | 11.9% |
| Codex | Luna | 0.7% | 3.5% | 12.7% |
| Codex | Sol | 4.7% | 14.6% | 15.6% |
| Codex | Sol 6.1 | 4.3% | 10.8% | 15.1% |
| Codex + GPT Researcher | Astra | 6.0% | 12.3% | 13.8% |
| Codex + GPT Researcher | Luna | -25.6% | 4.0% | 5.6% |
| Codex + GPT Researcher | Sol | -9.4% | 23.1% | 11.6% |
| Codex + GPT Researcher | Sol 6.1 | 2.6% | 13.0% | 12.9% |
| Shortcut | Astra | -1.5% | 21.6% | 20.6% |
| Shortcut | Luna | 3.6% | 7.9% | 8.3% |
| Shortcut | Opus 5.5 | 0.2% | 24.4% | 28.0% |
| Shortcut | Sol | -4.0% | 15.9% | 20.5% |
| Shortcut | Sol 6.1 | 1.7% | 17.2% | 25.4% |

## Main reason for each published move

A model coded each published forecast's stated rationale and closing answer with outcomes hidden, recording the main reason for the gap to the Street. Many forecasts cite several reasons, and small groups have wide intervals.

| Main reason | Forecasts | Closer than the Street | Median move | Moved down |
| --- | --- | --- | --- | --- |
| Recent company disclosure | 42 | 28 (67%) | 1.23% | 11 |
| Operating build from segments, units or backlog | 35 | 26 (74%) | 1.05% | 9 |
| Record of beating guidance or consensus | 28 | 26 (93%) | 2.38% | 0 |
| Interest, tax, share count or FX | 19 | 14 (74%) | 2.07% | 9 |
| No stated rationale | 13 | 9 (69%) | 2.12% | 4 |
| Costs or margin | 9 | 7 (78%) | 3.94% | 1 |
| Stale, dispersed or mismatched consensus | 6 | 5 (83%) | 12.47% | 1 |
| Peer or third-party data | 5 | 4 (80%) | 4.83% | 2 |

## Simple-rule checks

Nudges are 0.5%, picked with hindsight. StreetBench is Opus 5.5 on 150 companies.

| Check | Published record | StreetBench |
| --- | --- | --- |
| Actual above the Street | 136 of 157 | 84 of 150 |
| Forecast closer than the Street | 119 | 97 |
| Flat nudge closer | 136 | 84 |
| Nudge by profitability closer | 132 | 105 |
| Forecast pointed the right way | 121 | 103 |
| Always saying above | 136 | 84 |

## The improvement loop

Sol 6.1 in Shortcut on 68 unseen companies, with a pass mark written down before any forecast was scored. To pass, the 95% interval had to stay above zero and the median had to be at least zero. Gains are in capped % error points. Neither round passed, and the rule ended the loop after two failures in a row.

| Comparison | Pairs | Gain | 95% interval | Median | Wins-ties-losses |
| --- | --- | --- | --- | --- | --- |
| Round 1 tilt against the unchanged skill | 66 | +1.31 | -0.66 to 3.60 | +0.29 | 37-2-27 |
| Round 2 tilt, profitable companies only | 66 | +1.30 | -0.67 to 3.58 | 0.00 | 32-3-31 |
| Rerun of the unchanged skill against the original forecasts | 66 | -1.02 | -3.71 to 1.42 | +0.47 | 37-2-27 |
| Round 1 tilt against the original forecasts | 67 | +0.30 | -1.81 to 2.25 | +0.83 | 43-1-23 |
| Round 2 tilt against the original forecasts | 68 | +0.28 | -1.76 to 1.92 | +0.70 | 44-2-22 |

Provider outages stopped round 1 three times, and one was our own doing. We changed the failure rule each time before any judging score was seen, and kept every attempt on the record. Looking back, averaging both tilts against both runs of the unchanged skill gives +0.80 (-0.31 to 1.94) on 66 companies. That average was not part of the test.

A follow-up then ran the round 2 tilt and the unchanged skill once more on 50 of the 68 companies, chosen by hash, under rules fixed before any of its forecasts ran. It cannot change the loop's verdict. It would have been a lead for a held-back test only if the new runs showed a gain, the tilt had at most two more failed or flagged forecasts, and the pool's lower bound was above zero with a median of at least zero. The pool's lower bound is below zero, so it is not a lead, and we did not detect a gain.

| Follow-up comparison | Pairs | Gain | 95% interval | Median | Wins-ties-losses |
| --- | --- | --- | --- | --- | --- |
| New runs only, round 2 tilt against the unchanged skill | 50 | +0.42 | -0.80 to 1.70 | +0.10 | 25-2-23 |
| All runs pooled, per company, tilts against the unchanged skill | 66 | +0.71 | -0.21 to 1.67 | +0.83 | 38-1-27 |

## Keeping the answer out of a backtest

Leak judges on 471 test cases, spotting information released after a publication date.

| Judge | False negatives | False positives | Overall accuracy |
| --- | --- | --- | --- |
| TypeSafe Jev | 18 | 11 | 93.8% (442 of 471) |
| Claude Haiku | 78 | 9 | 81.5% (384 of 471) |

Four ways of bounding web evidence. The Wayback row comes from an earlier 113-company Q2 backtest, not StreetBench.

| Setup | What it did | What we found |
| --- | --- | --- |
| Open web | No date control | All 27 test runs saw the actual results |
| Date filter | Search only pages first published before the cutoff | Pages updated in place carry later text. 4 of 19 Wikipedia pages failed one check |
| Wayback + Jev | A Wayback capture from before the cutoff, with a leak judge as the fallback | About 3,540 pages blocked and 13,000 served. 18 of 113 runs said a search result showed them reported numbers, though a URL audit found no results page |
| Exa Snapshot | Every search and page read pinned to the case cutoff, with no live fallback | All 14,420 page records carried the cutoff. Of the 5,209 with a publication date, none was after it |
