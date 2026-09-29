# Try to beat Shortcut Astra

Shortcut Astra's mean absolute EPS error was **$0.120/share** on these 200 companies. The Street consensus averaged **$0.147/share**. Can a different model, agent setup, or research strategy get closer to the reported EPS?

This is a retrospective test of normalized diluted EPS in USD per share for Q2 2026. All 200 cases and their exact research cutoffs are in [the case file](data/cases.jsonl). The result of each earnings report is now public, so keep results out of the forecasting context and retain a record of what your agent saw.

## Run the 200 cases

1. **Keep the cases fixed.** Use every `case_id`, company, target quarter, and `cutoff_iso` in [the case file](data/cases.jsonl). Copy the [forecast template](data/submission-template.csv) and fill `forecast_eps` with one numeric estimate per case. Do not replace a difficult case.
2. **Build your forecast inputs.** Use historical financial rows you are authorized to access, and include only information that was available by each case's cutoff. The original task used prior-quarter normalized EPS consensus and actuals, revenue consensus and actuals, period end, and report date. Do not give your forecasting agent the target-quarter reported EPS or final consensus.
3. **Choose a research setup.** To match the web evidence boundary, use [Exa Snapshot](https://exa.ai/docs/search/snapshot) with the case's exact `cutoff_iso` as `snapshotAsOf` on both Search and Contents. The [benchmark spec](BENCHMARK_SPEC.md) gives the request shapes and explains why Snapshot content is time-bounded even though search ranking is current. Do not fall back to live search or admit a target-results headline. You can use another archived, pre-cutoff source if you label that run **other evidence** when comparing it with the reference.
4. **Run your model or architecture.** Produce one EPS estimate per case. Keep a methods note with the model, prompts, tools, data source, research volume, and any retries. Save enough retrieval metadata to check the evidence cutoff. An exposed attempt should be excluded and rerun from a clean context.
5. **Validate your forecasts.** From the repository root, run:

   ```sh
   python3 scripts/challenge.py validate path/to/forecasts.csv
   ```

   The validator requires exactly the frozen 200 IDs and one finite number for each.

## Score locally

Fill `actual_eps` in the [local answer template](data/answers-template.csv) for every case using **normalized diluted EPS** from a source you may use. Fill `consensus_eps` with the **final Street consensus** if you have it. Otherwise leave that column blank. Keep this file outside the repository if your data license requires it. Then run:

```sh
python3 scripts/challenge.py score-local path/to/forecasts.csv --answers path/to/local-answers.csv
```

The scorer reports your mean absolute EPS error and the gap from Shortcut Astra's reference. If you filled every consensus value, it also reports the Street's error and your percentage reduction in error. Lower MAE is better. A negative gap means your forecasts are closer to the EPS values in **your** answer file. The local answer file is self-supplied, so a different normalized EPS treatment or consensus feed can change the comparison. This is a useful local evaluation, not a certified reproduction of the original score.

The original answer values and licensed financial histories are not redistributed. The [synthetic example](examples/answers.jsonl) shows the answer fields without revealing company outcomes. For exact cohort, cutoff, and Snapshot rules, see the [benchmark spec](BENCHMARK_SPEC.md). Because the reports are already public, even a strong retrospective score does not by itself prove live forecasting ability.
