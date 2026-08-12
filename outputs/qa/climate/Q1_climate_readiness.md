# CLIMATE MASTER v1.1 - Q1 Climate Readiness

Final recommendation: GO_TO_PHENOLOGY_PHASE

## Boundary recovery

PASS. The previous IDEP access failure remains preserved under `outputs/qa/climate/history/v1_failed_boundary_attempt/`. CLIMATE MASTER v1.1 exhausted live IDEP delivery checks available from this environment, audited INEI SDMR, and selected the official INEI IDE `Distrito.rar` boundary snapshot, vintage 2023. The processed analytical derivative matches 55/55 certified panel UBIGEOs.

## Climate products

- Precipitation: CHIRPS_V3_FINAL monthly LATAM GeoTIFFs, 1981-01 to 2024-12.
- Temperature: CHIRTS-ERA5 monthly Tmax/Tmin GeoTIFFs, 1991-01 to 2024-12.
- PISCO: NOT_REPRODUCIBLY_ACCESSIBLE from a stable official no-credential raster endpoint.

## Spatial extraction

Whole-district polygon exposure was calculated using deterministic fractional overlap with geodesic cell-intersection areas. Centroids, nearest cells, and simple unweighted means were not used.

## Gates

- Main district-month rows: 5280
- Overlap rows: 6215
- Normal completeness: PASS
- Minimum spatial coverage: 0.999995
- Panel linkage: 1701 / 1701
- Independent extraction: 36 / 36
- Two-run reproducibility: PASS
- Temporal leakage: NONE
- Unauthorized modelling: NO

## Limitations

Only one official boundary dataset passed the 55/55 Piura panel acceptance gate, so cross-source geometry comparison and boundary climate sensitivity are not available. Coastal and low-pixel-support districts are documented for modelling-stage sensitivity review, but no district was removed or imputed.
