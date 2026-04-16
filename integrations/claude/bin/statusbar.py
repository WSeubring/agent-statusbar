#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Metrics:
    model: str | None = None
    context_pct: float | None = None
    five_hour_pct: float | None = None
    seven_day_pct: float | None = None
    extra_usage: bool = False


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

FG = {
    "slate": "\033[38;5;245m",
    "muted": "\033[38;5;242m",
    "violet": "\033[38;5;141m",
    "cyan": "\033[38;5;117m",
    "blue": "\033[38;5;75m",
    "green": "\033[38;5;78m",
    "amber": "\033[38;5;221m",
    "orange": "\033[38;5;215m",
    "red": "\033[38;5;203m",
    "pink": "\033[38;5;212m",
    "white": "\033[38;5;255m",
}

BG = {
    "panel": "\033[48;5;236m",
    "violet": "\033[48;5;60m",
    "blue": "\033[48;5;24m",
    "green": "\033[48;5;28m",
    "amber": "\033[48;5;94m",
    "red": "\033[48;5;88m",
    "neutral": "\033[48;5;238m",
}


def env_value(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return default


def env_flag(*names: str, default: bool = False) -> bool:
    value = env_value(*names)
    if value is None:
        return default
    return value.lower() not in {"0", "false", "no", "off", ""}


USE_COLOR = not env_flag("NO_COLOR", default=False)
USE_UNICODE = not env_flag("AGENT_STATUSBAR_ASCII", "CLAUDE_STATUSBAR_ASCII", default=False)
BAR_WIDTH = max(4, min(16, int(env_value("AGENT_STATUSBAR_BAR_WIDTH", "CLAUDE_STATUSBAR_BAR_WIDTH", default="10"))))
SHOW_MODEL = not env_flag("AGENT_STATUSBAR_HIDE_MODEL", "CLAUDE_STATUSBAR_HIDE_MODEL", default=False)
APP_LABEL = env_value("AGENT_STATUSBAR_LABEL", "CLAUDE_STATUSBAR_LABEL", default="CLAUDE") or "CLAUDE"


def style(text: str, *codes: str) -> str:
    if not USE_COLOR or not codes:
        return text
    return "".join(codes) + text + RESET


def flatten(obj: Any, prefix: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            next_prefix = prefix + (str(key),)
            yield next_prefix, value
            yield from flatten(value, next_prefix)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            next_prefix = prefix + (str(index),)
            yield next_prefix, value
            yield from flatten(value, next_prefix)


def parse_percentage(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if 0 <= number <= 1:
            return number * 100
        if 0 <= number <= 100:
            return number
        return None
    if isinstance(value, str):
        match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", value)
        if match:
            return float(match.group(1))
        try:
            number = float(value.strip())
        except ValueError:
            return None
        if 0 <= number <= 1:
            return number * 100
        if 0 <= number <= 100:
            return number
    return None


def clamp_pct(value: float | None) -> float | None:
    if value is None:
        return None
    return max(0.0, min(100.0, value))


def looks_like_model(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip().lower()
    return any(token in text for token in ["claude", "sonnet", "opus", "haiku", "gpt", "gemini"])


def best_match(flat: list[tuple[tuple[str, ...], Any]], groups: list[tuple[int, tuple[str, ...], tuple[str, ...]]]) -> float | None:
    candidates: list[tuple[int, float]] = []
    for path, value in flat:
        path_text = ".".join(path).lower()
        if any(skip in path_text for skip in ["remaining", "reset", "max", "available"]):
            continue
        percent = parse_percentage(value)
        if percent is None:
            continue
        score = 0
        for points, required, optional in groups:
            if all(token in path_text for token in required):
                score = max(score, points + sum(1 for token in optional if token in path_text))
        if score:
            candidates.append((score, percent))
    if not candidates:
        return None
    return clamp_pct(sorted(candidates, key=lambda item: item[0], reverse=True)[0][1])


def find_model(flat: list[tuple[tuple[str, ...], Any]]) -> str | None:
    preferred: list[tuple[int, str]] = []
    for path, value in flat:
        if not looks_like_model(value):
            continue
        path_text = ".".join(path).lower()
        score = 0
        if any(token in path_text for token in ["model.display_name", "model.name", "model.id"]):
            score += 6
        if "model" in path_text:
            score += 4
        if any(token in path_text for token in ["display", "name", "id"]):
            score += 2
        preferred.append((score, str(value).strip()))
    if not preferred:
        return None
    return sorted(preferred, key=lambda item: item[0], reverse=True)[0][1]


def find_extra_usage(flat: list[tuple[tuple[str, ...], Any]]) -> bool:
    """Detect extra-usage mode from payload signals.

    Checks for:
    - explicit boolean fields: extra_usage, extra_usage_active, over_limit, is_extra
    - billing.mode == "extra_usage"
    - rate-limit percentages at or above 100%
    """
    extra_keywords = {"extra_usage", "extra_usage_active", "over_limit", "is_extra", "is_over_limit", "overage"}
    for path, value in flat:
        path_text = ".".join(path).lower()
        key = path[-1].lower() if path else ""

        # explicit boolean flag
        if key in extra_keywords and isinstance(value, bool) and value:
            return True

        # string field containing "extra" in a billing/mode context
        if isinstance(value, str) and "extra" in value.lower():
            if any(tok in path_text for tok in ["billing", "mode", "usage", "plan"]):
                return True

        # rate-limit percentage >= 100 means quota exhausted → extra usage
        if any(tok in path_text for tok in ["rate_limit", "five_hour", "seven_day"]):
            if any(tok in path_text for tok in ["used", "percent", "usage"]):
                pct = parse_percentage(value)
                if pct is not None and pct >= 100:
                    return True

    return False


def extract_metrics(payload: Any) -> Metrics:
    flat = list(flatten(payload))
    return Metrics(
        model=find_model(flat),
        context_pct=best_match(
            flat,
            [
                (12, ("context",), ("percent", "percentage", "usage", "used", "window")),
                (10, ("contextwindow",), ("percent", "usage", "used")),
                (8, ("token", "context"), ("percent", "usage", "used")),
            ],
        ),
        five_hour_pct=best_match(
            flat,
            [
                (16, ("five_hour",), ("percent", "percentage", "used")),
                (14, ("rate_limit", "five_hour"), ("percent", "percentage", "used")),
                (12, ("session",), ("percent", "percentage", "usage", "used")),
                (10, ("limit", "session"), ("percent", "usage", "used")),
                (10, ("quota", "session"), ("percent", "usage", "used")),
            ],
        ),
        seven_day_pct=best_match(
            flat,
            [
                (16, ("seven_day",), ("percent", "percentage", "used")),
                (14, ("rate_limit", "seven_day"), ("percent", "percentage", "used")),
                (14, ("weekly",), ("percent", "percentage", "usage", "used")),
                (12, ("week",), ("percent", "percentage", "usage", "used")),
                (10, ("limit", "weekly"), ("percent", "usage", "used")),
                (10, ("quota", "weekly"), ("percent", "usage", "used")),
            ],
        ),
        extra_usage=find_extra_usage(flat),
    )


def pill(text: str, fg: str, bg: str | None = None, *, bold: bool = True) -> str:
    codes = [code for code in [bg, fg, BOLD if bold else ""] if code]
    return style(f" {text} ", *codes)


def muted(text: str) -> str:
    return style(text, FG["muted"], DIM)


def severity_color(value: float | None, warn: float, high: float = 90) -> str:
    if value is None:
        return FG["slate"]
    if value >= high:
        return FG["red"]
    if value >= warn:
        return FG["amber"]
    if value >= warn * 0.7:
        return FG["green"]
    return FG["cyan"]


def context_color(value: float | None) -> str:
    if value is None:
        return FG["slate"]
    if value >= 90:
        return FG["red"]
    if value >= 75:
        return FG["orange"]
    if value >= 55:
        return FG["amber"]
    return FG["green"]


def format_pct(value: float | None) -> str:
    if value is None:
        return "--"
    rounded = round(value)
    return f"{rounded}%"


def bar(value: float | None, width: int = BAR_WIDTH) -> str:
    if value is None:
        empty = "-" * width if not USE_UNICODE else "░" * width
        return muted(empty)

    filled = round((value / 100) * width)
    filled = max(0, min(width, filled))
    if USE_UNICODE:
        fill_char = "█"
        empty_char = "░"
    else:
        fill_char = "#"
        empty_char = "-"
    color = context_color(value)
    return style(fill_char * filled, color, BOLD) + muted(empty_char * (width - filled))


def location_line(cwd: Path | None = None) -> str | None:
    cwd = cwd or Path.cwd()
    cwd_name = cwd.name or str(cwd)

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=0.3,
            check=False,
        )
        branch = result.stdout.strip()
        if result.returncode == 0 and branch and branch != "HEAD":
            return muted(f"{cwd_name} ({branch})")
    except Exception:
        pass

    return muted(cwd_name)


def build_status_line(metrics: Metrics) -> str:
    parts: list[str] = []
    parts.append(pill(APP_LABEL, FG["white"], BG["violet"]))

    if metrics.extra_usage:
        icon = "⚡" if USE_UNICODE else "$"
        parts.append(pill(f"{icon} EXTRA USAGE", FG["white"], BG["red"]))

    if SHOW_MODEL and metrics.model:
        parts.append(pill(metrics.model, FG["white"], BG["blue"], bold=False))

    context_value = format_pct(metrics.context_pct)
    context_seg = " ".join(
        [
            style("◔", context_color(metrics.context_pct), BOLD) if USE_UNICODE else style("CTX", FG["green"], BOLD),
            style("ctx", FG["slate"], BOLD),
            bar(metrics.context_pct),
            style(context_value, context_color(metrics.context_pct), BOLD),
        ]
    )
    parts.append(context_seg)

    if metrics.five_hour_pct is not None:
        if metrics.five_hour_pct >= 50:
            icon = "▲"
            label = f"{icon} 5h {format_pct(metrics.five_hour_pct)}"
            parts.append(pill(label, FG["white"], BG["amber"], bold=False))
        else:
            label = f"• 5h {format_pct(metrics.five_hour_pct)}"
            parts.append(muted(label))

    if metrics.seven_day_pct is not None:
        if metrics.seven_day_pct >= 90:
            label = f"▲ 7d {format_pct(metrics.seven_day_pct)}"
            parts.append(pill(label, FG["white"], BG["red"], bold=False))
        elif metrics.seven_day_pct >= 75:
            label = f"▲ 7d {format_pct(metrics.seven_day_pct)}"
            parts.append(pill(label, FG["white"], BG["amber"], bold=False))
        elif metrics.seven_day_pct >= 50:
            label = f"• 7d {format_pct(metrics.seven_day_pct)}"
            parts.append(style(label, FG["amber"]))
        else:
            label = f"• 7d {format_pct(metrics.seven_day_pct)}"
            parts.append(muted(label))

    separator = muted(" │ ")
    top = separator.join(parts)
    bottom = location_line()
    if bottom:
        return f"{top}\n{bottom}"
    return top


DEMO_PAYLOAD = {
    "model": {"display_name": "Claude Sonnet 4"},
    "context_window": {"used_percentage": 68},
    "rate_limits": {
        "five_hour": {"used_percentage": 54, "resets_at": 1750000000},
        "seven_day": {"used_percentage": 81, "resets_at": 1750500000},
    },
}

DEMO_EXTRA_PAYLOAD = {
    "model": {"display_name": "Claude Sonnet 4"},
    "context_window": {"used_percentage": 42},
    "rate_limits": {
        "five_hour": {"used_percentage": 100, "resets_at": 1750000000},
        "seven_day": {"used_percentage": 95, "resets_at": 1750500000},
    },
}


def load_payload(argv: list[str]) -> Any:
    if len(argv) > 1 and argv[1] == "--demo":
        return DEMO_PAYLOAD
    if len(argv) > 1 and argv[1] == "--demo-extra":
        return DEMO_EXTRA_PAYLOAD

    if len(argv) > 1:
        path = Path(argv[1])
        if path.exists():
            return json.loads(path.read_text())

    stdin_data = sys.stdin.read().strip()
    if stdin_data:
        return json.loads(stdin_data)

    env_payload = env_value("AGENT_STATUSBAR_JSON", "CLAUDE_STATUSBAR_JSON")
    if env_payload:
        return json.loads(env_payload)

    return {}


def main() -> int:
    try:
        payload = load_payload(sys.argv)
        metrics = extract_metrics(payload)
        print(build_status_line(metrics))
        return 0
    except Exception as exc:  # noqa: BLE001
        fallback = style(APP_LABEL, FG["white"], BG["violet"], BOLD)
        print(f" {fallback} {muted('status unavailable')} ({exc})")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
