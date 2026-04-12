#!/usr/bin/env python3
"""Compatibility entrypoint for agent-statusbar.

Canonical implementation now lives at integrations/claude/bin/statusbar.py.
"""

from __future__ import annotations

import runpy
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "integrations" / "claude" / "bin" / "statusbar.py"


if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
