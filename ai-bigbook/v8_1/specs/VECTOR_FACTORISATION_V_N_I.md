# Vector Factorisation v_n_i for AI-BIGBOOK V8.3

## Purpose

Represent corpus elements as vectors and compress each section into a factorized semantic object.

## Registers

- R2: mathematical architecture.
- R3: local NumPy prototype.
- R4: benchmarked retrieval against baselines.
- R5: reproducible retrieval/evaluation protocol.

## Definitions

Let `v_{n,i,j}` be the vector representation of the j-th token or phrase in the i-th paragraph of section n.

Let `v_{n,i}` be the paragraph vector.

Let `v_n` be the section vector or low-rank factorized section object.

```text
v_n = tensor_factorise_i(v_{n,i})
```

Operationally, this can be PCA/SVD/Tucker/HOSVD depending on the input tensor shape.

## Canon equation

```text
paragraph vectors -> section matrix/tensor -> low-rank factorization -> section object -> HGFM node
```

## EvidenceGate constraints

The factorized vector is an index object, not truth.

```text
high similarity != proof
retrieval score != physical validation
embedding density != R5 evidence
```

## Baselines required for R4

- keyword/BM25 search,
- TF-IDF,
- standard embeddings,
- random projection control,
- duplicate-aware retrieval.

## Outputs

- `section_vectors.npy` or generated local equivalent,
- `section_factors.jsonl`,
- `retrieval_benchmark.md`,
- `vector_redteam_report.md`.
