# pi integration

TypeScript footer extension for pi.

This is the pi-specific implementation used by this repo. It focuses on a compact footer with the session information I care about most during normal terminal use.

## File

- `extensions/status-footer.ts` — canonical pi footer extension

## How to load it

Inside this repo, pi auto-loads the shim in `.pi/extensions/pi-status-footer.ts`.

To load the extension directly from somewhere else:

```bash
pi -e /absolute/path/to/integrations/pi/extensions/status-footer.ts
```

## What it shows

- model
- context usage with a mini bar
- optional session quota warning
- optional weekly quota warning
- cumulative input tokens
- cumulative output tokens
- cumulative cost
- current git branch

## Optional quota inputs

pi does not natively expose Claude subscription quota data, so session and weekly percentages are optional inputs.

### Environment variables

```bash
export PI_STATUS_SESSION_PCT=54
export PI_STATUS_WEEKLY_PCT=81
pi
```

### JSON file

```bash
export PI_STATUS_LIMITS_FILE=/absolute/path/to/limits.json
pi
```

Example file contents:

```json
{
  "session": 54,
  "weekly": 81
}
```

## Demo output

Representative footer output:

```text
PI │ Claude Sonnet 4 │ ctx █████░░░ 68% 143.2k │ session 54% │ weekly 81%    in 512.4k │ out 38.1k │ $2.173 │  main
```

Exact styling depends on your pi theme, terminal font, branch name, and live session stats.

## Notes

- The footer uses native pi APIs for context usage, git branch, and cumulative session usage.
- Quota values are intentionally optional and injected from env vars or a small JSON file.
- The `.pi/extensions/pi-status-footer.ts` file is only an auto-discovery shim.
