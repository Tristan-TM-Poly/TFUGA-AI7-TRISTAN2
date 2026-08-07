# Ω-PRIME-VALUE-T∞ R0.2

R0.2 turns the R0.1 mathematical kernel into a resumable evidence-producing campaign system.

## Components

- `CampaignPlanner`: deterministic Proth task manifests and finite shards;
- `CampaignStore`: SQLite/WAL state, events, certificates and local registry;
- `CampaignEngine`: screen → deterministic primality → Proth proof → certificate;
- `LocalPrimeRegistry`: anti-duplication inside Tristan campaigns;
- `ntt_kernel`: executable radix-2 NTT and convolution validated against a naive baseline;
- `PortfolioAllocator`: advisory UCB1 allocator for prestige, research and product arms;
- `benchmark`: deterministic interrupted/resumed campaign fixture.

## Commands

```bash
python -m omega_prime_value_t.r02 plan \
  --exponent-min 8 --exponent-max 16 --k-max 999 \
  --output campaign-manifest.json

python -m omega_prime_value_t.r02 run \
  --database generated/omega_prime_value_t/campaign.sqlite3 \
  --exponent-min 8 --exponent-max 16 --k-max 999 \
  --max-tasks 500 \
  --output campaign-receipt.json

python -m omega_prime_value_t.r02 convolve \
  --left 1,2,3,4 --right 5,6,7 \
  --modulus 998244353

python -m omega_prime_value_t.r02 benchmark \
  --output generated/omega_prime_value_t/r02-benchmark.json
```

Run the same `run` command again against the same database to continue the campaign. Existing task transitions are immutable through the engine; only planned tasks are processed.

## Evidence boundaries

- WAL and checkpoints provide software resumability, not distributed consensus.
- The local registry prevents duplicate work inside this database, not prior discovery elsewhere.
- Deterministic 64-bit Miller–Rabin and Proth verification establish primality in the supported domain, not novelty.
- Portfolio rewards are user-defined evidence utilities, not dollars or guaranteed returns.
- The NTT kernel is a correctness reference, not yet a constant-time cryptographic implementation.
