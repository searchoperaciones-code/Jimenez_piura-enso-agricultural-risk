# Freeze Policy

`DATASET_MASTER_v1 = IMMUTABLE`

`CLIMATE_MASTER_v1.1 = IMMUTABLE`

The scientific reference commit is:

`38e957e3c01fbffef242c386099b0a219d83ca70`

The scientific reference tag is:

`v0.2.0-data-climate-freeze`

Future work must not modify frozen outputs unless a formal scientific reopening occurs.

If a contradiction is found later:

1. Document it.
2. Stop downstream interpretation affected by it.
3. Explicitly reopen the corresponding phase.
4. Create a new version.
5. Never silently overwrite frozen evidence.

Next planned phase:

`PHENOLOGY_MASTER_v1`

PHENOLOGY MASTER must be implemented separately and must not modify the frozen DATASET MASTER v1 or CLIMATE MASTER v1.1 evidence.
