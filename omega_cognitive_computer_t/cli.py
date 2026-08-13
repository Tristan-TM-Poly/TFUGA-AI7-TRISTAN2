from __future__ import annotations

import argparse
import json

from .assembly import parse_assembly, render_assembly
from .computer import CognitiveComputer
from .isa import default_registry


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="omega-cognitive", description="Omega Cognitive Computer: inspectable cognitive ISA/compiler/runtime")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compile", help="Compile a problem into cognitive assembly")
    c.add_argument("problem")
    r = sub.add_parser("run", help="Compile and execute the structural v0 runtime")
    r.add_argument("problem")
    r.add_argument("--budget", type=float, default=30.0)
    a = sub.add_parser("asm", help="Parse cognitive assembly from a file")
    a.add_argument("path")
    sub.add_parser("operators", help="List the cognitive ISA")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    computer = CognitiveComputer.default()
    if args.cmd == "compile":
        print(render_assembly(computer.compile(args.problem)), end="")
        return 0
    if args.cmd == "run":
        from .runtime import RuntimeContext
        result = computer.execute(args.problem, context=RuntimeContext(budget=args.budget))
        print(json.dumps({"halted_reason": result.halted_reason, "spent": result.spent, "state": result.state.to_dict(), "trace": [t.__dict__ for t in result.trace]}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "asm":
        with open(args.path, "r", encoding="utf-8") as f:
            print(render_assembly(parse_assembly(f.read(), name=args.path)), end="")
        return 0
    if args.cmd == "operators":
        for spec in default_registry().list():
            dual = spec.dual.value if spec.dual else "-"
            print(f"{spec.opcode.value:14} {spec.category:14} cost={spec.base_cost:.1f} dual={dual:14} {spec.description}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
