from __future__ import annotations
from dataclasses import asdict, dataclass
import argparse, json
from typing import Any

@dataclass(frozen=True)
class PrimeNode:
    index: int
    prime: int
    primorial_digits: list[int]
    residues: list[int]
    gap_digits: dict[int, list[int]]
    modular_gaps: dict[int, list[int]]
    oak_status: str
    fertility: float

def primes_up_to_count(count: int) -> list[int]:
    if count < 0:
        raise ValueError('count must be non-negative')
    primes: list[int] = []
    candidate = 2
    while len(primes) < count:
        if all(candidate % p for p in primes if p * p <= candidate):
            primes.append(candidate)
        candidate = 3 if candidate == 2 else candidate + 2
    return primes

def primorials(primes: list[int]) -> list[int]:
    values = [1]
    acc = 1
    for prime in primes:
        acc *= prime
        values.append(acc)
    return values

def mixed_radix_digits(value: int, radices: list[int]) -> list[int]:
    if value < 0:
        raise ValueError('value must be non-negative')
    bases = primorials(radices)
    return [(value // bases[j]) % radices[j] for j in range(len(radices))]

def reconstruct_mixed_radix(digits: list[int], radices: list[int], overflow: int = 0) -> int:
    if len(digits) != len(radices):
        raise ValueError('digits and radices must have the same length')
    bases = primorials(radices)
    for digit, radix in zip(digits, radices):
        if digit < 0 or digit >= radix:
            raise ValueError('digit outside its radix')
    return sum(digit * bases[j] for j, digit in enumerate(digits)) + overflow * bases[len(radices)]

def overflow(value: int, radices: list[int]) -> int:
    bases = primorials(radices)
    return value // bases[len(radices)] if radices else value

def prime_coordinate_tensor(primes: list[int]) -> list[list[int]]:
    return [mixed_radix_digits(prime, primes[:i]) for i, prime in enumerate(primes)]

def residue_tensor(primes: list[int]) -> list[list[int]]:
    return [[prime % divisor for divisor in primes[:i]] for i, prime in enumerate(primes)]

def gap_value(primes: list[int], i: int, n: int) -> int:
    if n < 1:
        raise ValueError('n must be at least 1')
    if i < 0 or i + n >= len(primes):
        raise IndexError('gap outside finite prime table')
    return primes[i + n] - primes[i]

def gap_tensor(primes: list[int], max_jump: int = 1) -> dict[int, list[list[int]]]:
    if max_jump < 1:
        raise ValueError('max_jump must be at least 1')
    tensors: dict[int, list[list[int]]] = {}
    for n in range(1, max_jump + 1):
        rows: list[list[int]] = []
        for i, prime in enumerate(primes):
            if i + n >= len(primes):
                rows.append([])
            else:
                rows.append(mixed_radix_digits(primes[i + n] - prime, primes[:i]))
        tensors[n] = rows
    return tensors

def modular_gap_tensor(primes: list[int], max_jump: int = 1) -> dict[int, list[list[int]]]:
    tensors: dict[int, list[list[int]]] = {}
    for n in range(1, max_jump + 1):
        rows: list[list[int]] = []
        for i, prime in enumerate(primes):
            if i + n >= len(primes):
                rows.append([])
            else:
                gap = primes[i + n] - prime
                rows.append([gap % divisor for divisor in primes[:i]])
        tensors[n] = rows
    return tensors

def residue_gap_identity_holds(primes: list[int], max_jump: int = 1) -> bool:
    residues = residue_tensor(primes)
    modular = modular_gap_tensor(primes, max_jump)
    for n, rows in modular.items():
        for i, row in enumerate(rows):
            if i + n >= len(primes):
                continue
            for j, actual in enumerate(row):
                expected = (residues[i + n][j] - residues[i][j]) % primes[j]
                if actual != expected:
                    return False
    return True

def build_prime_nodes(count: int, max_jump: int = 1) -> list[PrimeNode]:
    primes = primes_up_to_count(count)
    coordinates = prime_coordinate_tensor(primes)
    residues = residue_tensor(primes)
    gaps = gap_tensor(primes, max_jump)
    modular_gaps = modular_gap_tensor(primes, max_jump)
    nodes: list[PrimeNode] = []
    for i, prime in enumerate(primes):
        node_gap_digits = {n: gaps[n][i] for n in gaps if gaps[n][i]}
        node_modular_gaps = {n: modular_gaps[n][i] for n in modular_gaps if modular_gaps[n][i]}
        fertility = 1.0 + len(coordinates[i]) + len(node_gap_digits)
        nodes.append(PrimeNode(i+1, prime, coordinates[i], residues[i], node_gap_digits, node_modular_gaps, 'observed', fertility))
    return nodes

def motif_hyperedges(nodes: list[PrimeNode], max_prefix: int = 3) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, tuple[int, ...]], list[int]] = {}
    for node in nodes:
        if node.residues:
            buckets.setdefault(('residue_prefix', tuple(node.residues[:max_prefix])), []).append(node.index)
        if 1 in node.modular_gaps and node.modular_gaps[1]:
            buckets.setdefault(('gap1_modular_prefix', tuple(node.modular_gaps[1][:max_prefix])), []).append(node.index)
    edges: list[dict[str, Any]] = []
    for (kind, signature), indices in sorted(buckets.items()):
        if len(indices) >= 2:
            edges.append({'kind': kind, 'signature': list(signature), 'node_indices': indices, 'oak_status': 'observed'})
    return edges

def finite_prime_tensor_packet(count: int = 12, max_jump: int = 2) -> dict[str, Any]:
    primes = primes_up_to_count(count)
    nodes = build_prime_nodes(count, max_jump)
    return {
        'name': 'prime_tensor_packet',
        'oak_status': 'observed',
        'limits': ['finite prefix only', 'not a proof of a new prime distribution theorem', 'stdlib reference implementation, not optimized'],
        'primes': primes,
        'nodes': [asdict(node) for node in nodes],
        'hyperedges': motif_hyperedges(nodes),
        'checks': {
            'residue_gap_identity': residue_gap_identity_holds(primes, max_jump),
            'reconstruction': all(reconstruct_mixed_radix(row, primes[:i], overflow(primes[i], primes[:i])) == primes[i] for i, row in enumerate(prime_coordinate_tensor(primes))),
        },
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Generate finite prime tensor OAK packet.')
    parser.add_argument('--count', type=int, default=12)
    parser.add_argument('--max-jump', type=int, default=2)
    args = parser.parse_args(argv)
    packet = finite_prime_tensor_packet(args.count, args.max_jump)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
