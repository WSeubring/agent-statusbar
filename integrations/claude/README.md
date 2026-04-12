# Claude Code integration

Python status line renderer for Claude-style JSON payloads.

This is the Claude-specific implementation used by this repo. It is small, standalone, and easy to adapt if you want different labels, thresholds, colors, or field selection.

## File

- `bin/statusbar.py` — canonical Claude renderer

## Quick run

```bash
python3 integrations/claude/bin/statusbar.py --demo
```

Compatibility entrypoint from the repo root:

```bash
python3 bin/agent-statusbar.py --demo
```

## Inputs

The renderer reads status JSON from, in order:

1. a file path passed as the first argument
2. stdin
3. `AGENT_STATUSBAR_JSON`
4. `CLAUDE_STATUSBAR_JSON`

It also supports both env var prefixes for compatibility:

- `AGENT_STATUSBAR_*`
- `CLAUDE_STATUSBAR_*`

## Useful environment variables

```bash
AGENT_STATUSBAR_ASCII=1
AGENT_STATUSBAR_BAR_WIDTH=12
AGENT_STATUSBAR_HIDE_MODEL=1
AGENT_STATUSBAR_LABEL=CLAUDE
```

Example:

```bash
AGENT_STATUSBAR_JSON='{"model":{"display_name":"Claude Sonnet 4"},"context":{"used_percent":42}}' \
python3 integrations/claude/bin/statusbar.py
```

## Demo output

```text
 AGENT │ Claude Sonnet 4 │ ◔ ctx ███████░░░ 68% │ ▲ session 54% │ ▲ weekly 81%
```

## Notes

- The renderer tries to find model, context, session, and weekly usage heuristically from nested JSON.
- If data is missing, the output degrades gracefully instead of failing hard.
- The top-level `bin/agent-statusbar.py` file is only a compatibility wrapper.
