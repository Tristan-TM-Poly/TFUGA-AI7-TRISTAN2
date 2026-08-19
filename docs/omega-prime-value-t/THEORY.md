# Ω-PRIME-VALUE-T∞ — formal research packet

## PrimeAsset

For a public candidate `p`, the project treats the potential asset as a bundle:

```text
PrimeAsset = p + proof + provenance + implementation + application + verification + narrative
```

The integer itself is not treated as exclusive property.

## PrimeGenome

```text
G(p) = (family, parameters, residues, algebraic constraints,
        proof path, compute cost, engineering utility, market evidence)
```

R0.1 materializes the Proth slice:

```text
p = k*2^n + 1, k odd, 0 < k < 2^n.
```

## Proth proof gate

A Proth candidate is proven prime when the implementation finds an integer `a` satisfying:

```text
a^((p-1)/2) = -1 mod p.
```

The certificate separately repeats a deterministic Miller–Rabin decision over the unsigned 64-bit domain. These are independent software checks, not independent institutions.

## Engineering gate

For proven prime `p`, write:

```text
p - 1 = odd_part * 2^s.
```

The value `s` is the two-adicity. A primitive `2^s`-th root of unity enables power-of-two NTTs up to length `2^s`.

## Hypergraph

Node classes:

- candidate;
- family;
- factor;
- proof method;
- certificate;
- application.

Hyperedge classes:

- belongs-to-family;
- certifies-compositeness;
- certifies-primality;
- supports-application.

## PrimeMarketScore

The score is a navigation heuristic:

```text
value = utility + proof quality + rarity + implementation + provenance
        - compute cost - risk.
```

It is not a valuation, price forecast, investment recommendation or evidence of customer demand.

## R0.2 frontier

1. ECPP/Primo adapter for arbitrary-size certificates.
2. Pocklington and `N-1`/`N+1` proof compilers.
3. segmented and wheel sieves with residue-class compilation.
4. Rust/C++ kernels and benchmark parity.
5. SQLite/WAL campaign scheduler with checkpoints.
6. external novelty adapters for PrimePages, PrimeGrid and project-specific tables.
7. append-only provenance and independent-machine receipts.
8. NTT benchmark harness using generated moduli.
9. candidate portfolio allocator: prestige, research, product.
10. explicit IP, licensing, sponsorship and customer-evidence gates.
