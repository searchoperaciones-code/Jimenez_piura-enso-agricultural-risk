# Manuscript Climate Provenance Draft

CLIMATE MASTER v1 source audit selected CHIRPS v3 FINAL as the primary precipitation product, using the official Climate Hazards Center CHIRPS v3 documentation and monthly Latin America GeoTIFF repository. The CHC documentation describes CHIRPS v3 as a 0.05 degree, quasi-global land precipitation dataset from 1981 to near-present, with final and preliminary products distinguished. This phase selected final monthly GeoTIFFs only.

For temperature, the source audit selected CHIRTS-ERA5 monthly Tmax and Tmin from the official Climate Hazards Center CHIRTS-ERA5 documentation and repository. The intended normal period is 1991-2020, with agricultural overlap products planned for 2015-08 through 2024-12 and the main agricultural panel period 2016-01 through 2023-12.

The required official district geometry source is the IDEP district boundary layer. During this execution, the IDEP FeatureServer/MapServer endpoints timed out at both HTTP and socket levels, so no official boundary snapshot was acquired. No unofficial or third-party geometry was substituted, and no district-level climate extraction, normals, anomalies, or product-sensitivity results are reported here.
