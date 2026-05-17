#!/usr/bin/env python3
"""Compact Claude Code status line: cost, context, and rate-limit usage."""
import json
import os
import sys


def pct(value):
    return f"{value:.0f}%" if isinstance(value, (int, float)) else "-"


def _workdir(data):
    ws = data.get("workspace") or {}
    return ws.get("current_dir") or data.get("cwd")


def repo(data):
    d = _workdir(data)
    return os.path.basename(d.rstrip("/")) if d else "-"


def main():
    data = json.load(sys.stdin)

    cost = data.get("cost", {}).get("total_cost_usd", 0)
    ctx = data.get("context_window", {}).get("used_percentage", 0)
    limits = data.get("rate_limits") or {}
    five_hour = (limits.get("five_hour") or {}).get("used_percentage")
    seven_day = (limits.get("seven_day") or {}).get("used_percentage")

    parts = [
        f"cost:${cost:.2f}",
        f"ctx:{ctx}%",
        f"5h:{pct(five_hour)}",
        f"wk:{pct(seven_day)}",
    ]
    print("  ".join(parts))


if __name__ == "__main__":
    main()
