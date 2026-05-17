# Design: expand `statusline.py` to 9 fields

**Date:** 2026-05-16
**Status:** Approved

## Goal

Grow the Claude Code status line from 4 fields to 9, adding session identity
and progress information. Keep the script single-file and dependency-free.

## Output format

```
my-repo  main  opus-4.7  cost:$0.42  ctx:37%  +120/-30  1h4m  5h:24%  wk:11%
```

Fields are ordered identity-first (stable left side: where you are) then
volatile session metrics, then rate limits. All 9 fields render on every
refresh — none are conditionally hidden. Fields are joined by two spaces.

## Fields

| Field | Source (stdin JSON unless noted) | Format | Fallback |
|---|---|---|---|
| repo | `workspace.current_dir` basename, then `cwd` basename | bare name | `-` |
| branch | `git -C <dir> rev-parse --abbrev-ref HEAD` (subprocess) | bare name | `-` if not a repo / git missing / error |
| model | `model.display_name`, parsed | `opus-4.7` (tier + version) | raw `display_name`, then `-` |
| cost | `cost.total_cost_usd` | `cost:$0.42` | `cost:$0.00` |
| ctx | `context_window.used_percentage` | `ctx:37%` | `ctx:0%` |
| diff | `cost.total_lines_added` / `cost.total_lines_removed` | `+120/-30` | `+0/-0` |
| duration | `cost.total_duration_ms` | `1h4m`, or `12m` under an hour | `0m` |
| 5h | `rate_limits.five_hour.used_percentage` | `5h:24%` (unchanged) | `5h:-` |
| wk | `rate_limits.seven_day.used_percentage` | `wk:11%` (unchanged) | `wk:-` |

## Implementation

Single file, no third-party dependencies. One new stdlib import:
`subprocess`. Grows from ~30 to ~70 lines.

Each field is produced by its own small helper that takes the parsed `data`
dict and returns a formatted string. `main()` reads stdin, then assembles the
list of helper outputs and prints them joined by two spaces.

Helpers:

- `repo(data)` — basename of `workspace.current_dir`, falling back to `cwd`;
  `-` if neither present.
- `branch(data)` — runs `git -C <workspace dir> rev-parse --abbrev-ref HEAD`
  via `subprocess.run(..., capture_output=True, text=True, timeout=1)`. The
  directory is `workspace.current_dir` (fall back to `cwd`). On non-zero exit,
  timeout, or any exception → `-`. `rev-parse` is sub-millisecond, so running
  it on every refresh is acceptable.
- `model(data)` — reads `model.display_name`, lowercases it, extracts the tier
  word (`opus` / `sonnet` / `haiku`) and the first `X.Y` version number, and
  joins them as `tier-version`. If the tier or version cannot be found, returns
  the raw `display_name`; if that is also absent, `-`.
- `diff(data)` — `+{added}/-{removed}` from `cost.total_lines_added` and
  `cost.total_lines_removed`, both defaulting to 0.
- `duration(data)` — converts `cost.total_duration_ms` to whole minutes;
  renders `{h}h{m}m` when an hour or more, else `{m}m`. Seconds are dropped.
  Missing/zero → `0m`.

The existing `pct()` helper and the cost/ctx formatting are retained.

## Error handling

Every field is independently guarded. A missing JSON key, malformed value, or
git failure degrades that single field to its fallback — it never raises and
never aborts the line. `main()` performs no field logic itself, so one bad
field cannot affect the others.

## Testing

The repo currently has no tests. Add `test_statusline.py`: plain `assert`
statements, no test framework (preserves the dependency-free constraint), run
with `python3 test_statusline.py`. Coverage:

- each helper's normal formatting path with representative JSON
- each helper's fallback path (missing keys, empty dict)
- `model()` parsing: full display name, unparseable string, missing
- `duration()`: under an hour, over an hour, zero
- one end-to-end `main()` check via captured stdout

`branch()` is tested for its fallback path (a directory that is not a git
repo); the success path is left to manual verification since it depends on
the ambient git state.

## Documentation

Update `README.md`: replace the 4-field example and field table with the
9-field versions.

## Out of scope

- The 200k-token-context warning field (`exceeds_200k_tokens`) — explicitly
  declined.
- Conditional hiding of empty fields.
- ANSI color.
