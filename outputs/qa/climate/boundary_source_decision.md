# Boundary Source Decision - CLIMATE MASTER v1.1

## Hierarchy outcome

- IDEP FeatureServer/5 filtered, POST, and returnIdsOnly strategies were attempted from this environment and failed to return geometry.
- IDEP MapServer/5 filtered and returnIdsOnly strategies were attempted from this environment and failed to return geometry.
- Alternate IDEP LIMITESTT MapServer/3 metadata was attempted and failed to return metadata.
- INEI SDMR catalog and download routes were audited. The GeoJSON route returned server error during access checks, and the Shapefile ZIP downloaded but the retrieved official archive contained 0 Piura features and 0 target-panel UBIGEO matches.
- INEI IDE official cartographic layer download `Distrito.rar` was accepted as the official fallback source.

## Selected source

- Institution: INEI
- Product: Distrito
- Interface: OFFICIAL_RAR_GPKG_DOWNLOAD
- Source URL: https://ide.inei.gob.pe/files/Distrito.rar
- Catalog URL: https://ide.inei.gob.pe/
- Vintage: 2023
- Source CRS: EPSG:4326
- Processed CRS: EPSG:4326
- National source features: 1890
- Piura features in source: 65
- Analytical Piura panel features: 55
- Panel UBIGEO match: 55 / 55

## Acceptance checks

The accepted derivative is restricted by official department attributes and panel UBIGEO, not by a hand-drawn bounding box. It contains polygon geometries, identified CRS, 6-character UBIGEO keys, no duplicate UBIGEO, no empty geometries, no unresolved invalid geometries, and a 55/55 match against the certified agricultural panel.

## Limitations

Only one official boundary dataset passed the Piura 55/55 acceptance gate, so cross-source geometry comparison is not available. This is documented as a provenance limitation, not silently ignored. Failed higher-priority attempts are preserved in `boundary_source_recovery.csv`; preserved v1 failure evidence remains in `outputs/qa/climate/history/v1_failed_boundary_attempt/`.

IDEP failed attempts counted in v1.1/historical evidence: 9.
