# Ω-PRIME-VALUE-T∞ R0.1

Ω-PRIME-VALUE-T∞ is an OAK-safe public prime-discovery, proof, certification and engineering-value laboratory.

R0.1 deliberately does **not** claim a new world record, mathematical novelty, economic exclusivity, patentability, or cryptographic-secret generation. It establishes a reproducible machine-size Proth/NTT kernel whose outputs can later be compared with external prime databases and record tables.

## Executable scope

- deterministic Miller–Rabin for every integer below `2**64`;
- Proth-family generation `N = k*2^n + 1`, with `k` odd and `k < 2^n`;
- modular small-prime screening and M⁻ receipts;
- constructive Proth witnesses and proof verification;
- primitive roots and maximum power-of-two NTT profiles;
- SHA-256-bound OAKPrime certificates;
- deterministic campaign reports and prime-landscape hypergraphs;
- heuristic PrimeMarketScore with explicit non-guarantee boundaries;
- CLI, schemas, examples, tests and Python 3.10–3.13 CI.

## Quick start

```bash
python -m omega_prime_value_t benchmark --output generated/omega_prime_value_t/benchmark.json
python -m omega_prime_value_t search --exponent 23 --k-min 1 --k-max 255 --max-results 5
python -m omega_prime_value_t inspect 998244353
python -m omega_prime_value_t prove-proth --k 119 --exponent 23
```

## State machine

```text
candidate
  -> small-prime screened
  -> deterministic 64-bit primality decision
  -> Proth theorem proof
  -> independent verifier
  -> NTT engineering profile
  -> OAKPrime certificate
  -> external novelty/precedence search (not implemented in R0.1)
  -> record/application/revenue decision
```

## Scientific boundary

A prime can be mathematically valid without being novel or commercially valuable. R0.1 proves public machine-size examples and emits infrastructure. A claim of “new prime”, “record prime” or “sellable exclusive number” requires external precedence checks, independent community verification and legal/commercial analysis.
