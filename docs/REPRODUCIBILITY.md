# Reproducibility

The repository distinguishes offline artifact verification from full scientific reproduction.

## A. Repository/Offline Verification

This workflow validates the committed processed results and QA artifacts. It does not require `data/raw/`, internet access or the local climate raster archive.

1. Create a Python 3.11 environment.
2. Install pinned repository verification dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Compile the repository code:

   ```bash
   python -m compileall build_dataset_master.py audit_dataset_master.py audit_climate_master.py scripts tests
   ```

4. Run the offline repository tests:

   ```bash
   python -m unittest tests/test_repository_offline.py -v
   ```

5. Run the CLIMATE MASTER artifact verifier:

   ```bash
   python audit_climate_master.py
   ```

The verifier writes `outputs/repository/climate_certification_verification.json`. This is a repository-level artifact and does not modify frozen scientific outputs.

## B. Full Scientific Reproduction

This workflow requires original agricultural raw data and the downloaded climate rasters listed in `outputs/qa/climate/climate_data_manifest.csv`.

Expected local storage includes approximately 23 GB for the raw climate raster archive, plus the raw institutional inputs under `data/raw/`.

1. Populate the required agricultural raw inputs documented in `data/README.md`.
2. Install the pinned DATASET environment when reproducing DATASET MASTER v1:

   ```bash
   pip install -r requirements-dataset.txt
   ```

3. Run DATASET MASTER and its audit:

   ```bash
   python build_dataset_master.py
   python audit_dataset_master.py
   ```

4. Install the pinned CLIMATE environment when reproducing CLIMATE MASTER v1.1:

   ```bash
   pip install -r requirements-climate.txt
   ```

5. Obtain/freeze climate inputs using the CLIMATE MASTER workflow. Do not assume a clean clone contains the raw climate files.
6. Run the CLIMATE MASTER pipeline only when full raw data are available and a scientific phase reopening or full reproduction is intended.
7. Run full-data integration tests only when raw climate rasters are locally present:

   ```bash
   python -m unittest tests/test_climate_pipeline.py -v
   ```

The certified local execution of CLIMATE MASTER v1.1 passed 37 / 37 full-data tests. That historical result is preserved in `outputs/qa/climate/automated_tests_report.json`.

## Python Version

Certified Python version: `3.11.7`.

## Frozen DATASET Packages

```text
pandas==3.0.2
numpy==2.3.5
openpyxl==3.1.5
```

## Frozen CLIMATE Packages

```text
pandas==3.0.2
numpy==2.3.5
geopandas==1.1.3
rasterio==1.4.4
shapely==2.1.2
pyproj==3.7.2
pyarrow==25.0.1
matplotlib==3.10.7
requests==2.33.1
exactextract==0.3.0
```
