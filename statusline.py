#!/usr/bin/env python3
"""Compact Claude Code status line: identity, cost, context, diff, and rate-limit usage."""
import json
import os
import re
import subprocess
import sys


def pct(value):
    return f"{value:.0f}%" if isinstance(value, (int, float)) else "-"


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _workdir(data):
    ws = data.get("workspace") or {}
    return ws.get("current_dir") or data.get("cwd")


def repo(data):
    d = _workdir(data)
    if not d:
        return "-"
    return os.path.basename(d.rstrip("/")) or "-"


def branch(data):
    d = _workdir(data)
    if not d:
        return "-"
    try:
        result = subprocess.run(
            ["git", "-C", d, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1,
        )
    except Exception:
        return "-"
    if result.returncode != 0:
        return "-"
    return result.stdout.strip() or "-"


def model(data):
    name = (data.get("model") or {}).get("display_name")
    if not name:
        return "-"
    low = name.lower()
    tier = next((t for t in ("opus", "sonnet", "haiku") if t in low), None)
    version = re.search(r"\d+\.\d+", low)
    if tier and version:
        return f"{tier}-{version.group()}"
    return name


def diff(data):
    cost = data.get("cost") or {}
    added = _int(cost.get("total_lines_added"))
    removed = _int(cost.get("total_lines_removed"))
    return f"+{added}/-{removed}"


def duration(data):
    ms = _int((data.get("cost") or {}).get("total_duration_ms"))
    minutes = ms // 60000
    h, m = divmod(minutes, 60)
    return f"{h}h{m}m" if h else f"{m}m"


def main():
    data = json.load(sys.stdin)

    cost = (data.get("cost") or {}).get("total_cost_usd", 0) or 0
    ctx = (data.get("context_window") or {}).get("used_percentage", 0) or 0
    limits = data.get("rate_limits") or {}
    five_hour = (limits.get("five_hour") or {}).get("used_percentage")
    seven_day = (limits.get("seven_day") or {}).get("used_percentage")

    parts = [
        repo(data),
        branch(data),
        model(data),
        f"cost:${cost:.2f}",
        f"ctx:{ctx}%",
        diff(data),
        duration(data),
        f"5h:{pct(five_hour)}",
        f"wk:{pct(seven_day)}",
    ]
    print("  ".join(parts))


if __name__ == "__main__":
    main()
