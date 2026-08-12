# CLIMATE MASTER v1 - Q1 Readiness Assessment

## 1. Upstream dataset integrity
VERIFIED: DATASET MASTER v1 remains certified and all run-1 deterministic hashes match.

## 2. Climate source selection
VERIFIED: CHIRPS v3 FINAL is selected as primary precipitation because PISCO did not pass reproducible official raster-access audit.

## 3. Precipitation provenance
VERIFIED: CHC CHIRPS v3 documentation and monthly LATAM GeoTIFF index were accessed and archived. SOURCE: https://www.chc.ucsb.edu/data/chirps3

## 4. Temperature provenance
VERIFIED: CHC CHIRTS-ERA5 documentation and monthly Tmax/Tmin GeoTIFF indexes were accessed and archived. SOURCE: https://www.chc.ucsb.edu/data/chirts-era5

## 5. District geometry provenance
UNRESOLVED: The required official IDEP district boundary service timed out from this environment. No substitute geometry was used.

## 6. Spatial aggregation methodology
FUTURE_PHASE: Fractional area-weighted extraction using exactextract/rasterio will be executed only after official IDEP geometries are acquired.

## 7. Temporal coverage
VERIFIED: Official CHC listings contain the requested CHIRPS and CHIRTS monthly windows. Extraction was not run.

## 8. WMO 1991-2020 climate normals
FUTURE_PHASE: Not constructed because the boundary blocker prevents district-level extraction.

## 9. Climate anomalies
FUTURE_PHASE: Not constructed.

## 10. Spatial coverage and pixel support
FUTURE_PHASE: Not constructed.

## 11. PISCO-CHIRPS product sensitivity
UNRESOLVED: PISCO rasters were not reproducibly acquired, so concordance was not available.

## 12. 2017 and 2023 diagnostic events
FUTURE_PHASE: Not constructed.

## 13. Agricultural-mask sensitivity
SENSITIVITY_ONLY: MIDAGRI page was inspected, but the 2024 mask was not used as primary exposure and no sensitivity extraction was run.

## 14. Independent extraction verification
FUTURE_PHASE: Not run.

## 15. Deterministic reproducibility
FUTURE_PHASE: Not run for climate outputs because no official boundary snapshot was available.

## 16. Remaining limitations
BLOCKING: IDEP official boundary access failure.
NONBLOCKING: PISCO and station validation endpoints remain unresolved.

## 17. Recommendation
HOLD_FOR_CORRECTION
