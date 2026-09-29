#!/usr/bin/env python3
"""Example harness: predict the point-in-time street consensus supplied in a task."""
import json
import sys

task = json.load(sys.stdin)
print(json.dumps({"eps_prediction": task["consensus_eps"]}))
