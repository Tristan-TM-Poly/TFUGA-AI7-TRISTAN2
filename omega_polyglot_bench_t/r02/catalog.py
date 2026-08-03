"""Deterministic algorithm catalog with 1,024 canonical research specifications."""
from __future__ import annotations

from collections.abc import Iterator

from .model import AlgorithmSpec, NumericalContract

FAMILIES: tuple[str, ...] = (
    "vector", "matrix", "tensor", "signal", "wavelet", "statistics", "optimization", "graph",
    "hypergraph", "geometry", "compression", "coding", "symbolic", "physics", "parsing", "systems",
)

OPERATIONS: tuple[str, ...] = (
    "affine", "sum", "product", "difference", "scale", "dot", "norm_l1", "norm_l2",
    "normalize", "prefix_sum", "moving_average", "convolution", "correlation", "covariance", "histogram", "quantile",
    "transpose", "matmul", "trace", "determinant", "solve", "qr", "svd", "eigen",
    "fft", "fwt", "ffwt", "dct", "stft", "filter", "deconvolution", "resample",
    "bfs", "dfs", "dijkstra", "pagerank", "components", "centrality", "triangle_count", "hyperedge_reduce",
    "gradient", "newton", "adam", "coordinate_descent", "line_search", "projection", "proximal", "annealing",
    "encode", "decode", "compress", "decompress", "hash", "checksum", "ecc_encode", "ecc_decode",
    "integrate", "differentiate", "interpolate", "root_find", "ode_step", "pde_stencil", "monte_carlo", "bayes_update",
)

DTYPES: tuple[str, ...] = ("float64", "float32", "int64", "complex128")
RANKS: tuple[int, ...] = (1, 2, 3, 0)
BASE_PROPERTIES = (
    "deterministic-under-fixed-order", "shape-checked", "oak-conformance-required", "differential-testable",
)
BASE_TRANSFORMATIONS = (
    "scalar", "unrolled-2", "unrolled-4", "unrolled-8", "simd-auto", "blocked",
    "parallel-chunks", "streaming", "in-place-when-proven", "out-of-place",
)


def _equation(operation: str, rank: int) -> str:
    index = "i" if rank <= 1 else "i,j" if rank == 2 else "i,j,k"
    equations = {
        "affine": f"out[{index}] = a*x[{index}] + y[{index}]",
        "sum": f"out = Σ x[{index}]",
        "product": f"out = Π x[{index}]",
        "difference": f"out[{index}] = x[{index}] - y[{index}]",
        "scale": f"out[{index}] = a*x[{index}]",
        "dot": "out = Σ_i x[i]*y[i]",
        "matmul": "C[i,j] = Σ_k A[i,k]*B[k,j]",
        "convolution": "out[n] = Σ_k x[k] h[n-k]",
        "correlation": "out[τ] = Σ_t conj(x[t])*y[t+τ]",
        "covariance": "cov = E[(X-E[X])(Y-E[Y])]",
        "fft": "X[k] = Σ_n x[n] exp(-2πikn/N)",
        "fwt": "coefficients = wavelet_filterbank(x)",
        "ffwt": "coefficients = fractal_multiscale_filterbank(x)",
        "bfs": "distance[v] = min path length from source",
        "dijkstra": "distance[v] = min weighted path cost from source",
        "gradient": "x_next = x - η∇f(x)",
        "root_find": "find x such that f(x)=0",
        "ode_step": "state_next = integrator(state, dt)",
        "pde_stencil": "u_next[cell] = stencil(u, neighborhood)",
        "bayes_update": "posterior ∝ likelihood × prior",
    }
    return equations.get(operation, f"out = {operation}(inputs)")


def _complexity(operation: str) -> str:
    if operation in {"matmul", "svd", "eigen", "solve", "qr"}:
        return "O(n^3) baseline; optimized variants admissible"
    if operation in {"fft", "fwt", "ffwt", "dct", "stft"}:
        return "O(n log n) target; specification does not certify implementation"
    if operation in {"dijkstra", "pagerank", "components", "centrality"}:
        return "graph-dependent; record |V| and |E|"
    return "O(n) baseline unless operation-specific proof overrides"


def generate_catalog(count: int = 1024) -> tuple[AlgorithmSpec, ...]:
    if count < 1:
        return ()
    specs: list[AlgorithmSpec] = []
    for index in range(count):
        family = FAMILIES[index % len(FAMILIES)]
        operation = OPERATIONS[(index // len(FAMILIES)) % len(OPERATIONS)]
        dtype = DTYPES[(index // (len(FAMILIES) * len(OPERATIONS))) % len(DTYPES)]
        rank = RANKS[(index // 7) % len(RANKS)]
        arity = 2 if operation in {"affine", "difference", "dot", "matmul", "convolution", "correlation", "covariance"} else 1
        algorithm_id = f"{family}.{operation}.{dtype}.r{rank}.{index:04d}"
        forbidden = ("reassociate-floating-reduction",) if operation in {"sum", "product", "dot", "covariance"} else ()
        contract = NumericalContract(
            absolute_tolerance=1e-12 if dtype in {"float64", "complex128"} else 1e-5,
            relative_tolerance=1e-12 if dtype in {"float64", "complex128"} else 1e-5,
            deterministic=True,
        )
        spec = AlgorithmSpec(
            algorithm_id=algorithm_id,
            family=family,
            operation=operation,
            arity=arity,
            rank=rank,
            dtype=dtype,
            equation=_equation(operation, rank),
            complexity=_complexity(operation),
            properties=BASE_PROPERTIES,
            admissible_transformations=BASE_TRANSFORMATIONS,
            forbidden_transformations=forbidden,
            contract=contract,
        )
        spec.validate()
        specs.append(spec)
    return tuple(specs)


def catalog_index(count: int = 1024) -> dict[str, AlgorithmSpec]:
    return {spec.algorithm_id: spec for spec in generate_catalog(count)}


def iter_catalog(count: int = 1024) -> Iterator[AlgorithmSpec]:
    yield from generate_catalog(count)
