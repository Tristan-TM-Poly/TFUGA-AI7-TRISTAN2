from __future__ import annotations

import json

from omega_depth_t import build_oakgate_depth9


def main() -> int:
    graph = build_oakgate_depth9()
    artifacts = graph.write_bundle("generated/omega_depth_t/oakgate-depth9")
    print(json.dumps({"summary": graph.summary(), "artifacts": artifacts}, ensure_ascii=False, indent=2))
    return 0 if not graph.validate() else 2


if __name__ == "__main__":
    raise SystemExit(main())
