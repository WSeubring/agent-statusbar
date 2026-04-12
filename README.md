# agent-statusbar

Personal status bars for the coding agents I use.

This is a public personal repo, not a general-purpose framework. I keep my own status bar integrations here, publish them so they are easy to reuse, and organize them so each agent can have its own implementation without turning the repo into a mess.

If you want something polished and universal, this probably is not that. If you want practical, hackable status bars you can copy and adapt, that is exactly what this repo is for.

## What this repo contains

Right now the repo has two integrations:

- **Claude Code**: a Python status line renderer that reads JSON payloads
- **pi**: a TypeScript footer extension for pi

Both integrations share the same rough goal:

- show the active model
- show context usage clearly
- optionally show session or weekly quota warnings when available
- keep the output compact enough for day-to-day terminal use

## Personal-repo note

This repo is intentionally opinionated.

It reflects:

- my preferred formatting
- my preferred thresholds and warnings
- the agents I actually use
- the level of abstraction I personally want

So the intended workflow is usually:

1. clone it
2. copy the integration you care about
3. tweak colors, labels, thresholds, or fields

## Repo layout

```text
agent-statusbar/
├── bin/
│   └── agent-statusbar.py              # compatibility entrypoint for Claude
├── integrations/
│   ├── claude/
│   │   ├── README.md
│   │   └── bin/
│   │       └── statusbar.py           # canonical Claude renderer
│   └── pi/
│       ├── README.md
│       └── extensions/
│           └── status-footer.ts       # canonical pi footer extension
└── .pi/
    └── extensions/
        └── pi-status-footer.ts        # auto-discovery shim for local pi use
```

## Quick start

### Claude Code

Run the demo:

```bash
python3 integrations/claude/bin/statusbar.py --demo
```

Compatibility entrypoint:

```bash
python3 bin/agent-statusbar.py --demo
```

The Claude renderer reads JSON from:

1. stdin
2. a file path passed as the first argument
3. `AGENT_STATUSBAR_JSON`

It also still supports the older `CLAUDE_STATUSBAR_*` environment variables.

Useful environment variables:

```bash
AGENT_STATUSBAR_JSON='{"context":{"used_percent":42}}'
AGENT_STATUSBAR_ASCII=1
AGENT_STATUSBAR_BAR_WIDTH=12
AGENT_STATUSBAR_HIDE_MODEL=1
AGENT_STATUSBAR_LABEL=CLAUDE
```

If Claude Code can send status JSON to a command on stdin, point it at one of:

```bash
python3 /absolute/path/to/bin/agent-statusbar.py
python3 /absolute/path/to/integrations/claude/bin/statusbar.py
```

### pi

Inside this repo, pi auto-loads the shim in `.pi/extensions/pi-status-footer.ts`.

If you want to load the integration directly from elsewhere:

```bash
pi -e /absolute/path/to/integrations/pi/extensions/status-footer.ts
```

The pi footer shows:

- model
- context usage with a mini bar
- optional session warning at `50%+`
- optional weekly warning at `75%+`
- git branch
- cumulative input/output tokens
- cumulative cost

pi does not natively expose Claude subscription quotas, so those quota values are optional inputs:

```bash
export PI_STATUS_SESSION_PCT=54
export PI_STATUS_WEEKLY_PCT=81
pi
```

or:

```bash
export PI_STATUS_LIMITS_FILE=/absolute/path/to/limits.json
pi
```

with:

```json
{
  "session": 54,
  "weekly": 81
}
```

## Design goals

- **small and readable** over highly abstract
- **copyable** over packaged
- **good defaults** over endless configuration
- **agent-specific implementations** over forcing everything through one API

## Current naming

The repo uses generic naming at the top level so more integrations can be added later:

- repo: `agent-statusbar`
- Claude implementation: `integrations/claude/bin/statusbar.py`
- pi implementation: `integrations/pi/extensions/status-footer.ts`

The wrapper files stay in place so existing local usage does not break.

## Future additions

Possible future integrations:

- `integrations/codex/`
- `integrations/opencode/`
- `integrations/gemini-cli/`

But this repo will stay personal and practical. I do not plan to turn it into a giant compatibility layer unless there is a real need.

## License

MIT. See `LICENSE`.

## Publishing notes

Suggested GitHub repo description:

**Personal status bars for coding agents**
