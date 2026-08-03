# Ω-PRIME-VALUE-T∞ R0.3

R0.3 extends the machine-size R0.1 proof kernel and the resumable R0.2 campaign engine with four independently testable capabilities:

1. **Pocklington proof compiler** for integers larger than `2**64` whenever a proven part `F` of `N - 1` satisfies `F > sqrt(N)`.
2. **Merkle provenance** for candidate, proof, verification and OAK receipts.
3. **SQLite/WAL worker leases** with atomic claims, renewal, expiry, requeue, monotonic completion and event evidence.
4. **Python/C++/Rust parity vectors** covering deterministic unsigned-64 primality, modular exponentiation and NTT convolution.

The deterministic fixture proves

```text
N = 9 * 2^65 + 1
  = 332041393326771929089
```

through Pocklington with known factor product `F = 2^65` and witness `19`. The probable-prime prefilter is recorded but is not treated as the proof.

## Commands

```bash
python -m omega_prime_value_t.r03 benchmark --output generated/omega_prime_value_t/r03.json
python -m omega_prime_value_t.r03 prove-pocklington \
  332041393326771929089 --factor '2^65' --output certificate.json
python -m omega_prime_value_t.r03 verify-pocklington certificate.json
```

## OAK boundary

R0.3 proves primality for its certificate fixtures. It does not establish that a proven number is new, record-setting, economically valuable or exclusively ownable. The precedence layer only reports what was or was not present in supplied, hashed snapshots. Even two fixture snapshots cannot establish global novelty.

The C++ and Rust kernels are public arithmetic research fixtures. They do not claim constant-time behavior, side-channel resistance, consensus safety or production cryptographic suitability.
