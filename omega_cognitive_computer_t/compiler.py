from __future__ import annotations

from dataclasses import dataclass
import re

from .isa import Instruction, Opcode, Program


@dataclass(frozen=True)
class ProblemFingerprint:
    domain: str
    dimensionality: str = "unknown"
    nonlinearity: float = 0.0
    uncertainty: float = 0.5
    symmetry_signal: float = 0.0
    scale_signal: float = 0.0
    proofness: float = 0.0
    empiricalness: float = 0.0
    engineeringness: float = 0.0
    constraint_density: float = 0.0
    tokens: tuple[str, ...] = ()


_MATH = {"prove", "proof", "theorem", "conjecture", "lemma", "matrix", "polynomial", "zero", "equation", "zeta", "determinant"}
_ENGINEERING = {"design", "material", "circuit", "device", "prototype", "thermal", "mechanical", "optical", "electrical", "manufacture", "engineering"}
_EMPIRICAL = {"measure", "experiment", "data", "dataset", "observed", "sensor", "benchmark", "simulation"}
_THEORY = {"theory", "hypothesis", "model", "framework", "mechanism", "discover", "research"}


def fingerprint_problem(text: str) -> ProblemFingerprint:
    tokens = tuple(re.findall(r"[A-Za-zÀ-ÿ0-9_]+", text.lower()))
    bag = set(tokens)
    proof = min(1.0, len(bag & _MATH) / 2)
    eng = min(1.0, len(bag & _ENGINEERING) / 2)
    emp = min(1.0, len(bag & _EMPIRICAL) / 2)
    theory = min(1.0, len(bag & _THEORY) / 2)
    domain = "mathematics" if proof >= max(eng, emp, theory) and proof > 0 else "engineering" if eng >= max(emp, theory) and eng > 0 else "empirical_science" if emp > 0 else "theory" if theory > 0 else "general"
    return ProblemFingerprint(
        domain=domain,
        nonlinearity=1.0 if {"nonlinear", "chaos", "chaotic"} & bag else 0.0,
        uncertainty=0.8 if {"uncertain", "unknown", "noisy"} & bag else 0.5,
        symmetry_signal=1.0 if {"symmetry", "invariant", "noether"} & bag else 0.0,
        scale_signal=1.0 if {"multiscale", "scale", "fractal", "recursive"} & bag else 0.0,
        proofness=proof,
        empiricalness=emp,
        engineeringness=eng,
        constraint_density=min(1.0, len(bag & {"constraint", "limit", "cost", "safety", "requirement"}) / 2),
        tokens=tokens,
    )


class CognitiveCompiler:
    """Heuristic v0 compiler: intent -> fingerprint -> inspectable cognitive program."""

    def compile(self, problem: str, *, fingerprint: ProblemFingerprint | None = None) -> Program:
        fp = fingerprint or fingerprint_problem(problem)
        if fp.domain == "mathematics":
            instructions = (
                Instruction(Opcode.DECOMPOSE),
                Instruction(Opcode.REPRESENT, ("symbolic",)),
                Instruction(Opcode.REPRESENT, ("geometric",)),
                Instruction(Opcode.REPRESENT, ("computational",)),
                Instruction(Opcode.INVARIANTS),
                Instruction(Opcode.SPECIALIZE),
                Instruction(Opcode.COUNTER),
                Instruction(Opcode.ATTACK),
                Instruction(Opcode.PROVE),
                Instruction(Opcode.OAK),
                Instruction(Opcode.CRYSTALLIZE),
            )
        elif fp.domain == "engineering":
            instructions = (
                Instruction(Opcode.DECOMPOSE),
                Instruction(Opcode.ZOOM, ("materials",)),
                Instruction(Opcode.REPRESENT, ("physical",)),
                Instruction(Opcode.REPRESENT, ("system",)),
                Instruction(Opcode.SIMULATE),
                Instruction(Opcode.ATTACK, ("constraints",)),
                Instruction(Opcode.RESIDUAL),
                Instruction(Opcode.BENCHMARK),
                Instruction(Opcode.OAK),
                Instruction(Opcode.CRYSTALLIZE),
            )
        elif fp.domain == "empirical_science":
            instructions = (
                Instruction(Opcode.DECOMPOSE),
                Instruction(Opcode.REPRESENT, ("causal",)),
                Instruction(Opcode.REPRESENT, ("statistical",)),
                Instruction(Opcode.COUNTER),
                Instruction(Opcode.SIMULATE),
                Instruction(Opcode.MEASURE),
                Instruction(Opcode.RESIDUAL),
                Instruction(Opcode.BENCHMARK),
                Instruction(Opcode.OAK),
                Instruction(Opcode.CRYSTALLIZE),
            )
        else:
            instructions = (
                Instruction(Opcode.DECOMPOSE),
                Instruction(Opcode.REPRESENT, ("structural",)),
                Instruction(Opcode.REPRESENT, ("hypergraph",)),
                Instruction(Opcode.EXPAND),
                Instruction(Opcode.GENERALIZE),
                Instruction(Opcode.TRANSFER),
                Instruction(Opcode.MERGE),
                Instruction(Opcode.ATTACK),
                Instruction(Opcode.COUNTER),
                Instruction(Opcode.RESIDUAL),
                Instruction(Opcode.COMPRESS),
                Instruction(Opcode.OAK),
                Instruction(Opcode.CRYSTALLIZE),
            )
        if fp.scale_signal and Opcode.ZOOM not in [i.opcode for i in instructions]:
            instructions = (Instruction(Opcode.ZOOM), Instruction(Opcode.DEZOOM), *instructions)
        return Program(name=f"compiled:{fp.domain}", instructions=tuple(instructions), tags=("compiled", fp.domain), metadata={"fingerprint": fp.__dict__})
