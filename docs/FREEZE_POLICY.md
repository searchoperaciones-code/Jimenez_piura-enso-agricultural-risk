# Freeze Policy

`DATASET_MASTER_v1 = IMMUTABLE`

`CLIMATE_MASTER_v1.1 = IMMUTABLE`

`PHENOLOGY_MASTER_v1_EVIDENCE_ARCHITECTURE = IMMUTABLE`

The scientific reference commit is:

`38e957e3c01fbffef242c386099b0a219d83ca70`

The scientific reference tag is:

`v0.2.0-data-climate-freeze`

Future work must not modify frozen outputs unless a formal scientific reopening occurs.

The DATASET MASTER v1 and CLIMATE MASTER v1.1 scientific reference commit and tag above remain unchanged. The PHENOLOGY MASTER v1 evidence/architecture freeze is defined by the canonical file `data/processed/phenology/phenology_windows_frozen.csv`, the freeze certificate `outputs/phenology/PHENOLOGY_MASTER_V1_FREEZE.md`, and the QA report/manifest under `outputs/phenology/qa/`.

`data/processed/phenology/phenology_windows_frozen.csv` is immutable unless PHENOLOGY MASTER is formally reopened and versioned.

If a contradiction is found later:

1. Document it.
2. Stop downstream interpretation affected by it.
3. Explicitly reopen the corresponding phase.
4. Create a new version.
5. Never silently overwrite frozen evidence.

Next planned phase:

`CLIMATE_EXPOSURE_BUILD`

Climate Exposure Build must use the frozen PHENOLOGY MASTER v1 evidence/architecture and must not modify the frozen DATASET MASTER v1, CLIMATE MASTER v1.1, or PHENOLOGY MASTER v1 evidence/architecture artifacts.
