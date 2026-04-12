# Status bar feature reference

Small reference for this repo.

This file is intended as **context for LLMs and future edits** so we have a shared idea of what the status bar/footer should support across integrations.

## Goal

Provide a compact, readable status surface for coding agents that shows the most important session state at a glance.

## Core support targets

These are the main features we want to support when the host agent exposes the data.

### 1. Agent label
- Examples: `CLAUDE`, `PI`
- Should be easy to customize per integration

### 2. Active model
- Show the current model name
- Prefer human-friendly display names over raw IDs when available

### 3. Thinking / effort / reasoning level
- Show for reasoning-capable models
- Examples:
  - `Claude Sonnet 4 (high)`
  - `GPT-4.5 (high)`
- If the agent does not expose this cleanly, omit it rather than guessing badly

### 4. Context usage
- Show current context usage percent
- Prefer a compact bar + percent
- If token count is available, include it
- Examples:
  - `ctx █████░░░ 68%`
  - `ctx █████░░░ 68% 143.2k`

### 5. Quota / limit warnings
- Session usage if available
- Weekly usage if available
- These are optional and should degrade gracefully
- Thresholds can be integration-specific, but warnings should become visually stronger as usage rises

### 6. Usage totals
If available from the host:
- cumulative input tokens
- cumulative output tokens
- cumulative cost

### 7. Working location
Show on a second line when possible:
- current directory name
- git branch

Example:

```text
agent-statusbar (main)
```

If no branch is available:

```text
agent-statusbar
```

## Display expectations

### Compactness
- Optimize for everyday terminal use
- Keep the first line focused on model + context + limits + totals
- Put location on the second line

### Graceful degradation
- Missing data should not break rendering
- Omit unavailable fields cleanly
- Prefer partial output over failure

### Readability
- Important warnings should stand out
- Normal state should stay visually quiet
- Avoid noisy formatting or excessive decoration

### Portability
- Support color when available
- Support ASCII fallback where practical
- Avoid hard dependencies on one shell theme or font

## Current repo-level feature shape

### Claude integration
Current/expected support:
- label
- model
- context percent + bar
- session quota if present in payload
- weekly quota if present in payload
- second line with `dir (branch)`

Nice-to-have if Claude exposes it later:
- effort in the rendered model label
- token totals
- cost totals

### pi integration
Current/expected support:
- label
- model
- thinking level
- context percent + bar + token count
- optional session quota
- optional weekly quota
- cumulative input tokens
- cumulative output tokens
- cumulative cost
- second line with `dir (branch)`

## Prioritization order

When space or data is limited, prefer this order:

1. label
2. model
3. thinking / effort
4. context usage
5. session / weekly warnings
6. token / cost totals
7. location line

## Non-goals

This repo is **not** trying to define:
- a universal status bar spec for all agents
- a strict shared API across integrations
- pixel-perfect consistency between agents

Each integration should stay native to its host, while aiming for the same overall information architecture.

## Guidance for LLMs editing this repo

When changing an integration:
- preserve compactness
- prefer native host data over invented state
- keep optional fields optional
- do not fail hard on missing metrics
- keep the feature set aligned with this file unless the user asks otherwise
