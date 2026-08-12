# Manuscript Data Provenance Summary

The DATASET MASTER v1 phase uses the GORE Piura monthly agricultural campaign dataset as the primary agricultural source. The raw agricultural file contains 124514 rows, 96 crop codes, and 55 districts, with monthly coverage from 2015-08 through 2024-12.

The analytical crop set is defined by five exact source crop codes: arroz, mango, limon sutil, platanos y bananas, and maiz amarillo duro. Monthly observations are aggregated to annual UBIGEO x crop x year groups for the 2016-2023 main panel. Annual yield is constructed as annual production divided by annual harvested area, using the sum of monthly production and harvested-area records. The physical unit of PRODUCCION is not explicitly certified in the supplied dictionary, so YIELD_RAW is retained with unit UNRESOLVED.

Annual farm-gate price is computed as a production-weighted mean of monthly PRECIO_CHACRA over months with positive observed production and positive observed price. The MIDAGRI 2024 agricultural physical-land table is linked by UBIGEO to quantify spatial land coverage, not to assert currently cultivated or reassignable area. The official ICEN monthly text file is cleaned and audited for 2016-2023 coverage, but it is not merged into district-level agricultural outcomes in this phase.

The source metadata distinguish zero from blank: zero denotes absence of activity, while blank denotes data not registered. DATASET MASTER v1 preserves this distinction during ingestion and annual aggregation. No causal, climate-raster, scenario, portfolio-risk, or crop-allocation claims are made in this phase.
