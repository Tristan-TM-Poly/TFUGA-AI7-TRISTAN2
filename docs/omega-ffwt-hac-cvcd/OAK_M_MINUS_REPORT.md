# FFWT-HAC-CVCD Benchmark — OAK / M-minus Report

Issue: #88  
Status: benchmark scaffold with CI.

## OAK checks

| Check | Result |
|---|---|
| FFT baseline | pass |
| DWT baseline | pass |
| FFWT-HAC feature set | pass |
| FFWT+FFT hybrid | pass |
| Noise sweep | pass |
| Held-out split | pass |
| Feature ablation table | pass |
| CSV adapter | pass |
| Reconstruction/compression metric | pass |
| CI workflow | pass |

## M-minus limitations

- Built-in datasets are deterministic synthetic/fixture datasets.
- The CSV adapter exists, but no external real dataset is bundled or claimed.
- Haar DWT is only one DWT baseline.
- Scattering-transform and learned baselines are not included because this package is stdlib-only.
- Classification accuracy can improve while reconstruction/compression worsens.
- FFWT-HAC must not be called generally superior until it wins across external datasets and tasks.

## Promotion rule

Move from exploratory to demonstrated only after:

1. at least one cited external dataset is added through the CSV adapter;
2. DWT and FFT baselines remain present;
3. noise sweep includes at least three levels;
4. reconstruction/compression metrics are reported;
5. failure cases are recorded in M-minus.

## Next actions

1. Add an external open dataset adapter run with citation and version.
2. Add a stronger DWT/scattering baseline if dependency policy allows.
3. Add confusion matrix and per-class failure analysis.
4. Compare FFWT-HAC under compression, denoising, and anomaly detection tasks.
