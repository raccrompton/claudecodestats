# Expanded Status Line Fields Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grow `statusline.py` from 4 fields to 9, adding repo, git branch, model, lines-changed, and session-duration.

**Architecture:** Each new field is produced by a small pure helper function taking the parsed JSON `data` dict. `main()` assembles helper outputs into a list and prints them joined by two spaces. Every helper degrades to a fallback string on missing/malformed input and never raises.

**Tech Stack:** Python 3 standard library only — `json`, `os`, `re`, `subprocess`, `sys`. No third-party dependencies. Tests are plain `assert` statements, no framework.

---

## File Structure

- `statusline.py` — modified. Gains helpers `_workdir`, `repo`, `branch`, `model`, `diff`, `duration`; `main()` rewired.
- `test_statusline.py` — created. Plain-assert tests + a `__main__` runner that discovers `test_*` functions.
- `README.md` — modified. Example and field table updated to 9 fields.

Helpers are added to `statusline.py` incrementally; an unused helper does not affect the existing `main()`, so each task leaves the script runnable. `main()` is rewired only in the final code task.

---

### Task 1: `repo` helper + test harness

**Files:**
- Modify: `statusline.py`
- Create: `test_statusline.py`

- [ ] **Step 1: Write the failing test**

Create `test_statusline.py`:

```python
#!/usr/bin/env python3
"""Tests for statusline.py — plain asserts, no framework. Run: python3 test_statusline.py"""
import sys

import statusline


def test_repo():
    assert statusline.repo({"workspace": {"current_dir": "/home/u/my-repo"}}) == "my-repo"
    assert statusline.repo({"workspace": {"current_dir": "/home/u/my-repo/"}}) == "my-repo"
    assert statusline.repo({"cwd": "/home/u/other"}) == "other"
    assert statusline.repo({}) == "-"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if failures else 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: FAIL — `AttributeError: module 'statusline' has no attribute 'repo'` (the runner prints the failure and exits non-zero).

- [ ] **Step 3: Write minimal implementation**

In `statusline.py`, add `import os` to the import block (so it reads `import json`, `import os`, `import sys`), and add these functions after `pct`:

```python
def _workdir(data):
    ws = data.get("workspace") or {}
    return ws.get("current_dir") or data.get("cwd")


def repo(data):
    d = _workdir(data)
    return os.path.basename(d.rstrip("/")) if d else "-"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: `PASS test_repo`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add statusline.py test_statusline.py
git commit -m "Add repo field helper and test harness"
```

---

### Task 2: `branch` helper

**Files:**
- Modify: `statusline.py`
- Modify: `test_statusline.py`

- [ ] **Step 1: Write the failing test**

Add to `test_statusline.py` (before the `__main__` block):

```python
def test_branch():
    # Not a git repo -> fallback.
    assert statusline.branch({"cwd": "/"}) == "-"
    # No workdir at all -> fallback.
    assert statusline.branch({}) == "-"
    # This repo's checkout -> a non-empty branch name.
    here = statusline.branch({"cwd": __import__("os").path.dirname(__import__("os").path.abspath(__file__))})
    assert here != "-" and here != ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: FAIL — `AttributeError: module 'statusline' has no attribute 'branch'`.

- [ ] **Step 3: Write minimal implementation**

In `statusline.py`, add `import subprocess` to the import block (keep imports alphabetical: `json`, `os`, `subprocess`, `sys`), and add after `repo`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: `PASS test_branch` (and `PASS test_repo`), exit 0.

- [ ] **Step 5: Commit**

```bash
git add statusline.py test_statusline.py
git commit -m "Add git branch field helper"
```

---

### Task 3: `model` helper

**Files:**
- Modify: `statusline.py`
- Modify: `test_statusline.py`

- [ ] **Step 1: Write the failing test**

Add to `test_statusline.py` (before the `__main__` block):

```python
def test_model():
    assert statusline.model({"model": {"display_name": "Claude Opus 4.7"}}) == "opus-4.7"
    assert statusline.model({"model": {"display_name": "Claude Sonnet 4.6"}}) == "sonnet-4.6"
    # Unparseable -> raw display name returned verbatim.
    assert statusline.model({"model": {"display_name": "Mystery Model"}}) == "Mystery Model"
    # Missing -> fallback.
    assert statusline.model({}) == "-"
    assert statusline.model({"model": {}}) == "-"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: FAIL — `AttributeError: module 'statusline' has no attribute 'model'`.

- [ ] **Step 3: Write minimal implementation**

In `statusline.py`, add `import re` to the import block (alphabetical: `json`, `os`, `re`, `subprocess`, `sys`), and add after `branch`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: `PASS test_model`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add statusline.py test_statusline.py
git commit -m "Add model field helper"
```

---

### Task 4: `diff` helper

**Files:**
- Modify: `statusline.py`
- Modify: `test_statusline.py`

- [ ] **Step 1: Write the failing test**

Add to `test_statusline.py` (before the `__main__` block):

```python
def test_diff():
    assert statusline.diff({"cost": {"total_lines_added": 120, "total_lines_removed": 30}}) == "+120/-30"
    assert statusline.diff({"cost": {}}) == "+0/-0"
    assert statusline.diff({}) == "+0/-0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: FAIL — `AttributeError: module 'statusline' has no attribute 'diff'`.

- [ ] **Step 3: Write minimal implementation**

In `statusline.py`, add after `model`:

```python
def diff(data):
    cost = data.get("cost") or {}
    added = cost.get("total_lines_added", 0) or 0
    removed = cost.get("total_lines_removed", 0) or 0
    return f"+{added}/-{removed}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: `PASS test_diff`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add statusline.py test_statusline.py
git commit -m "Add lines-changed field helper"
```

---

### Task 5: `duration` helper

**Files:**
- Modify: `statusline.py`
- Modify: `test_statusline.py`

- [ ] **Step 1: Write the failing test**

Add to `test_statusline.py` (before the `__main__` block):

```python
def test_duration():
    assert statusline.duration({"cost": {"total_duration_ms": 12 * 60000}}) == "12m"
    assert statusline.duration({"cost": {"total_duration_ms": 64 * 60000}}) == "1h4m"
    # Sub-minute rounds down to 0m.
    assert statusline.duration({"cost": {"total_duration_ms": 5000}}) == "0m"
    assert statusline.duration({"cost": {}}) == "0m"
    assert statusline.duration({}) == "0m"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: FAIL — `AttributeError: module 'statusline' has no attribute 'duration'`.

- [ ] **Step 3: Write minimal implementation**

In `statusline.py`, add after `diff`:

```python
def duration(data):
    ms = (data.get("cost") or {}).get("total_duration_ms", 0) or 0
    minutes = int(ms // 60000)
    h, m = divmod(minutes, 60)
    return f"{h}h{m}m" if h else f"{m}m"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: `PASS test_duration`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add statusline.py test_statusline.py
git commit -m "Add session duration field helper"
```

---

### Task 6: Rewire `main()` to assemble all 9 fields

**Files:**
- Modify: `statusline.py`
- Modify: `test_statusline.py`

- [ ] **Step 1: Write the failing test**

Add to `test_statusline.py` (before the `__main__` block):

```python
def test_main_end_to_end():
    import io
    import json

    payload = {
        "workspace": {"current_dir": "/home/u/my-repo"},
        "model": {"display_name": "Claude Opus 4.7"},
        "cost": {
            "total_cost_usd": 0.42,
            "total_lines_added": 120,
            "total_lines_removed": 30,
            "total_duration_ms": 64 * 60000,
        },
        "context_window": {"used_percentage": 37},
        "rate_limits": {
            "five_hour": {"used_percentage": 24},
            "seven_day": {"used_percentage": 11},
        },
    }
    old_stdin, old_stdout = sys.stdin, sys.stdout
    sys.stdin = io.StringIO(json.dumps(payload))
    sys.stdout = io.StringIO()
    try:
        statusline.main()
        line = sys.stdout.getvalue().strip()
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout
    fields = line.split("  ")
    assert fields[0] == "my-repo", fields
    assert fields[2] == "opus-4.7", fields
    assert fields[3] == "cost:$0.42", fields
    assert fields[4] == "ctx:37%", fields
    assert fields[5] == "+120/-30", fields
    assert fields[6] == "1h4m", fields
    assert fields[7] == "5h:24%", fields
    assert fields[8] == "wk:11%", fields
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: FAIL — `test_main_end_to_end` fails because the current `main()` prints only 4 fields, so `fields[0]` is `cost:$0.42`, not `my-repo`.

- [ ] **Step 3: Write minimal implementation**

Replace the entire `main()` function in `statusline.py` with:

```python
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
```

Also update the module docstring on line 2 to:

```python
"""Compact Claude Code status line: identity, cost, context, diff, and rate-limit usage."""
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `cd /home/alex/github/claudecodestats && python3 test_statusline.py`
Expected: all six tests print `PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add statusline.py test_statusline.py
git commit -m "Assemble all 9 fields in main()"
```

---

### Task 7: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the example and field table**

In `README.md`, replace the example block:

```
cost:$0.42  ctx:37%  5h:24%  wk:11%
```

with:

```
my-repo  main  opus-4.7  cost:$0.42  ctx:37%  +120/-30  1h4m  5h:24%  wk:11%
```

Replace the entire field table with:

```markdown
| Field | Meaning |
| --- | --- |
| `my-repo` | Working directory / repo name |
| `main` | Current git branch (`-` outside a repo) |
| `opus-4.7` | Active model |
| `cost:$0.42` | Total cost of the current session, USD |
| `ctx:37%` | Context window used |
| `+120/-30` | Lines added / removed this session |
| `1h4m` | Session duration |
| `5h:24%` | Share of the rolling 5-hour rate limit consumed |
| `wk:11%` | Share of the rolling 7-day rate limit consumed |
```

Update the sentence above "## Install" — the line `four numbers I actually care about` becomes `numbers I actually care about` (no longer four).

- [ ] **Step 2: Verify the change**

Run: `cd /home/alex/github/claudecodestats && grep -c "opus-4.7" README.md`
Expected: `2` (one in the example block, one in the table).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Update README for 9-field status line"
```

---

### Task 8: Deploy the updated script locally

**Files:**
- None in repo — copies the script to the live location.

- [ ] **Step 1: Copy the script to the installed location**

Run: `cp /home/alex/github/claudecodestats/statusline.py /home/alex/.claude/statusline.py && chmod +x /home/alex/.claude/statusline.py`
Expected: no output, exit 0.

- [ ] **Step 2: Verify the live status line renders 9 fields**

Run:

```bash
echo '{"workspace":{"current_dir":"/home/u/my-repo"},"model":{"display_name":"Claude Opus 4.7"},"cost":{"total_cost_usd":0.42,"total_lines_added":120,"total_lines_removed":30,"total_duration_ms":3840000},"context_window":{"used_percentage":37},"rate_limits":{"five_hour":{"used_percentage":24},"seven_day":{"used_percentage":11}}}' | python3 /home/alex/.claude/statusline.py
```

Expected: `my-repo  main  opus-4.7  cost:$0.42  ctx:37%  +120/-30  1h4m  5h:24%  wk:11%`

No commit — this step modifies a file outside the repo.

---

## Self-Review

**Spec coverage:** All 9 fields (repo, branch, model, cost, ctx, diff, duration, 5h, wk) — Tasks 1–6. Helper-per-field structure — Tasks 1–5. Independent error guards — each helper's fallback path tested. `test_statusline.py` plain-assert harness — Task 1. README update — Task 7. Local deploy (the copy step from the spec's deployment context) — Task 8. 200k warning, conditional hiding, ANSI color — correctly absent (out of scope).

**Placeholder scan:** No TBD/TODO; every code step shows complete code; every command shows expected output.

**Type consistency:** `_workdir` defined in Task 1, reused by `branch` in Task 2. Helper names `repo`/`branch`/`model`/`diff`/`duration` match between definitions and the `main()` assembly in Task 6. `pct` is the pre-existing helper, left intact.
