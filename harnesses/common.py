"""Shared user task for all public harness adapters."""
import json


def forecast_prompt(task: dict, asof_tools: bool = False) -> str:
    source_rule = (
        "Start with asof_search to inspect the archived evidence. "
        "You may use only asof_search and asof_read on the supplied archived documents; "
        "do not use live web or other files. " if asof_tools else
        "Use only the supplied task data and your reasoning; do not browse, use tools, "
        "read other files, or look up the reported outcome. "
    )
    return (
        "Forecast normalized diluted EPS in USD/share for the target fiscal quarter. "
        + source_rule + "Return only a JSON object "
        "with the numeric eps_prediction.\n\nTask:\n" + json.dumps(task, indent=2)
    )
