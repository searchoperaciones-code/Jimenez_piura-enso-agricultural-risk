# Optimizing Agricultural Economic Value under El Niño 2026–2027 Risk in Piura, Peru: District-Level Climate–Yield Estimation and Spatial Mean–CVaR Crop Allocation

Working research title.

This repository contains the frozen research-software and evidence artifacts for the completed DATASET MASTER v1 and CLIMATE MASTER v1.1 phases of a district-level agricultural risk study for Piura, Peru. Later phenology, econometrics, ENSO-scenario and optimization phases have not started in this repository state.

## Scientific status

| Phase | Status |
| --- | --- |
| DATASET MASTER v1 | PASS - FROZEN |
| CLIMATE MASTER v1.1 | PASS - FROZEN |
| PHENOLOGY MASTER v1 | NOT STARTED |
| ECONOMETRICS | NOT STARTED |
| ENSO SCENARIOS | NOT STARTED |
| MEAN-CVaR OPTIMIZATION | NOT STARTED |

## Current empirical foundation

The certified repository state contains:

- 1,701 main district x crop x year observations.
- 480 balanced-panel observations.
- 12 balanced districts.
- 55 districts with climate support.
- 2016-2023 main agricultural panel.
- CHIRPS v3 FINAL precipitation.
- CHIRTS-ERA5 monthly Tmax/Tmin.
- 1991-2020 climatological normals.
- 5,280 district-month climate observations for 2016-2023.
- 6,215 agricultural-overlap district-month records for 2015-08 to 2024-12.
- 1,701 / 1,701 agricultural observations with climate support.
- 36 / 36 independent climate extraction checks.
- 37 / 37 full-data climate tests in the certified local execution.
- Deterministic two-run reproducibility for committed deterministic climate outputs.

## Important unresolved issue

`YIELD_RAW` physical unit remains UNRESOLVED because the physical unit of `PRODUCCION` has not been certified from the supplied official documentation.

Do not call `YIELD_RAW` t/ha. Do not construct final gross value of production interpretation from an assumed production unit.

## Scientific non-claims

The current repository does not yet:

- estimate climate-yield causal effects;
- claim causal identification;
- estimate final fixed-effects models;
- simulate 2026-2027 outcomes;
- fit copulas;
- calculate final CVaR;
- optimize crop allocation;
- identify an optimal crop portfolio.

## Repository structure

- `build_dataset_master.py`: DATASET MASTER v1 construction script.
- `audit_dataset_master.py`: DATASET MASTER artifact audit.
- `audit_climate_master.py`: read-only CLIMATE MASTER v1.1 certification verifier for committed artifacts.
- `scripts/`: climate acquisition, boundary recovery and extraction scripts, including the v1.1 pipeline.
- `tests/`: repository/offline tests and full-data integration tests.
- `data/processed/`: certified processed DATASET and CLIMATE artifacts retained in Git.
- `data/raw/`: local-only raw institutional and climate inputs; intentionally ignored by Git.
- `outputs/qa/`: frozen scientific QA evidence for DATASET MASTER v1 and CLIMATE MASTER v1.1.
- `outputs/figures/climate_qa/`: frozen CLIMATE MASTER v1.1 QA figures.
- `outputs/repository/`: repository-hardening QA artifacts generated after the scientific freeze.
- `docs/`: reproducibility, freeze, licensing and citation-status documentation.

## Data availability

Large raw climate rasters and original institutional raw inputs are intentionally not stored in Git. The repository retains provenance, source URLs, product versions and SHA-256 hashes for certified inputs and outputs.

Key provenance files:

- `outputs/qa/data_sources.csv`
- `outputs/qa/data_manifest.csv`
- `outputs/qa/climate/climate_data_manifest.csv`
- `outputs/qa/climate/climate_sources_frozen.csv`

`data/raw/climate/` contains large downloadable raster inputs during full scientific reproduction and is intentionally excluded from Git. Original agricultural raw inputs are likewise local-only. Processed certified outputs are retained under `data/processed/`.

## Reproduction overview

Repository/offline verification can validate the committed processed results and QA artifacts without the raw climate archive.

Full scientific reproduction requires:

1. Populate required agricultural raw inputs under `data/raw/`.
2. Run DATASET MASTER v1 construction and audit.
3. Obtain and freeze the required climate inputs listed in `outputs/qa/climate/climate_data_manifest.csv`.
4. Run CLIMATE MASTER v1.1.
5. Run audits, including the climate certification verifier.
6. Run tests appropriate to the available data: offline repository tests for a clean clone, and full-data integration tests only when the raw climate archive is locally available.

Cloning this repository alone does not reproduce the approximately 23 GB local climate raster archive.

## Certified freeze

The scientific reference state is:

- Commit: `38e957e3c01fbffef242c386099b0a219d83ca70`
- Tag: `v0.2.0-data-climate-freeze`
- Tag message: `Certified DATASET MASTER v1 and CLIMATE MASTER v1.1 scientific freeze`

Repository-hardening changes after this commit must not modify the frozen scientific contents under `data/processed/`, `outputs/qa/` or `outputs/figures/climate_qa/`.

## Limitations

- `PRODUCCION` physical unit remains unresolved, so `YIELD_RAW` physical unit remains unresolved.
- PISCO stable reproducible no-credential raster endpoint was unavailable.
- SENAMHI station validation remains unresolved.
- Only one official boundary source achieved accepted 55/55 Piura panel coverage.
- Low raster-pixel support in small districts is documented for later sensitivity analysis.
