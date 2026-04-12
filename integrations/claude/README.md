# Claude integration

Files specific to Claude Code.

## Files

- `bin/statusbar.py` — status line renderer for Claude-style JSON payloads

## Run

```bash
python3 integrations/claude/bin/statusbar.py --demo
```

## Notes

The renderer still supports both:

- `AGENT_STATUSBAR_*`
- `CLAUDE_STATUSBAR_*`

so older setups continue to work while the repo becomes more generic.
