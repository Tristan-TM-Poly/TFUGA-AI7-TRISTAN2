# Ω-POLYGLOT-BENCH-T R0.3 — Persistent Zero-Copy Throughput

R0.3 converts the native backends from a demonstration of fast kernels hidden behind expensive list conversion into a usable persistent-buffer execution path.

## Problem measured in R0.1

The original convenience interface accepts Python lists and, for every native call:

1. allocates two ctypes input arrays;
2. converts every Python float into those arrays;
3. allocates a native output array;
4. executes the native kernel;
5. converts the native output back into a Python list.

For the simple affine kernel, those boundary costs dominate the arithmetic. A fast native loop can therefore appear slower than the plain Python oracle when measured end to end through that interface.

## R0.3 execution boundaries

R0.3 records three separate modes for each backend:

| Mode | Included in timed region |
|---|---|
| `end_to_end_list` | Python-list conversion, input copies, output allocation, kernel, output-list materialization |
| `zero_copy_buffer` | ctypes view construction, FFI dispatch, kernel; payload buffers and output are reused |
| `kernel_only_prepared` | FFI dispatch and kernel; payload buffers and ctypes views are reused |

The names describe measurement boundaries, not absolute hardware truths. In particular, `kernel_only_prepared` still includes Python-to-ctypes function dispatch.

## Persistent buffer API

```python
from omega_polyglot_bench_t.r03 import NativeAffineLibrary, as_double_array
from omega_polyglot_bench_t.r03.buffers import empty_double_array

x = as_double_array([1.0, 2.0, 3.0])
y = as_double_array([4.0, 5.0, 6.0])
out = empty_double_array(len(x))

library = NativeAffineLibrary("cpp")
library.run_into(x, y, 2.0, out)
assert list(out) == [6.0, 9.0, 12.0]

prepared = library.prepare(x, y, out)
prepared.run(3.0)
assert list(out) == [7.0, 11.0, 15.0]
```

The buffers must be `array('d')`, which provides contiguous native-endian float64 storage without requiring NumPy. A prepared call pins ctypes views into those arrays. The arrays must not be resized while the prepared call exists.

## Commands

Build all native implementations:

```bash
python -m omega_polyglot_bench_t.r03 build --backends c,cpp,rust
```

Run the separated-boundary benchmark:

```bash
python -m omega_polyglot_bench_t.r03 benchmark \
  --backends c,cpp,rust \
  --sizes 4096,100000,1000000 \
  --warmups 3 \
  --repetitions 15 \
  --output report.json
```

## Local reference measurement

The committed reference was measured on 2026-08-03 in a Linux x86-64 container using Python 3.13.5 and GCC/G++ 14.2 with `-O3 -shared -fPIC`. Rust was unavailable in that local environment and remains delegated to GitHub Actions.

| Elements | Python median | Best native boundary | Native median | Speedup |
|---:|---:|---|---:|---:|
| 4,096 | 197.223 µs | C++ prepared | 1.973 µs | 99.96× |
| 100,000 | 5.488 ms | C prepared | 29.093 µs | **188.65×** |
| 1,000,000 | 59.722 ms | C++ zero-copy | 462.537 µs | 129.12× |

All measured outputs had maximum absolute error `0.0` against the Python oracle.

The old list interface remained slower:

| Elements | Best old list-native median | Relative to Python |
|---:|---:|---:|
| 4,096 | 887.097 µs | 4.50× slower |
| 100,000 | 23.791 ms | 4.34× slower |
| 1,000,000 | 250.413 ms | 4.19× slower |

This demonstrates why execution-boundary design matters as much as language choice.

## Setup amortization

Creating persistent buffers still has a one-time cost because Python values must initially be materialized as contiguous float64 storage. A backend should therefore be selected using total workload cost:

```text
total = setup + number_of_calls × steady_state_call
```

For one isolated affine operation on existing Python lists, the plain Python oracle can remain preferable. Persistent native buffers become useful when:

- data already lives in compatible contiguous buffers;
- the same buffers participate in repeated operations;
- several native operations are fused before returning to Python;
- output stays native for downstream kernels;
- the algorithm has greater arithmetic intensity than the affine pilot.

## OAK constraints

R0.3 does not claim:

- that C, C++, or Rust universally beats Python;
- that the CI runner represents Tristan's target hardware;
- that effective GiB/s is a hardware memory-counter measurement;
- that energy, RSS, cache misses, or SIMD instructions were measured;
- that the affine kernel predicts FFWT, tensor, graph, PDE, or parsing performance;
- that `kernel_only_prepared` is an end-user latency measurement.

Every report retains:

- backend and execution mode;
- correctness and maximum absolute error;
- median, mean, and p95;
- one-time setup cost;
- speedup against the plain Python oracle;
- an effective traffic estimate;
- explicit non-claims for energy and universal language superiority.

## CI evidence

The R0.3 workflow builds C, C++, and Rust on Python 3.10 and 3.13, runs all buffer-contract tests, validates the JSON schema, benchmarks 4,096 and 100,000 elements, and uploads each JSON report as a retained workflow artifact.

CI gates require that:

- every native backend is available;
- every execution mode is numerically correct;
- maximum absolute error is at most `1e-12`;
- zero-copy and prepared modes beat the old list boundary for each backend;
- at least one correct native mode beats the plain Python oracle for each tested size;
- no universal-winner or energy claim is emitted.

## Next performance layers

1. Support generic writable buffer-protocol objects and NumPy without copies.
2. Add fused multi-operation pipelines so outputs remain native.
3. Separate FFI dispatch from the native loop using batched call counts.
4. Add aligned allocation and explicit SIMD kernels.
5. Add OpenMP and Rayon parallel variants for suitable sizes.
6. Measure resident memory, allocations, cache misses, branches, and energy where supported.
7. Replace the affine pilot with FFWT, convolution, tensor products, graph traversal, and physical solvers.
8. Train the runtime selector on hardware fingerprints and break-even call counts.

## Status

R0.3 is a software-performance research prototype. The local reference is evidence for one environment, not certification across hardware. GitHub Actions artifacts are the next independent measurements.
