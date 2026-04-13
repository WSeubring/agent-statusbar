# agent-statusbar

[![License: MIT](https://img.shields.io/github/license/WSeubring/agent-statusbar)](LICENSE)
![Scope: personal](https://img.shields.io/badge/scope-personal-blue)
![Status: active](https://img.shields.io/badge/status-active-success)

Personal status bars for the coding agents I use.

> Public repo, personal project.
> 
> This is where I keep the status bar integrations I actually run, tweak, and maintain for myself. It is meant to be readable and copyable, not a giant universal framework.

## Screenshot

<img width="1241" height="101" alt="image" src="https://github.com/user-attachments/assets/ab342828-9b49-4286-b247-40c49f734bff" />


A clean demo-style screenshot for the current integrations. It is representative rather than a literal live terminal capture.

## What it is

This repo currently contains two small, agent-specific integrations:

- [Claude Code](integrations/claude/README.md): a Python status line renderer that reads JSON payloads
- [pi](integrations/pi/README.md): a TypeScript footer extension for pi

Shared goals:

- show the active model
- show context usage clearly
- optionally show session or weekly quota warnings when available
- stay compact enough for everyday terminal use

Feature reference for future edits and LLM context:
- [STATUSBAR_FEATURES.md](STATUSBAR_FEATURES.md)

## What it is not

This repo is **not** trying to be:

- a generic status bar framework
- a packaged multi-agent SDK
- a one-config-fits-all solution

It is intentionally opinionated and personal. The expected workflow is:

1. clone it
2. use the integration you care about
3. tweak the formatting, labels, thresholds, or fields to match your own setup

## Demo output

### Claude Code

Example output from `python3 integrations/claude/bin/statusbar.py --demo`:

```text
 CLAUDE │ Claude Sonnet 4 │ ◔ ctx ███████░░░ 68% │ ▲ session 54% │ ▲ weekly 81%
agent-statusbar (main)
```

### pi

Representative footer output:

```text
PI │ Claude Sonnet 4 (high) │ ctx █████░░░ 68% 143.2k │ session 54% │ weekly 81%    in 512.4k │ out 38.1k │ $2.173
agent-statusbar (main)
```

Exact colors, spacing, token counts, and branch display depend on your terminal, theme, model, and active session.

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

The renderer reads JSON from:

1. a file path passed as the first argument
2. stdin
3. `AGENT_STATUSBAR_JSON`

It also supports the older `CLAUDE_STATUSBAR_*` environment variables for compatibility.

Useful environment variables:

```bash
AGENT_STATUSBAR_JSON='{"context":{"used_percent":42}}'
AGENT_STATUSBAR_ASCII=1
AGENT_STATUSBAR_BAR_WIDTH=12
AGENT_STATUSBAR_HIDE_MODEL=1
AGENT_STATUSBAR_LABEL=CLAUDE
```

Add this to `~/.claude/settings.json` to enable it in Claude Code:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 /absolute/path/to/integrations/claude/bin/statusbar.py",
    "refreshInterval": 5
  }
}
```

The Claude renderer also shows the current directory and git branch on a second line.

More details: [integrations/claude/README.md](integrations/claude/README.md)

### pi

Inside this repo, pi auto-loads the shim in `.pi/extensions/pi-status-footer.ts`.

To install the integration globally for your pi agent:

```bash
pi install git:github.com/WSeubring/agent-statusbar
```

To install it only for the current project, use local mode:

```bash
pi install git:github.com/WSeubring/agent-statusbar -l
```

The pi footer shows:

- model with thinking level for reasoning-capable models
- context usage with a mini bar
- optional session warning at `50%+`
- optional weekly warning at `75%+`
- current directory with git branch on a second line
- cumulative input/output tokens
- cumulative cost

Optional quota inputs:

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

More details: [integrations/pi/README.md](integrations/pi/README.md)

## Design choices

This repo prefers:

- **small and readable** over abstract
- **copyable source** over packaging
- **good defaults** over endless configuration
- **agent-specific implementations** over forcing everything through one API

## Naming

Top-level naming is generic so I can add more integrations later without renaming the whole repo:

- repo: `agent-statusbar`
- Claude implementation: `integrations/claude/bin/statusbar.py`
- pi implementation: `integrations/pi/extensions/status-footer.ts`

Compatibility wrappers stay in place so my local usage does not break when files move.

## Possible future integrations

Maybe, if I end up using them enough:

- `integrations/codex/`
- `integrations/opencode/`
- `integrations/gemini-cli/`

## License

MIT. See [LICENSE](LICENSE).
