"""Demo for omega_git_jkd."""

from __future__ import annotations

import json

from omega_git_jkd import default_events, size_mode, summarize


def main() -> int:
    payload = {
        "summary": summarize(default_events()),
        "small_40": size_mode(40),
        "large_160": size_mode(160),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
