# Manuscript Climate Provenance

CLIMATE MASTER v1 first failed because the official IDEP district FeatureServer could not be reached from the execution environment. That failure was preserved without deleting or rewriting the original audit outputs. CLIMATE MASTER v1.1 then executed an official boundary recovery hierarchy: IDEP FeatureServer, IDEP MapServer, alternate IDEP LIMITESTT, INEI SDMR GeoJSON/Shapefile, and finally the official INEI IDE cartographic layer download.

The accepted official primary boundary source is INEI IDE `Distrito.rar`, vintage 2023, distributed as a RAR archive containing `DISTRITO.gpkg`. The processed derivative is `data/processed/climate/district_boundaries_piura.geojson`, EPSG:4326, restricted by official department attributes and certified panel UBIGEO. It matched 55/55 target districts. INEI SDMR was audited but the retrieved Shapefile archive did not contain Piura districts, so cross-source concordance was not available.

Precipitation exposures use CHIRPS v3 FINAL monthly Latin America GeoTIFFs from the Climate Hazards Center for 1981-01 through 2024-12. PISCO remains `NOT_REPRODUCIBLY_ACCESSIBLE` because no stable official no-credential monthly raster endpoint was verified. Temperature exposures use CHIRTS-ERA5 monthly Tmax and Tmin GeoTIFFs from 1991-01 through 2024-12. Daily temperature and phenological-window search were not run.

District monthly climate values were calculated over whole-district polygons using deterministic fractional overlap and geodesic cell-intersection areas. The normal period is WMO 1991-2020. Anomalies are simple departures from district-by-calendar-month normals, with standardized anomalies only where reference-period standard deviations are positive.

The main agricultural climate period, 2016-01 to 2023-12, contains 5280 district-month records. The agricultural overlap period, 2015-08 to 2024-12, contains 6215 records. Minimum spatial support was 0.999995. The climate tables linked completely to 1701 agricultural outcome rows. Independent extraction checks passed 36 of 36 checks, and two-run reproducibility of core scientific outputs was True.
