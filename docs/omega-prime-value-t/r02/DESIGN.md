# R0.2 design and invariants

## 1. Manifest invariant

For every task:

```text
value = k*2^exponent + 1
k odd
0 < k < 2^exponent
value < 2^64
```

The manifest SHA-256 binds the ordered task list and policy. Task ordinals are contiguous and task identifiers are unique.

## 2. Storage invariant

The task state machine is monotone:

```text
planned -> filtered_composite
planned -> composite
planned -> probable_prime
planned -> certified
planned -> failed
```

R0.2 does not silently retry completed tasks. A future retry protocol must create a new attempt receipt rather than rewrite history.

## 3. Certification invariant

A certified task must contain:

1. deterministic unsigned-64-bit Miller–Rabin acceptance;
2. a valid Proth theorem witness;
3. a valid NTT root profile;
4. a SHA-256-bound certificate;
5. explicit negative claims for record, novelty, exclusivity and secret material.

## 4. NTT invariant

For transform length `L`:

```text
L is a power of two
L divides p-1
root^L = 1 mod p
root^(L/2) != 1 mod p
inverse(ntt(x)) = x mod p
```

Convolution evidence is accepted only when the fast kernel equals the quadratic reference.

## 5. Portfolio invariant

The allocator chooses among three arms:

- prestige;
- research;
- product.

The observations are evidence scores divided by compute units. They are not transformed into a financial forecast.

## 6. OAK failure modes retained in M⁻

- small-factor rejection;
- deterministic composite without extracted factor;
- proof construction failure;
- certificate mismatch;
- database transition conflict;
- NTT root or convolution mismatch;
- duplicate local registry insertion;
- malformed or tampered manifest.
