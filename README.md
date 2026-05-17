# claudecodestats

A tiny, no-dependencies status line for [Claude Code](https://claude.com/claude-code) that shows the four numbers I actually care about during a session:

```
cost:$0.42  ctx:37%  5h:24%  wk:11%
```

| Field | Meaning |
| --- | --- |
| `cost:$0.42` | Total cost of the current session, USD |
| `ctx:37%` | Context window used |
| `5h:24%` | Share of the rolling 5-hour rate limit consumed |
| `wk:11%` | Share of the rolling 7-day rate limit consumed |

Rate-limit fields fall back to `-` when Claude Code hasn't reported them yet (e.g. fresh sessions, or accounts/plans where they're not surfaced).

## Install

1. Drop `statusline.py` somewhere stable, e.g. `~/.claude/statusline.py`:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/raccrompton/claudecodestats/main/statusline.py \
     -o ~/.claude/statusline.py
   chmod +x ~/.claude/statusline.py
   ```

2. Point Claude Code at it. In `~/.claude/settings.json`:

   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "python3 ~/.claude/statusline.py"
     }
   }
   ```

3. Restart Claude Code (or `/config` reload). That's it — no dependencies beyond Python 3.

## How it works

Claude Code pipes a JSON blob describing the current session to the configured `statusLine.command` on every refresh. The script reads stdin, pulls out four fields, formats one line, and prints it. Full input schema lives in the [Claude Code docs](https://docs.claude.com/en/docs/claude-code/statusline).

## Customise

The script is ~20 lines — fork it, change the format string, add git branch / model name / whatever. PRs welcome for genuinely useful additions; please keep it dependency-free.

## License

MIT — see [LICENSE](LICENSE).
