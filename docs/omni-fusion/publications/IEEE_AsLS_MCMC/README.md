# IEEE AsLS-MCMC Raman Manuscript Packet

Status: OAK-safe draft / publication scaffold.
Author: Tristan Tardif-Morency.
Branch: feature/omega-manuscript-asls.

This directory contains a first GitHub-native publication packet for an uncertainty-aware Raman spectroscopy baseline-correction manuscript centered on Asymmetric Least Squares (AsLS) and Markov Chain Monte Carlo (MCMC) parameter exploration.

## Files

- Manuscript_Raman_AsLS_MCMC_v1_0.tex: IEEE-style LaTeX manuscript scaffold.
- OAK_CLAIMS_AND_VALIDATION.md: claims register, risk ledger, and promotion gates.
- validation_protocol_asls_mcmc.md: reproducible validation plan for synthetic and measured Raman spectra.

## OAK boundary

This packet does not claim that RMSE < 1e-8 has been validated inside this repository. No raw Raman dataset, benchmark report, external reproduction, or CI artifact proving that value was found in the current accessible context.

Current status:

    DRAFT / METHOD SPECIFICATION / VALIDATION PROTOCOL READY

A stronger claim may be promoted only after the repository contains a synthetic spectrum generator, measured dataset or documented public dataset reference, baseline ground truth or defensible proxy, reproducible benchmark script, uncertainty report, and CI artifact containing metrics, commit hash, environment, and failure cases.

## Canonical law

A named method is callable. A protocol is testable. A benchmark is evidence. A reproduced benchmark is stronger evidence. Only proof, data, uncertainty, and failure analysis can promote a claim.
