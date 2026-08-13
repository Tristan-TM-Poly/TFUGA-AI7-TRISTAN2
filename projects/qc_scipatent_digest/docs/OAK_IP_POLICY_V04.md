# OAK-IP Policy v0.4

This project digests public scientific and patent metadata. It must not be used as legal advice or as proof that an invention works.

## Required classification before public disclosure

Every generated opportunity must be classified as one of:

```text
open | publishable | patentable | trade_secret | licensed | blocked | unknown
```

Default status is `unknown` or `internal_review_required`.

## Locks

1. Do not disclose potentially patentable inventions before IP review.
2. Do not claim freedom to operate without professional analysis.
3. Do not treat patent filing as experimental proof.
4. Do not treat publication metadata as reproducibility proof.
5. Do not ingest copyrighted full text unless it is open, licensed, or otherwise permitted.
6. Keep live datasets and private analysis out of public GitHub unless reviewed.

## Safe outputs

- metadata summaries;
- OAK warnings;
- internal review queues;
- source links;
- reproducibility questions;
- prototype ideas marked as internal review required.
