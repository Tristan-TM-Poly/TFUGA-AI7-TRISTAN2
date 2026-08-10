# Ω-INVERSE-T∞ v0.1 release checklist

## Formal core

- [x] shifted local-series contract documented;
- [x] regular / critical / degenerate gate implemented;
- [x] exact triangular reversion implemented;
- [x] formal Newton reversion implemented independently;
- [x] inverse derivative jet exported;
- [x] left composition checked through requested order;
- [x] right composition checked through requested order;
- [x] direct/Newton agreement recorded.

## Critical branch path

- [x] ordinary Taylor inverse rejected when `a1 == 0`;
- [x] finite multiplicity detected from first nonzero term;
- [x] `m` Puiseux branches emitted for `z=t^m`;
- [x] branch coefficients labeled numeric/truncated-polynomial prototype;
- [ ] Newton-polygon general implicit Puiseux support;
- [ ] certified branch continuation;
- [ ] monodromy tests.

## Reconstruction layer

- [x] Padé approximant;
- [x] rational finite-series candidate with holdout coefficients;
- [x] low-degree algebraic relation candidate with holdout coefficients;
- [x] rational coefficient-ratio candidate;
- [x] every candidate explicitly labeled non-proof;
- [ ] D-finite/P-recursive guesser;
- [ ] special-function database recognizer;
- [ ] proof-obligation export.

## Reference evidence

- [x] `x+x^2` -> Catalan-sign inverse coefficients;
- [x] `exp(x)-1` -> `log(1+z)` coefficients;
- [x] `x exp(x)` -> Lambert-W coefficients;
- [x] `sin(x)` -> arcsine coefficients;
- [x] `x/(1-x)` -> exact rational inverse candidate;
- [x] `x^2` -> two Puiseux branches;
- [x] critical point/value test for `x+x^2`;
- [x] CLI JSON and Markdown report test;
- [ ] dedicated GitHub Actions run green on PR;
- [ ] generated reference reports inspected from workflow artifact.

## OAK boundary

- [x] no global invertibility claim;
- [x] no exact convergence-radius claim from truncated critical values;
- [x] no Padé-pole-equals-singularity claim;
- [x] no finite-pattern-equals-proof claim;
- [x] M-minus limitations stored;
- [x] knowledge cell added;
- [x] master system index entry added.

## Promotion rule

Promote from `X/D candidate` to `D` only after the dedicated PR workflow passes and the generated evidence reports preserve the documented OAK boundaries. Promote beyond `D` only after broader independent benchmarks, certified convergence/branch evidence where claimed, and stable downstream reuse.
